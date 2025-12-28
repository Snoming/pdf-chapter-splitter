'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAppStore, useCurrentFile, useUploadedFiles, useMessages, useIsTyping, useIsLoading, useError, useKnowledgeGraph } from '@/store/useAppStore';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { FullScreenLoading } from '@/components/Loading';
import { FileUpload } from '@/components/FileUpload';
import { ApiService } from '@/lib/api';
import KnowledgeGraphVisualization from '@/components/KnowledgeGraphVisualization';

function ErrorAlert() {
  const error = useError();
  const { setError } = useAppStore();

  if (!error) return null;

  return (
    <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">操作失败</h3>
          <p className="mt-1 text-sm text-red-700">{error}</p>
        </div>
        <div className="ml-auto pl-3">
          <button onClick={() => setError(null)} className="inline-flex text-red-400 hover:text-red-600">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: any }) {
  const isUser = message.type === 'user';
  
  return (
    <div className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] ${isUser ? 'flex items-end' : 'flex items-end'}`}>
        <div className={`w-8 h-8 rounded-full mr-2 ${isUser ? 'order-2 bg-blue-600 text-white flex items-center justify-center' : 'order-1 bg-purple-600 text-white flex items-center justify-center'}`}>
          {isUser ? '我' : 'AI'}
        </div>
        
        <div className={`rounded-lg shadow-md p-4 ${isUser ? 
          'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-tr-none' : 
          'bg-white text-gray-900 rounded-tl-none border border-gray-200'}`}>
          <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
          
          {message.references && message.references.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-300/30 text-sm">
              <h4 className="font-semibold mb-2 text-gray-700 dark:text-gray-300">📚 引用内容</h4>
              {message.references.map((ref: any, index: number) => (
                <div key={index} className="mb-2 p-3 bg-white/90 dark:bg-gray-800/90 rounded-lg shadow-sm border border-gray-200/50">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">第 {ref.page} 页</span>
                    <span className="text-xs text-gray-500">PDF原文</span>
                  </div>
                  <div className="text-sm text-gray-800 dark:text-gray-200 leading-tight">{ref.content}</div>
                </div>
              ))}
            </div>
          )}
          
          {message.relatedKnowledge && message.relatedKnowledge.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-300/30 text-sm">
              <h4 className="font-semibold mb-2 text-gray-700 dark:text-gray-300">🔗 相关知识点</h4>
              <div className="flex flex-wrap gap-2">
                {message.relatedKnowledge.map((knowledge: any, index: number) => (
                  <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-xs hover:bg-blue-200 transition-colors cursor-pointer">
                    {knowledge.label}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          <div className={`text-xs mt-2 opacity-75 ${isUser ? 'text-right' : 'text-left'}`}>
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-end">
        <div className="w-8 h-8 rounded-full mr-2 bg-purple-600 text-white flex items-center justify-center">AI</div>
        
        <div className="bg-white text-gray-900 p-4 rounded-lg shadow-sm rounded-tl-none border border-gray-200 max-w-[200px]">
          <div className="flex space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ChatInput() {
  const [input, setInput] = useState('');
  const { sendMessage } = useAppStore();
  const currentFile = useCurrentFile();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && currentFile) {
      await sendMessage(input.trim());
      setInput('');
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="flex space-x-3">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={currentFile ? '请输入您的问题...' : '请先上传PDF文件'}
        disabled={!currentFile}
        className="flex-1 px-5 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-500 placeholder-gray-400 text-gray-900 shadow-sm"
      />
      <button
        type="submit"
        disabled={!input.trim() || !currentFile}
        className="px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-full hover:from-blue-600 hover:to-blue-700 transition-all disabled:bg-gray-300 disabled:cursor-not-allowed shadow-md hover:shadow-lg flex items-center justify-center"
      >
        <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      </button>
    </form>
  );
}

function MessageContainer() {
  const messages = useMessages();
  const isTyping = useIsTyping();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const currentFile = useCurrentFile();
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);
  
  return (
    <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-gray-50 to-gray-100">
      {messages.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-24 h-24 mx-auto mb-6 bg-blue-100 rounded-full flex items-center justify-center">
            <svg className="h-16 w-16 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-3">开始智能对话</h3>
          <p className="text-gray-600 max-w-md mx-auto">
            {currentFile ? (
              <>上传的PDF文件已准备就绪，您可以开始提问关于文件内容的问题</>
            ) : (
              <>请先在左侧上传PDF文件，上传完成后即可开始对话</>
            )}
          </p>
          {currentFile && (
            <div className="mt-6 px-6 py-4 bg-white rounded-lg shadow-sm border border-gray-200 inline-block">
              <p className="text-sm text-gray-600">💡 提示：</p>
              <p className="text-sm text-gray-600">您可以问"文档的主要内容是什么？"或"第5页讲了什么？"</p>
            </div>
          )}
        </div>
      ) : (
        messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))
      )}
      
      {isTyping && <TypingIndicator />}
      
      <div ref={messagesEndRef} />
    </div>
  );
}

function KnowledgeGraphSection() {
  const knowledgeGraph = useKnowledgeGraph();
  const currentFile = useCurrentFile();
  const { buildKnowledgeGraph, setKnowledgeGraphError } = useAppStore();
  const [isBuilding, setIsBuilding] = useState(false);
  
  const handleBuildGraph = async () => {
    if (!currentFile) return;
    
    try {
      setIsBuilding(true);
      setKnowledgeGraphError(null);
      await buildKnowledgeGraph(currentFile.fileId, true);
    } catch (error) {
      setKnowledgeGraphError(error instanceof Error ? error.message : '构建知识图谱失败');
    } finally {
      setIsBuilding(false);
    }
  };
  
  return (
    <div className="h-full flex flex-col">
      <div className="mb-4 flex justify-between items-center">
        {currentFile && (
          <button
            onClick={handleBuildGraph}
            disabled={isBuilding}
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all disabled:bg-gray-300 disabled:cursor-not-allowed text-sm shadow-sm hover:shadow-md"
          >
            {isBuilding ? (
              <div className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                构建中...
              </div>
            ) : knowledgeGraph ? (
              '重新构建图谱'
            ) : (
              '构建图谱'
            )}
          </button>
        )}
      </div>
      
      {knowledgeGraph ? (
        <div className="flex-1 bg-gray-50 rounded-lg border border-gray-200 overflow-hidden shadow-inner">
          <KnowledgeGraphVisualization graph={knowledgeGraph} width="100%" height="100%" isBuilding={isBuilding} />
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg border border-gray-200">
          <div className="text-center p-6">
            {currentFile ? (
              <>
                <div className="w-20 h-20 mx-auto mb-4 bg-purple-100 rounded-full flex items-center justify-center">
                  <svg className="h-12 w-12 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h4 className="text-lg font-medium text-gray-900 mb-2">构建知识图谱</h4>
                <p className="text-gray-600 text-sm mb-4">点击上方按钮生成文档的知识图谱</p>
                <div className="text-xs text-gray-500">
                  知识图谱将展示文档中的实体关系和关键概念
                </div>
              </>
            ) : (
              <>
                <div className="w-20 h-20 mx-auto mb-4 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="h-12 w-12 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h4 className="text-lg font-medium text-gray-900 mb-2">等待文件上传</h4>
                <p className="text-gray-600 text-sm">请先在左侧上传PDF文件</p>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function LeftSidebar() {
  const currentFile = useCurrentFile();
  const uploadedFiles = useUploadedFiles();
  const { setCurrentFile, setChapters, setLoading, setError, setPdfMetadata, removeUploadedFile } = useAppStore();
  
  const handleUploadSuccess = async (fileInfo: any) => {
    try {
      setLoading(true);
      setError(null);
      
      // 只有当没有当前文件时，才自动设置为当前文件
      if (!currentFile) {
        setCurrentFile(fileInfo);
        
        const result = await ApiService.analyzeChapters(fileInfo.fileId);
        setChapters(result.chapters);
        
        setPdfMetadata({
          fileId: fileInfo.fileId,
          filename: fileInfo.filename,
          totalPages: result.totalPages,
          fileSize: fileInfo.fileSize,
          chapters: result.chapters,
          createdAt: new Date().toISOString(),
          status: 'analyzed'
        });
      }
    } catch (err) {
      setError('章节分析失败，请重试');
      console.error('章节分析失败:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleFileSelect = async (file: any) => {
    try {
      setLoading(true);
      setError(null);
      setCurrentFile(file);
      
      const result = await ApiService.analyzeChapters(file.fileId);
      setChapters(result.chapters);
      
      setPdfMetadata({
        fileId: file.fileId,
        filename: file.filename,
        totalPages: result.totalPages,
        fileSize: file.fileSize,
        chapters: result.chapters,
        createdAt: new Date().toISOString(),
        status: 'analyzed'
      });
    } catch (err) {
      setError('章节分析失败，请重试');
      console.error('章节分析失败:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleRemoveFile = (fileId: string) => {
    removeUploadedFile(fileId);
  };
  
  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 p-4 h-full min-h-[500px] flex flex-col">
      <div className="flex-1 flex flex-col">
        {/* 文件上传区域 */}
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">文件上传</h2>
          <p className="text-sm text-gray-600 mb-4">上传PDF文件，支持最大50MB，可批量上传</p>
          
          <FileUpload
            onUploadSuccess={handleUploadSuccess}
            onUploadError={(error) => setError(error)}
            maxSizeMB={50}
          />
        </div>
        
        {/* 已上传文件列表 */}
        {uploadedFiles.length > 0 && (
          <div className="mt-6 flex-1 overflow-y-auto">
            <h3 className="text-md font-semibold text-gray-900 mb-3 flex items-center">
              <svg className="h-4 w-4 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              已上传文件 ({uploadedFiles.length})
            </h3>
            
            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
              {uploadedFiles.map((file) => (
                <div 
                  key={file.fileId}
                  className={`flex items-center justify-between p-3 rounded-lg border transition-all duration-200 cursor-pointer ${currentFile?.fileId === file.fileId ? 'border-blue-500 bg-blue-50 shadow-sm' : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'}`}
                  onClick={() => handleFileSelect(file)}
                >
                  <div className="flex items-center flex-1 min-w-0">
                    <div className="flex-shrink-0 h-8 w-8 rounded-md bg-blue-100 flex items-center justify-center text-blue-600">
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="ml-3 flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.filename}
                      </p>
                      <p className="text-xs text-gray-500 flex items-center">
                        {(file.fileSize / (1024 * 1024)).toFixed(2)} MB • 
                        <span className="ml-1">{new Date(file.uploadTime).toLocaleTimeString()}</span>
                      </p>
                    </div>
                  </div>
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation(); // 阻止事件冒泡，避免触发文件选择
                      handleRemoveFile(file.fileId);
                    }}
                    className="ml-3 p-1 rounded-full text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                    title="删除文件"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MiddleChatArea() {
  return (
    <div className="bg-white rounded-xl shadow-md border border-gray-200 h-full min-h-[500px] flex flex-col">
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-xl">
        <h2 className="text-lg font-semibold text-gray-900">智能对话</h2>
        <p className="text-sm text-gray-600">针对上传的PDF内容进行提问</p>
      </div>
      <MessageContainer />
      <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
        <ChatInput />
      </div>
    </div>
  );
}

