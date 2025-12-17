"""
任务管理服务
"""

import asyncio
import json
from typing import Dict, Optional, List
from datetime import datetime
from uuid import uuid4
from pathlib import Path

from loguru import logger

from ..models.schemas import SplitTask, TaskStatus, ChapterInfo
from ..core.config import settings
from .pdf_splitter import PDFSplitter


class TaskService:
    """任务管理服务"""
    
    def __init__(self):
        self.tasks: Dict[str, SplitTask] = {}
        self.pdf_splitter = PDFSplitter()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self._initialized = False
        
        # 任务队列和并发控制
        self._task_queue = asyncio.Queue()
        self._processing_tasks: Dict[str, asyncio.Task] = {}
        self._max_concurrent_tasks = settings.MAX_CONCURRENT_TASKS
        self._worker_tasks: List[asyncio.Task] = []
    
    async def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            await self._load_existing_tasks()
            await self._start_workers()
            self._initialized = True
    
    async def _start_workers(self):
        """启动工作线程"""
        for i in range(self._max_concurrent_tasks):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._worker_tasks.append(worker)
        logger.info(f"启动了 {self._max_concurrent_tasks} 个任务处理工作线程")
    
    async def _worker(self, worker_name: str):
        """任务处理工作线程"""
        logger.info(f"任务处理工作线程 {worker_name} 启动")
        
        while True:
            try:
                # 从队列获取任务
                task_id = await self._task_queue.get()
                
                if task_id is None:  # 停止信号
                    break
                
                task = self.tasks.get(task_id)
                if task and task.status == TaskStatus.PENDING:
                    logger.info(f"工作线程 {worker_name} 开始处理任务: {task_id}")
                    
                    # 创建处理任务
                    processing_task = asyncio.create_task(self._process_split_task(task))
                    self._processing_tasks[task_id] = processing_task
                    
                    try:
                        await processing_task
                    finally:
                        # 清理处理任务
                        if task_id in self._processing_tasks:
                            del self._processing_tasks[task_id]
                
                # 标记任务完成
                self._task_queue.task_done()
                
            except Exception as e:
                logger.error(f"工作线程 {worker_name} 处理任务时出错: {str(e)}")
                self._task_queue.task_done()
    
    async def stop_workers(self):
        """停止所有工作线程"""
        # 发送停止信号
        for _ in self._worker_tasks:
            await self._task_queue.put(None)
        
        # 等待所有工作线程完成
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        
        # 取消所有正在处理的任务
        for task in self._processing_tasks.values():
            task.cancel()
        
        logger.info("所有任务处理工作线程已停止")
    
    async def create_split_task(self, file_id: str, chapters: List[ChapterInfo]) -> SplitTask:
        """
        创建拆分任务
        
        Args:
            file_id: 文件ID
            chapters: 章节列表
            
        Returns:
            拆分任务
        """
        await self._ensure_initialized()
        task_id = str(uuid4())
        
        task = SplitTask(
            task_id=task_id,
            file_id=file_id,
            chapters=chapters,
            status=TaskStatus.PENDING,
            progress=0
        )
        
        # 保存任务
        self.tasks[task_id] = task
        await self._save_task(task)
        
        # 将任务添加到队列
        await self._task_queue.put(task_id)
        
        logger.info(f"创建拆分任务: {task_id} - 文件: {file_id}，已加入处理队列")
        return task
    
    async def get_task_status(self, task_id: str) -> Optional[SplitTask]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息或None
        """
        await self._ensure_initialized()
        return self.tasks.get(task_id)
    
    async def list_tasks(self, file_id: Optional[str] = None) -> List[SplitTask]:
        """
        列出任务
        
        Args:
            file_id: 文件ID（可选，用于过滤）
            
        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())
        
        if file_id:
            tasks = [task for task in tasks if task.file_id == file_id]
        
        # 按创建时间倒序排列
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        
        return tasks
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功
        """
        task = self.tasks.get(task_id)
        
        if not task:
            return False
        
        if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            task.status = TaskStatus.FAILED
            task.error_message = "任务已被取消"
            task.completed_at = datetime.now()
            
            await self._save_task(task)
            logger.info(f"任务已取消: {task_id}")
            return True
        
        return False
    
    async def get_queue_status(self) -> dict:
        """
        获取任务队列状态
        
        Returns:
            队列状态信息
        """
        await self._ensure_initialized()
        
        pending_count = sum(1 for task in self.tasks.values() if task.status == TaskStatus.PENDING)
        processing_count = sum(1 for task in self.tasks.values() if task.status == TaskStatus.PROCESSING)
        completed_count = sum(1 for task in self.tasks.values() if task.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for task in self.tasks.values() if task.status == TaskStatus.FAILED)
        
        return {
            "queue_size": self._task_queue.qsize(),
            "active_workers": len([t for t in self._worker_tasks if not t.done()]),
            "processing_tasks": len(self._processing_tasks),
            "task_counts": {
                "pending": pending_count,
                "processing": processing_count,
                "completed": completed_count,
                "failed": failed_count,
                "total": len(self.tasks)
            }
        }
    
    async def get_active_tasks(self) -> List[SplitTask]:
        """
        获取活跃任务列表
        
        Returns:
            活跃任务列表
        """
        await self._ensure_initialized()
        
        active_tasks = [
            task for task in self.tasks.values() 
            if task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]
        ]
        
        # 按创建时间排序
        active_tasks.sort(key=lambda x: x.created_at)
        
        return active_tasks
    
    async def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """
        清理已完成的任务
        
        Args:
            max_age_hours: 最大保留时间（小时）
            
        Returns:
            清理的任务数量
        """
        try:
            cleaned_count = 0
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            tasks_to_remove = []
            
            for task_id, task in self.tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    if task.completed_at and task.completed_at.timestamp() < cutoff_time:
                        tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
                # 删除任务文件
                task_file = self.upload_dir / "tasks" / f"{task_id}.json"
                if task_file.exists():
                    task_file.unlink()
                cleaned_count += 1
            
            logger.info(f"清理了 {cleaned_count} 个已完成任务")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理任务失败: {str(e)}")
            return 0
    
    async def _process_split_task(self, task: SplitTask) -> None:
        """处理拆分任务"""
        try:
            logger.info(f"开始处理拆分任务: {task.task_id}")
            
            # 更新任务状态
            task.status = TaskStatus.PROCESSING
            task.progress = 0
            await self._save_task(task)
            
            # 获取文件路径
            file_path = self.upload_dir / task.file_id / "original.pdf"
            
            if not file_path.exists():
                raise Exception(f"文件不存在: {file_path}")
            
            # 创建输出目录
            output_dir = self.upload_dir / task.file_id / "chapters"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 执行PDF拆分
            download_links = await self.pdf_splitter.split_pdf(
                str(file_path),
                task.chapters,
                str(output_dir),
                progress_callback=lambda progress: self._update_task_progress(task.task_id, progress)
            )
            
            # 任务完成
            task.status = TaskStatus.COMPLETED
            task.progress = 100
            task.completed_at = datetime.now()
            task.download_links = download_links
            
            await self._save_task(task)
            
            logger.info(f"拆分任务完成: {task.task_id}")
            
        except Exception as e:
            logger.error(f"拆分任务失败: {task.task_id} - {str(e)}")
            
            # 更新任务状态为失败
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            
            await self._save_task(task)
    
    def _update_task_progress(self, task_id: str, progress: int) -> None:
        """更新任务进度"""
        task = self.tasks.get(task_id)
        if task:
            task.progress = progress
            # 异步保存任务状态
            asyncio.create_task(self._save_task(task))
    
    async def _save_task(self, task: SplitTask) -> None:
        """保存任务到文件"""
        try:
            tasks_dir = self.upload_dir / "tasks"
            tasks_dir.mkdir(parents=True, exist_ok=True)
            
            task_file = tasks_dir / f"{task.task_id}.json"
            
            # 转换为字典并处理datetime序列化
            data = task.model_dump()
            data['created_at'] = task.created_at.isoformat()
            if task.completed_at:
                data['completed_at'] = task.completed_at.isoformat()
            
            with open(task_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存任务失败: {str(e)}")
    
    async def _load_existing_tasks(self) -> None:
        """加载现有任务"""
        try:
            tasks_dir = self.upload_dir / "tasks"
            
            if not tasks_dir.exists():
                return
            
            for task_file in tasks_dir.glob("*.json"):
                try:
                    with open(task_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # 处理datetime反序列化
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if data.get('completed_at'):
                        data['completed_at'] = datetime.fromisoformat(data['completed_at'])
                    
                    task = SplitTask(**data)
                    self.tasks[task.task_id] = task
                    
                except Exception as e:
                    logger.error(f"加载任务文件失败: {task_file} - {str(e)}")
            
            logger.info(f"加载了 {len(self.tasks)} 个现有任务")
            
        except Exception as e:
            logger.error(f"加载现有任务失败: {str(e)}")