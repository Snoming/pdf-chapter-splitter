#!/usr/bin/env python3
"""
测试Neo4j登录脚本
使用最新的密码设置
"""

from neo4j import GraphDatabase
import traceback

# 获取当前环境变量中的密码
from dotenv import load_dotenv
import os

# 加载.env文件
load_dotenv()

# 连接参数
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password")
database = os.getenv("NEO4J_DATABASE", "neo4j")

def test_neo4j_login():
    """测试Neo4j登录"""
    print("=== Neo4j登录测试 ===")
    print(f"连接地址: {uri}")
    print(f"用户名: {user}")
    print(f"密码: {'*' * len(password)}")
    print(f"数据库: {database}")
    print("=" * 50)
    
    try:
        # 创建驱动实例
        print("1. 创建驱动实例...")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 验证连接
        print("2. 验证连接...")
        with driver.session(database=database) as session:
            result = session.run("RETURN 'Hello, Neo4j!' AS greeting")
            for record in result:
                print(f"3. 登录成功！消息: {record['greeting']}")
        
        # 关闭驱动
        driver.close()
        print("4. 连接已关闭")
        
        print("=" * 50)
        print("🎉 Neo4j登录测试成功！")
        return True
        
    except Exception as e:
        print("=" * 50)
        print("❌ Neo4j登录测试失败！")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {e}")
        print("\n详细错误堆栈:")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = test_neo4j_login()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
