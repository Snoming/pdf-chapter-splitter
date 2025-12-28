'use client';

import React, { useEffect, useState } from 'react';
import { useAppStore, useCurrentFile, useKnowledgeGraph, useIsBuildingGraph, useKnowledgeGraphError } from '@/store/useAppStore';
import KnowledgeGraphVisualization from './KnowledgeGraphVisualization';
import { ApiService } from '@/lib/api';

interface KnowledgeGraphStepProps {
  onNextStep: () => void;
  onPrevStep: () => void;
}

export const KnowledgeGraphStep: React.FC<KnowledgeGraphStepProps> = ({ onNextStep, onPrevStep }) => {
  const currentFile = useCurrentFile();
  const knowledgeGraph = useKnowledgeGraph();
  const isBuildingGraph = useIsBuildingGraph();
  const knowledgeGraphError = useKnowledgeGraphError();
  const { setKnowledgeGraph, buildKnowledgeGraph } = useAppStore();
  
  const [useLlm, setUseLlm] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 自动构建知识图谱
  useEffect(() => {
    if (currentFile && !knowledgeGraph) {
      handleBuildGraph();
    }
  }, [currentFile, knowledgeGraph]);

  const handleBuildGraph = async () => {
    if (!currentFile) return;

    try {
      setIsLoading(true);
      setError(null);
      
      // 调用API构建知识图谱
      const result = await ApiService.getKnowledgeGraphVisualization(currentFile.fileId);
      
      // 更新状态
      setKnowledgeGraph({
        bookId: currentFile.fileId,
        nodes: result.nodes,
        links: result.links,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      });
      
      setIsLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : '构建知识图谱失败');
      setIsLoading(false);
    }
  };

  if (!currentFile) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">请先上传PDF文件</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">知识图谱</h2>
        <div className="flex space-x-3">
          <button
            className="btn-secondary"
            onClick={onPrevStep}
          >
            返回
          </button>
          <button
            className="btn-primary"
            onClick={onNextStep}
          >
            完成
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6">
          <div>
            <h3 className="text-lg font-medium text-gray-800">
              {currentFile.filename} 的知识图谱
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              基于 "书-章-节-知识点" 四层架构构建
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <div className="flex items-center space-x-2">
              <button
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${isBuildingGraph || isLoading ? 'bg-gray-400 cursor-not-allowed' : 'bg-primary-500 text-white hover:bg-primary-600'}`}
                onClick={handleBuildGraph}
                disabled={isBuildingGraph || isLoading}
              >
                {isBuildingGraph || isLoading ? '构建中...' : '重新构建图谱'}
              </button>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="use-llm"
                  checked={useLlm}
                  onChange={(e) => setUseLlm(e.target.checked)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  disabled={isBuildingGraph || isLoading}
                />
                <label htmlFor="use-llm" className="text-sm text-gray-700">
                  使用大模型增强
                </label>
              </div>
            </div>
          </div>
        </div>

        {knowledgeGraphError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h4 className="text-red-800 font-medium">构建失败</h4>
            <p className="text-red-700 text-sm mt-1">{knowledgeGraphError}</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <h4 className="text-red-800 font-medium">构建失败</h4>
            <p className="text-red-700 text-sm mt-1">{error}</p>
          </div>
        )}

        {isBuildingGraph || isLoading ? (
          <div className="flex justify-center items-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mb-4"></div>
              <h3 className="text-lg font-medium text-gray-800">正在构建知识图谱...</h3>
              <p className="text-gray-600 mt-2">这可能需要几分钟时间，请耐心等待</p>
            </div>
          </div>
        ) : knowledgeGraph ? (
          <div className="space-y-6">
            <div className="h-[600px]">
              <KnowledgeGraphVisualization
                graph={knowledgeGraph}
                width="100%"
                height={600}
              />
            </div>
            
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-800 mb-2">知识图谱统计</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500 block">总节点数</span>
                  <span className="text-gray-900 font-medium">{knowledgeGraph.nodes.length}</span>
                </div>
                <div>
                  <span className="text-gray-500 block">总边数</span>
                  <span className="text-gray-900 font-medium">{knowledgeGraph.links.length}</span>
                </div>
                <div>
                  <span className="text-gray-500 block">书籍节点</span>
                  <span className="text-gray-900 font-medium">
                    {knowledgeGraph.nodes.filter(node => node.type === 'book').length}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500 block">知识节点</span>
                  <span className="text-gray-900 font-medium">
                    {knowledgeGraph.nodes.filter(node => node.type === 'knowledge').length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600">未找到知识图谱数据</p>
            <button
              className="mt-4 px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors"
              onClick={handleBuildGraph}
            >
              手动构建图谱
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
