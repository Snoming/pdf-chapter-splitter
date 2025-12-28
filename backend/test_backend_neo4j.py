#!/usr/bin/env python3
"""
测试后端服务的Neo4j连接
使用后端现有的Neo4j连接基础设施
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.neo4j_database import neo4j_db
from loguru import logger
import traceback

def test_backend_neo4j_connection():
    """测试后端服务的Neo4j连接"""
    print("=== 后端Neo4j连接测试 ===")
    print("使用后端现有的Neo4j连接基础设施")
    print("=" * 50)
    
    try:
        print("1. 获取全局Neo4j实例")
        print(f"   实例类型: {type(neo4j_db)}")
        
        print("2. 获取Neo4j会话...")
        for session in neo4j_db.get_session():
            print("3. 执行查询...")
            query = "RETURN 'Hello from Backend!' AS greeting"
            result = session.run(query)
            
            print("4. 处理查询结果...")
            for record in result:
                print(f"   查询结果: {record['greeting']}")
        
        print("5. 会话已关闭")
        
        print("=" * 50)
        print("🎉 后端Neo4j连接测试成功！")
        return True
        
    except Exception as e:
        print("=" * 50)
        print("❌ 后端Neo4j连接测试失败！")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        print("\n详细错误堆栈:")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = test_backend_neo4j_connection()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
