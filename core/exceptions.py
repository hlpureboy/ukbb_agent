#!/usr/bin/env python3
"""
Custom Exceptions
自定义异常类
"""

from typing import Optional, Any, Dict

class UKBSearchException(Exception):
    """基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class ConfigurationError(UKBSearchException):
    """配置错误"""
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "CONFIG_ERROR", details)

class DatabaseError(UKBSearchException):
    """数据库错误"""
    
    def __init__(self, message: str, query: str = None, details: Dict[str, Any] = None):
        details = details or {}
        if query:
            details["query"] = query
        super().__init__(message, "DATABASE_ERROR", details)

class APIError(UKBSearchException):
    """API调用错误"""
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None, details: Dict[str, Any] = None):
        details = details or {}
        if api_name:
            details["api_name"] = api_name
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, "API_ERROR", details)

class ValidationError(UKBSearchException):
    """输入验证错误"""
    
    def __init__(self, message: str, field: str = None, value: Any = None, details: Dict[str, Any] = None):
        details = details or {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, "VALIDATION_ERROR", details)

class FieldNotFoundError(UKBSearchException):
    """字段未找到错误"""
    
    def __init__(self, field_id: int, details: Dict[str, Any] = None):
        message = f"Field {field_id} not found in database"
        details = details or {}
        details["field_id"] = field_id
        super().__init__(message, "FIELD_NOT_FOUND", details)

class EncodingNotFoundError(UKBSearchException):
    """编码未找到错误"""
    
    def __init__(self, encoding_id: int, details: Dict[str, Any] = None):
        message = f"Encoding {encoding_id} not found in database"
        details = details or {}
        details["encoding_id"] = encoding_id
        super().__init__(message, "ENCODING_NOT_FOUND", details)

class CategoryNotFoundError(UKBSearchException):
    """分类未找到错误"""
    
    def __init__(self, category_name: str, details: Dict[str, Any] = None):
        message = f"Category '{category_name}' not found in database"
        details = details or {}
        details["category_name"] = category_name
        super().__init__(message, "CATEGORY_NOT_FOUND", details)

class RateLimitError(UKBSearchException):
    """请求频率限制错误"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, details: Dict[str, Any] = None):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)

class ToolExecutionError(UKBSearchException):
    """工具执行错误"""
    
    def __init__(self, tool_name: str, message: str, details: Dict[str, Any] = None):
        details = details or {}
        details["tool_name"] = tool_name
        super().__init__(f"Tool '{tool_name}' execution failed: {message}", "TOOL_EXECUTION_ERROR", details)

class PromptError(UKBSearchException):
    """Prompt相关错误"""
    
    def __init__(self, message: str, template_name: str = None, details: Dict[str, Any] = None):
        details = details or {}
        if template_name:
            details["template_name"] = template_name
        super().__init__(message, "PROMPT_ERROR", details)

# 异常处理装饰器
def handle_exceptions(default_return=None, log_error=True):
    """异常处理装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except UKBSearchException:
                # 重新抛出自定义异常
                raise
            except Exception as e:
                # 将其他异常包装为自定义异常
                if log_error:
                    from core.logger import logger
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
                
                if default_return is not None:
                    return default_return
                
                raise UKBSearchException(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    "UNEXPECTED_ERROR",
                    {"function": func.__name__, "original_error": str(e)}
                )
        return wrapper
    return decorator

# 异常转换工具
def convert_error_to_response(error: UKBSearchException, language: str = "zh") -> Dict[str, Any]:
    """将异常转换为API响应格式"""
    from config.prompts import get_error_message, Language
    
    lang = Language.CHINESE if language == "zh" else Language.ENGLISH
    
    # 根据错误类型获取用户友好的消息
    if isinstance(error, FieldNotFoundError):
        user_message = get_error_message("field_not_found", lang, field_id=error.details.get("field_id"))
    elif isinstance(error, EncodingNotFoundError):
        user_message = get_error_message("encoding_not_found", lang, encoding_id=error.details.get("encoding_id"))
    elif isinstance(error, CategoryNotFoundError):
        user_message = get_error_message("category_not_found", lang, category=error.details.get("category_name"))
    elif isinstance(error, RateLimitError):
        user_message = get_error_message("rate_limit_exceeded", lang)
    else:
        user_message = get_error_message("api_error", lang, error=error.message)
    
    return {
        "ok": False,
        "error": error.error_code,
        "message": user_message,
        "details": error.details if isinstance(error, UKBSearchException) else {}
    }

if __name__ == "__main__":
    # 测试异常系统
    try:
        raise FieldNotFoundError(123, {"context": "test"})
    except UKBSearchException as e:
        print(f"Error Code: {e.error_code}")
        print(f"Message: {e.message}")
        print(f"Details: {e.details}")
        
        # 测试异常转换
        response = convert_error_to_response(e, "zh")
        print(f"API Response: {response}")
    
    # 测试装饰器
    @handle_exceptions(default_return="default")
    def test_function():
        raise ValueError("Test error")
    
    result = test_function()
    print(f"Decorated function result: {result}")