"""
数据库模型定义
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base


class KnowledgeGraphDB(Base):
    """知识图谱数据库模型"""
    __tablename__ = "knowledge_graphs"
    
    id = Column(String, primary_key=True, index=True)
    book_id = Column(String, index=True, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    nodes = relationship("GraphNodeDB", back_populates="graph", cascade="all, delete-orphan")
    edges = relationship("GraphEdgeDB", back_populates="graph", cascade="all, delete-orphan")


class GraphNodeDB(Base):
    """知识图谱节点数据库模型"""
    __tablename__ = "graph_nodes"
    
    id = Column(String, primary_key=True, index=True)
    graph_id = Column(String, ForeignKey("knowledge_graphs.id"), nullable=False)
    type = Column(String, index=True, nullable=False)  # book/chapter/section/knowledge
    content = Column(String, nullable=False)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    graph = relationship("KnowledgeGraphDB", back_populates="nodes")
    outgoing_edges = relationship("GraphEdgeDB", foreign_keys="GraphEdgeDB.source_id", back_populates="source_node")
    incoming_edges = relationship("GraphEdgeDB", foreign_keys="GraphEdgeDB.target_id", back_populates="target_node")


class GraphEdgeDB(Base):
    """知识图谱边数据库模型"""
    __tablename__ = "graph_edges"
    
    id = Column(String, primary_key=True, index=True)
    graph_id = Column(String, ForeignKey("knowledge_graphs.id"), nullable=False)
    source_id = Column(String, ForeignKey("graph_nodes.id"), nullable=False)
    target_id = Column(String, ForeignKey("graph_nodes.id"), nullable=False)
    relation_type = Column(String, index=True, nullable=False)
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    graph = relationship("KnowledgeGraphDB", back_populates="edges")
    source_node = relationship("GraphNodeDB", foreign_keys=[source_id], back_populates="outgoing_edges")
    target_node = relationship("GraphNodeDB", foreign_keys=[target_id], back_populates="incoming_edges")
