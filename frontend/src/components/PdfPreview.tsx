/**
 * PDF预览组件
 * 使用iframe嵌入方式实现PDF预览，确保与Next.js 14兼容
 */

'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { useAppStore } from '@/store/useAppStore';
import { ApiService } from '@/lib/api';
import { InlineLoading } from './Loading';

interface PdfPreviewProps {
  fileId: string;
  filename: string;
  onPageChange?: (page: number) => void;
}

export function PdfPreview({ fileId, filename, onPageChange }: PdfPreviewProps) {
  const [pdfUrl, setPdfUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [totalPages, setTotalPages] = useState<number>(0);

  // 获取PDF文件URL
  const getPdfUrl = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // 构建PDF文件的预览URL（不强制下载）
      const url = ApiService.getDownloadUrl(fileId, undefined, false);
      setPdfUrl(url);
      
    } catch (err) {
      setError('获取PDF文件失败');
      console.error('获取PDF文件失败:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fileId]);

  // 初始化PDF预览
  useEffect(() => {
    getPdfUrl();
  }, [getPdfUrl]);

  // 处理页码变化
  const handlePageChange = useCallback((newPageNumber: number) => {
    setPageNumber(newPageNumber);
    if (onPageChange) {
      onPageChange(newPageNumber);
    }
  }, [onPageChange]);

  // 处理iframe加载完成
  const handleIframeLoad = useCallback((event: React.SyntheticEvent<HTMLIFrameElement>) => {
    const iframe = event.target as HTMLIFrameElement;
    console.log('PDF iframe加载完成');
    
    // 尝试获取PDF总页数（这个方法只在部分浏览器中有效）
    try {
      // 这是一个尝试，不同浏览器和PDF查看器可能支持不同的API
      // 对于不支持的浏览器，我们就不显示总页数
    } catch (err) {
      console.log('无法获取PDF总页数:', err);
    }
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {filename}
        </h3>
      </div>
      
      {/* PDF内容区域 */}
      <div className="flex justify-center mb-4 bg-gray-50 p-4 rounded-md">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-96">
            <InlineLoading text="加载PDF中..." />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-96 text-center">
            <svg
              className="w-12 h-12 mb-2 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-red-600 mb-2">{error}</p>
            <button
              onClick={getPdfUrl}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            >
              重试
            </button>
          </div>
        ) : pdfUrl ? (
          <div className="w-full max-w-4xl">
            {/* 使用iframe嵌入PDF */}
            <iframe
              src={pdfUrl}
              title={`PDF Preview: ${filename}`}
              className="w-full h-[800px] border border-gray-200 rounded-md shadow-sm"
              onLoad={handleIframeLoad}
              frameBorder="0"
            />
            
            {/* PDF操作链接 */}
            <div className="mt-4 flex justify-between items-center">
              <a
                href={pdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                🔗 在新窗口中打开PDF
              </a>
              
              <a
                href={ApiService.getDownloadUrl(fileId, undefined, true)}
                className="text-blue-600 hover:text-blue-800 text-sm"
              >
                💾 下载PDF文件
              </a>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-96">
            <p className="text-gray-600">无法加载PDF文件</p>
          </div>
        )}
      </div>
    </div>
  );
}
