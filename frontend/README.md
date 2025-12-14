# PDF章节拆分器 - 前端

基于Next.js 14的现代化PDF章节拆分工具前端应用。

## 技术栈

- **Next.js 14** - React框架，支持App Router
- **TypeScript** - 类型安全的JavaScript
- **Tailwind CSS** - 实用优先的CSS框架
- **Ant Design** - 企业级UI组件库
- **React PDF** - PDF预览和渲染
- **React Hook Form** - 高性能表单处理
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
│   ├── FileUpload/        # 文件上传组件
│   ├── PDFPreview/        # PDF预览组件
│   ├── ChapterEditor/     # 章节编辑组件
│   └── DownloadLinks/     # 下载链接组件
├── lib/                   # 工具函数和配置
│   ├── api.ts            # API客户端
│   ├── types.ts          # TypeScript类型定义
│   └── utils.ts          # 通用工具函数
└── hooks/                 # 自定义React Hooks
    ├── useFileUpload.ts   # 文件上传Hook
    ├── usePDFPreview.ts   # PDF预览Hook
    └── useChapterEditor.ts # 章节编辑Hook
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

- 📁 拖拽文件上传，支持最大50MB PDF文件
- 👀 浏览器内PDF预览，支持页面导航和缩放
- ✂️ 智能章节识别和手动编辑
- 📊 实时处理进度显示
- 💾 章节文件下载和批量下载
- 📱 响应式设计，支持桌面和移动设备

## API集成

前端通过RESTful API与Go后端服务通信：

- `POST /api/upload` - 文件上传
- `POST /api/analyze` - 章节分析
- `POST /api/split` - PDF拆分
- `GET /api/download/{id}` - 文件下载

## 部署

### Docker部署

```bash
docker build -t pdf-splitter-frontend .
docker run -p 3000:3000 pdf-splitter-frontend
```

### 环境配置

生产环境需要配置：
- `NEXT_PUBLIC_API_URL` - 后端API地址
- 其他环境特定配置