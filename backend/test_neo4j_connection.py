#!/usr/bin/env python3
"""
测试Neo4j数据库连接脚本
用于验证后端服务是否能成功连接到Neo4j数据库
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.neo4j_database import neo4j_db
from loguru import logger


def test_neo4j_connection():
    """测试Neo4j数据库连接"""
    try:
        logger.info("开始测试Neo4j数据库连接...")
        
        # 触发Neo4j连接初始化
        for session in neo4j_db.get_session():
            result = session.run("RETURN 'Hello, Neo4j!' AS greeting")
            for record in result:
                logger.info(f"Neo4j连接成功！消息: {record['greeting']}")
        
        logger.info("Neo4j连接测试完成，连接正常！")
        return True
    except Exception as e:
        logger.error(f"Neo4j连接测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_neo4j_connection()
    sys.exit(0 if success else 1)
