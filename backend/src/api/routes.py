"""
API路由定义
"""

import os
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from loguru import logger

from ..models.schemas import (
    UploadResponse, 
    AnalyzeRequest, 
    AnalyzeResponse, 
    SplitRequest, 
    SplitResponse,
    TaskStatusResponse,
    ErrorResponse,
    ValidationResult,
    ChapterInfo
)
from ..services.file_service import FileService
from ..services.pdf_analyzer import PDFAnalyzer
from ..services.task_service import TaskService
from ..core.config import settings


router = APIRouter()

# 服务实例
file_service = FileService()
pdf_analyzer = PDFAnalyzer()
task_service = TaskService()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    上传PDF文件
    
    Args:
        file: 上传的PDF文件
        
    Returns:
        上传结果
    """
    try:
        logger.info(f"接收文件上传请求: {file.filename}")
        
        # 保存文件
        file_info = await file_service.save_uploaded_file(file)
        
        response = UploadResponse(
            file_id=file_info.file_id,
            filename=file_info.filename,
            file_size=file_info.file_size,
            message="文件上传成功"
        )
        
        logger.info(f"文件上传成功: {file_info.file_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_chapters(request: AnalyzeRequest):
    """
    分析PDF章节结构
    
    Args:
        request: 分析请求
        
    Returns:
        章节分析结果
    """
    try:
        logger.info(f"接收章节分析请求: {request.file_id}")
        
        # 获取文件路径
        file_path = await file_service.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        # 执行章节分析
        chapters, pdf_metadata = pdf_analyzer.analyze_pdf(file_path, request.file_id)
        
        # 更新文件状态
        await file_service.update_file_status(request.file_id, "analyzed")
        
        # 生成备选建议（如果需要）
        suggestions = None
        if len(chapters) == 0:
            suggestions = pdf_analyzer._generate_default_chapters(pdf_metadata.total_pages)
        
        response = AnalyzeResponse(
            success=True,
            chapters=chapters,
            total_pages=pdf_metadata.total_pages,
            message=f"成功识别 {len(chapters)} 个章节",
            suggestions=suggestions
        )
        
        logger.info(f"章节分析完成: {request.file_id} - {len(chapters)} 个章节")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"章节分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"章节分析失败: {str(e)}"
        )


@router.post("/split", response_model=SplitResponse)
async def split_pdf(request: SplitRequest):
    """
    拆分PDF文件
    
    Args:
        request: 拆分请求
        
    Returns:
        拆分任务信息
    """
    try:
        logger.info(f"接收PDF拆分请求: {request.file_id}")
        
        # 验证文件存在
        file_path = await file_service.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        # 验证章节信息
        if not request.chapters:
            raise HTTPException(
                status_code=400,
                detail="章节列表不能为空"
            )
        
        # 创建拆分任务
        task = await task_service.create_split_task(request.file_id, request.chapters)
        
        response = SplitResponse(
            task_id=task.task_id,
            status=task.status,
            message="拆分任务已创建，正在处理中"
        )
        
        logger.info(f"拆分任务创建成功: {task.task_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建拆分任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建拆分任务失败: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
    """
    try:
        task = await task_service.get_task_status(task_id)
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail="任务不存在"
            )
        
        response = TaskStatusResponse(
            task_id=task.task_id,
            file_id=task.file_id,
            status=task.status,
            progress=task.progress,
            error_message=task.error_message,
            created_at=task.created_at,
            completed_at=task.completed_at,
            download_links=task.download_links
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取任务状态失败: {str(e)}"
        )


@router.get("/download/{file_id}")
async def download_file(file_id: str, chapter: str = None, download: bool = False):
    """
    下载或预览文件
    
    Args:
        file_id: 文件ID
        chapter: 章节文件名（可选）
        download: 是否强制下载（默认False，即预览模式）
        
    Returns:
        文件下载或预览响应
    """
    try:
        import urllib.parse
        # 对章节名进行URL解码
        decoded_chapter = urllib.parse.unquote(chapter) if chapter else None
        
        # 获取文件路径
        file_path = await file_service.get_download_path(file_id, decoded_chapter)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        # 确定文件名
        if chapter:
            filename = chapter
        else:
            file_info = await file_service.get_file_info(file_id)
            filename = file_info.filename if file_info else "download.pdf"
        
        logger.info(f"文件访问: {file_id} - {filename} (download={download})")
        
        # 根据download参数决定是预览还是下载
        response = FileResponse(
            path=file_path,
            media_type="application/pdf"
        )
        
        # 只有当download为True时，才设置filename参数（强制下载）
        if download:
            response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        else:
            # 预览模式，使用inline
            response.headers["Content-Disposition"] = f"inline; filename={filename}"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件下载失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"文件下载失败: {str(e)}"
        )


