"""
数据模型和模式定义
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FileStatus(str, Enum):
    """文件状态枚举"""
    UPLOADED = "uploaded"
    ANALYZED = "analyzed"
    SPLIT = "split"
    ERROR = "error"


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


class FileInfo(BaseModel):
    """文件信息模型"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    file_path: str = Field(..., description="文件存储路径")
    upload_time: datetime = Field(..., description="上传时间")
    status: FileStatus = Field(default=FileStatus.UPLOADED, description="文件状态")


class PDFMetadata(BaseModel):
    """PDF元数据模型"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="文件名")
    total_pages: int = Field(..., ge=1, description="总页数")
    file_size: int = Field(..., ge=0, description="文件大小（字节）")
    chapters: List[ChapterInfo] = Field(default_factory=list, description="章节列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    status: FileStatus = Field(default=FileStatus.UPLOADED, description="处理状态")
    has_bookmarks: bool = Field(default=False, description="是否包含书签")
    has_text: bool = Field(default=False, description="是否包含可提取文本")


class SplitTask(BaseModel):
    """拆分任务模型"""
    task_id: str = Field(..., description="任务唯一标识")
    file_id: str = Field(..., description="文件唯一标识")
    chapters: List[ChapterInfo] = Field(..., description="章节列表")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    progress: int = Field(default=0, ge=0, le=100, description="进度百分比")
    error_message: Optional[str] = Field(None, description="错误消息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    download_links: List[str] = Field(default_factory=list, description="下载链接")


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


class SplitRequest(BaseModel):
    """PDF拆分请求"""
    file_id: str = Field(..., description="文件唯一标识")
    chapters: List[ChapterInfo] = Field(..., description="章节列表")


class SplitResponse(BaseModel):
    """PDF拆分响应"""
    task_id: str = Field(..., description="任务唯一标识")
    status: TaskStatus = Field(..., description="任务状态")
    message: str = Field(..., description="响应消息")
    download_links: List[str] = Field(default_factory=list, description="下载链接")


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str = Field(..., description="任务唯一标识")
    file_id: str = Field(..., description="文件唯一标识")
    status: TaskStatus = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比")
    error_message: Optional[str] = Field(None, description="错误消息")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    download_links: List[str] = Field(default_factory=list, description="下载链接")


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