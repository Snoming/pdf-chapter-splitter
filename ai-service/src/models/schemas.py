"""
数据模型和模式定义
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChapterInfo(BaseModel):
    """章节信息模型"""
    title: str = Field(..., description="章节标题")
    start_page: int = Field(..., ge=1, description="起始页码")
    end_page: int = Field(..., ge=1, description="结束页码")
    page_count: int = Field(..., ge=1, description="页面数量")
    
    def model_post_init(self, __context) -> None:
        """模型初始化后验证"""
        if self.end_page < self.start_page:
            raise ValueError("结束页码不能小于起始页码")
        
        expected_count = self.end_page - self.start_page + 1
        if self.page_count != expected_count:
            self.page_count = expected_count


class AnalyzeRequest(BaseModel):
    """章节分析请求模型"""
    file_path: str = Field(..., description="PDF文件路径")
    auto_detect: bool = Field(True, description="是否自动检测章节")
    min_pages_per_chapter: int = Field(1, ge=1, description="每章最少页数")


class AnalyzeResponse(BaseModel):
    """章节分析响应模型"""
    success: bool = Field(..., description="分析是否成功")
    chapters: List[ChapterInfo] = Field(default_factory=list, description="章节列表")
    total_pages: int = Field(..., ge=0, description="总页数")
    message: Optional[str] = Field(None, description="响应消息")
    suggestions: Optional[List[ChapterInfo]] = Field(None, description="备选建议")


class PDFInfo(BaseModel):
    """PDF文件信息模型"""
    filename: str = Field(..., description="文件名")
    total_pages: int = Field(..., ge=1, description="总页数")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    has_bookmarks: bool = Field(False, description="是否包含书签")
    has_text: bool = Field(False, description="是否包含可提取文本")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[dict] = Field(None, description="错误详情")