@router.get("/files/{file_id}/chapters")
async def list_chapter_files(file_id: str):
    """
    列出章节文件
    
    Args:
        file_id: 文件ID
        
    Returns:
        章节文件列表
    """
    try:
        files = await file_service.list_chapter_files(file_id)
        
        return {
            "file_id": file_id,
            "chapter_files": files,
            "count": len(files)
        }
        
    except Exception as e:
        logger.error(f"列出章节文件失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"列出章节文件失败: {str(e)}"
        )


@router.post("/validate-chapters")
async def validate_chapters(chapters: List[dict], total_pages: int):
    """
    验证章节信息
    
    Args:
        chapters: 章节列表
        total_pages: 总页数
        
    Returns:
        验证结果
    """
    try:
        # 转换为ChapterInfo对象
        chapter_infos = [ChapterInfo(**chapter) for chapter in chapters]
        
        # 执行验证
        result = pdf_analyzer.validate_chapters_detailed(chapter_infos, total_pages)
        
        return result
        
    except Exception as e:
        logger.error(f"章节验证失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"章节验证失败: {str(e)}"
        )


@router.get("/pdf-info/{file_id}")
async def get_pdf_info(file_id: str):
    """
    获取PDF文件信息
    
    Args:
        file_id: 文件ID
        
    Returns:
        PDF文件信息
    """
    try:
        file_path = await file_service.get_file_path(file_id)
        
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        # 获取文件信息
        file_info = await file_service.get_file_info(file_id)
        
        return {
            "file_id": file_id,
            "filename": file_info.filename if file_info else "unknown.pdf",
            "file_size": file_info.file_size if file_info else 0,
            "upload_time": file_info.upload_time if file_info else None,
            "status": file_info.status if file_info else "unknown"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取PDF信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取PDF信息失败: {str(e)}"
        )


@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """
    删除文件
    
    Args:
        file_id: 文件ID
        
    Returns:
        删除结果
    """
    try:
        success = await file_service.delete_file(file_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        return {
            "message": "文件删除成功",
            "file_id": file_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除文件失败: {str(e)}"
        )


@router.get("/queue/status")
async def get_queue_status():
    """
    获取任务队列状态
    
    Returns:
        队列状态信息
    """
    try:
        status = await task_service.get_queue_status()
        return status
        
    except Exception as e:
        logger.error(f"获取队列状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取队列状态失败: {str(e)}"
        )


@router.get("/queue/active")
async def get_active_tasks():
    """
    获取活跃任务列表
    
    Returns:
        活跃任务列表
    """
    try:
        tasks = await task_service.get_active_tasks()
        
        return {
            "active_tasks": [
                {
                    "task_id": task.task_id,
                    "file_id": task.file_id,
                    "status": task.status,
                    "progress": task.progress,
                    "created_at": task.created_at,
                    "chapters_count": len(task.chapters)
                }
                for task in tasks
            ],
            "count": len(tasks)
        }
        
    except Exception as e:
        logger.error(f"获取活跃任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取活跃任务失败: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_files():
    """
    清理临时文件和过期任务
    
    Returns:
        清理结果
    """
    try:
        # 清理临时文件
        temp_files_cleaned = await file_service.cleanup_temp_files()
        
        # 清理过期任务
        tasks_cleaned = await task_service.cleanup_completed_tasks()
        
        return {
            "message": "清理完成",
            "temp_files_cleaned": temp_files_cleaned,
            "tasks_cleaned": tasks_cleaned
        }
        
    except Exception as e:
        logger.error(f"清理失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"清理失败: {str(e)}"
        )