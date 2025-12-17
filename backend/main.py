"""
PDF章节拆分器 - 统一后端服务
基于FastAPI的完整后端服务，集成文件管理、章节识别、PDF拆分等功能
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from src.api.routes import router
from src.core.config import settings


# 配置日志
logging.basicConfig(level=logging.INFO)
logger.add("logs/backend.log", rotation="1 day", retention="7 days")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("PDF章节拆分器后端服务启动中...")
    
    # 创建必要的目录
    os.makedirs("logs", exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    
    yield
    
    # 关闭时执行
    logger.info("PDF章节拆分器后端服务关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="PDF章节拆分器 - 后端服务",
    description="基于FastAPI的PDF章节拆分完整后端服务",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置 - WSL环境适配
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
        # WSL环境下的地址
        "http://172.17.0.1:3000",
        "http://172.18.0.1:3000",
        "http://172.19.0.1:3000",
        "http://172.20.0.1:3000",
        # 允许所有本地地址用于开发
        "http://10.0.0.0:3000",
        "http://192.168.0.0:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（用于文件下载）
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files")

# 注册API路由
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "service": "PDF章节拆分器 - 后端服务",
        "version": "1.0.0",
        "status": "healthy",
        "description": "统一的FastAPI后端服务，提供文件管理、章节识别、PDF拆分等功能"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "pdf-chapter-splitter-backend",
        "version": "1.0.0",
        "upload_dir": settings.UPLOAD_DIR,
        "temp_dir": settings.TEMP_DIR,
        "max_file_size": settings.MAX_FILE_SIZE
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