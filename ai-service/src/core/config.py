"""
配置管理模块
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # 文件处理配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    TEMP_DIR: str = "./temp"
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]
    
    # 章节识别配置
    MIN_CHAPTER_PAGES: int = 1
    MAX_CHAPTERS: int = 50
    CHAPTER_PATTERNS: List[str] = [
        r"第[一二三四五六七八九十\d]+章",
        r"Chapter\s+\d+",
        r"第\d+章",
        r"CHAPTER\s+\d+",
        r"第[一二三四五六七八九十]+章",
    ]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/ai-service.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()