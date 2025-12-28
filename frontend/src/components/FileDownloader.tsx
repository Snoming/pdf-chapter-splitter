/**
 * 文件下载组件
 * 显示可下载的章节文件，并提供下载功能
 */

'use client';

import React, { useState } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { ApiService } from '@/lib/api';

interface FileDownloaderProps {
  onRestart?: () => void;
}

export function FileDownloader({ onRestart }: FileDownloaderProps) {
  const { currentFile, currentTask } = useAppStore();
  const [previewFile, setPreviewFile] = useState<string | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(false);

  // 获取文件下载链接
  const getDownloadUrl = (filename: string) => {
    // 优先使用currentTask的fileId，因为它是当前拆分任务的fileId
    const fileId = currentTask?.fileId || currentFile?.fileId;
    if (!fileId) return '';
    return ApiService.getDownloadUrl(fileId, filename);
  };
  
  // 获取预览URL
  const getPreviewUrl = (filename: string) => {
    // 优先使用currentTask的fileId，因为它是当前拆分任务的fileId
    const fileId = currentTask?.fileId || currentFile?.fileId;
    if (!fileId) return '';
    // 使用download=false参数确保文件预览而非下载
    return ApiService.getDownloadUrl(fileId, filename, false);
  };
  
  // 打开预览
  const openPreview = (filename: string) => {
    setPreviewFile(filename);
    setIsPreviewOpen(true);
  };
  
  // 关闭预览
  const closePreview = () => {
    setIsPreviewOpen(false);
    setPreviewFile(null);
  };

  // 下载所有文件（在新标签页中打开）
  const downloadAllFiles = () => {
    if (!currentTask?.downloadLinks) return;
    
    currentTask.downloadLinks.forEach(link => {
      const url = getDownloadUrl(link);
      window.open(url, '_blank');
    });
  };

  // 单个文件下载
  const downloadFile = (filename: string) => {
    const url = getDownloadUrl(filename);
    window.open(url, '_blank');
  };

  // 获取文件大小（模拟）
  const getFileSize = (filename: string) => {
    // 这里应该从后端获取实际文件大小，目前使用模拟数据
    return `${Math.floor(Math.random() * 1000) + 100} KB`;
  };

  if (!currentFile || !currentTask) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">请先完成PDF拆分</p>
      </div>
    );
  }

  return (
    <div className="file-downloader space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">下载文件</h2>
          <p className="text-sm text-gray-600 mt-1">
            共 {currentTask.downloadLinks.length} 个文件
          </p>
        </div>
        
        <div className="flex gap-2">
          <button 
            className="btn-primary"
            onClick={downloadAllFiles}
            disabled={currentTask.downloadLinks.length === 0}
          >
            下载所有文件
          </button>
          {onRestart && (
            <button 
              className="btn-secondary"
              onClick={onRestart}
            >
              重新开始
            </button>
          )}
        </div>
      </div>
      
      {/* 拆分章节文件列表 */}
      
      {/* 拆分后的章节文件 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-lg font-medium text-gray-800 mb-3">拆分章节文件</h3>
        
        {currentTask.downloadLinks.length === 0 ? (
          <div className="text-center py-6">
            <p className="text-gray-500">暂无可下载的章节文件</p>
          </div>
        ) : (
          <div className="space-y-2">
            {currentTask.downloadLinks.map((filename, index) => (
              <div key={index} className="flex items-center justify-between p-3 border border-gray-200 rounded hover:bg-gray-50 transition-colors">
                <div>
                  <p className="font-medium text-gray-800">{filename}</p>
                  <p className="text-sm text-gray-600">
                    文件大小: {getFileSize(filename)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button 
                    className="text-blue-500 hover:text-blue-600 flex items-center gap-1"
                    onClick={() => openPreview(filename)}
                    title="预览章节"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    预览
                  </button>
                  <button 
                    className="text-primary-500 hover:text-primary-600 flex items-center gap-1"
                    onClick={() => downloadFile(filename)}
                    title="下载章节"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    下载
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* 完成提示 */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-green-800">
              PDF章节拆分已完成！
            </h3>
            <div className="mt-2 text-sm text-green-700">
              <p>
                您已成功拆分PDF文件，共生成 {currentTask.downloadLinks.length} 个章节文件。
              </p>
              <p className="mt-1">
                您可以预览章节内容后再下载，或直接下载单个文件或全部文件，然后重新开始处理新的PDF文件。
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* 预览模态框 */}
      {isPreviewOpen && previewFile && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* 模态框头部 */}
            <div className="flex justify-between items-center p-4 border-b">
              <h3 className="text-lg font-semibold text-gray-900">
                章节预览: {previewFile}
              </h3>
              <div className="flex gap-2">
                <button
                  onClick={() => downloadFile(previewFile)}
                  className="px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600"
                >
                  下载此章节
                </button>
                <button
                  onClick={closePreview}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                >
                  关闭
                </button>
              </div>
            </div>
            
            {/* 预览内容 */}
            <div className="flex-1 overflow-auto">
              <iframe
                src={getPreviewUrl(previewFile)}
                title={`Preview: ${previewFile}`}
                className="w-full h-[70vh] border-0"
              />
            </div>
            
            {/* 模态框底部 */}
            <div className="p-4 border-t text-center text-sm text-gray-500">
              <p>使用PDF阅读器查看章节内容，确认无误后可点击下载按钮保存到本地。</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default FileDownloader;