function KnowledgeGraphModal({ isOpen, onClose, graph }: { isOpen: boolean; onClose: () => void; graph: any }) {
  if (!isOpen || !graph) return null;
  
  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-pink-50 rounded-t-xl flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900">知识图谱 - 全屏查看</h2>
          <button 
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="flex-1 p-6 overflow-hidden">
          <div className="w-full h-full bg-gray-50 rounded-lg border border-gray-200 overflow-hidden shadow-inner">
            <KnowledgeGraphVisualization graph={graph} />
          </div>
        </div>
        
        <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-xl text-center">
          <p className="text-sm text-gray-600">点击空白区域或右上角关闭按钮退出全屏查看</p>
        </div>
      </div>
    </div>
  );
}

function RightKnowledgeGraphArea() {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const knowledgeGraph = useKnowledgeGraph();
  
  return (
    <>
      <div className="bg-white rounded-xl shadow-md border border-gray-200 h-full min-h-[500px] flex flex-col">
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-pink-50 rounded-t-xl">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">知识图谱</h2>
              <p className="text-sm text-gray-600">可视化展示文档知识结构</p>
            </div>
            {knowledgeGraph && (
              <button 
                onClick={() => setIsFullscreen(true)}
                className="text-gray-500 hover:text-purple-600 transition-colors p-2 rounded-full hover:bg-purple-100"
                title="全屏查看"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              </button>
            )}
          </div>
        </div>
        <div className="p-4 overflow-hidden flex-1">
          <KnowledgeGraphSection />
        </div>
      </div>
      
      <KnowledgeGraphModal 
        isOpen={isFullscreen} 
        onClose={() => setIsFullscreen(false)} 
        graph={knowledgeGraph} 
      />
    </>
  );
}

