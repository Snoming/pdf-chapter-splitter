/**
 * 应用全局状态管理
 * 使用Zustand进行状态管理
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

// 类型定义
export interface FileInfo {
  fileId: string;
  filename: string;
  fileSize: number;
  uploadTime: string;
  status: 'uploaded' | 'analyzed' | 'split' | 'error';
}

// 对话消息类型
export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  references?: {
    page: number;
    content: string;
  }[];
  relatedKnowledge?: {
    id: string;
    label: string;
    type: string;
    relation: string;
  }[];
}

export interface KnowledgePoint {
  id?: string;
  title: string;
  content: string;
  startPage: number;
  endPage: number;
  pageCount: number;
  relatedPoints?: string[];
}

export interface SectionInfo {
  id?: string;
  title: string;
  startPage: number;
  endPage: number;
  pageCount: number;
  knowledgePoints?: KnowledgePoint[];
}

export interface ChapterInfo {
  id?: string;
  title: string;
  startPage: number;
  endPage: number;
  pageCount: number;
  sections?: SectionInfo[];
}

export interface PDFMetadata {
  fileId: string;
  filename: string;
  totalPages: number;
  fileSize: number;
  chapters: ChapterInfo[];
  createdAt: string;
  status: string;
}



export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  metadata?: any;
}

export interface KnowledgeGraphLink {
  source: string;
  target: string;
  relation: string;
  weight: number;
}

export interface KnowledgeGraph {
  bookId: string;
  nodes: KnowledgeGraphNode[];
  links: KnowledgeGraphLink[];
  createdAt: string;
  updatedAt: string;
}



// 状态接口
interface AppState {
  // 文件相关
  currentFile: FileInfo | null;
  uploadedFiles: FileInfo[]; // 新增：已上传文件列表
  pdfMetadata: PDFMetadata | null;
  
  // 章节相关
  chapters: ChapterInfo[];
  originalChapters: ChapterInfo[]; // 保存原始识别的章节
  
  // 知识图谱相关
  knowledgeGraph: KnowledgeGraph | null;
  isBuildingGraph: boolean;
  knowledgeGraphError: string | null;
  
  // 对话相关
  messages: Message[];
  isTyping: boolean;
  
  // UI状态
  isLoading: boolean;
  error: string | null;
  
  // 上传进度
  uploadProgress: number;
  uploadQueue: number; // 新增：上传队列数量
  currentUploadIndex: number; // 新增：当前上传索引
}

// 动作接口
interface AppActions {
  // 文件操作
  setCurrentFile: (file: FileInfo | null) => void;
  addUploadedFile: (file: FileInfo) => void;
  removeUploadedFile: (fileId: string) => void;
  setUploadedFiles: (files: FileInfo[]) => void;
  setPdfMetadata: (metadata: PDFMetadata | null) => void;
  
  // 章节操作
  setChapters: (chapters: ChapterInfo[]) => void;
  updateChapter: (index: number, chapter: ChapterInfo) => void;
  addChapter: (chapter: ChapterInfo) => void;
  removeChapter: (index: number) => void;
  resetChapters: () => void;
  
  // 知识图谱操作
  setKnowledgeGraph: (graph: KnowledgeGraph | null) => void;
  setIsBuildingGraph: (isBuilding: boolean) => void;
  setKnowledgeGraphError: (error: string | null) => void;
  buildKnowledgeGraph: (fileId: string, useLlm: boolean) => Promise<void>;
  
  // 对话操作
  addMessage: (message: Message) => void;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  setIsTyping: (isTyping: boolean) => void;
  
  // UI状态
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setUploadProgress: (progress: number) => void;
  setUploadQueue: (queue: number) => void;
  setCurrentUploadIndex: (index: number) => void;
  
  // 重置状态
  reset: () => void;
}

// 初始状态
const initialState: AppState = {
  currentFile: null,
  uploadedFiles: [], // 初始化为空数组
  pdfMetadata: null,
  chapters: [],
  originalChapters: [],
  knowledgeGraph: null,
  isBuildingGraph: false,
  knowledgeGraphError: null,
  messages: [],
  isTyping: false,
  isLoading: false,
  error: null,
  uploadProgress: 0,
  uploadQueue: 0, // 初始化为0
  currentUploadIndex: 0, // 初始化为0
};

// 创建store
export const useAppStore = create<AppState & AppActions>()(
  devtools(
    (set, get) => ({
      ...initialState,
      
      // 文件操作
      setCurrentFile: (file) => set({ currentFile: file }),
      
      addUploadedFile: (file) => {
        const { uploadedFiles } = get();
        // 检查文件是否已存在，避免重复添加
        const fileExists = uploadedFiles.some(existingFile => existingFile.fileId === file.fileId);
        if (!fileExists) {
          set({ uploadedFiles: [...uploadedFiles, file] });
        }
      },
      
      removeUploadedFile: (fileId) => {
        const { uploadedFiles, currentFile } = get();
        const newUploadedFiles = uploadedFiles.filter(file => file.fileId !== fileId);
        // 如果删除的是当前文件，将currentFile重置为null
        const newCurrentFile = currentFile?.fileId === fileId ? null : currentFile;
        set({ uploadedFiles: newUploadedFiles, currentFile: newCurrentFile });
      },
      
      setUploadedFiles: (files) => set({ uploadedFiles: files }),
      
      setPdfMetadata: (metadata) => set({ pdfMetadata: metadata }),
      
      // 章节操作
      setChapters: (chapters) => {
        set({ 
          chapters,
          originalChapters: chapters.length > 0 ? [...chapters] : get().originalChapters
        });
      },
      
      updateChapter: (index, chapter) => {
        const { chapters } = get();
        const newChapters = [...chapters];
        newChapters[index] = chapter;
        set({ chapters: newChapters });
      },
      
      addChapter: (chapter) => {
        const { chapters } = get();
        set({ chapters: [...chapters, chapter] });
      },
      
      removeChapter: (index) => {
        const { chapters } = get();
        const newChapters = chapters.filter((_, i) => i !== index);
        set({ chapters: newChapters });
      },
      
      resetChapters: () => {
        const { originalChapters } = get();
        set({ chapters: [...originalChapters] });
      },
      
      // UI状态
      setLoading: (isLoading) => set({ isLoading }),
      
      setError: (error) => set({ error }),
      
      setUploadProgress: (uploadProgress) => set({ uploadProgress }),
      
      setUploadQueue: (queue) => set({ uploadQueue: queue }),
      
      setCurrentUploadIndex: (index) => set({ currentUploadIndex: index }),
      
      // 知识图谱操作
      setKnowledgeGraph: (graph) => set({ knowledgeGraph: graph }),
      
      setIsBuildingGraph: (isBuilding) => set({ isBuildingGraph: isBuilding }),
      
      setKnowledgeGraphError: (error) => set({ knowledgeGraphError: error }),
      
      buildKnowledgeGraph: async (fileId, useLlm = true) => {
        try {
          set({ isBuildingGraph: true, knowledgeGraphError: null });
          
          // 调用真实API服务来构建知识图谱
          const { ApiService } = await import('@/lib/api');
          const result = await ApiService.buildKnowledgeGraph(fileId, useLlm);
          
          if (result.success && result.graph) {
            // 使用API返回的真实知识图谱数据
            set({ knowledgeGraph: result.graph, isBuildingGraph: false });
          } else {
            throw new Error(result.message || '构建知识图谱失败');
          }
        } catch (error) {
          set({ 
            knowledgeGraphError: error instanceof Error ? error.message : '构建知识图谱失败',
            isBuildingGraph: false 
          });
        }
      },
      
      // 对话操作
      addMessage: (message) => {
        const { messages } = get();
        set({ messages: [...messages, message] });
      },
      
      sendMessage: async (content) => {
        try {
          const { currentFile, messages } = get();
          if (!currentFile) {
            throw new Error('请先上传PDF文件');
          }
          
          // 添加用户消息
          const userMessage: Message = {
            id: `msg-${Date.now()}-user`,
            type: 'user',
            content,
            timestamp: new Date().toISOString(),
          };
          set({ messages: [...messages, userMessage], isTyping: true });
          
          // 模拟API调用获取回复
          // 实际项目中这里应该调用真实的后端API
          await new Promise(resolve => setTimeout(resolve, 1500));
          
          // 模拟回复消息
          const assistantMessage: Message = {
            id: `msg-${Date.now()}-assistant`,
            type: 'assistant',
            content: `这是对"${content}"的回复。\n\nPDF分析结果：\n- 文档标题：${currentFile.filename}\n- 总页数：${get().pdfMetadata?.totalPages || '未知'}\n- 章节数：${get().chapters.length || 0}`,
            timestamp: new Date().toISOString(),
            references: [
              {
                page: 1,
                content: '文档介绍部分内容...',
              },
              {
                page: 5,
                content: '相关章节内容...',
              },
            ],
            relatedKnowledge: [
              {
                id: 'knowledge-1',
                label: '知识点1',
                type: 'knowledge',
                relation: '相关',
              },
              {
                id: 'knowledge-2',
                label: '知识点2',
                type: 'knowledge',
                relation: '相关',
              },
            ],
          };
          
          set({ 
            messages: [...get().messages, assistantMessage],
            isTyping: false 
          });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : '发送消息失败',
            isTyping: false 
          });
        }
      },
      
      clearMessages: () => set({ messages: [] }),
      
      setIsTyping: (isTyping) => set({ isTyping }),
      
      // 重置状态
      reset: () => set(initialState),
    }),
    {
      name: 'pdf-splitter-store',
    }
  )
);

// 选择器hooks
export const useCurrentFile = () => useAppStore((state) => state.currentFile);
export const useUploadedFiles = () => useAppStore((state) => state.uploadedFiles);
export const usePdfMetadata = () => useAppStore((state) => state.pdfMetadata);
export const useChapters = () => useAppStore((state) => state.chapters);
export const useKnowledgeGraph = () => useAppStore((state) => state.knowledgeGraph);
export const useIsBuildingGraph = () => useAppStore((state) => state.isBuildingGraph);
export const useKnowledgeGraphError = () => useAppStore((state) => state.knowledgeGraphError);
export const useIsLoading = () => useAppStore((state) => state.isLoading);
export const useError = () => useAppStore((state) => state.error);
export const useUploadProgress = () => useAppStore((state) => state.uploadProgress);
export const useUploadQueue = () => useAppStore((state) => state.uploadQueue);
export const useCurrentUploadIndex = () => useAppStore((state) => state.currentUploadIndex);
// 对话相关选择器
export const useMessages = () => useAppStore((state) => state.messages);
export const useIsTyping = () => useAppStore((state) => state.isTyping);