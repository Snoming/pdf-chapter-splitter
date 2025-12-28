"""
配置管理模块
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 服务配置 - WSL环境适配
    HOST: str = "0.0.0.0"  # 绑定到所有接口，支持WSL访问
    PORT: int = 8080       # 使用8080端口与docker-compose配置一致
    DEBUG: bool = False
    
    # 文件处理配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "./uploads"
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
    
    # 任务处理配置
    MAX_CONCURRENT_TASKS: int = 5
    TASK_TIMEOUT: int = 300  # 5分钟
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/backend.log"
    
    # 大模型API配置
    LLM_API_KEY: str = ""
    LLM_API_ENDPOINT: str = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    LLM_MODEL_NAME: str = "qwen-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    LLM_RETRY_COUNT: int = 3
    LLM_TIMEOUT: int = 30  # 秒
    
    # Neo4j图数据库配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()