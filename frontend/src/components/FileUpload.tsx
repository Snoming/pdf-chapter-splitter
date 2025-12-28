/**
 * 文件上传组件
 * 支持拖拽上传和文件选择器
 */

'use client';

import React, { useCallback, useState, useRef } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { ApiService } from '@/lib/api';
import { validateFileType, validateFileSize, formatFileSize, getErrorMessage } from '@/lib/utils';
import { InlineLoading } from './Loading';

interface FileUploadProps {
  onUploadSuccess?: (fileInfo: any) => void;
  onUploadError?: (error: string) => void;
  maxSizeMB?: number;
  className?: string;
}

export function FileUpload({ 
  onUploadSuccess, 
  onUploadError, 
  maxSizeMB = 50,
  className = '' 
}: FileUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const { 
    setCurrentFile, 
    setUploadProgress, 
    setError, 
    setLoading,
    addUploadedFile,
    setUploadQueue,
    setCurrentUploadIndex
  } = useAppStore();

  // 批量处理文件上传
  const handleFileUpload = useCallback(async (files: File[]) => {
    try {
      if (files.length === 0) return;
      
      setIsUploading(true);
      setError(null);
      setUploadProgress(0);
      
      // 设置上传队列信息
      setUploadQueue(files.length);
      setCurrentUploadIndex(0);

      // 遍历上传文件
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setCurrentUploadIndex(i + 1);
        
        // 验证文件类型
        if (!validateFileType(file)) {
          throw new Error(`文件 ${file.name} 不是PDF文件，请选择PDF文件`);
        }

        // 验证文件大小
        if (!validateFileSize(file, maxSizeMB)) {
          throw new Error(`文件 ${file.name} 大小超过${maxSizeMB}MB限制`);
        }

        console.log(`开始上传文件 ${i + 1}/${files.length}:`, file.name, formatFileSize(file.size));
        
        // 上传文件
        const fileInfo = await ApiService.uploadFile(file, (progress) => {
          setUploadProgress(progress);
        });

        console.log('文件上传成功:', fileInfo);

        // 更新状态
        addUploadedFile(fileInfo);
        
        // 如果是第一个文件，设置为当前文件
        if (i === 0) {
          setCurrentFile(fileInfo);
        }
        
        // 回调
        onUploadSuccess?.(fileInfo);
      }

    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error('文件上传失败:', errorMessage);
      
      setError(errorMessage);
      onUploadError?.(errorMessage);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      setUploadQueue(0);
      setCurrentUploadIndex(0);
    }
  }, [maxSizeMB, setCurrentFile, setUploadProgress, setError, setLoading, onUploadSuccess, onUploadError, addUploadedFile, setUploadQueue, setCurrentUploadIndex]);

  // 拖拽事件处理
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files);
    }
  }, [handleFileUpload]);

  // 文件选择处理
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(Array.from(files));
    }
    // 清空input值，允许重复选择同一文件
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [handleFileUpload]);

  // 点击选择文件
  const handleSelectClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  return (
    <div className={`w-full ${className}`}>
      <div
        className={`
          upload-area
          ${isDragOver ? 'dragover' : ''}
          ${isUploading ? 'pointer-events-none opacity-75' : 'cursor-pointer'}
        `}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleSelectClick}
      >
        <div className="text-center">
          {isUploading ? (
            <div className="space-y-4">
              <div className="mx-auto h-12 w-12 text-primary-500">
                <svg className="animate-spin h-full w-full" fill="none" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  正在上传文件...
                </h3>
                <div className="w-full max-w-xs mx-auto space-y-3">
                  {/* 上传队列信息 */}
                  {useAppStore.getState().uploadQueue > 1 && (
                    <div className="text-sm text-gray-600">
                      正在上传 {useAppStore.getState().currentUploadIndex}/{useAppStore.getState().uploadQueue}
                    </div>
                  )}
                  {/* 进度条 */}
                  <div className="progress-bar">
                    <div 
                      className="progress-fill"
                      style={{ width: `${useAppStore.getState().uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-sm text-gray-600 mt-1 text-center">
                    {useAppStore.getState().uploadProgress}%
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <>
              <svg
                className="mx-auto h-12 w-12 text-gray-400 mb-4"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                上传PDF文件
              </h3>
              <p className="text-gray-600 mb-4">
                拖拽文件到此处或点击选择文件
              </p>
              <p className="text-sm text-gray-500 mb-4">
                支持PDF格式，最大{maxSizeMB}MB
              </p>
              <button 
                className="btn-primary"
                disabled={isUploading}
              >
                选择文件
              </button>
            </>
          )}
        </div>
      </div>

      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileSelect}
        className="hidden"
        multiple // 新增：支持多文件选择
      />
    </div>
  );
}

// 简化版文件上传组件
export function SimpleFileUpload() {
  return (
    <FileUpload
      onUploadSuccess={(fileInfo) => {
        console.log('文件上传成功:', fileInfo);
      }}
      onUploadError={(error) => {
        console.error('文件上传失败:', error);
      }}
    />
  );
}

export default FileUpload;