"""
数据库配置和初始化
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

# 数据库URL配置
DATABASE_URL = "sqlite:///./knowledge_graph.db"

# 创建SQLAlchemy引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite特定配置，允许在同一线程中多次连接
)

# 创建SessionLocal类，用于创建数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类，用于定义数据库模型
Base = declarative_base()


def get_db():
    """
    数据库会话依赖项
    
    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库，创建所有表
    """
    try:
        # 导入所有模型，确保它们被注册到Base.metadata
        from ..models import database_models
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化成功，所有表已创建")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise
