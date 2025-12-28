from neo4j import GraphDatabase

# 连接配置
uri = "bolt://localhost:7687"
username = "neo4j"
password = "neo4j@123456"

try:
    # 创建驱动
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # 测试连接
    with driver.session() as session:
        result = session.run("RETURN 'Hello, Neo4j!' AS greeting")
        greeting = result.single()[0]
        print(f"Neo4j连接成功: {greeting}")
    
    # 关闭驱动
    driver.close()
except Exception as e:
    print(f"Neo4j连接失败: {str(e)}")
    import traceback
    traceback.print_exc()