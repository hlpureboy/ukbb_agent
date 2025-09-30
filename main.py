#!/usr/bin/env python3
"""
MiniSearch FastAPI Application
UK Biobank数据字典智能搜索系统
"""

import time
from typing import Any, Dict, Optional
from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

# 应用配置和组件
from config.settings import settings, validate_config, PROJECT_ROOT, STATIC_DIR
from config.prompts import detect_language, Language
from agents.ukb_agent import run_agent_safe
from core.logger import setup_logger, request_logger, log_request
from core.exceptions import UKBSearchException, convert_error_to_response

# 验证配置
try:
    validate_config()
except ValueError as e:
    print(f"❌ Configuration validation failed: {e}")
    exit(1)

# 设置应用日志
logger = setup_logger("main")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="UK Biobank数据字典智能搜索系统 - Intelligent search system for UK Biobank data dictionary",
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# 安全中间件
if settings.environment.value == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=settings.server.cors_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # 记录请求日志
        client_ip = request.client.host if request.client else "unknown"
        log_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration=duration,
            user_ip=client_ip
        )
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Request failed: {request.method} {request.url.path} - {str(e)}")
        
        # 返回标准错误响应
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": "INTERNAL_ERROR",
                "message": "Internal server error occurred"
            }
        )

# 静态文件服务
if STATIC_DIR.exists():
    app.mount("/public", StaticFiles(directory=str(STATIC_DIR)), name="public")
    logger.info(f"Static files mounted from: {STATIC_DIR}")
else:
    logger.warning(f"Static directory not found: {STATIC_DIR}")

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment.value,
        "timestamp": time.time()
    }

# 应用信息端点
@app.get("/info")
async def app_info():
    """应用信息端点"""
    from api.client import get_glm_client
    
    try:
        client = get_glm_client()
        model_info = client.get_model_info()
    except Exception as e:
        model_info = {"error": str(e)}
    
    return {
        "app": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment.value,
            "debug": settings.debug,
        },
        "api": model_info,
        "features": {
            "rate_limiting": settings.enable_rate_limiting,
            "metrics": settings.enable_metrics,
        }
    }

# 根路径
@app.get("/")
async def root():
    """返回前端页面"""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        raise HTTPException(status_code=404, detail="Frontend not found")

# 主要搜索API端点
@app.get("/api/search")
async def api_search(
    q: str = Query(..., min_length=1, max_length=1000, description="查询词"),
    sys_prompt: Optional[str] = Query(None, max_length=2000, description="自定义系统提示词"),
    lang: Optional[str] = Query(None, regex="^(zh|en)$", description="语言设置 (zh/en)")
) -> Dict[str, Any]:
    """
    智能搜索API
    
    Args:
        q: 查询词
        sys_prompt: 可选的自定义系统提示词
        lang: 可选的语言设置
        
    Returns:
        搜索结果
    """
    try:
        # 语言处理
        language = None
        if lang:
            language = Language.CHINESE if lang == "zh" else Language.ENGLISH
        
        # 调用智能代理
        result = run_agent_safe(
            user_query=q,
            system_prompt=sys_prompt,
            language=language
        )
        
        logger.info(f"Search completed - Query: {q[:50]}... - Success: {result.get('ok', False)}")
        return result
        
    except UKBSearchException as e:
        logger.warning(f"Search failed with known error: {e}")
        return convert_error_to_response(e, lang or "zh")
    
    except Exception as e:
        logger.error(f"Unexpected error in search API: {e}", exc_info=True)
        return {
            "ok": False,
            "error": "SEARCH_ERROR",
            "message": "搜索服务暂时不可用，请稍后重试。" if (lang or "zh") == "zh" else "Search service temporarily unavailable, please try again later.",
            "details": {"error": str(e)} if settings.debug else {}
        }

# 工具测试端点（仅调试模式）
if settings.debug:
    @app.get("/api/tools/test")
    async def test_tools():
        """测试工具可用性"""
        from ukb_tools import UKBTools
        
        try:
            tools = UKBTools()
            
            # 测试基本功能
            test_results = {
                "database_connection": False,
                "field_query": False,
                "search": False,
                "categories": False
            }
            
            # 测试数据库连接
            try:
                conn = tools._get_connection()
                conn.close()
                test_results["database_connection"] = True
            except Exception as e:
                logger.error(f"Database test failed: {e}")
            
            # 测试字段查询
            try:
                result = tools.explain_field_by_id(31)
                test_results["field_query"] = "error" not in result
            except Exception as e:
                logger.error(f"Field query test failed: {e}")
            
            # 测试搜索
            try:
                result = tools.search_fields_by_keyword("heart", 5)
                test_results["search"] = len(result) > 0
            except Exception as e:
                logger.error(f"Search test failed: {e}")
            
            # 测试分类
            try:
                result = tools.get_all_categories()
                test_results["categories"] = len(result) > 0
            except Exception as e:
                logger.error(f"Categories test failed: {e}")
            
            return {
                "ok": True,
                "tests": test_results,
                "overall": all(test_results.values())
            }
            
        except Exception as e:
            return {
                "ok": False,
                "error": str(e)
            }

def create_app() -> FastAPI:
    """应用工厂函数"""
    return app

def main():
    """主函数"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment.value}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload and settings.debug,
        workers=settings.server.workers if not settings.debug else 1,
        log_level=settings.logging.level.lower(),
        access_log=False  # 使用自定义请求日志
    )

if __name__ == "__main__":
    main()
