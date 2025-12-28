#!/usr/bin/env python3
"""
详细的Neo4j连接测试脚本
用于捕获完整的错误信息
"""

from neo4j import GraphDatabase
import traceback

# 连接参数
uri = "bolt://localhost:7687"
user = "neo4j"
password = "password"
database = "neo4j"

def test_detailed_connection():
    """详细测试Neo4j连接"""
    print("=== Neo4j连接测试 ===")
    print(f"连接地址: {uri}")
    print(f"用户名: {user}")
    print(f"密码: {'*' * len(password)}")
    print(f"数据库: {database}")
    print("=" * 50)
    
    try:
        print("1. 创建驱动实例...")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        print("2. 验证驱动创建成功")
        print(f"   驱动类型: {type(driver)}")
        
        print("3. 开始会话...")
        with driver.session(database=database) as session:
            print("4. 执行查询...")
            query = "RETURN 'Hello, Neo4j!' AS greeting"
            result = session.run(query)
            
            print("5. 处理查询结果...")
            for record in result:
                print(f"   查询结果: {record['greeting']}")
        
        print("6. 关闭驱动...")
        driver.close()
        
        print("=" * 50)
        print("🎉 连接测试成功！")
        return True
        
    except Exception as e:
        print("=" * 50)
        print("❌ 连接测试失败！")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {e}")
        print("\n详细错误堆栈:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_detailed_connection()
