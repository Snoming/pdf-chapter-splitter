#!/usr/bin/env python3
"""
简单的Neo4j连接测试脚本
"""

from neo4j import GraphDatabase

def main():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "password"
    
    try:
        print("正在连接到Neo4j...")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            result = session.run("RETURN 'Hello' AS greeting")
            print(f"成功！结果: {result.single()['greeting']}")
        
        driver.close()
        print("测试完成")
    except Exception as e:
        print(f"失败: {e}")

if __name__ == "__main__":
    main()
