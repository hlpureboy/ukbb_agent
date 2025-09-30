#!/usr/bin/env python3
"""
Logging Configuration
统一的日志配置管理
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from config.settings import settings

class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # 添加颜色
        color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # 格式化消息
        return super().format(record)

def setup_logger(
    name: str = "ukbb_search",
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_colors: bool = True
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径
        enable_console: 是否启用控制台输出
        enable_colors: 是否启用颜色（仅控制台）
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 设置日志级别
    log_level = level or settings.logging.level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 日志格式
    log_format = settings.logging.format
    
    # 控制台处理器
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        if enable_colors and sys.stdout.isatty():
            formatter = ColoredFormatter(log_format)
        else:
            formatter = logging.Formatter(log_format)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    file_path = log_file or settings.logging.file_path
    if file_path:
        log_file_path = Path(file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用RotatingFileHandler进行日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=settings.logging.max_size,
            backupCount=settings.logging.backup_count,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "ukbb_search") -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger(name)

# 创建默认日志记录器
logger = setup_logger()

# 请求日志记录器
request_logger = setup_logger(
    name="ukbb_search.requests", 
    log_file="logs/requests.log" if settings.logging.file_path else None
)

# API调用日志记录器  
api_logger = setup_logger(
    name="ukbb_search.api",
    log_file="logs/api.log" if settings.logging.file_path else None
)

# 数据库操作日志记录器
db_logger = setup_logger(
    name="ukbb_search.database",
    log_file="logs/database.log" if settings.logging.file_path else None
)

def log_request(method: str, path: str, status_code: int, duration: float, user_ip: str = "unknown"):
    """记录HTTP请求"""
    request_logger.info(
        f"{method} {path} - {status_code} - {duration:.3f}s - {user_ip}"
    )

def log_api_call(model: str, tokens_used: int, duration: float, success: bool = True):
    """记录API调用"""
    status = "SUCCESS" if success else "FAILED"
    api_logger.info(
        f"GLM API Call - Model: {model} - Tokens: {tokens_used} - Duration: {duration:.3f}s - Status: {status}"
    )

def log_db_query(query_type: str, duration: float, success: bool = True, error: str = None):
    """记录数据库查询"""
    status = "SUCCESS" if success else "FAILED"
    log_msg = f"DB Query - Type: {query_type} - Duration: {duration:.3f}s - Status: {status}"
    if error:
        log_msg += f" - Error: {error}"
    
    if success:
        db_logger.info(log_msg)
    else:
        db_logger.error(log_msg)

class LoggerMixin:
    """日志记录器混入类"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志记录器"""
        return get_logger(f"ukbb_search.{self.__class__.__name__.lower()}")

if __name__ == "__main__":
    # 测试日志系统
    test_logger = setup_logger("test", level="DEBUG")
    
    test_logger.debug("这是一条调试消息")
    test_logger.info("这是一条信息消息")
    test_logger.warning("这是一条警告消息")
    test_logger.error("这是一条错误消息")
    test_logger.critical("这是一条严重错误消息")
    
    # 测试专用日志记录器
    log_request("GET", "/api/search", 200, 0.156, "127.0.0.1")
    log_api_call("glm-4.5-Flash", 1234, 2.5)
    log_db_query("search_fields", 0.045)