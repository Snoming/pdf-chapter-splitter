"""
知识图谱服务模块
负责构建和管理知识图谱
"""

import uuid
from typing import List, Dict, Any, Optional
from loguru import logger
from datetime import datetime

from ..models.schemas import (
    KnowledgeGraph, GraphNode, GraphEdge, 
    BookInfo, ChapterInfo, SectionInfo, KnowledgePoint
)
from ..core.neo4j_database import neo4j_db
from .llm_service import llm_service


class KnowledgeGraphService:
    """知识图谱服务类"""
    
    def __init__(self):
        pass
    
    async def build_knowledge_graph(
        self, 
        chapters: List[ChapterInfo], 
        book_info: Optional[BookInfo] = None,
        use_llm: bool = True,
        save_to_db: bool = True
    ) -> KnowledgeGraph:
        """
        构建知识图谱
        
        Args:
            chapters: 章节列表
            book_info: 书籍信息
            use_llm: 是否使用大模型增强
            save_to_db: 是否保存到数据库
            
        Returns:
            知识图谱对象
        """
        try:
            logger.info(f"开始构建知识图谱，章节数量: {len(chapters)}")
            
            # 创建书籍节点
            nodes: List[GraphNode] = []
            edges: List[GraphEdge] = []
            
            # 生成书籍ID
            book_id = book_info.id if book_info and book_info.id else str(uuid.uuid4())
            
            # 创建书籍节点
            book_node = GraphNode(
                id=book_id,
                type="book",
                content=book_info.title if book_info else "未命名书籍",
                metadata={
                    "author": book_info.author if book_info else None,
                    "description": book_info.description if book_info else None,
                    "total_pages": book_info.total_pages if book_info else None
                }
            )
            nodes.append(book_node)
            
            # 收集所有知识点，用于后续关系抽取
            all_knowledge_points: List[KnowledgePoint] = []
            
            # 构建章节、节、知识点节点和边
            for chapter in chapters:
                # 确保章节有ID
                if not chapter.id:
                    chapter.id = str(uuid.uuid4())
                
                # 创建章节节点
                chapter_node = GraphNode(
                    id=chapter.id,
                    type="chapter",
                    content=chapter.title,
                    metadata={
                        "start_page": chapter.start_page,
                        "end_page": chapter.end_page,
                        "page_count": chapter.page_count
                    }
                )
                nodes.append(chapter_node)
                
                # 创建书籍到章节的边
                book_to_chapter_edge = GraphEdge(
                    source_id=book_id,
                    target_id=chapter.id,
                    relation_type="contains",
                    weight=1.0
                )
                edges.append(book_to_chapter_edge)
                
                # 处理节
                for section in chapter.sections:
                    # 确保节有ID
                    if not section.id:
                        section.id = str(uuid.uuid4())
                    
                    # 创建节节点
                    section_node = GraphNode(
                        id=section.id,
                        type="section",
                        content=section.title,
                        metadata={
                            "start_page": section.start_page,
                            "end_page": section.end_page,
                            "page_count": section.page_count
                        }
                    )
                    nodes.append(section_node)
                    
                    # 创建章节到节的边
                    chapter_to_section_edge = GraphEdge(
                        source_id=chapter.id,
                        target_id=section.id,
                        relation_type="contains",
                        weight=1.0
                    )
                    edges.append(chapter_to_section_edge)
                    
                    # 处理知识点
                    for knowledge_point in section.knowledge_points:
                        # 确保知识点有ID
                        if not knowledge_point.id:
                            knowledge_point.id = str(uuid.uuid4())
                        
                        # 创建知识点节点
                        kp_node = GraphNode(
                            id=knowledge_point.id,
                            type="knowledge",
                            content=knowledge_point.title,
                            metadata={
                                "content": knowledge_point.content,
                                "start_page": knowledge_point.start_page,
                                "end_page": knowledge_point.end_page,
                                "page_count": knowledge_point.page_count
                            }
                        )
                        nodes.append(kp_node)
                        
                        # 创建节到知识点的边
                        section_to_kp_edge = GraphEdge(
                            source_id=section.id,
                            target_id=knowledge_point.id,
                            relation_type="contains",
                            weight=1.0
                        )
                        edges.append(section_to_kp_edge)
                        
                        # 添加到知识点列表
                        all_knowledge_points.append(knowledge_point)
            
            # 如果启用大模型且有知识点，提取关联关系
            if use_llm and all_knowledge_points:
                # 使用大模型提取知识点间的关联关系
                extracted_edges = await llm_service.extract_relations(all_knowledge_points)
                
                # 添加知识点间的关联边
                for edge_data in extracted_edges:
                    source_id = edge_data.get("source_id")
                    target_id = edge_data.get("target_id")
                    relation_type = edge_data.get("relation_type", "related_to")
                    weight = edge_data.get("weight", 1.0)
                    
                    # 检查源节点和目标节点是否存在
                    source_exists = any(node.id == source_id for node in nodes)
                    target_exists = any(node.id == target_id for node in nodes)
                    
                    if source_exists and target_exists:
                        # 检查边是否已存在
                        edge_exists = any(
                            edge.source_id == source_id and edge.target_id == target_id
                            for edge in edges
                        )
                        
                        if not edge_exists:
                            kp_relation_edge = GraphEdge(
                                source_id=source_id,
                                target_id=target_id,
                                relation_type=relation_type,
                                weight=weight
                            )
                            edges.append(kp_relation_edge)
            
            # 创建知识图谱
            knowledge_graph = KnowledgeGraph(
                book_id=book_id,
                nodes=nodes,
                edges=edges
            )
            
            # 输出构建的节点信息
            logger.info(f"知识图谱构建完成，初始节点数: {len(nodes)}, 边数: {len(edges)}")
            
            # 按类型统计节点
            node_type_counts = {}
            for node in nodes:
                node_type_counts[node.type] = node_type_counts.get(node.type, 0) + 1
            logger.info(f"节点类型分布: {node_type_counts}")
            
            # 输出每种类型的示例节点
            for node_type, count in node_type_counts.items():
                example_nodes = [node for node in nodes if node.type == node_type][:3]  # 每个类型输出前3个示例
                for i, example in enumerate(example_nodes):
                    logger.info(f"{node_type}节点示例 {i+1}/{count}: ID={example.id}, 内容='{example.content[:50]}...', 元数据={example.metadata}")
            
            # 如果启用大模型，增强知识图谱
            if use_llm:
                try:
                    # 转换为字典格式进行增强
                    graph_dict = {
                        "nodes": [node.model_dump() for node in nodes],
                        "edges": [edge.model_dump() for edge in edges]
                    }
                    
                    # 使用大模型增强知识图谱
                    enhanced_graph_dict = await llm_service.enhance_knowledge_graph(graph_dict)
                    
                    # 确保enhanced_graph_dict是字典类型
                    if isinstance(enhanced_graph_dict, dict):
                        # 获取增强后的节点和边，并确保它们是列表类型
                        enhanced_nodes_data = enhanced_graph_dict.get("nodes", [])
                        enhanced_edges_data = enhanced_graph_dict.get("edges", [])
                        
                        if isinstance(enhanced_nodes_data, list) and isinstance(enhanced_edges_data, list):
                            # 转换回模型对象，仅处理有效的节点和边数据
                            enhanced_nodes = []
                            for node_data in enhanced_nodes_data:
                                if isinstance(node_data, dict):
                                    try:
                                        enhanced_nodes.append(GraphNode(**node_data))
                                    except Exception as e:
                                        logger.warning(f"无效的节点数据，跳过: {str(e)}")
                                        continue
                            
                            enhanced_edges = []
                            for edge_data in enhanced_edges_data:
                                if isinstance(edge_data, dict):
                                    try:
                                        enhanced_edges.append(GraphEdge(**edge_data))
                                    except Exception as e:
                                        logger.warning(f"无效的边数据，跳过: {str(e)}")
                                        continue
                            
                            # 更新知识图谱
                            knowledge_graph.nodes = enhanced_nodes
                            knowledge_graph.edges = enhanced_edges
                            
                            # 输出增强后的节点信息
                            logger.info(f"知识图谱增强完成，增强后节点数: {len(enhanced_nodes)}, 边数: {len(enhanced_edges)}")
                            
                            # 按类型统计增强后的节点
                            enhanced_node_type_counts = {}
                            for node in enhanced_nodes:
                                enhanced_node_type_counts[node.type] = enhanced_node_type_counts.get(node.type, 0) + 1
                            logger.info(f"增强后节点类型分布: {enhanced_node_type_counts}")
                except Exception as e:
                    logger.error(f"大模型增强知识图谱失败: {str(e)}")
                    # 增强失败时，保留原始图谱
                    pass
            
            logger.info(f"知识图谱最终构建完成，节点数: {len(knowledge_graph.nodes)}, 边数: {len(knowledge_graph.edges)}")
            
            # 保存知识图谱到数据库（如果启用）
            if save_to_db:
                try:
                    self.save_graph(knowledge_graph)
                    logger.info(f"知识图谱保存到数据库成功")
                except Exception as e:
                    logger.warning(f"知识图谱保存到数据库失败: {str(e)}")
                    # 保存失败时，仍返回构建好的知识图谱
            
            return knowledge_graph
            
        except Exception as e:
            logger.error(f"构建知识图谱失败: {str(e)}")
            raise
    
    async def update_knowledge_graph(
        self, 
        graph: KnowledgeGraph, 
        new_chapters: List[ChapterInfo],
        use_llm: bool = True
    ) -> KnowledgeGraph:
        """
        更新知识图谱
        
        Args:
            graph: 原知识图谱
            new_chapters: 新的章节数据
            use_llm: 是否使用大模型增强
            
        Returns:
            更新后的知识图谱
        """
        try:
            logger.info(f"开始更新知识图谱，当前节点数: {len(graph.nodes)}")
            
            # 获取现有节点和边的ID集合
            existing_node_ids = set(node.id for node in graph.nodes)
            existing_edge_ids = set((edge.source_id, edge.target_id, edge.relation_type) for edge in graph.edges)
            
            # 收集所有现有知识点
            existing_kps = {node.id: node for node in graph.nodes if node.type == "knowledge"}
            
            # 构建新的章节、节、知识点节点和边
            new_nodes = []
            new_edges = []
            new_knowledge_points = []
            
            # 遍历新章节数据
            for chapter in new_chapters:
                # 确保章节有ID
                if not chapter.id:
                    chapter.id = str(uuid.uuid4())
                
                # 如果章节节点不存在，创建新节点
                if chapter.id not in existing_node_ids:
                    chapter_node = GraphNode(
                        id=chapter.id,
                        type="chapter",
                        content=chapter.title,
                        metadata={
                            "start_page": chapter.start_page,
                            "end_page": chapter.end_page,
                            "page_count": chapter.page_count
                        }
                    )
                    new_nodes.append(chapter_node)
                    existing_node_ids.add(chapter.id)
                
                # 创建章节到书籍的边
                book_to_chapter_edge_key = (graph.book_id, chapter.id, "contains")
                if book_to_chapter_edge_key not in existing_edge_ids:
                    new_edges.append(GraphEdge(
                        source_id=graph.book_id,
                        target_id=chapter.id,
                        relation_type="contains",
                        weight=1.0
                    ))
                    existing_edge_ids.add(book_to_chapter_edge_key)
                
                # 处理节
                for section in chapter.sections:
                    # 确保节有ID
                    if not section.id:
                        section.id = str(uuid.uuid4())
                    
                    # 如果节节点不存在，创建新节点
                    if section.id not in existing_node_ids:
                        section_node = GraphNode(
                            id=section.id,
                            type="section",
                            content=section.title,
                            metadata={
                                "start_page": section.start_page,
                                "end_page": section.end_page,
                                "page_count": section.page_count
                            }
                        )
                        new_nodes.append(section_node)
                        existing_node_ids.add(section.id)
                    
                    # 创建章节到节的边
                    chapter_to_section_edge_key = (chapter.id, section.id, "contains")
                    if chapter_to_section_edge_key not in existing_edge_ids:
                        new_edges.append(GraphEdge(
                            source_id=chapter.id,
                            target_id=section.id,
                            relation_type="contains",
                            weight=1.0
                        ))
                        existing_edge_ids.add(chapter_to_section_edge_key)
                    
                    # 处理知识点
                    for knowledge_point in section.knowledge_points:
                        # 确保知识点有ID
                        if not knowledge_point.id:
                            knowledge_point.id = str(uuid.uuid4())
                        
                        # 如果知识点节点不存在，创建新节点
                        if knowledge_point.id not in existing_node_ids:
                            kp_node = GraphNode(
                                id=knowledge_point.id,
                                type="knowledge",
                                content=knowledge_point.title,
                                metadata={
                                    "content": knowledge_point.content,
                                    "start_page": knowledge_point.start_page,
                                    "end_page": knowledge_point.end_page,
                                    "page_count": knowledge_point.page_count
                                }
                            )
                            new_nodes.append(kp_node)
                            existing_node_ids.add(knowledge_point.id)
                            new_knowledge_points.append(knowledge_point)
                        
                        # 创建节到知识点的边
                        section_to_kp_edge_key = (section.id, knowledge_point.id, "contains")
                        if section_to_kp_edge_key not in existing_edge_ids:
                            new_edges.append(GraphEdge(
                                source_id=section.id,
                                target_id=knowledge_point.id,
                                relation_type="contains",
                                weight=1.0
                            ))
                            existing_edge_ids.add(section_to_kp_edge_key)
            
            # 如果有新知识点，使用大模型提取与现有知识点的关联关系
            if use_llm and new_knowledge_points and existing_kps:
                # 合并新旧知识点
                all_kps = list(existing_kps.values()) + new_knowledge_points
                
                # 提取关联关系
                extracted_edges = await llm_service.extract_relations(all_kps)
                
                # 添加新的关联边
                for edge_data in extracted_edges:
                    source_id = edge_data.get("source_id")
                    target_id = edge_data.get("target_id")
                    relation_type = edge_data.get("relation_type", "related_to")
                    weight = edge_data.get("weight", 1.0)
                    
                    edge_key = (source_id, target_id, relation_type)
                    if edge_key not in existing_edge_ids:
                        # 检查源节点和目标节点是否存在
                        if source_id in existing_node_ids and target_id in existing_node_ids:
                            new_edges.append(GraphEdge(
                                source_id=source_id,
                                target_id=target_id,
                                relation_type=relation_type,
                                weight=weight
                            ))
                            existing_edge_ids.add(edge_key)
            
            # 更新知识图谱
            updated_graph = KnowledgeGraph(
                book_id=graph.book_id,
                nodes=graph.nodes + new_nodes,
                edges=graph.edges + new_edges
            )
            
            # 输出更新后的节点信息
            logger.info(f"知识图谱更新完成，新增节点数: {len(new_nodes)}, 新增边数: {len(new_edges)}, 更新后总节点数: {len(updated_graph.nodes)}, 总边数: {len(updated_graph.edges)}")
            
            # 按类型统计更新后的节点
            updated_node_type_counts = {}
            for node in updated_graph.nodes:
                updated_node_type_counts[node.type] = updated_node_type_counts.get(node.type, 0) + 1
            logger.info(f"更新后节点类型分布: {updated_node_type_counts}")
            
            # 输出每种类型的示例节点
            for node_type, count in updated_node_type_counts.items():
                example_nodes = [node for node in updated_graph.nodes if node.type == node_type][:3]  # 每个类型输出前3个示例
                for i, example in enumerate(example_nodes):
                    logger.info(f"{node_type}节点示例 {i+1}/{count}: ID={example.id}, 内容='{example.content[:50]}...', 元数据={example.metadata}")
            
            # 如果启用大模型，增强更新后的知识图谱
            if use_llm:
                try:
                    # 转换为字典格式进行增强
                    graph_dict = {
                        "nodes": [node.model_dump() for node in updated_graph.nodes],
                        "edges": [edge.model_dump() for edge in updated_graph.edges]
                    }
                    
                    # 使用大模型增强知识图谱
                    enhanced_graph_dict = await llm_service.enhance_knowledge_graph(graph_dict)
                    
                    # 确保enhanced_graph_dict是字典类型
                    if isinstance(enhanced_graph_dict, dict):
                        # 获取增强后的节点和边，并确保它们是列表类型
                        enhanced_nodes_data = enhanced_graph_dict.get("nodes", [])
                        enhanced_edges_data = enhanced_graph_dict.get("edges", [])
                        
                        if isinstance(enhanced_nodes_data, list) and isinstance(enhanced_edges_data, list):
                            # 转换回模型对象，仅处理有效的节点和边数据
                            enhanced_nodes = []
                            for node_data in enhanced_nodes_data:
                                if isinstance(node_data, dict):
                                    try:
                                        enhanced_nodes.append(GraphNode(**node_data))
                                    except Exception as e:
                                        logger.warning(f"无效的节点数据，跳过: {str(e)}")
                                        continue
                            
                            enhanced_edges = []
                            for edge_data in enhanced_edges_data:
                                if isinstance(edge_data, dict):
                                    try:
                                        enhanced_edges.append(GraphEdge(**edge_data))
                                    except Exception as e:
                                        logger.warning(f"无效的边数据，跳过: {str(e)}")
                                        continue
                            
                            # 更新知识图谱
                            updated_graph.nodes = enhanced_nodes
                            updated_graph.edges = enhanced_edges
                            
                            # 输出增强后的节点信息
                            logger.info(f"知识图谱增强完成，增强后节点数: {len(enhanced_nodes)}, 边数: {len(enhanced_edges)}")
                            
                            # 按类型统计增强后的节点
                            enhanced_node_type_counts = {}
                            for node in enhanced_nodes:
                                enhanced_node_type_counts[node.type] = enhanced_node_type_counts.get(node.type, 0) + 1
                            logger.info(f"增强后节点类型分布: {enhanced_node_type_counts}")
                except Exception as e:
                    logger.error(f"大模型增强知识图谱失败: {str(e)}")
                    # 增强失败时，保留更新后的图谱
                    pass
            
            # 保存更新后的知识图谱到数据库
            self.save_graph(updated_graph)
            
            return updated_graph
            
        except Exception as e:
            logger.error(f"更新知识图谱失败: {str(e)}")
            raise
    
    def get_knowledge_points(
        self, 
        graph: KnowledgeGraph,
        node_type: Optional[str] = None
    ) -> List[GraphNode]:
        """
        获取知识图谱中的节点
        
        Args:
            graph: 知识图谱
            node_type: 节点类型过滤，可选值: book/chapter/section/knowledge
            
        Returns:
            节点列表
        """
        try:
            if node_type:
                return [node for node in graph.nodes if node.type == node_type]
            return graph.nodes
        except Exception as e:
            logger.error(f"获取节点失败: {str(e)}")
            return []
    
    def get_relations(
        self, 
        graph: KnowledgeGraph,
        relation_type: Optional[str] = None
    ) -> List[GraphEdge]:
        """
        获取知识图谱中的关系
        
        Args:
            graph: 知识图谱
            relation_type: 关系类型过滤
            
        Returns:
            关系列表
        """
        try:
            if relation_type:
                return [edge for edge in graph.edges if edge.relation_type == relation_type]
            return graph.edges
        except Exception as e:
            logger.error(f"获取关系失败: {str(e)}")
            return []
    
    def search_knowledge_points(
        self, 
        graph: KnowledgeGraph,
        keyword: str
    ) -> List[GraphNode]:
        """
        搜索知识点
        
        Args:
            graph: 知识图谱
            keyword: 搜索关键词
            
        Returns:
            匹配的知识点列表
        """
        try:
            keyword_lower = keyword.lower()
            return [
                node for node in graph.nodes 
                if node.type == "knowledge" 
                and (keyword_lower in node.content.lower() 
                     or keyword_lower in node.metadata.get("content", "").lower())
            ]
        except Exception as e:
            logger.error(f"搜索知识点失败: {str(e)}")
            return []
    
    def visualize_graph(self, graph: KnowledgeGraph) -> Dict[str, Any]:
        """
        生成优化的可视化数据
        
        Args:
            graph: 知识图谱
            
        Returns:
            优化的可视化数据字典，适合D3.js等可视化库
        """
        try:
            # 生成适合D3.js等可视化库的格式
            visualize_data = {
                "nodes": [],
                "links": [],
                "metadata": {
                    "total_nodes": len(graph.nodes),
                    "total_edges": len(graph.edges),
                    "node_types": {
                        "book": 0,
                        "chapter": 0,
                        "section": 0,
                        "knowledge": 0
                    },
                    "relation_types": {}
                }
            }
            
            # 节点类型样式映射
            node_styles = {
                "book": {
                    "color": "#2c3e50",
                    "size": 25,
                    "shape": "circle",
                    "level": 0
                },
                "chapter": {
                    "color": "#3498db",
                    "size": 20,
                    "shape": "circle",
                    "level": 1
                },
                "section": {
                    "color": "#27ae60",
                    "size": 15,
                    "shape": "circle",
                    "level": 2
                },
                "knowledge": {
                    "color": "#e74c3c",
                    "size": 12,
                    "shape": "circle",
                    "level": 3
                }
            }
            
            # 关系类型样式映射
            relation_styles = {
                "contains": {
                    "color": "#95a5a6",
                    "width": 2,
                    "dash": ""
                },
                "依赖": {
                    "color": "#3498db",
                    "width": 2,
                    "dash": ""
                },
                "包含": {
                    "color": "#27ae60",
                    "width": 2,
                    "dash": ""
                },
                "相似": {
                    "color": "#f39c12",
                    "width": 1.5,
                    "dash": "5,5"
                },
                "对比": {
                    "color": "#e74c3c",
                    "width": 1.5,
                    "dash": "3,3"
                },
                "因果": {
                    "color": "#9b59b6",
                    "width": 2,
                    "dash": ""
                },
                "递进": {
                    "color": "#1abc9c",
                    "width": 1.5,
                    "dash": "2,2"
                },
                "related_to": {
                    "color": "#bdc3c7",
                    "width": 1,
                    "dash": "8,3"
                }
            }
            
            # 统计节点类型和关系类型
            for node in graph.nodes:
                if node.type in visualize_data["metadata"]["node_types"]:
                    visualize_data["metadata"]["node_types"][node.type] += 1
            
            for edge in graph.edges:
                if edge.relation_type not in visualize_data["metadata"]["relation_types"]:
                    visualize_data["metadata"]["relation_types"][edge.relation_type] = 0
                visualize_data["metadata"]["relation_types"][edge.relation_type] += 1
            
            # 转换节点，添加样式信息
            for node in graph.nodes:
                node_style = node_styles.get(node.type, node_styles["knowledge"])
                
                # 计算节点大小，根据内容长度和类型进行调整
                content_length = len(node.content)
                base_size = node_style["size"]
                adjusted_size = min(max(base_size, base_size + (content_length - 10) * 0.5), 35)
                
                visualize_data["nodes"].append({
                    "id": node.id,
                    "label": node.content,
                    "type": node.type,
                    "metadata": node.metadata,
                    "style": {
                        "color": node_style["color"],
                        "size": adjusted_size,
                        "shape": node_style["shape"],
                        "level": node_style["level"]
                    },
                    "content_length": content_length,
                    "has_content": bool(node.metadata.get("content", ""))
                })
            
            # 转换边，添加样式信息
            for edge in graph.edges:
                edge_style = relation_styles.get(edge.relation_type, relation_styles["related_to"])
                
                # 根据权重调整边的宽度
                adjusted_width = edge_style["width"] * edge.weight
                
                visualize_data["links"].append({
                    "source": edge.source_id,
                    "target": edge.target_id,
                    "relation": edge.relation_type,
                    "weight": edge.weight,
                    "style": {
                        "color": edge_style["color"],
                        "width": adjusted_width,
                        "dash": edge_style["dash"]
                    },
                    "strength": edge.weight
                })
            
            return visualize_data
        except Exception as e:
            logger.error(f"生成可视化数据失败: {str(e)}")
            return {
                "nodes": [], 
                "links": [],
                "metadata": {
                    "total_nodes": 0,
                    "total_edges": 0,
                    "node_types": {},
                    "relation_types": {}
                }
            }
    
    def save_graph(self, graph: KnowledgeGraph) -> KnowledgeGraph:
        """
        保存知识图谱到Neo4j图数据库
        
        Args:
            graph: 知识图谱对象
            
        Returns:
            保存后的知识图谱
        """
        try:
            logger.info(f"开始保存知识图谱到Neo4j，书籍ID: {graph.book_id}")
            
            # 获取Neo4j会话
            for session in neo4j_db.get_session():
                # 使用事务批量保存数据
                with session.begin_transaction() as tx:
                    # 1. 删除现有图谱（如果存在）
                    tx.run("MATCH (b:Book {book_id: $book_id})-[r*0..]->(n) DELETE r, n", book_id=graph.book_id)
                    
                    # 2. 保存所有节点
                    node_map = {}
                    for node in graph.nodes:
                        # 根据节点类型创建不同的标签
                        if node.type == "book":
                            tx.run(
                                "CREATE (b:Book:GraphNode {id: $id, book_id: $book_id, content: $content, metadata: $metadata, created_at: $created_at, updated_at: $updated_at})",
                                id=node.id,
                                book_id=graph.book_id,
                                content=node.content,
                                metadata=node.metadata,
                                created_at=graph.created_at.isoformat(),
                                updated_at=graph.updated_at.isoformat()
                            )
                        elif node.type == "chapter":
                            tx.run(
                                "CREATE (c:Chapter:GraphNode {id: $id, content: $content, metadata: $metadata, created_at: $created_at, updated_at: $updated_at})",
                                id=node.id,
                                content=node.content,
                                metadata=node.metadata,
                                created_at=graph.created_at.isoformat(),
                                updated_at=graph.updated_at.isoformat()
                            )
                        elif node.type == "section":
                            tx.run(
                                "CREATE (s:Section:GraphNode {id: $id, content: $content, metadata: $metadata, created_at: $created_at, updated_at: $updated_at})",
                                id=node.id,
                                content=node.content,
                                metadata=node.metadata,
                                created_at=graph.created_at.isoformat(),
                                updated_at=graph.updated_at.isoformat()
                            )
                        elif node.type == "knowledge":
                            tx.run(
                                "CREATE (k:Knowledge:GraphNode {id: $id, content: $content, metadata: $metadata, created_at: $created_at, updated_at: $updated_at})",
                                id=node.id,
                                content=node.content,
                                metadata=node.metadata,
                                created_at=graph.created_at.isoformat(),
                                updated_at=graph.updated_at.isoformat()
                            )
                        
                        node_map[node.id] = node
                    
                    # 3. 保存所有边
                    for edge in graph.edges:
                        # 创建关系，使用关系类型作为关系标签
                        # 使用APOC库或动态创建关系的方式（这里使用参数化查询）
                        relation_type = edge.relation_type.upper()
                        query = f"""
                        MATCH (a:GraphNode {{id: $source_id}}), (b:GraphNode {{id: $target_id}}) 
                        CREATE (a)-[r:{relation_type} {{weight: $weight}}]->(b)
                        """
                        tx.run(
                            query,
                            source_id=edge.source_id,
                            target_id=edge.target_id,
                            weight=edge.weight
                        )
                    
                    # 4. 提交事务
                    tx.commit()
            
            logger.info(f"知识图谱保存到Neo4j成功，书籍ID: {graph.book_id}")
            return graph
        except Exception as e:
            logger.error(f"保存知识图谱到Neo4j失败: {str(e)}")
            raise
    
    def load_graph(self, book_id: str) -> Optional[KnowledgeGraph]:
        """
        从Neo4j图数据库加载知识图谱
        
        Args:
            book_id: 书籍ID
            
        Returns:
            知识图谱对象，如果不存在则返回None
        """
        try:
            logger.info(f"开始从Neo4j加载知识图谱，书籍ID: {book_id}")
            
            nodes = []
            edges = []
            created_at = datetime.now()
            updated_at = datetime.now()
            
            # 获取Neo4j会话
            for session in neo4j_db.get_session():
                # 查询书籍节点以获取时间信息
                book_result = session.run(
                    "MATCH (b:Book {book_id: $book_id}) RETURN b.created_at as created_at, b.updated_at as updated_at",
                    book_id=book_id
                )
                
                book_record = book_result.single()
                if not book_record:
                    logger.warning(f"未找到知识图谱，书籍ID: {book_id}")
                    return None
                
                # 解析时间信息
                created_at = datetime.fromisoformat(book_record["created_at"])
                updated_at = datetime.fromisoformat(book_record["updated_at"])
                
                # 查询所有相关节点
                node_results = session.run(
                    "MATCH (b:Book {book_id: $book_id})-[*0..]->(n:GraphNode) RETURN n.id as id, n.content as content, labels(n) as labels, n.metadata as metadata",
                    book_id=book_id
                )
                
                # 构建节点列表
                for record in node_results:
                    # 确定节点类型
                    node_type = "knowledge"  # 默认类型
                    if "Book" in record["labels"]:
                        node_type = "book"
                    elif "Chapter" in record["labels"]:
                        node_type = "chapter"
                    elif "Section" in record["labels"]:
                        node_type = "section"
                    
                    node = GraphNode(
                        id=record["id"],
                        type=node_type,
                        content=record["content"],
                        metadata=record["metadata"]
                    )
                    nodes.append(node)
                
                # 查询所有关系
                edge_results = session.run(
                    "MATCH (b:Book {book_id: $book_id})-[*0..]->(a:GraphNode)-[r]->(c:GraphNode) "
                    "RETURN a.id as source_id, c.id as target_id, type(r) as relation_type, r.weight as weight",
                    book_id=book_id
                )
                
                # 构建边列表
                for record in edge_results:
                    edge = GraphEdge(
                        source_id=record["source_id"],
                        target_id=record["target_id"],
                        relation_type=record["relation_type"].lower(),
                        weight=record["weight"] if record["weight"] is not None else 1.0
                    )
                    edges.append(edge)
            
            # 创建知识图谱对象
            graph = KnowledgeGraph(
                book_id=book_id,
                nodes=nodes,
                edges=edges,
                created_at=created_at,
                updated_at=updated_at
            )
            
            logger.info(f"从Neo4j加载知识图谱成功，书籍ID: {book_id}, 节点数: {len(nodes)}, 边数: {len(edges)}")
            return graph
        except Exception as e:
            logger.error(f"从Neo4j加载知识图谱失败: {str(e)}")
            return None
    
    def delete_graph(self, book_id: str) -> bool:
        """
        从Neo4j图数据库删除知识图谱
        
        Args:
            book_id: 书籍ID
            
        Returns:
            删除成功返回True，否则返回False
        """
        try:
            logger.info(f"开始从Neo4j删除知识图谱，书籍ID: {book_id}")
            
            # 获取Neo4j会话
            for session in neo4j_db.get_session():
                result = session.run(
                    "MATCH (b:Book {book_id: $book_id})-[r*0..]->(n) DELETE r, n RETURN count(n) as deleted_count",
                    book_id=book_id
                )
                
                record = result.single()
                if record and record["deleted_count"] > 0:
                    logger.info(f"从Neo4j删除知识图谱成功，书籍ID: {book_id}, 删除节点数: {record['deleted_count']}")
                    return True
                else:
                    logger.warning(f"未找到知识图谱，书籍ID: {book_id}")
                    return False
        except Exception as e:
            logger.error(f"从Neo4j删除知识图谱失败: {str(e)}")
            return False
    
    def list_graphs(self) -> List[Dict[str, Any]]:
        """
        列出Neo4j图数据库中所有知识图谱
        
        Returns:
            知识图谱列表，包含基本信息
        """
        try:
            logger.info("开始列出Neo4j中的所有知识图谱")
            
            graphs_info = []
            
            # 获取Neo4j会话
            for session in neo4j_db.get_session():
                # 查询所有书籍节点及其相关统计信息
                results = session.run(
                    "MATCH (b:Book) "
                    "OPTIONAL MATCH (b)-[*0..]->(n:GraphNode) "
                    "OPTIONAL MATCH (b)-[*0..]->(a:GraphNode)-[r]->(c:GraphNode) "
                    "RETURN b.book_id as book_id, b.created_at as created_at, b.updated_at as updated_at, "
                    "count(DISTINCT n) as node_count, count(DISTINCT r) as edge_count "
                    "GROUP BY b.book_id, b.created_at, b.updated_at"
                )
                
                # 构建结果列表
                for record in results:
                    graphs_info.append({
                        "book_id": record["book_id"],
                        "created_at": datetime.fromisoformat(record["created_at"]),
                        "updated_at": datetime.fromisoformat(record["updated_at"]),
                        "node_count": record["node_count"],
                        "edge_count": record["edge_count"]
                    })
            
            logger.info(f"成功列出Neo4j中的 {len(graphs_info)} 个知识图谱")
            return graphs_info
        except Exception as e:
            logger.error(f"列出Neo4j中的知识图谱失败: {str(e)}")
            return []


# 创建全局服务实例
knowledge_graph_service = KnowledgeGraphService()