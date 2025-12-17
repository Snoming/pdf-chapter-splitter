"""
文件管理服务
"""

import os
import json
import shutil
from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from pathlib import Path

from fastapi import UploadFile, HTTPException
from loguru import logger

from ..models.schemas import FileInfo, FileStatus
from ..core.config import settings


class FileService:
    """文件管理服务"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.temp_dir = Path(settings.TEMP_DIR)
        
        # 确保目录存在
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> FileInfo:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件
            
        Returns:
            文件信息
        """
        try:
            # 验证文件格式
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail="仅支持PDF文件格式"
                )
            
            # 读取文件内容
            content = await file.read()
            
            # 验证文件大小
            if len(content) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE} 字节)"
                )
            
            # 验证PDF文件头
            if not content.startswith(b'%PDF'):
                raise HTTPException(
                    status_code=400,
                    detail="文件格式无效，请上传有效的PDF文件"
                )
            
            # 生成文件ID和目录
            file_id = str(uuid4())
            file_dir = self.upload_dir / file_id
            file_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存原始文件
            file_path = file_dir / "original.pdf"
            with open(file_path, "wb") as f:
                f.write(content)
            
            # 创建文件信息
            file_info = FileInfo(
                file_id=file_id,
                filename=file.filename,
                file_size=len(content),
                file_path=str(file_path),
                upload_time=datetime.now(),
                status=FileStatus.UPLOADED
            )
            
            # 保存元数据
            await self._save_file_metadata(file_info)
            
            logger.info(f"文件上传成功: {file_id} - {file.filename}")
            return file_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"文件上传失败: {str(e)}"
            )
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """
        获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件信息或None
        """
        try:
            metadata_path = self.upload_dir / file_id / "metadata.json"
            
            if not metadata_path.exists():
                return None
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return FileInfo(**data)
                
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return None
    
    async def get_file_path(self, file_id: str) -> Optional[str]:
        """
        获取文件路径
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件路径或None
        """
        file_path = self.upload_dir / file_id / "original.pdf"
        
        if file_path.exists():
            return str(file_path)
        
        return None
    
    async def get_download_path(self, file_id: str, chapter_name: Optional[str] = None) -> Optional[str]:
        """
        获取下载文件路径
        
        Args:
            file_id: 文件ID
            chapter_name: 章节文件名（可选）
            
        Returns:
            下载文件路径或None
        """
        if chapter_name:
            # 返回特定章节文件
            chapter_path = self.upload_dir / file_id / "chapters" / chapter_name
            if chapter_path.exists():
                return str(chapter_path)
        else:
            # 返回原始文件
            original_path = self.upload_dir / file_id / "original.pdf"
            if original_path.exists():
                return str(original_path)
        
        return None
    
    async def list_chapter_files(self, file_id: str) -> List[str]:
        """
        列出章节文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            章节文件名列表
        """
        chapters_dir = self.upload_dir / file_id / "chapters"
        
        if not chapters_dir.exists():
            return []
        
        try:
            files = []
            for file_path in chapters_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                    files.append(file_path.name)
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"列出章节文件失败: {str(e)}")
            return []
    
    async def update_file_status(self, file_id: str, status: FileStatus) -> bool:
        """
        更新文件状态
        
        Args:
            file_id: 文件ID
            status: 新状态
            
        Returns:
            是否成功
        """
        try:
            file_info = await self.get_file_info(file_id)
            if not file_info:
                return False
            
            file_info.status = status
            await self._save_file_metadata(file_info)
            
            return True
            
        except Exception as e:
            logger.error(f"更新文件状态失败: {str(e)}")
            return False
    
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        清理临时文件
        
        Args:
            max_age_hours: 最大保留时间（小时）
            
        Returns:
            清理的文件数量
        """
        try:
            cleaned_count = 0
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"清理临时文件: {file_path}")
            
            logger.info(f"清理了 {cleaned_count} 个临时文件")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
            return 0
    
    async def delete_file(self, file_id: str) -> bool:
        """
        删除文件及其相关数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            是否成功
        """
        try:
            file_dir = self.upload_dir / file_id
            
            if file_dir.exists():
                shutil.rmtree(file_dir)
                logger.info(f"删除文件: {file_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除文件失败: {str(e)}")
            return False
    
    async def _save_file_metadata(self, file_info: FileInfo) -> None:
        """保存文件元数据"""
        try:
            file_dir = self.upload_dir / file_info.file_id
            metadata_path = file_dir / "metadata.json"
            
            # 转换为字典并处理datetime序列化
            data = file_info.model_dump()
            data['upload_time'] = file_info.upload_time.isoformat()
            
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存文件元数据失败: {str(e)}")
            raise