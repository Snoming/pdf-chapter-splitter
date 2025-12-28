/**
 * API客户端
 * 处理与后端服务的通信
 */

import axios, { AxiosProgressEvent } from 'axios';
import { FileInfo, ChapterInfo, PDFMetadata, SplitTask } from '@/store/useAppStore';

// API基础配置 - WSL2环境适配
const getApiBaseUrl = () => {
  // 优先使用环境变量配置
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // WSL2环境下的地址检测
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // 如果是在WSL2环境中运行，尝试不同的地址
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8080';
    }
    
    // 如果是Docker环境或其他网络环境
    return `http://${hostname}:8080`;
  }
  
  // 服务端渲染时的默认地址
  return 'http://localhost:8080';
};

const API_BASE_URL = getApiBaseUrl();

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30秒超时
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 添加明显的日志标记，确保能被看到
    console.log('🔄 [API请求]', `${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ [API请求错误]', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ [API响应]', `${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    // 统一错误处理
    const errorMessage = error.response?.data?.detail || 
                        error.response?.data?.message || 
                        error.message || 
                        '网络请求失败';
    
    console.error('❌ [API错误]', `${error.response?.status} ${error.config.url} - ${errorMessage}`);
    return Promise.reject(new Error(errorMessage));
  }
);

// 添加全局调试日志，确保日志系统正常工作
console.log('📝 [前端应用] 初始化完成，API客户端已配置');


// API接口定义
export interface UploadResponse {
  file_id: string;
  filename: string;
  file_size: number;
  message: string;
}

export interface AnalyzeRequest {
  file_id: string;
  auto_detect?: boolean;
  min_pages_per_chapter?: number;
}

export interface AnalyzeResponse {
  success: boolean;
  chapters: ChapterInfo[];
  total_pages: number;
  message?: string;
  suggestions?: ChapterInfo[];
}



// API方法
export class ApiService {
  /**
   * 上传PDF文件
   */
  static async uploadFile(
    file: File, 
    onProgress?: (progress: number) => void
  ): Promise<FileInfo> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post<UploadResponse>('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    
    const data = response.data;
    
    return {
      fileId: data.file_id,
      filename: data.filename,
      fileSize: data.file_size,
      uploadTime: new Date().toISOString(),
      status: 'uploaded',
    };
  }
  
  /**
   * 分析PDF章节结构
   */
  static async analyzeChapters(fileId: string): Promise<{
    chapters: ChapterInfo[];
    totalPages: number;
    suggestions?: ChapterInfo[];
  }> {
    const request: AnalyzeRequest = {
      file_id: fileId,
      auto_detect: true,
      min_pages_per_chapter: 1,
    };
    
    const response = await apiClient.post<AnalyzeResponse>('/api/analyze', request);
    const data = response.data;
    
    return {
      chapters: data.chapters.map(chapter => {
        const ch = chapter as any;
        return {
          title: ch.title,
          startPage: ch.start_page || ch.startPage,
          endPage: ch.end_page || ch.endPage,
          pageCount: ch.page_count || ch.pageCount || (ch.end_page - ch.start_page + 1),
        };
      }),
      totalPages: data.total_pages,
      suggestions: data.suggestions?.map(chapter => {
        const ch = chapter as any;
        return {
          title: ch.title,
          startPage: ch.start_page || ch.startPage,
          endPage: ch.end_page || ch.endPage,
          pageCount: ch.page_count || ch.pageCount || (ch.end_page - ch.start_page + 1),
        };
      }),
    };
  }
  

  
  /**
   * 获取PDF信息
   */
  static async getPdfInfo(fileId: string): Promise<{
    fileId: string;
    filename: string;
    fileSize: number;
    uploadTime: string;
    status: string;
  }> {
    const response = await apiClient.get(`/api/pdf-info/${fileId}`);
    return {
      fileId: response.data.file_id,
      filename: response.data.filename,
      fileSize: response.data.file_size,
      uploadTime: response.data.upload_time,
      status: response.data.status,
    };
  }
  
  /**
   * 验证章节信息
   */
  static async validateChapters(
    chapters: ChapterInfo[], 
    totalPages: number
  ): Promise<{
    valid: boolean;
    validatedChapters: ChapterInfo[];
    issues: string[];
    totalPagesCovered: number;
  }> {
    const request = {
      chapters: chapters.map(chapter => ({
        title: chapter.title,
        start_page: chapter.startPage,
        end_page: chapter.endPage,
        page_count: chapter.pageCount,
      })),
      total_pages: totalPages,
    };
    
    const response = await apiClient.post('/api/validate-chapters', request);
    const data = response.data;
    
    return {
      valid: data.valid,
      validatedChapters: data.validated_chapters.map((chapter: any) => ({
        title: chapter.title,
        startPage: chapter.start_page,
        endPage: chapter.end_page,
        pageCount: chapter.page_count,
      })),
      issues: data.issues,
      totalPagesCovered: data.total_pages_covered,
    };
  }
  
  /**
   * 健康检查
   */
  static async healthCheck(): Promise<{
    status: string;
    service: string;
    version: string;
  }> {
    const response = await apiClient.get('/health');
    return response.data;
  }
  
  /**
   * 构建知识图谱
   */
  static async buildKnowledgeGraph(fileId: string, useLlm: boolean = true): Promise<{    success: boolean;
    graph?: any;
    message?: string;
  }> {
    const request = {
      file_id: fileId,
      use_llm: useLlm,
    };
    
    const response = await apiClient.post('/api/knowledge-graph', request);
    return response.data;
  }
  
  /**
   * 获取知识图谱
   */
  static async getKnowledgeGraph(fileId: string): Promise<{    success: boolean;
    graph?: any;
    message?: string;
  }> {
    const response = await apiClient.get(`/api/knowledge-graph/${fileId}`);
    return response.data;
  }
  
  /**
   * 获取知识图谱可视化数据
   */
  static async getKnowledgeGraphVisualization(fileId: string): Promise<{
    nodes: any[];
    links: any[];
  }> {
    const response = await apiClient.get(`/api/knowledge-graph/${fileId}/visualize`);
    return response.data;
  }
  
  /**
   * 搜索知识点
   */
  static async searchKnowledgePoints(fileId: string, keyword: string): Promise<{
    keyword: string;
    matched_points: any[];
    count: number;
  }> {
    const response = await apiClient.get(`/api/knowledge-graph/${fileId}/search`, {
      params: { keyword },
    });
    return response.data;
  }
  
  /**
   * 管理知识点
   */
  static async manageKnowledgePoints(
    fileId: string,
    knowledgePoints: any[]
  ): Promise<{
    success: boolean;
    message?: string;
    knowledge_points: any[];
  }> {
    const request = {
      file_id: fileId,
      knowledge_points: knowledgePoints,
    };
    
    const response = await apiClient.post('/api/knowledge-points', request);
    return response.data;
  }
}

export default ApiService;