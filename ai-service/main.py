"""
PDF章节拆分器 - AI服务
基于FastAPI的PDF章节识别服务
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.api.routes import router
from src.core.config import settings


# 配置日志
logging.basicConfig(level=logging.INFO)
logger.add("logs/ai-service.log", rotation="1 day", retention="7 days")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("AI服务启动中...")
    
    # 创建必要的目录
    os.makedirs("logs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    
    yield
    
    # 关闭时执行
    logger.info("AI服务关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="PDF章节拆分器 - AI服务",
    description="基于FastAPI的PDF章节识别服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "service": "PDF章节拆分器 - AI服务",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )