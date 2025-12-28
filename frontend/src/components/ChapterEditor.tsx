/**
 * 章节编辑组件
 * 允许用户编辑、添加、删除章节
 */

'use client';

import React, { useState, useCallback } from 'react';
import { useAppStore, ChapterInfo, SectionInfo, KnowledgePoint } from '@/store/useAppStore';
import { ApiService } from '@/lib/api';

interface ChapterEditorProps {
  onSave?: () => void;
  onCancel?: () => void;
  onValidate?: () => boolean;
}

export function ChapterEditor({ onSave, onCancel, onValidate }: ChapterEditorProps) {
  const {
    chapters,
    setChapters,
    updateChapter,
    addChapter,
    removeChapter,
    resetChapters,
    pdfMetadata
  } = useAppStore();
  
  const [isValidating, setIsValidating] = useState<boolean>(false);
  const [validationIssues, setValidationIssues] = useState<string[]>([]);
  const [isValid, setIsValid] = useState<boolean>(true);
  
  // 展开状态管理
  const [expandedChapters, setExpandedChapters] = useState<Set<number>>(new Set());
  const [expandedSections, setExpandedSections] = useState<Map<number, Set<number>>>(new Map());

  // 切换章节展开状态
  const toggleChapterExpand = (index: number) => {
    const newExpanded = new Set(expandedChapters);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedChapters(newExpanded);
  };

  // 切换节展开状态
  const toggleSectionExpand = (chapterIndex: number, sectionIndex: number) => {
    const newExpanded = new Map(expandedSections);
    const chapterSections = newExpanded.get(chapterIndex) || new Set();
    if (chapterSections.has(sectionIndex)) {
      chapterSections.delete(sectionIndex);
    } else {
      chapterSections.add(sectionIndex);
    }
    newExpanded.set(chapterIndex, chapterSections);
    setExpandedSections(newExpanded);
  };

  // 更新章节
  const handleUpdateChapter = useCallback((index: number, chapter: ChapterInfo) => {
    updateChapter(index, chapter);
  }, [updateChapter]);

  // 添加章节
  const handleAddChapter = useCallback(() => {
    addChapter({
      title: `章节 ${chapters.length + 1}`, 
      startPage: 1, 
      endPage: pdfMetadata?.totalPages || 1, 
      pageCount: 1,
      sections: []
    });
  }, [addChapter, chapters, pdfMetadata]);

  // 添加节
  const handleAddSection = useCallback((chapterIndex: number) => {
    const chapter = chapters[chapterIndex];
    if (!chapter) return;

    const newSections = [...(chapter.sections || []), {
      title: `节 ${(chapter.sections?.length || 0) + 1}`,
      startPage: chapter.startPage,
      endPage: chapter.endPage,
      pageCount: 1,
      knowledgePoints: []
    }];

    const updatedChapter = {
      ...chapter,
      sections: newSections
    };

    updateChapter(chapterIndex, updatedChapter);
  }, [chapters, updateChapter]);

  // 更新节
  const handleUpdateSection = useCallback((chapterIndex: number, sectionIndex: number, section: SectionInfo) => {
    const chapter = chapters[chapterIndex];
    if (!chapter || !chapter.sections) return;

    const newSections = [...chapter.sections];
    newSections[sectionIndex] = section;

    const updatedChapter = {
      ...chapter,
      sections: newSections
    };

    updateChapter(chapterIndex, updatedChapter);
  }, [chapters, updateChapter]);

  // 移除节
  const handleRemoveSection = useCallback((chapterIndex: number, sectionIndex: number) => {
    const chapter = chapters[chapterIndex];
    if (!chapter || !chapter.sections || chapter.sections.length <= 1) return;

    const newSections = chapter.sections.filter((_, i) => i !== sectionIndex);

    const updatedChapter = {
      ...chapter,
      sections: newSections
    };

    updateChapter(chapterIndex, updatedChapter);
  }, [chapters, updateChapter]);

  // 添加知识点
  const handleAddKnowledgePoint = useCallback((chapterIndex: number, sectionIndex: number) => {
    const chapter = chapters[chapterIndex];
    if (!chapter || !chapter.sections) return;

    const section = chapter.sections[sectionIndex];
    if (!section) return;

    const newKnowledgePoints = [...(section.knowledgePoints || []), {
      title: `知识点 ${(section.knowledgePoints?.length || 0) + 1}`,
      content: '',
      startPage: section.startPage,
      endPage: section.endPage,
      pageCount: 1,
      relatedPoints: []
    }];

    const updatedSection = {
      ...section,
      knowledgePoints: newKnowledgePoints
    };

    const newSections = [...chapter.sections];
    newSections[sectionIndex] = updatedSection;

    const updatedChapter = {
      ...chapter,
      sections: newSections
    };

    updateChapter(chapterIndex, updatedChapter);
  }, [chapters, updateChapter]);

  // 更新知识点
  const handleUpdateKnowledgePoint = useCallback((
    chapterIndex: number, 
    sectionIndex: number, 
    kpIndex: number, 
    knowledgePoint: KnowledgePoint
  ) => {
    const chapter = chapters[chapterIndex];
    if (!chapter || !chapter.sections) return;

    const section = chapter.sections[sectionIndex];
    if (!section || !section.knowledgePoints) return;

    const newKnowledgePoints = [...section.knowledgePoints];
    newKnowledgePoints[kpIndex] = knowledgePoint;

    const updatedSection = {
      ...section,
      knowledgePoints: newKnowledgePoints
    };

    const newSections = [...chapter.sections];
    newSections[sectionIndex] = updatedSection;

    const updatedChapter = {
      ...chapter,
      sections: newSections
    };

    updateChapter(chapterIndex, updatedChapter);
  }, [chapters, updateChapter]);

  // 移除知识点
  const handleRemoveKnowledgePoint = useCallback((
    chapterIndex: number, 
    sectionIndex: number, 
    kpIndex: number
  ) => {
    const chapter = chapters[chapterIndex];
    if (!chapter || !chapter.sections) return;

    const section = chapter.sections[sectionIndex];
    if (!section || !section.knowledgePoints || section.knowledgePoints.length <= 1) return;

    const newKnowledgePoints = section.knowledgePoints.filter((_, i) => i !== kpIndex);

    const updatedSection = {
      ...section,
      knowledgePoints: newKnowledgePoints
    };

    const newSections = [...chapter.sections];
    newSections[sectionIndex] = updatedSection;

    const updatedChapter = {
      ...chapter,
      sections: newSections
    };

    updateChapter(chapterIndex, updatedChapter);
  }, [chapters, updateChapter]);

  // 验证章节信息
  const validateChapters = useCallback(async () => {
    if (!chapters || chapters.length === 0) {
      setValidationIssues(['章节列表不能为空']);
      setIsValid(false);
      return false;
    }

    if (!pdfMetadata) {
      setValidationIssues(['无法获取PDF元数据']);
      setIsValid(false);
      return false;
    }

    const issues: string[] = [];
    const totalPages = pdfMetadata.totalPages || 0;

    // 检查章节标题是否为空
    for (let i = 0; i < chapters.length; i++) {
      const chapter = chapters[i];
      if (!chapter.title.trim()) {
        issues.push(`第${i + 1}章标题不能为空`);
      }

      // 检查章节下的节
      if (chapter.sections) {
        for (let j = 0; j < chapter.sections.length; j++) {
          const section = chapter.sections[j];
          if (!section.title.trim()) {
            issues.push(`第${i + 1}章第${j + 1}节节标题不能为空`);
          }

          // 检查节下的知识点
          if (section.knowledgePoints) {
            for (let k = 0; k < section.knowledgePoints.length; k++) {
              const kp = section.knowledgePoints[k];
              if (!kp.title.trim()) {
                issues.push(`第${i + 1}章第${j + 1}节第${k + 1}个知识点标题不能为空`);
              }
            }
          }
        }
      }
    }

    // 检查章节页码是否连续且不超过总页数
    let lastEndPage = 0;
    for (let i = 0; i < chapters.length; i++) {
      const chapter = chapters[i];
      const startPage = chapter.startPage;
      const endPage = chapter.endPage;

      // 检查开始页码是否大于上一章结束页码
      if (startPage <= lastEndPage) {
        issues.push(`第${i + 1}章开始页码必须大于第${i}章结束页码`);
      }

      // 检查结束页码是否大于开始页码
      if (endPage < startPage) {
        issues.push(`第${i + 1}章结束页码必须大于开始页码`);
      }

      // 检查页码是否超过总页数
      if (startPage > totalPages || endPage > totalPages) {
        issues.push(`第${i + 1}章页码超出PDF总页数(${totalPages}页)`);
      }

      lastEndPage = endPage;
    }

    if (issues.length > 0) {
      setValidationIssues(issues);
      setIsValid(false);
      return false;
    }

    setValidationIssues([]);
    setIsValid(true);
    return true;
  }, [chapters, pdfMetadata]);

  // 保存章节
  const handleSave = useCallback(async () => {
    setIsValidating(true);
    
    try {
      const isValid = await validateChapters();
      if (isValid) {
        onSave?.();
      }
    } catch (error) {
      console.error('保存章节失败:', error);
      setValidationIssues(['保存章节失败，请重试']);
      setIsValid(false);
    } finally {
      setIsValidating(false);
    }
  }, [validateChapters, onSave]);

  // 取消编辑
  const handleCancel = useCallback(() => {
    onCancel?.();
  }, [onCancel]);

  // 重置章节
  const handleReset = useCallback(() => {
    resetChapters();
  }, [resetChapters]);

  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-4">章节编辑 - 四层架构</h2>
      
      {/* 验证错误信息 */}
      {!isValid && validationIssues.length > 0 && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <h3 className="font-semibold text-red-700 mb-2">验证错误</h3>
          <ul className="list-disc pl-5 space-y-1 text-red-600">
            {validationIssues.map((issue, index) => (
              <li key={index}>{issue}</li>
            ))}
          </ul>
        </div>
      )}
      
      {/* 四层架构说明 */}
      <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
        <h3 className="font-semibold text-blue-700 mb-2">四层架构说明</h3>
        <p className="text-sm text-blue-600">
          系统支持 "书-章-节-知识点" 四层架构，您可以通过点击左侧箭头展开/折叠章节和节，添加或编辑内容。
        </p>
      </div>
      
      {/* 章节列表 */}
      <div className="mb-6 space-y-4 max-h-[70vh] overflow-y-auto p-2 bg-gray-50 rounded-md">
        {chapters.map((chapter: ChapterInfo, index: number) => (
          <div key={index} className="space-y-2">
            {/* 章节标题行 */}
            <div className="flex items-center gap-3 p-3 bg-white rounded-md shadow-sm hover:shadow-md transition-shadow">
              {/* 展开/折叠按钮 */}
              <button
                onClick={() => toggleChapterExpand(index)}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                {expandedChapters.has(index) ? '▼' : '▶'}
              </button>
              
              {/* 章节标题 */}
              <div className="flex-1 min-w-0">
                <input
                  type="text"
                  placeholder={`章节 ${index + 1} 标题`}
                  value={chapter.title}
                  onChange={(e) => handleUpdateChapter(index, { ...chapter, title: e.target.value })}
                  className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              {/* 章节页码 */}
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1">
                  <span className="text-sm text-gray-600">开始:</span>
                  <input
                    type="number"
                    min="1"
                    max={pdfMetadata?.totalPages || 9999}
                    value={chapter.startPage}
                    onChange={(e) => handleUpdateChapter(index, { ...chapter, startPage: parseInt(e.target.value) || 1 })}
                    className="w-16 p-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-sm text-gray-600">结束:</span>
                  <input
                    type="number"
                    min={chapter.startPage}
                    max={pdfMetadata?.totalPages || 9999}
                    value={chapter.endPage}
                    onChange={(e) => handleUpdateChapter(index, { ...chapter, endPage: parseInt(e.target.value) || chapter.startPage })}
                    className="w-16 p-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              {/* 操作按钮 */}
              <div className="flex items-center gap-2">
                {/* 添加节按钮 */}
                <button
                  onClick={() => handleAddSection(index)}
                  className="p-1 text-blue-600 hover:bg-blue-100 rounded-md transition-colors"
                  title="添加节"
                >
                  + 节
                </button>
                
                {/* 删除章节按钮 */}
                <button
                  onClick={() => removeChapter(index)}
                  disabled={chapters.length <= 1}
                  className="p-1 text-red-600 hover:bg-red-100 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  title="删除章节"
                >
                  删除
                </button>
              </div>
            </div>
            
            {/* 展开的章节内容 */}
            {expandedChapters.has(index) && (
              <div className="ml-6 space-y-3">
                {/* 节列表 */}
                {(chapter.sections || []).map((section: SectionInfo, sectionIndex: number) => (
                  <div key={sectionIndex} className="space-y-2">
                    {/* 节标题行 */}
                    <div className="flex items-center gap-3 p-3 bg-white rounded-md shadow-sm hover:shadow-md transition-shadow">
                      {/* 展开/折叠按钮 */}
                      <button
                        onClick={() => toggleSectionExpand(index, sectionIndex)}
                        className="text-gray-500 hover:text-gray-700 transition-colors"
                      >
                        {(expandedSections.get(index)?.has(sectionIndex) || false) ? '▼' : '▶'}
                      </button>
                      
                      {/* 节标题 */}
                      <div className="flex-1 min-w-0">
                        <input
                          type="text"
                          placeholder={`节 ${sectionIndex + 1} 标题`}
                          value={section.title}
                          onChange={(e) => handleUpdateSection(index, sectionIndex, { ...section, title: e.target.value })}
                          className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                        />
                      </div>
                      
                      {/* 节页码 */}
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1">
                          <span className="text-sm text-gray-600">开始:</span>
                          <input
                            type="number"
                            min={chapter.startPage}
                            max={chapter.endPage}
                            value={section.startPage}
                            onChange={(e) => handleUpdateSection(index, sectionIndex, { ...section, startPage: parseInt(e.target.value) || chapter.startPage })}
                            className="w-14 p-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                          />
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-sm text-gray-600">结束:</span>
                          <input
                            type="number"
                            min={section.startPage}
                            max={chapter.endPage}
                            value={section.endPage}
                            onChange={(e) => handleUpdateSection(index, sectionIndex, { ...section, endPage: parseInt(e.target.value) || section.startPage })}
                            className="w-14 p-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                          />
                        </div>
                      </div>
                      
                      {/* 操作按钮 */}
                      <div className="flex items-center gap-2">
                        {/* 添加知识点按钮 */}
                        <button
                          onClick={() => handleAddKnowledgePoint(index, sectionIndex)}
                          className="p-1 text-purple-600 hover:bg-purple-100 rounded-md transition-colors"
                          title="添加知识点"
                        >
                          + 知识点
                        </button>
                        
                        {/* 删除节按钮 */}
                        <button
                          onClick={() => handleRemoveSection(index, sectionIndex)}
                          disabled={!chapter.sections || chapter.sections.length <= 1}
                          className="p-1 text-red-600 hover:bg-red-100 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          title="删除节"
                        >
                          删除
                        </button>
                      </div>
                    </div>
                    
                    {/* 展开的节内容 */}
                    {(expandedSections.get(index)?.has(sectionIndex) || false) && (
                      <div className="ml-6 space-y-3">
                        {/* 知识点列表 */}
                        {(section.knowledgePoints || []).map((kp: KnowledgePoint, kpIndex: number) => (
                          <div key={kpIndex} className="p-3 bg-white rounded-md shadow-sm hover:shadow-md transition-shadow">
                            {/* 知识点标题 */}
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-medium text-purple-700">知识点 {kpIndex + 1}:</span>
                              <input
                                type="text"
                                placeholder={`知识点标题`}
                                value={kp.title}
                                onChange={(e) => handleUpdateKnowledgePoint(index, sectionIndex, kpIndex, { ...kp, title: e.target.value })}
                                className="flex-1 p-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                              />
                            </div>
                            
                            {/* 知识点内容 */}
                            <div className="mb-2">
                              <textarea
                                placeholder={`知识点内容`}
                                value={kp.content}
                                onChange={(e) => handleUpdateKnowledgePoint(index, sectionIndex, kpIndex, { ...kp, content: e.target.value })}
                                className="w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                                rows={2}
                              />
                            </div>
                            
                            {/* 知识点页码 */}
                            <div className="flex items-center gap-3 mb-2">
                              <div className="flex items-center gap-1">
                                <span className="text-xs text-gray-600">开始:</span>
                                <input
                                  type="number"
                                  min={section.startPage}
                                  max={section.endPage}
                                  value={kp.startPage}
                                  onChange={(e) => handleUpdateKnowledgePoint(index, sectionIndex, kpIndex, { ...kp, startPage: parseInt(e.target.value) || section.startPage })}
                                  className="w-12 p-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                                />
                              </div>
                              <div className="flex items-center gap-1">
                                <span className="text-xs text-gray-600">结束:</span>
                                <input
                                  type="number"
                                  min={kp.startPage}
                                  max={section.endPage}
                                  value={kp.endPage}
                                  onChange={(e) => handleUpdateKnowledgePoint(index, sectionIndex, kpIndex, { ...kp, endPage: parseInt(e.target.value) || kp.startPage })}
                                  className="w-12 p-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                                />
                              </div>
                            </div>
                            
                            {/* 删除知识点按钮 */}
                            <button
                              onClick={() => handleRemoveKnowledgePoint(index, sectionIndex, kpIndex)}
                              disabled={!section.knowledgePoints || section.knowledgePoints.length <= 1}
                              className="text-xs px-2 py-1 text-red-600 hover:bg-red-100 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                              title="删除知识点"
                            >
                              删除知识点
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                
                {/* 空状态提示 */}
                {!chapter.sections || chapter.sections.length === 0 && (
                  <div className="ml-6 p-3 text-sm text-gray-500 italic">
                    点击 "+ 节" 按钮添加节
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* 操作按钮 */}
      <div className="flex flex-wrap gap-3 mb-4">
        <button
          onClick={handleAddChapter}
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
        >
          添加章节
        </button>
        <button
          onClick={handleReset}
          className="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 transition-colors"
        >
          重置章节
        </button>
      </div>
      
      {/* 底部按钮 */}
      <div className="flex justify-end gap-3">
        <button
          onClick={handleCancel}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
        >
          取消
        </button>
        <button
          onClick={handleSave}
          disabled={isValidating}
          className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isValidating ? '保存中...' : '保存章节'}
        </button>
      </div>
    </div>
  );
}
