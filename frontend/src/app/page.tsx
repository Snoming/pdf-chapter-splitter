'use client';

import { useState } from 'react';

export default function HomePage() {
  const [currentStep, setCurrentStep] = useState<'upload' | 'preview' | 'edit' | 'split' | 'download'>('upload');

  return (
    <div className="container mx-auto px-4 py-8">
      <header className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          PDF章节拆分器
        </h1>
        <p className="text-gray-600">
          简化的在线PDF文档章节拆分工具，支持最大50MB文件
        </p>
      </header>

      {/* 步骤指示器 */}
      <div className="flex justify-center mb-8">
        <div className="flex items-center space-x-4">
          {[
            { key: 'upload', label: '上传文件' },
            { key: 'preview', label: '预览文档' },
            { key: 'edit', label: '编辑章节' },
            { key: 'split', label: '拆分处理' },
            { key: 'download', label: '下载文件' },
          ].map((step, index) => (
            <div key={step.key} className="flex items-center">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  currentStep === step.key
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {index + 1}
              </div>
              <span className="ml-2 text-sm text-gray-600">{step.label}</span>
              {index < 4 && (
                <div className="w-8 h-0.5 bg-gray-200 ml-4" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 主要内容区域 */}
      <div className="max-w-4xl mx-auto">
        {currentStep === 'upload' && (
          <div className="upload-area">
            <div className="text-center">
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
                拖拽文件到此处或点击选择文件（最大50MB）
              </p>
              <button className="btn-primary">
                选择文件
              </button>
            </div>
          </div>
        )}

        {/* 其他步骤的占位符 */}
        {currentStep !== 'upload' && (
          <div className="text-center py-12">
            <p className="text-gray-600">
              {currentStep === 'preview' && '文档预览功能开发中...'}
              {currentStep === 'edit' && '章节编辑功能开发中...'}
              {currentStep === 'split' && '拆分处理功能开发中...'}
              {currentStep === 'download' && '文件下载功能开发中...'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}