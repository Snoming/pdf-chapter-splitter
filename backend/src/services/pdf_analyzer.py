"""
PDF章节分析服务
集成了AI服务的章节识别功能
"""

import re
import fitz  # PyMuPDF
import os
import uuid
from typing import List, Tuple, Optional, Dict, Any
from loguru import logger

from ..models.schemas import ChapterInfo, PDFMetadata, ValidationResult, SectionInfo, KnowledgePoint
from ..core.config import settings
from .llm_service import llm_service


class PDFAnalyzer:
    """PDF章节分析器"""
    
    def __init__(self):
        self.chapter_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in settings.CHAPTER_PATTERNS
        ]
    
    async def analyze_pdf(self, file_path: str, file_id: str, use_llm: bool = True) -> Tuple[List[ChapterInfo], PDFMetadata]:
        """
        分析PDF文件，提取章节信息
        
        Args:
            file_path: PDF文件路径
            file_id: 文件唯一标识
            use_llm: 是否使用大模型增强分析
            
        Returns:
            章节列表和PDF元数据的元组
        """
        try:
            # 打开PDF文件
            doc = fitz.open(file_path)
            
            # 获取PDF基本信息
            pdf_metadata = self._get_pdf_metadata(doc, file_path, file_id)
            
            # 尝试从书签提取章节
            chapters = self._extract_from_bookmarks(doc)
            
            # 如果书签提取失败，尝试文本模式识别
            if not chapters:
                chapters = self._extract_from_text_patterns(doc)
            
            # 如果仍然没有章节，生成默认分割建议
            if not chapters:
                chapters = self._generate_default_chapters(pdf_metadata.total_pages)
            
            # 验证和修正章节信息
            chapters = self._validate_chapters(chapters, pdf_metadata.total_pages)
            
            # 如果启用大模型分析，提取节和知识点
            if use_llm and chapters:
                chapters = await self._enhance_with_llm(doc, chapters)
            
            # 更新PDF元数据
            pdf_metadata.chapters = chapters
            pdf_metadata.status = "analyzed"
            
            doc.close()
            
            logger.info(f"PDF分析完成: {len(chapters)}个章节, 总页数: {pdf_metadata.total_pages}")
            return chapters, pdf_metadata
            
        except Exception as e:
            logger.error(f"PDF分析失败: {str(e)}")
            raise
    
    async def _enhance_with_llm(self, doc: fitz.Document, chapters: List[ChapterInfo]) -> List[ChapterInfo]:
        """
        使用大模型增强章节分析，提取节和知识点
        
        Args:
            doc: PDF文档对象
            chapters: 章节列表
            
        Returns:
            增强后的章节列表
        """
        try:
            logger.info(f"开始使用大模型增强分析，章节数量: {len(chapters)}")
            
            enhanced_chapters = []
            
            for chapter in chapters:
                # 提取章节文本
                chapter_text = self._extract_text_from_pages(doc, chapter.start_page, chapter.end_page)
                
                # 使用大模型分析章节内容
                analysis_result = await llm_service.analyze_pdf_content(chapter_text, context=chapter.title)
                
                # 生成章节ID
                chapter_id = str(uuid.uuid4())
                
                # 构建增强后的章节
                enhanced_chapter = ChapterInfo(
                    id=chapter_id,
                    title=chapter.title,
                    start_page=chapter.start_page,
                    end_page=chapter.end_page,
                    page_count=chapter.page_count,
                    sections=[]
                )
                
                # 确保analysis_result是字典类型
                if isinstance(analysis_result, dict):
                    # 处理节和知识点
                    if "chapters" in analysis_result and isinstance(analysis_result["chapters"], list) and analysis_result["chapters"]:
                        # 假设第一个章节匹配当前章节
                        llm_chapter = analysis_result["chapters"][0]
                        
                        if isinstance(llm_chapter, dict) and "sections" in llm_chapter and isinstance(llm_chapter["sections"], list):
                            for section_data in llm_chapter["sections"]:
                                # 生成节ID
                                section_id = str(uuid.uuid4())
                                
                                # 确保section_data是字典类型
                                section = SectionInfo(
                                    id=section_id,
                                    title=section_data if isinstance(section_data, str) else section_data.get("title", "无标题节"),
                                    start_page=chapter.start_page,  # 后续可优化为更精确的页码
                                    end_page=chapter.end_page,
                                    page_count=1,
                                    knowledge_points=[]
                                )
                                
                                # 处理知识点
                                if isinstance(section_data, dict) and "knowledge_points" in section_data and isinstance(section_data["knowledge_points"], list):
                                    for kp_data in section_data["knowledge_points"]:
                                        # 生成知识点ID
                                        kp_id = str(uuid.uuid4())
                                        
                                        # 创建知识点对象
                                        knowledge_point = KnowledgePoint(
                                            id=kp_id,
                                            title=kp_data if isinstance(kp_data, str) else kp_data.get("title", "无标题知识点"),
                                            content=kp_data if isinstance(kp_data, str) else kp_data.get("content", ""),
                                            start_page=chapter.start_page,  # 后续可优化为更精确的页码
                                            end_page=chapter.end_page,
                                            page_count=1,
                                            related_points=[]
                                        )
                                        section.knowledge_points.append(knowledge_point)
                                
                                enhanced_chapter.sections.append(section)
                
                enhanced_chapters.append(enhanced_chapter)
            
            logger.info(f"大模型增强分析完成")
            return enhanced_chapters
            
        except Exception as e:
            logger.error(f"大模型增强分析失败: {str(e)}")
            return chapters
    
    def _extract_text_from_pages(self, doc: fitz.Document, start_page: int, end_page: int) -> str:
        """
        从指定页面范围提取文本
        
        Args:
            doc: PDF文档对象
            start_page: 起始页码（从1开始）
            end_page: 结束页码
            
        Returns:
            提取的文本
        """
        text = ""
        
        # 确保页码在有效范围内
        start_idx = max(0, start_page - 1)
        end_idx = min(len(doc) - 1, end_page - 1)
        
        for page_num in range(start_idx, end_idx + 1):
            page = doc[page_num]
            text += page.get_text() + "\n"
        
        return text
    
    def _get_pdf_metadata(self, doc: fitz.Document, file_path: str, file_id: str) -> PDFMetadata:
        """获取PDF基本信息"""
        total_pages = len(doc)
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # 检查是否有书签
        has_bookmarks = len(doc.get_toc()) > 0
        
        # 检查是否有可提取的文本
        has_text = False
        if total_pages > 0:
            page = doc[0]
            text = page.get_text()
            has_text = len(text.strip()) > 0
        
        return PDFMetadata(
            file_id=file_id,
            filename=filename,
            total_pages=total_pages,
            file_size=file_size,
            has_bookmarks=has_bookmarks,
            has_text=has_text
        )
    
    def _extract_from_bookmarks(self, doc: fitz.Document) -> List[ChapterInfo]:
        """从PDF书签提取章节信息"""
        chapters = []
        toc = doc.get_toc()
        
        if not toc:
            return chapters
        
        logger.info(f"发现 {len(toc)} 个书签")
        
        # 过滤顶级章节（level 1）
        chapter_bookmarks = [item for item in toc if item[0] == 1]
        
        for i, bookmark in enumerate(chapter_bookmarks):
            level, title, page_num = bookmark
            start_page = page_num
            
            # 确定结束页码
            if i + 1 < len(chapter_bookmarks):
                end_page = chapter_bookmarks[i + 1][2] - 1
            else:
                end_page = len(doc)
            
            # 验证页码范围
            if start_page <= end_page and start_page >= 1:
                chapter = ChapterInfo(
                    title=title.strip(),
                    start_page=start_page,
                    end_page=end_page,
                    page_count=end_page - start_page + 1
                )
                chapters.append(chapter)
        
        logger.info(f"从书签提取到 {len(chapters)} 个章节")
        return chapters
    
    def _extract_from_text_patterns(self, doc: fitz.Document) -> List[ChapterInfo]:
        """从文本模式识别章节"""
        chapters = []
        chapter_pages = []
        
        # 扫描每一页寻找章节标题
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # 检查是否匹配章节模式
            for pattern in self.chapter_patterns:
                matches = pattern.findall(text)
                if matches:
                    # 提取完整的章节标题
                    lines = text.split('\n')
                    for line in lines:
                        if pattern.search(line):
                            title = line.strip()
                            if len(title) > 0 and len(title) < 100:  # 合理的标题长度
                                chapter_pages.append((page_num + 1, title))
                                break
                    break
        
        # 构建章节信息
        for i, (start_page, title) in enumerate(chapter_pages):
            if i + 1 < len(chapter_pages):
                end_page = chapter_pages[i + 1][0] - 1
            else:
                end_page = len(doc)
            
            if start_page <= end_page:
                chapter = ChapterInfo(
                    title=title,
                    start_page=start_page,
                    end_page=end_page,
                    page_count=end_page - start_page + 1
                )
                chapters.append(chapter)
        
        logger.info(f"从文本模式识别到 {len(chapters)} 个章节")
        return chapters
    
    def _generate_default_chapters(self, total_pages: int) -> List[ChapterInfo]:
        """生成默认章节分割建议"""
        chapters = []
        
        # 确保至少有1页
        if total_pages < 1:
            return chapters
        
        # 根据页数决定章节数量
        if total_pages <= 2:
            chapter_count = 1
        elif total_pages <= 20:
            chapter_count = 2
        elif total_pages <= 50:
            chapter_count = 3
        elif total_pages <= 100:
            chapter_count = 5
        else:
            chapter_count = min(10, total_pages // 20)
        
        # 确保章节数不超过页数
        chapter_count = min(chapter_count, total_pages)
        
        pages_per_chapter = total_pages // chapter_count
        remainder = total_pages % chapter_count
        
        current_page = 1
        for i in range(chapter_count):
            # 分配剩余页面到前几个章节
            chapter_pages = pages_per_chapter + (1 if i < remainder else 0)
            
            # 确保至少有1页
            if chapter_pages < 1:
                chapter_pages = 1
            
            end_page = current_page + chapter_pages - 1
            
            # 确保不超过总页数
            if end_page > total_pages:
                end_page = total_pages
                chapter_pages = end_page - current_page + 1
            
            if chapter_pages > 0:  # 只添加有效章节
                chapter = ChapterInfo(
                    title=f"第{i + 1}部分",
                    start_page=current_page,
                    end_page=end_page,
                    page_count=chapter_pages
                )
                chapters.append(chapter)
                
                current_page = end_page + 1
                
                # 如果已经到达最后一页，停止
                if current_page > total_pages:
                    break
        
        logger.info(f"生成默认章节分割: {len(chapters)} 个章节")
        return chapters
    
    def _validate_chapters(self, chapters: List[ChapterInfo], total_pages: int) -> List[ChapterInfo]:
        """验证和修正章节信息"""
        if not chapters:
            return chapters
        
        validated_chapters = []
        
        for i, chapter in enumerate(chapters):
            # 确保页码在有效范围内
            start_page = max(1, chapter.start_page)
            end_page = min(total_pages, chapter.end_page)
            
            # 确保章节至少有一页
            if start_page <= end_page:
                validated_chapter = ChapterInfo(
                    title=chapter.title,
                    start_page=start_page,
                    end_page=end_page,
                    page_count=end_page - start_page + 1
                )
                validated_chapters.append(validated_chapter)
        
        # 检查章节覆盖是否完整
        if validated_chapters:
            # 调整第一个章节从第1页开始
            if validated_chapters[0].start_page > 1:
                first_chapter = validated_chapters[0]
                validated_chapters[0] = ChapterInfo(
                    title=first_chapter.title,
                    start_page=1,
                    end_page=first_chapter.end_page,
                    page_count=first_chapter.end_page - 1 + 1
                )
            
            # 调整最后一个章节到最后一页结束
            if validated_chapters[-1].end_page < total_pages:
                last_chapter = validated_chapters[-1]
                validated_chapters[-1] = ChapterInfo(
                    title=last_chapter.title,
                    start_page=last_chapter.start_page,
                    end_page=total_pages,
                    page_count=total_pages - last_chapter.start_page + 1
                )
        
        logger.info(f"章节验证完成: {len(validated_chapters)} 个有效章节")
        return validated_chapters
    
    def validate_chapters_detailed(self, chapters: List[ChapterInfo], total_pages: int) -> ValidationResult:
        """详细验证章节信息"""
        validated_chapters = self._validate_chapters(chapters, total_pages)
        issues = []
        
        if validated_chapters:
            # 检查是否从第1页开始
            if validated_chapters[0].start_page > 1:
                issues.append("章节未从第1页开始")
            
            # 检查是否到最后一页结束
            if validated_chapters[-1].end_page < total_pages:
                issues.append("章节未覆盖到最后一页")
            
            # 检查章节间是否有重叠或间隙
            for i in range(len(validated_chapters) - 1):
                current_end = validated_chapters[i].end_page
                next_start = validated_chapters[i + 1].start_page
                
                if current_end >= next_start:
                    issues.append(f"章节 {i+1} 和 {i+2} 存在重叠")
                elif current_end + 1 < next_start:
                    issues.append(f"章节 {i+1} 和 {i+2} 之间存在间隙")
        
        total_pages_covered = sum(ch.page_count for ch in validated_chapters)
        
        return ValidationResult(
            valid=len(issues) == 0,
            validated_chapters=validated_chapters,
            issues=issues,
            total_pages_covered=total_pages_covered
        )