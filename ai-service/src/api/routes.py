"""
API路由定义
"""

import os
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File
from loguru import logger

from ..models.schemas import (
    AnalyzeRequest, 
    AnalyzeResponse, 
    ChapterInfo, 
    ErrorResponse
)
from ..services.pdf_analyzer import PDFAnalyzer
from ..core.config import settings


router = APIRouter()
pdf_analyzer = PDFAnalyzer()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_pdf_chapters(request: AnalyzeRequest):
    """
    分析PDF章节结构
    
    Args:
        request: 包含文件路径的分析请求
        
    Returns:
        章节分析结果
    """
    try:
        # 验证文件是否存在
        if not os.path.exists(request.file_path):
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {request.file_path}"
            )
        
        # 验证文件格式
        if not request.file_path.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="仅支持PDF文件格式"
            )
        
        logger.info(f"开始分析PDF文件: {request.file_path}")
        
        # 执行章节分析
        chapters, pdf_info = pdf_analyzer.analyze_pdf(request.file_path)
        
        # 生成备选建议（如果需要）
        suggestions = None
        if len(chapters) == 0:
            # 如果没有识别到章节，提供平均分割建议
            suggestions = pdf_analyzer._generate_default_chapters(pdf_info.total_pages)
        
        response = AnalyzeResponse(
            success=True,
            chapters=chapters,
            total_pages=pdf_info.total_pages,
            message=f"成功识别 {len(chapters)} 个章节",
            suggestions=suggestions
        )
        
        logger.info(f"PDF分析完成: {len(chapters)} 个章节")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF分析失败: {str(e)}"
        )


@router.post("/upload-and-analyze", response_model=AnalyzeResponse)
async def upload_and_analyze_pdf(file: UploadFile = File(...)):
    """
    上传并分析PDF文件
    
    Args:
        file: 上传的PDF文件
        
    Returns:
        章节分析结果
    """
    try:
        # 验证文件格式
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="仅支持PDF文件格式"
            )
        
        # 验证文件大小
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE} 字节)"
            )
        
        # 保存临时文件
        temp_path = os.path.join(settings.TEMP_DIR, file.filename)
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        
        with open(temp_path, "wb") as temp_file:
            temp_file.write(content)
        
        logger.info(f"临时文件保存: {temp_path}")
        
        try:
            # 分析PDF
            chapters, pdf_info = pdf_analyzer.analyze_pdf(temp_path)
            
            # 生成备选建议
            suggestions = None
            if len(chapters) == 0:
                suggestions = pdf_analyzer._generate_default_chapters(pdf_info.total_pages)
            
            response = AnalyzeResponse(
                success=True,
                chapters=chapters,
                total_pages=pdf_info.total_pages,
                message=f"成功识别 {len(chapters)} 个章节",
                suggestions=suggestions
            )
            
            return response
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f"临时文件已清理: {temp_path}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传和分析失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"处理失败: {str(e)}"
        )


@router.get("/pdf-info")
async def get_pdf_info(file_path: str):
    """
    获取PDF文件基本信息
    
    Args:
        file_path: PDF文件路径
        
    Returns:
        PDF文件信息
    """
    try:
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        _, pdf_info = pdf_analyzer.analyze_pdf(file_path)
        return pdf_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取PDF信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取PDF信息失败: {str(e)}"
        )


@router.post("/validate-chapters")
async def validate_chapters(chapters: List[ChapterInfo], total_pages: int):
    """
    验证章节信息的有效性
    
    Args:
        chapters: 章节列表
        total_pages: 总页数
        
    Returns:
        验证结果
    """
    try:
        # 验证章节信息
        validated_chapters = pdf_analyzer._validate_chapters(chapters, total_pages)
        
        # 检查覆盖完整性
        coverage_issues = []
        
        if validated_chapters:
            # 检查是否从第1页开始
            if validated_chapters[0].start_page > 1:
                coverage_issues.append("章节未从第1页开始")
            
            # 检查是否到最后一页结束
            if validated_chapters[-1].end_page < total_pages:
                coverage_issues.append("章节未覆盖到最后一页")
            
            # 检查章节间是否有重叠或间隙
            for i in range(len(validated_chapters) - 1):
                current_end = validated_chapters[i].end_page
                next_start = validated_chapters[i + 1].start_page
                
                if current_end >= next_start:
                    coverage_issues.append(f"章节 {i+1} 和 {i+2} 存在重叠")
                elif current_end + 1 < next_start:
                    coverage_issues.append(f"章节 {i+1} 和 {i+2} 之间存在间隙")
        
        return {
            "valid": len(coverage_issues) == 0,
            "validated_chapters": validated_chapters,
            "issues": coverage_issues,
            "total_pages_covered": sum(ch.page_count for ch in validated_chapters)
        }
        
    except Exception as e:
        logger.error(f"章节验证失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"章节验证失败: {str(e)}"
        )