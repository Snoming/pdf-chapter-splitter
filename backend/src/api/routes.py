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
    ValidationResult,
    ChapterInfo,
    KnowledgeGraphRequest,
    KnowledgeGraphResponse,
    KnowledgePointRequest,
    KnowledgePointResponse,
    GraphNodeResponse,
    GraphEdgeResponse
)
from ..services.file_service import FileService
from ..services.pdf_analyzer import PDFAnalyzer
from ..services.knowledge_graph_service import KnowledgeGraphService
from ..core.config import settings


router = APIRouter()

# 服务实例
file_service = FileService()
pdf_analyzer = PDFAnalyzer()
knowledge_graph_service = KnowledgeGraphService()


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
        chapters, pdf_metadata = await pdf_analyzer.analyze_pdf(file_path, request.file_id)
        
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








# ------------------------
# 知识图谱相关API
# ------------------------


@router.post("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def build_knowledge_graph(request: KnowledgeGraphRequest):
    """
    构建知识图谱
    
    Args:
        request: 知识图谱构建请求
        
    Returns:
        知识图谱构建响应
    """
    try:
        logger.info(f"接收知识图谱构建请求: {request.file_id}")
        
        # 获取文件路径
        file_path = await file_service.get_file_path(request.file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        # 分析PDF文件，提取章节、节和知识点
        chapters, pdf_metadata = await pdf_analyzer.analyze_pdf(file_path, request.file_id, use_llm=request.use_llm)
        
        # 构建知识图谱，跳过数据库保存
        knowledge_graph = await knowledge_graph_service.build_knowledge_graph(chapters, use_llm=request.use_llm, save_to_db=False)
        
        response = KnowledgeGraphResponse(
            success=True,
            graph=knowledge_graph,
            message=f"知识图谱构建成功，节点数: {len(knowledge_graph.nodes)}, 边数: {len(knowledge_graph.edges)}"
        )
        
        logger.info(f"知识图谱构建完成: {request.file_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"构建知识图谱失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"构建知识图谱失败: {str(e)}"
        )


@router.get("/knowledge-graph/{file_id}", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(file_id: str):
    """
    获取知识图谱
    
    Args:
        file_id: 文件唯一标识
        
    Returns:
        知识图谱响应
    """
    try:
        logger.info(f"接收知识图谱获取请求: {file_id}")
        
        # 这里可以从数据库或缓存中获取知识图谱
        # 目前先返回空响应，后续可以扩展
        
        response = KnowledgeGraphResponse(
            success=True,
            graph=None,
            message="知识图谱获取成功"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识图谱失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取知识图谱失败: {str(e)}"
        )


@router.get("/knowledge-graph/{file_id}/nodes", response_model=GraphNodeResponse)
async def get_graph_nodes(file_id: str, node_type: str = None):
    """
    获取知识图谱节点
    
    Args:
        file_id: 文件唯一标识
        node_type: 节点类型过滤
        
    Returns:
        节点列表响应
    """
    try:
        logger.info(f"接收知识图谱节点获取请求: {file_id}")
        
        # 这里可以从数据库或缓存中获取知识图谱节点
        # 目前先返回空响应，后续可以扩展
        
        response = GraphNodeResponse(
            nodes=[],
            total=0
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识图谱节点失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取知识图谱节点失败: {str(e)}"
        )


@router.get("/knowledge-graph/{file_id}/edges", response_model=GraphEdgeResponse)
async def get_graph_edges(file_id: str, relation_type: str = None):
    """
    获取知识图谱边
    
    Args:
        file_id: 文件唯一标识
        relation_type: 关系类型过滤
        
    Returns:
        边列表响应
    """
    try:
        logger.info(f"接收知识图谱边获取请求: {file_id}")
        
        # 这里可以从数据库或缓存中获取知识图谱边
        # 目前先返回空响应，后续可以扩展
        
        response = GraphEdgeResponse(
            edges=[],
            total=0
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取知识图谱边失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取知识图谱边失败: {str(e)}"
        )


@router.get("/knowledge-graph/{file_id}/visualize")
async def visualize_knowledge_graph(file_id: str):
    """
    获取知识图谱可视化数据
    
    Args:
        file_id: 文件唯一标识
        
    Returns:
        可视化数据
    """
    try:
        logger.info(f"接收知识图谱可视化请求: {file_id}")
        
        # 获取文件路径
        file_path = await file_service.get_file_path(file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        # 分析PDF文件，提取章节、节和知识点
        chapters, pdf_metadata = await pdf_analyzer.analyze_pdf(file_path, file_id)
        
        # 构建知识图谱，跳过数据库保存
        knowledge_graph = await knowledge_graph_service.build_knowledge_graph(chapters, save_to_db=False)
        
        # 生成可视化数据
        visualize_data = knowledge_graph_service.visualize_graph(knowledge_graph)
        
        logger.info(f"知识图谱可视化数据生成完成: {file_id}")
        return visualize_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成知识图谱可视化数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"生成知识图谱可视化数据失败: {str(e)}"
        )


@router.post("/knowledge-points", response_model=KnowledgePointResponse)
async def manage_knowledge_points(request: KnowledgePointRequest):
    """
    管理知识点
    
    Args:
        request: 知识点管理请求
        
    Returns:
        知识点管理响应
    """
    try:
        logger.info(f"接收知识点管理请求: {request.file_id}")
        
        # 这里可以实现知识点的管理逻辑
        # 目前先返回空响应，后续可以扩展
        
        response = KnowledgePointResponse(
            success=True,
            message="知识点管理成功",
            knowledge_points=request.knowledge_points
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"管理知识点失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"管理知识点失败: {str(e)}"
        )


@router.get("/knowledge-graph/{file_id}/search")
async def search_knowledge_points(file_id: str, keyword: str):
    """
    搜索知识点
    
    Args:
        file_id: 文件唯一标识
        keyword: 搜索关键词
        
    Returns:
        搜索结果
    """
    try:
        logger.info(f"接收知识点搜索请求: {file_id}, 关键词: {keyword}")
        
        # 获取文件路径
        file_path = await file_service.get_file_path(file_id)
        if not file_path:
            raise HTTPException(
                status_code=404,
                detail="文件不存在"
            )
        
        # 分析PDF文件，提取章节、节和知识点
        chapters, pdf_metadata = await pdf_analyzer.analyze_pdf(file_path, file_id)
        
        # 构建知识图谱
        knowledge_graph = await knowledge_graph_service.build_knowledge_graph(chapters)
        
        # 搜索知识点
        matched_points = knowledge_graph_service.search_knowledge_points(knowledge_graph, keyword)
        
        logger.info(f"知识点搜索完成: {file_id}, 匹配数: {len(matched_points)}")
        return {
            "keyword": keyword,
            "matched_points": matched_points,
            "count": len(matched_points)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索知识点失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索知识点失败: {str(e)}"
        )