function HomePage() {
  const isLoading = useIsLoading();
  
  return (
    <>
      {isLoading && <FullScreenLoading />}
      
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <header className="bg-white shadow-md border-b border-gray-200">
          <div className="container mx-auto px-4 py-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
              <div>
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
                  <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600">
                    PDF对话助手
                  </span>
                </h1>
                <p className="text-gray-600">上传PDF文件，进行智能对话和知识图谱分析</p>
              </div>
              <div className="mt-4 md:mt-0 flex items-center space-x-2">
                <div className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                  支持PDF格式
                </div>
                <div className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                  最大50MB
                </div>
              </div>
            </div>
          </div>
        </header>
        
        <main className="container mx-auto px-4 py-8">
          <ErrorAlert />
          
          <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-12 gap-6">
            <div className="md:col-span-4 lg:col-span-3">
              <LeftSidebar />
            </div>
            
            <div className="md:col-span-4 lg:col-span-6">
              <MiddleChatArea />
            </div>
            
            <div className="md:col-span-4 lg:col-span-3">
              <RightKnowledgeGraphArea />
            </div>
          </div>
        </main>
        

      </div>
    </>
  );
}

export default function HomePageWithErrorBoundary() {
  return (
    <ErrorBoundary>
      <HomePage />
    </ErrorBoundary>
  );
}
