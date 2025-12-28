"""
数据模型和模式定义
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class FileStatus(str, Enum):
    """文件状态枚举"""
    UPLOADED = "uploaded"
    ANALYZED = "analyzed"
    ERROR = "error"


class SectionInfo(BaseModel):
    """节信息模型"""
    id: Optional[str] = Field(None, description="节唯一标识")
    title: str = Field(..., description="节标题")
    start_page: int = Field(..., ge=1, description="起始页码")
    end_page: int = Field(..., ge=1, description="结束页码")
    page_count: int = Field(..., ge=1, description="页面数量")
    knowledge_points: List["KnowledgePoint"] = Field(default_factory=list, description="知识点列表")
    
    def model_post_init(self, __context) -> None:
        """模型初始化后验证"""
        if self.end_page < self.start_page:
            raise ValueError("结束页码不能小于起始页码")
        
        expected_count = self.end_page - self.start_page + 1
        if self.page_count != expected_count:
            self.page_count = expected_count


class KnowledgePoint(BaseModel):
    """知识点模型"""
    id: Optional[str] = Field(None, description="知识点唯一标识")
    title: str = Field(..., description="知识点标题")
    content: str = Field(..., description="知识点内容")
    start_page: int = Field(..., ge=1, description="起始页码")
    end_page: int = Field(..., ge=1, description="结束页码")
    page_count: int = Field(..., ge=1, description="页面数量")
    related_points: List[str] = Field(default_factory=list, description="关联知识点ID列表")
    
    def model_post_init(self, __context) -> None:
        """模型初始化后验证"""
        if self.end_page < self.start_page:
            raise ValueError("结束页码不能小于起始页码")
        
        expected_count = self.end_page - self.start_page + 1
        if self.page_count != expected_count:
            self.page_count = expected_count


class ChapterInfo(BaseModel):
    """章节信息模型"""
    id: Optional[str] = Field(None, description="章节唯一标识")
    title: str = Field(..., description="章节标题")
    start_page: int = Field(..., ge=1, description="起始页码")
    end_page: int = Field(..., ge=1, description="结束页码")
    page_count: int = Field(..., ge=1, description="页面数量")
    sections: List[SectionInfo] = Field(default_factory=list, description="节列表")
    
    def model_post_init(self, __context) -> None:
        """模型初始化后验证"""
        if self.end_page < self.start_page:
            raise ValueError("结束页码不能小于起始页码")
        
        expected_count = self.end_page - self.start_page + 1
        if self.page_count != expected_count:
            self.page_count = expected_count


class FileInfo(BaseModel):
    """文件信息模型"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    file_path: str = Field(..., description="文件存储路径")
    upload_time: datetime = Field(..., description="上传时间")
    status: FileStatus = Field(default=FileStatus.UPLOADED, description="文件状态")


class BookInfo(BaseModel):
    """书籍信息模型"""
    id: Optional[str] = Field(None, description="书籍唯一标识")
    title: str = Field(..., description="书籍标题")
    author: Optional[str] = Field(None, description="作者")
    description: Optional[str] = Field(None, description="书籍描述")
    total_pages: int = Field(..., ge=1, description="总页数")
    chapters: List[ChapterInfo] = Field(default_factory=list, description="章节列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class GraphNode(BaseModel):
    """知识图谱节点模型"""
    id: str = Field(..., description="节点唯一标识")
    type: str = Field(..., description="节点类型: book/chapter/section/knowledge")
    content: str = Field(..., description="节点内容")
    metadata: Optional[dict] = Field(default_factory=dict, description="节点元数据")


class GraphEdge(BaseModel):
    """知识图谱边模型"""
    source_id: str = Field(..., description="源节点ID")
    target_id: str = Field(..., description="目标节点ID")
    relation_type: str = Field(..., description="关系类型")
    weight: float = Field(default=1.0, description="关系权重")


class KnowledgeGraph(BaseModel):
    """知识图谱模型"""
    book_id: str = Field(..., description="关联书籍ID")
    nodes: List[GraphNode] = Field(default_factory=list, description="节点列表")
    edges: List[GraphEdge] = Field(default_factory=list, description="边列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class PDFMetadata(BaseModel):
    """PDF元数据模型"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="文件名")
    total_pages: int = Field(..., ge=1, description="总页数")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    book_info: Optional[BookInfo] = Field(None, description="书籍信息")
    chapters: List[ChapterInfo] = Field(default_factory=list, description="章节列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    status: FileStatus = Field(default=FileStatus.UPLOADED, description="处理状态")
    has_bookmarks: bool = Field(default=False, description="是否包含书签")
    has_text: bool = Field(default=False, description="是否包含可提取文本")


# API请求和响应模型

class UploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    message: str = Field(..., description="响应消息")


class AnalyzeRequest(BaseModel):
    """章节分析请求"""
    file_id: str = Field(..., description="文件唯一标识")
    auto_detect: bool = Field(default=True, description="是否自动检测章节")
    min_pages_per_chapter: int = Field(default=1, ge=1, description="每章最少页数")


class AnalyzeResponse(BaseModel):
    """章节分析响应"""
    success: bool = Field(..., description="分析是否成功")
    chapters: List[ChapterInfo] = Field(default_factory=list, description="章节列表")
    total_pages: int = Field(..., ge=0, description="总页数")
    message: Optional[str] = Field(None, description="响应消息")
    suggestions: Optional[List[ChapterInfo]] = Field(None, description="备选建议")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[dict] = Field(None, description="错误详情")


class ValidationResult(BaseModel):
    """章节验证结果"""
    valid: bool = Field(..., description="是否有效")
    validated_chapters: List[ChapterInfo] = Field(..., description="验证后的章节列表")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    total_pages_covered: int = Field(..., description="覆盖的总页数")


# 知识图谱相关API模型

class KnowledgeGraphRequest(BaseModel):
    """知识图谱构建请求"""
    file_id: str = Field(..., description="文件唯一标识")
    use_llm: bool = Field(default=True, description="是否使用大模型增强分析")


class KnowledgeGraphResponse(BaseModel):
    """知识图谱构建响应"""
    success: bool = Field(..., description="构建是否成功")
    graph: Optional[KnowledgeGraph] = Field(None, description="知识图谱")
    message: Optional[str] = Field(None, description="响应消息")


class KnowledgePointRequest(BaseModel):
    """知识点管理请求"""
    file_id: str = Field(..., description="文件唯一标识")
    knowledge_points: List[KnowledgePoint] = Field(..., description="知识点列表")


class KnowledgePointResponse(BaseModel):
    """知识点管理响应"""
    success: bool = Field(..., description="操作是否成功")
    message: Optional[str] = Field(None, description="响应消息")
    knowledge_points: List[KnowledgePoint] = Field(default_factory=list, description="知识点列表")


class GraphNodeResponse(BaseModel):
    """知识图谱节点响应"""
    nodes: List[GraphNode] = Field(default_factory=list, description="节点列表")
    total: int = Field(..., description="节点总数")


class GraphEdgeResponse(BaseModel):
    """知识图谱边响应"""
    edges: List[GraphEdge] = Field(default_factory=list, description="边列表")
    total: int = Field(..., description="边总数")


# 更新模型引用
SectionInfo.model_rebuild()
KnowledgePoint.model_rebuild()