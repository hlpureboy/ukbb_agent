#!/usr/bin/env python3
"""
GLM API Client
智谱AI客户端封装
"""

import json
import time
from typing import List, Dict, Any, Optional

from zai import ZhipuAiClient

from config.settings import settings
from config.prompts import DEFAULT_SYSTEM_PROMPT, detect_language, Language
from core.logger import api_logger, LoggerMixin
from core.exceptions import APIError, RateLimitError, handle_exceptions

class GLMClient(LoggerMixin):
    """智谱AI客户端封装"""
    
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or settings.api.glm_api_key
        self.model = model or settings.api.glm_model
        self.base_url = base_url or settings.api.glm_base_url
        
        # 验证API密钥
        if not self.api_key or self.api_key == "your-api-key-here":
            raise APIError("GLM API key is not configured properly")
        
        # 初始化客户端
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            
        self.client = ZhipuAiClient(**client_kwargs)
        
        # API配置
        self.max_tokens = settings.api.max_tokens
        self.temperature = settings.api.temperature
        self.rate_limit = settings.api.rate_limit_per_minute
        
        # 请求计数（简单的内存限流）
        self._requests = []
        
        self.logger.info(f"GLM Client initialized - Model: {self.model}")
    
    def _check_rate_limit(self):
        """检查请求频率限制"""
        if not settings.enable_rate_limiting:
            return
        
        now = time.time()
        # 清理一分钟前的请求记录
        self._requests = [req_time for req_time in self._requests if now - req_time < 60]
        
        if len(self._requests) >= self.rate_limit:
            raise RateLimitError(
                f"Rate limit exceeded. Maximum {self.rate_limit} requests per minute.",
                retry_after=60
            )
        
        self._requests.append(now)
    
    @handle_exceptions()
    def build_messages(self, user_query: str, system_prompt: str = None, language: Language = None) -> List[Dict[str, str]]:
        """构建对话消息"""
        # 自动检测语言
        if language is None:
            language = detect_language(user_query)
        
        # 使用对应语言的系统prompt
        if system_prompt is None:
            system_prompt = DEFAULT_SYSTEM_PROMPT.get(language)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        self.logger.debug(f"Built messages - Language: {language} - User query length: {len(user_query)}")
        return messages
    
    @handle_exceptions()
    def chat_completion(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """执行聊天完成请求"""
        # 检查请求频率
        self._check_rate_limit()
        
        start_time = time.time()
        
        try:
            # 构建请求参数
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "thinking": {"type": "false"}  # 关闭动态思考以提升性能
            }
            
            if tools:
                params["tools"] = tools
            
            # 发送请求
            response = self.client.chat.completions.create(**params)
            
            duration = time.time() - start_time
            
            # 记录成功的API调用
            usage = getattr(response, 'usage', None)
            tokens_used = usage.total_tokens if usage else 0
            
            api_logger.info(
                f"GLM API Success - Model: {self.model} - Tokens: {tokens_used} - Duration: {duration:.3f}s"
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # 记录失败的API调用
            api_logger.error(
                f"GLM API Failed - Model: {self.model} - Duration: {duration:.3f}s - Error: {str(e)}"
            )
            
            # 处理特定的API错误
            if "rate limit" in str(e).lower():
                raise RateLimitError("API rate limit exceeded")
            elif "invalid api key" in str(e).lower():
                raise APIError("Invalid API key", "GLM")
            elif "model not found" in str(e).lower():
                raise APIError(f"Model '{self.model}' not found", "GLM")
            else:
                raise APIError(f"GLM API request failed: {str(e)}", "GLM")
    
    @handle_exceptions()
    def single_turn_chat(self, user_query: str, system_prompt: str = None, language: Language = None) -> str:
        """单轮对话（无工具调用）"""
        messages = self.build_messages(user_query, system_prompt, language)
        response = self.chat_completion(messages)
        
        choice = response.choices[0]
        return choice.message.content or ""
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "rate_limit": self.rate_limit,
            "api_configured": bool(self.api_key and self.api_key != "your-api-key-here")
        }

# 工厂函数
def create_glm_client(api_key: str = None, model: str = None) -> GLMClient:
    """创建GLM客户端实例"""
    return GLMClient(api_key=api_key, model=model)

# 全局客户端实例（延迟初始化）
_global_client = None

def get_glm_client() -> GLMClient:
    """获取全局GLM客户端实例"""
    global _global_client
    if _global_client is None:
        _global_client = create_glm_client()
    return _global_client

if __name__ == "__main__":
    # 测试GLM客户端
    try:
        client = create_glm_client()
        print(f"Client info: {client.get_model_info()}")
        
        # 测试简单对话
        response = client.single_turn_chat("Hello, how are you?")
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error: {e}")