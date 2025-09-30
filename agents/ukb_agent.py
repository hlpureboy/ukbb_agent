#!/usr/bin/env python3
"""
UKB Agent - Intelligent assistant for UK Biobank data dictionary
智能UK Biobank数据字典助手
"""

import json
import time
from typing import Any, Dict, List, Optional

from api.client import get_glm_client
from config.settings import settings
from config.prompts import DEFAULT_SYSTEM_PROMPT, detect_language, Language
from core.logger import logger, LoggerMixin
from core.exceptions import (
    APIError, ToolExecutionError, UKBSearchException, 
    handle_exceptions, convert_error_to_response
)
from ukb_tools import (
    explain_field_by_id,
    search_fields_by_keyword,
    get_category_fields,
    get_encoding_values,
    recommend_related_fields,
    get_all_categories,
    get_recommended_fields,
)

class UKBAgent(LoggerMixin):
    """UK Biobank智能助手"""
    
    def __init__(self):
        self.client = get_glm_client()
        self.max_iterations = 6  # 防止无限循环
        
        self.logger.info("UKB Agent initialized")

    @property
    def tools_schema(self) -> List[Dict[str, Any]]:
        """工具清单（GLM Function Call 规范）"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "explain_field_by_id",
                    "description": "根据 field_id 获取字段完整解释信息",
                    "parameters": {
                        "type": "object",
                        "properties": {"field_id": {"type": "integer"}},
                        "required": ["field_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_fields_by_keyword",
                    "description": "按关键字搜索字段",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keyword": {"type": "string"},
                            "limit": {"type": "integer", "default": 20},
                        },
                        "required": ["keyword"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_category_fields",
                    "description": "获取分类下字段",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category_name": {"type": "string"},
                            "limit": {"type": "integer", "default": 50},
                        },
                        "required": ["category_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_encoding_values",
                    "description": "获取编码值含义",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "encoding_id": {"type": "integer"},
                            "limit": {"type": "integer", "default": 50},
                        },
                        "required": ["encoding_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "recommend_related_fields",
                    "description": "推荐与指定字段相关的字段",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "field_id": {"type": "integer"},
                            "limit": {"type": "integer", "default": 10},
                        },
                        "required": ["field_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_all_categories",
                    "description": "获取所有分类列表",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recommended_fields",
                    "description": "获取推荐字段",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category_name": {"type": ["string", "null"]},
                            "limit": {"type": "integer", "default": 20},
                        },
                    },
                },
            },
        ]
    
    @property
    def tools_dispatch(self) -> Dict[str, callable]:
        """工具分发表"""
        return {
            "explain_field_by_id": explain_field_by_id,
            "search_fields_by_keyword": search_fields_by_keyword,
            "get_category_fields": get_category_fields,
            "get_encoding_values": get_encoding_values,
            "recommend_related_fields": recommend_related_fields,
            "get_all_categories": get_all_categories,
            "get_recommended_fields": get_recommended_fields,
        }
    
    @handle_exceptions()
    def _execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """执行工具调用"""
        handler = self.tools_dispatch.get(tool_name)
        if not handler:
            raise ToolExecutionError(tool_name, f"Tool '{tool_name}' not found")
        
        try:
            # 处理参数兼容性
            import inspect
            sig = inspect.signature(handler)
            valid_args = {k: v for k, v in tool_args.items() if k in sig.parameters}
            
            result = handler(**valid_args)
            self.logger.debug(f"Tool '{tool_name}' executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Tool '{tool_name}' execution failed: {e}")
            raise ToolExecutionError(tool_name, str(e))

    @handle_exceptions()
    def run(self, user_query: str, system_prompt: str = None, language: Language = None) -> str:
        """运行智能助手"""
        # 自动检测语言
        if language is None:
            language = detect_language(user_query)
        
        # 构建初始消息
        if system_prompt is None:
            system_prompt = DEFAULT_SYSTEM_PROMPT.get(language)
        
        messages = self.client.build_messages(user_query, system_prompt, language)
        
        start_time = time.time()
        self.logger.info(f"Starting agent run - Language: {language} - Query: {user_query[:100]}...")
        
        # 多轮对话循环
        for iteration in range(self.max_iterations):
            try:
                # 发送请求到GLM
                response = self.client.chat_completion(messages, self.tools_schema)
                choice = response.choices[0]
                message = choice.message
                
                # 检查是否有工具调用
                if not getattr(message, "tool_calls", None):
                    # 无工具调用，返回最终结果
                    duration = time.time() - start_time
                    self.logger.info(f"Agent completed - Duration: {duration:.3f}s - Iterations: {iteration + 1}")
                    return message.content or ""
                
                # 执行工具调用
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments or {}
                    
                    # 解析参数
                    if isinstance(tool_args, str):
                        tool_args = json.loads(tool_args)
                    
                    # 执行工具
                    try:
                        tool_result = self._execute_tool(tool_name, tool_args)
                    except Exception as e:
                        tool_result = json.dumps({
                            "error": f"{type(e).__name__}: {str(e)}"
                        }, ensure_ascii=False)
                    
                    # 添加工具调用结果到对话历史
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result
                    })
                
                # 添加助手消息到历史
                messages.append({
                    "role": "assistant", 
                    "content": message.content or ""
                })
                
            except Exception as e:
                self.logger.error(f"Error in agent iteration {iteration + 1}: {e}")
                raise
        
        # 达到最大迭代次数
        duration = time.time() - start_time
        self.logger.warning(f"Agent reached max iterations - Duration: {duration:.3f}s")
        return "对话轮次过多，请简化您的问题重新提问。" if language == Language.CHINESE else "Too many conversation rounds, please simplify your question."

# 全局代理实例
_global_agent = None

def get_agent() -> UKBAgent:
    """获取全局代理实例"""
    global _global_agent
    if _global_agent is None:
        _global_agent = UKBAgent()
    return _global_agent

def run_agent(user_query: str, system_prompt: str = None, language: Language = None) -> str:
    """运行代理的便捷函数（向后兼容）"""
    agent = get_agent()
    return agent.run(user_query, system_prompt, language)

def run_agent_safe(user_query: str, system_prompt: str = None, language: Language = None) -> Dict[str, Any]:
    """安全运行代理，返回标准化响应"""
    try:
        # 自动检测语言
        if language is None:
            language = detect_language(user_query)
        
        result = run_agent(user_query, system_prompt, language)
        
        return {
            "ok": True,
            "query": user_query,
            "answer": result,
            "language": language.value
        }
        
    except UKBSearchException as e:
        return convert_error_to_response(e, language.value if language else "zh")
    except Exception as e:
        logger.error(f"Unexpected error in run_agent_safe: {e}", exc_info=True)
        return {
            "ok": False,
            "error": "UNEXPECTED_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {"error": str(e)}
        }

if __name__ == "__main__":
    # 测试代理
    agent = UKBAgent()
    
    test_queries = [
        "请解释字段31的含义",
        "What are the depression related fields?",
        "心血管相关的字段有哪些？"
    ]
    
    for query in test_queries:
        print(f"\n=== Testing: {query} ===")
        try:
            result = agent.run(query)
            print(f"Result: {result[:200]}...")
        except Exception as e:
            print(f"Error: {e}")