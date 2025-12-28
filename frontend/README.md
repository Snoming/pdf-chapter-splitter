# PDF分析与知识图谱可视化系统 - 前端

基于Next.js 14的现代化PDF分析与知识图谱可视化前端应用。

## 技术栈

- **Next.js 14** - React框架，支持App Router
- **TypeScript** - 类型安全的JavaScript
- **Tailwind CSS** - 实用优先的CSS框架
- **D3.js** - 知识图谱可视化
- **Zustand** - 轻量级状态管理
- **Axios** - HTTP客户端

## 开发环境设置

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
npm start
```

## 项目结构

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # 根布局组件
│   ├── page.tsx           # 主页面
│   └── globals.css        # 全局样式
├── components/            # 可复用组件
│   ├── FileUpload.tsx     # 文件上传组件
│   ├── PdfPreview.tsx     # PDF预览组件
│   ├── ChapterEditor.tsx  # 章节编辑组件
│   ├── KnowledgeGraphStep.tsx     # 知识图谱构建步骤组件
│   ├── KnowledgeGraphVisualization.tsx # 知识图谱可视化组件
│   ├── SplitProgress.tsx  # 处理进度组件
│   ├── FileDownloader.tsx # 文件下载组件
│   └── ErrorBoundary.tsx  # 错误边界组件
├── lib/                   # 工具函数和配置
│   ├── api.ts            # API客户端
│   └── utils.ts          # 通用工具函数
├── store/                 # 状态管理
│   └── useAppStore.ts     # Zustand状态管理
```

## 环境变量

创建 `.env.local` 文件：

```env
NEXT_PUBLIC_API_URL=http://localhost:8080
```

## 开发规范

### 代码格式化

项目使用Prettier进行代码格式化：

```bash
npm run lint
```

### 类型检查

```bash
npm run type-check
```

## 功能特性

- 📁 **文件上传**：支持拖拽上传，最大50MB PDF文件
- 👀 **PDF预览**：浏览器内预览，支持页面导航和缩放
- ✂️ **章节编辑**：智能章节识别和手动编辑
- 🧠 **知识图谱**：交互式知识图谱可视化，展示知识点关联
- 💬 **智能对话**：基于PDF内容的自然语言问答
- 📊 **处理进度**：实时显示PDF处理和知识图谱构建进度
- 💾 **文件下载**：支持章节文件下载和批量下载
- 📱 **响应式设计**：支持桌面和移动设备

## API集成

前端通过RESTful API与Python后端服务通信：

- `POST /api/upload` - 文件上传
- `POST /api/analyze` - PDF内容分析
- `POST /api/knowledge-graph` - 构建知识图谱
- `GET /api/knowledge-graph/:file_id` - 获取知识图谱
- `GET /api/knowledge-graph/:file_id/visualize` - 获取知识图谱可视化数据
- `POST /api/query` - 智能问答

## 部署

### Docker部署

```bash
docker build -t pdf-analyzer-frontend .
docker run -p 3000:3000 pdf-analyzer-frontend
```

### 环境配置

生产环境需要配置：
- `NEXT_PUBLIC_API_URL` - 后端API地址
- 其他环境特定配置

## 核心功能说明

### 1. 文件上传与PDF预览
- 支持拖拽文件上传
- 实时PDF预览
- 页面导航和缩放功能

### 2. 章节管理
- 自动章节识别
- 手动章节编辑
- 章节验证和调整

### 3. 知识图谱构建与可视化
- 基于大模型的知识点提取
- 知识点关联关系分析
- 交互式D3.js可视化
- 支持节点拖拽和缩放

### 4. 智能对话
- 基于PDF内容的自然语言问答
- 支持上下文理解
- 精确的内容引用

### 5. 文件下载
- 单章节下载
- 批量下载
- 支持多种格式

## 技术特色

- **现代化架构**：Next.js 14 + App Router
- **类型安全**：完整的TypeScript支持
- **响应式设计**：适配各种屏幕尺寸
- **高性能**：优化的渲染和状态管理
- **可扩展**：模块化设计，易于功能扩展
- **用户友好**：直观的界面设计和流畅的用户体验

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。