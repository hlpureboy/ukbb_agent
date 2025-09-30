#!/usr/bin/env python3
"""
Application Configuration Management
支持环境变量和配置文件的设置管理
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from enum import Enum

class Environment(str, Enum):
    """环境枚举"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class Language(str, Enum):
    """支持的语言"""
    CHINESE = "zh"
    ENGLISH = "en"

class APISettings(BaseSettings):
    """API相关配置"""
    # GLM API配置
    glm_api_key: str = Field(..., env="GLM_API_KEY", description="智谱AI API密钥")
    glm_model: str = Field("glm-4.5-Flash", env="GLM_MODEL", description="GLM模型名称")
    glm_base_url: Optional[str] = Field(None, env="GLM_BASE_URL", description="GLM API基础URL")
    
    # API限制配置
    rate_limit_per_minute: int = Field(60, env="RATE_LIMIT_PER_MINUTE", description="每分钟请求限制")
    max_tokens: int = Field(4096, env="MAX_TOKENS", description="最大token数")
    temperature: float = Field(0.4, env="TEMPERATURE", description="生成温度")
    
    model_config = {"env_prefix": "API_", "env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False, "extra": "ignore"}

class DatabaseSettings(BaseSettings):
    """数据库配置"""
    db_path: str = Field("./ukb_datadict.db", env="DB_PATH", description="数据库文件路径")
    connection_timeout: int = Field(30, env="DB_CONNECTION_TIMEOUT", description="数据库连接超时")
    query_timeout: int = Field(60, env="DB_QUERY_TIMEOUT", description="查询超时")
    
    model_config = {"env_prefix": "DB_", "env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False, "extra": "ignore"}

class ServerSettings(BaseSettings):
    """服务器配置"""
    host: str = Field("0.0.0.0", env="HOST", description="服务器主机")
    port: int = Field(8000, env="PORT", description="服务器端口")
    reload: bool = Field(True, env="RELOAD", description="是否启用热重载")
    workers: int = Field(1, env="WORKERS", description="工作进程数")
    
    # CORS配置
    cors_origins: str = Field("*", env="CORS_ORIGINS", description="允许的源")
    cors_credentials: bool = Field(True, env="CORS_CREDENTIALS", description="是否允许凭据")
    
    model_config = {"env_prefix": "SERVER_", "env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False, "extra": "ignore"}

class LoggingSettings(BaseSettings):
    """日志配置"""
    level: str = Field("INFO", env="LOG_LEVEL", description="日志级别")
    format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="日志格式"
    )
    file_path: Optional[str] = Field(None, env="LOG_FILE", description="日志文件路径")
    max_size: int = Field(10 * 1024 * 1024, env="LOG_MAX_SIZE", description="日志文件最大大小")
    backup_count: int = Field(5, env="LOG_BACKUP_COUNT", description="备份日志文件数量")
    
    model_config = {"env_prefix": "LOG_", "env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False, "extra": "ignore"}

class AppSettings(BaseSettings):
    """应用主配置"""
    app_name: str = Field("MiniSearch", env="APP_NAME", description="应用名称")
    app_version: str = Field("0.2.0", env="APP_VERSION", description="应用版本")
    environment: Environment = Field(Environment.DEVELOPMENT, env="ENVIRONMENT", description="运行环境")
    debug: bool = Field(True, env="DEBUG", description="是否启用调试模式")
    
    # 默认语言配置
    default_language: Language = Field(Language.CHINESE, env="DEFAULT_LANGUAGE", description="默认语言")
    
    # 功能开关
    enable_rate_limiting: bool = Field(True, env="ENABLE_RATE_LIMITING", description="是否启用限流")
    enable_metrics: bool = Field(False, env="ENABLE_METRICS", description="是否启用指标收集")
    
    # 子配置
    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False, "extra": "ignore"}

# 全局配置实例
def get_settings() -> AppSettings:
    """获取应用配置"""
    return AppSettings()

# 创建全局配置对象
settings = get_settings()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 静态资源目录
STATIC_DIR = PROJECT_ROOT / "public"

# 配置validation
def validate_config():
    """验证配置"""
    errors = []
    
    # 验证API密钥
    if not settings.api.glm_api_key or settings.api.glm_api_key == "your-api-key-here":
        errors.append("GLM_API_KEY is required and must be set to a valid API key")
    
    # 验证数据库文件
    db_path = Path(settings.database.db_path)
    if not db_path.exists():
        errors.append(f"Database file not found: {db_path}")
    
    # 验证静态文件目录
    if not STATIC_DIR.exists():
        errors.append(f"Static directory not found: {STATIC_DIR}")
    
    if errors:
        raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))

if __name__ == "__main__":
    # 配置测试
    print(f"App Name: {settings.app_name}")
    print(f"Environment: {settings.environment}")
    print(f"Debug Mode: {settings.debug}")
    print(f"API Model: {settings.api.glm_model}")
    print(f"Database Path: {settings.database.db_path}")
    print(f"Server: {settings.server.host}:{settings.server.port}")
    
    try:
        validate_config()
        print("✅ Configuration validation passed")
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")