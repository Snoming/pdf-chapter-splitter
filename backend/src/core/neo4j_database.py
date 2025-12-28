"""
Neo4j数据库配置和管理模块
负责Neo4j驱动的初始化、会话管理和连接池配置
"""

from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j import Record, Result
from typing import Optional, AsyncGenerator, Generator, Any
from loguru import logger

from .config import settings


class Neo4jDatabase:
    """Neo4j数据库管理类"""
    
    def __init__(self):
        """初始化Neo4j驱动"""
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
        self.database = settings.NEO4J_DATABASE
        self._driver = None
        self._async_driver = None
        
    def init_driver(self) -> None:
        """初始化同步驱动"""
        try:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,  # 连接最大生命周期（秒）
                max_connection_pool_size=50,     # 连接池最大大小
                connection_acquisition_timeout=60  # 连接获取超时（秒）
            )
            
            # 验证连接
            self.verify_connection()
            logger.info("Neo4j同步驱动初始化成功")
        except Exception as e:
            logger.error(f"Neo4j同步驱动初始化失败: {str(e)}")
            raise
    
    def init_async_driver(self) -> None:
        """初始化异步驱动"""
        try:
            self._async_driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            logger.info("Neo4j异步驱动初始化成功")
        except Exception as e:
            logger.error(f"Neo4j异步驱动初始化失败: {str(e)}")
            raise
    
    def verify_connection(self) -> None:
        """验证数据库连接是否正常"""
        try:
            with self._driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j连接验证成功")
        except Exception as e:
            logger.error(f"Neo4j连接验证失败: {str(e)}")
            raise
    
    def get_session(self) -> Generator:
        """获取同步会话"""
        if not self._driver:
            self.init_driver()
        
        with self._driver.session(database=self.database) as session:
            yield session
    
    async def get_async_session(self) -> AsyncGenerator:
        """获取异步会话"""
        if not self._async_driver:
            self.init_async_driver()
        
        async with self._async_driver.session(database=self.database) as session:
            yield session
    
    def close(self) -> None:
        """关闭同步驱动"""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j同步驱动已关闭")
    
    async def async_close(self) -> None:
        """关闭异步驱动"""
        if self._async_driver:
            await self._async_driver.close()
            logger.info("Neo4j异步驱动已关闭")


# 创建全局Neo4j数据库实例
neo4j_db = Neo4jDatabase()