/**
 * PDF拆分进度组件
 * 显示PDF拆分的进度和结果
 */

'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { useAppStore, SplitTask } from '@/store/useAppStore';
import { ApiService } from '@/lib/api';

interface SplitProgressProps {
  task: SplitTask;
  onComplete?: () => void;
}

export function SplitProgress({ task, onComplete }: SplitProgressProps) {
  const [progress, setProgress] = useState<number>(task.progress);
  const [status, setStatus] = useState<SplitTask['status']>(task.status);
  const [errorMessage, setErrorMessage] = useState<string | undefined>(task.errorMessage);
  const [isCheckingStatus, setIsCheckingStatus] = useState<boolean>(true);
  const { updateTaskProgress, setCurrentTask } = useAppStore();

  // 定期检查任务状态
  const checkTaskStatus = useCallback(async () => {
    try {
      const updatedTask = await ApiService.getTaskStatus(task.taskId);
      
      setProgress(updatedTask.progress);
      setStatus(updatedTask.status);
      setErrorMessage(updatedTask.errorMessage);
      
      // 更新全局状态
      updateTaskProgress(updatedTask.progress);
      setCurrentTask(updatedTask);
      
      // 如果任务完成或失败，停止检查
      if (updatedTask.status === 'completed' || updatedTask.status === 'failed') {
        setIsCheckingStatus(false);
        if (onComplete && updatedTask.status === 'completed') {
          onComplete();
        }
      }
      
    } catch (err) {
      console.error('获取任务状态失败:', err);
      setIsCheckingStatus(false);
    }
  }, [task.taskId, updateTaskProgress, setCurrentTask, onComplete]);

  // 初始化和定期检查
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    // 立即检查一次
    checkTaskStatus();
    
    // 如果任务还在处理中，定期检查状态
    if (status === 'pending' || status === 'processing') {
      intervalId = setInterval(checkTaskStatus, 2000); // 每2秒检查一次
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [status, checkTaskStatus]);

  // 获取状态文本
  const getStatusText = () => {
    switch (status) {
      case 'pending':
        return '等待处理...';
      case 'processing':
        return '正在拆分PDF...';
      case 'completed':
        return '拆分完成！';
      case 'failed':
        return '拆分失败';
      default:
        return '未知状态';
    }
  };

  // 获取状态颜色
  const getStatusColor = () => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600';
      case 'processing':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="split-progress space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">PDF拆分进度</h2>
        
        <div className="space-y-6">
          {/* 任务信息 */}
          <div>
            <h3 className="text-lg font-medium text-gray-800">任务信息</h3>
            <div className="grid grid-cols-2 gap-4 mt-2">
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-600">任务ID</p>
                <p className="text-sm font-mono break-all">{task.taskId}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-600">文件ID</p>
                <p className="text-sm font-mono break-all">{task.fileId}</p>
              </div>
            </div>
          </div>
          
          {/* 进度条 */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">拆分进度</span>
              <span className={cn('text-sm font-medium', getStatusColor())}>
                {progress}%
              </span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
          
          {/* 状态信息 */}
          <div>
            <div className="flex items-center gap-2">
              <div className={cn(
                'w-3 h-3 rounded-full',
                status === 'pending' ? 'bg-yellow-400' : '',
                status === 'processing' ? 'bg-blue-400 animate-pulse' : '',
                status === 'completed' ? 'bg-green-400' : '',
                status === 'failed' ? 'bg-red-400' : ''
              )} />
              <span className={cn('text-sm font-medium', getStatusColor())}>
                {getStatusText()}
              </span>
            </div>
            
            {/* 错误信息 */}
            {errorMessage && (
              <div className="mt-3 bg-red-50 border border-red-200 rounded p-3">
                <p className="text-sm text-red-700">{errorMessage}</p>
              </div>
            )}
            
            {/* 检查状态提示 */}
            {isCheckingStatus && (
              <p className="mt-2 text-xs text-gray-500">
                正在检查任务状态...
              </p>
            )}
          </div>
          
          {/* 章节信息 */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">拆分章节</h3>
            <div className="bg-gray-50 rounded overflow-hidden border border-gray-200">
              {task.chapters.map((chapter, index) => (
                <div key={index} className="p-2 border-b last:border-b-0 border-gray-200">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-800">
                      {index + 1}. {chapter.title}
                    </span>
                    <span className="text-xs text-gray-600">
                      第 {chapter.startPage}-{chapter.endPage} 页
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// 工具函数
function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(' ');
}

export default SplitProgress;
