"""
PDF拆分服务
"""

import fitz  # PyMuPDF
from typing import List, Callable, Optional
from pathlib import Path

from loguru import logger

from ..models.schemas import ChapterInfo


class PDFSplitter:
    """PDF拆分器"""
    
    async def split_pdf(
        self, 
        input_path: str, 
        chapters: List[ChapterInfo], 
        output_dir: str,
        progress_callback: Optional[Callable[[int], None]] = None
    ) -> List[str]:
        """
        拆分PDF文件
        
        Args:
            input_path: 输入PDF文件路径
            chapters: 章节列表
            output_dir: 输出目录
            progress_callback: 进度回调函数
            
        Returns:
            生成的文件路径列表
        """
        try:
            logger.info(f"开始拆分PDF: {input_path}")
            
            # 打开PDF文件
            doc = fitz.open(input_path)
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            download_links = []
            total_chapters = len(chapters)
            
            for i, chapter in enumerate(chapters):
                try:
                    # 创建新的PDF文档
                    new_doc = fitz.open()
                    
                    # 复制指定页面范围
                    for page_num in range(chapter.start_page - 1, chapter.end_page):
                        if page_num < len(doc):
                            page = doc[page_num]
                            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                    
                    # 生成文件名
                    safe_title = self._sanitize_filename(chapter.title)
                    filename = f"{i+1:02d}_{safe_title}.pdf"
                    file_path = output_path / filename
                    
                    # 保存文件
                    new_doc.save(str(file_path))
                    new_doc.close()
                    
                    # 添加到下载链接
                    download_links.append(filename)
                    
                    # 更新进度
                    progress = int((i + 1) / total_chapters * 100)
                    if progress_callback:
                        progress_callback(progress)
                    
                    logger.info(f"章节拆分完成: {filename}")
                    
                except Exception as e:
                    logger.error(f"拆分章节失败: {chapter.title} - {str(e)}")
                    continue
            
            doc.close()
            
            logger.info(f"PDF拆分完成: 生成 {len(download_links)} 个文件")
            return download_links
            
        except Exception as e:
            logger.error(f"PDF拆分失败: {str(e)}")
            raise
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不安全字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 移除或替换不安全字符
        unsafe_chars = '<>:"/\\|?*'
        safe_filename = filename
        
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        # 限制长度
        if len(safe_filename) > 50:
            safe_filename = safe_filename[:50]
        
        # 确保不为空
        if not safe_filename.strip():
            safe_filename = "chapter"
        
        return safe_filename.strip()
    
    async def merge_pdfs(self, input_paths: List[str], output_path: str) -> bool:
        """
        合并PDF文件
        
        Args:
            input_paths: 输入文件路径列表
            output_path: 输出文件路径
            
        Returns:
            是否成功
        """
        try:
            logger.info(f"开始合并PDF: {len(input_paths)} 个文件")
            
            # 创建新的PDF文档
            merged_doc = fitz.open()
            
            for input_path in input_paths:
                if Path(input_path).exists():
                    doc = fitz.open(input_path)
                    merged_doc.insert_pdf(doc)
                    doc.close()
                else:
                    logger.warning(f"文件不存在: {input_path}")
            
            # 保存合并后的文件
            merged_doc.save(output_path)
            merged_doc.close()
            
            logger.info(f"PDF合并完成: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"PDF合并失败: {str(e)}")
            return False
    
    def get_pdf_info(self, file_path: str) -> dict:
        """
        获取PDF文件信息
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            PDF信息字典
        """
        try:
            doc = fitz.open(file_path)
            
            info = {
                "total_pages": len(doc),
                "metadata": doc.metadata,
                "has_bookmarks": len(doc.get_toc()) > 0,
                "file_size": Path(file_path).stat().st_size
            }
            
            # 检查是否有文本
            has_text = False
            if len(doc) > 0:
                page = doc[0]
                text = page.get_text()
                has_text = len(text.strip()) > 0
            
            info["has_text"] = has_text
            
            doc.close()
            return info
            
        except Exception as e:
            logger.error(f"获取PDF信息失败: {str(e)}")
            return {}