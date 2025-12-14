"""
PDF章节分析服务
"""

import re
import fitz  # PyMuPDF
from typing import List, Tuple, Optional
from loguru import logger

from ..models.schemas import ChapterInfo, PDFInfo
from ..core.config import settings


class PDFAnalyzer:
    """PDF章节分析器"""
    
    def __init__(self):
        self.chapter_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in settings.CHAPTER_PATTERNS
        ]
    
    def analyze_pdf(self, file_path: str) -> Tuple[List[ChapterInfo], PDFInfo]:
        """
        分析PDF文件，提取章节信息
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            章节列表和PDF信息的元组
        """
        try:
            # 打开PDF文件
            doc = fitz.open(file_path)
            
            # 获取PDF基本信息
            pdf_info = self._get_pdf_info(doc, file_path)
            
            # 尝试从书签提取章节
            chapters = self._extract_from_bookmarks(doc)
            
            # 如果书签提取失败，尝试文本模式识别
            if not chapters:
                chapters = self._extract_from_text_patterns(doc)
            
            # 如果仍然没有章节，生成默认分割建议
            if not chapters:
                chapters = self._generate_default_chapters(pdf_info.total_pages)
            
            # 验证和修正章节信息
            chapters = self._validate_chapters(chapters, pdf_info.total_pages)
            
            doc.close()
            
            logger.info(f"PDF分析完成: {len(chapters)}个章节, 总页数: {pdf_info.total_pages}")
            return chapters, pdf_info
            
        except Exception as e:
            logger.error(f"PDF分析失败: {str(e)}")
            raise
    
    def _get_pdf_info(self, doc: fitz.Document, file_path: str) -> PDFInfo:
        """获取PDF基本信息"""
        import os
        
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
        
        return PDFInfo(
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
        
        # 根据页数决定章节数量
        if total_pages <= 20:
            chapter_count = 2
        elif total_pages <= 50:
            chapter_count = 3
        elif total_pages <= 100:
            chapter_count = 5
        else:
            chapter_count = min(10, total_pages // 20)
        
        pages_per_chapter = total_pages // chapter_count
        remainder = total_pages % chapter_count
        
        current_page = 1
        for i in range(chapter_count):
            # 分配剩余页面到前几个章节
            chapter_pages = pages_per_chapter + (1 if i < remainder else 0)
            end_page = current_page + chapter_pages - 1
            
            chapter = ChapterInfo(
                title=f"第{i + 1}部分",
                start_page=current_page,
                end_page=end_page,
                page_count=chapter_pages
            )
            chapters.append(chapter)
            
            current_page = end_page + 1
        
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