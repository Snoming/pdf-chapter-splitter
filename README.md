# PDF章节拆分器

简化的在线PDF文档章节拆分工具，专注于50MB以内的文档处理，采用现代化微服务架构。

## 项目概述

PDF章节拆分器是一个基于Web的应用程序，允许用户上传PDF文件，自动或手动识别章节结构，并将其拆分为独立的章节文件。系统采用前后端分离架构，提供直观的用户界面和强大的处理能力。

## 技术架构

### 前端 (Next.js)
- **框架**: Next.js 14 + TypeScript
- **UI库**: Ant Design + Tailwind CSS
- **功能**: 文件上传、PDF预览、章节编辑、下载管理

### 后端 (Go)
- **框架**: Gin + Go 1.21
- **功能**: API服务、文件管理、任务调度

### AI服务 (Python)
- **框架**: FastAPI + PyMuPDF
- **功能**: 智能章节识别、文本分析

### PDF处理引擎 (Rust)
- **功能**: 高性能PDF拆分、文件处理

## 快速开始

### 使用Docker Compose（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd pdf-chapter-splitter

# 启动所有服务
docker-compose up -d

# 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:8080
# AI服务: http://localhost:8000
```

### 本地开发

#### 前端开发
```bash
cd frontend
npm install
npm run dev
```

#### 后端开发
```bash
cd backend
go mod download
go run main.go
```

#### AI服务开发
```bash
cd ai-service
pip install -r requirements.txt
python main.py
```

## 功能特性

### 🚀 核心功能
- 📁 **文件上传**: 支持拖拽上传，最大50MB PDF文件
- 👀 **PDF预览**: 浏览器内预览，支持页面导航和缩放
- 🤖 **智能识别**: AI驱动的章节自动识别
- ✏️ **手动编辑**: 灵活的章节边界调整
- ✂️ **高效拆分**: Rust引擎提供高性能PDF处理
- 💾 **批量下载**: 支持单个或批量下载章节文件

### 🎯 技术特色
- **微服务架构**: 服务解耦，易于扩展和维护
- **响应式设计**: 支持桌面和移动设备
- **实时进度**: WebSocket实时更新处理状态
- **错误恢复**: 完善的错误处理和重试机制
- **安全可靠**: 文件验证、大小限制、路径安全

## 项目结构

```
pdf-chapter-splitter/
├── frontend/                  # Next.js前端应用
│   ├── src/
│   │   ├── app/              # App Router页面
│   │   ├── components/       # React组件
│   │   ├── lib/              # 工具函数
│   │   └── hooks/            # 自定义Hooks
│   ├── package.json
│   └── Dockerfile
├── backend/                   # Go后端API
│   ├── internal/
│   │   ├── api/              # HTTP处理器
│   │   ├── config/           # 配置管理
│   │   ├── models/           # 数据模型
│   │   └── service/          # 业务逻辑
│   ├── main.go
│   └── Dockerfile
├── ai-service/                # Python AI服务
│   ├── src/
│   │   ├── api/              # FastAPI路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据模型
│   │   └── services/         # AI服务
│   ├── main.py
│   └── Dockerfile
├── pdf-processor/             # Rust PDF处理引擎
│   ├── src/
│   ├── Cargo.toml
│   └── Dockerfile
├── .kiro/                     # 项目规格文档
│   └── specs/
│       └── pdf-chapter-splitter/
├── docker-compose.yml         # Docker编排配置
└── README.md
```

## API文档

### 后端API (Port 8080)
- `POST /api/upload` - 文件上传
- `POST /api/analyze` - 章节分析
- `POST /api/split` - PDF拆分
- `GET /api/download/:id` - 文件下载
- `GET /api/task/:id` - 任务状态

### AI服务API (Port 8000)
- `POST /api/analyze` - 智能章节识别
- `POST /api/upload-and-analyze` - 上传并分析
- `POST /api/validate-chapters` - 章节验证
- `GET /api/pdf-info` - PDF信息获取

## 开发指南

### 环境要求
- Node.js 18+
- Go 1.21+
- Python 3.11+
- Rust 1.70+
- Docker & Docker Compose

### 代码规范
- **前端**: ESLint + Prettier
- **后端**: gofmt + golint
- **AI服务**: Black + isort + flake8
- **Rust**: rustfmt + clippy

### 测试
```bash
# 前端测试
cd frontend && npm test

# 后端测试
cd backend && go test ./...

# AI服务测试
cd ai-service && pytest

# Rust测试
cd pdf-processor && cargo test
```

## 部署

### 生产环境部署
```bash
# 构建并启动生产环境
docker-compose -f docker-compose.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 环境变量配置
参考各服务目录下的README文件了解详细的环境变量配置。

## 监控和日志

- **应用日志**: 各服务产生结构化日志
- **访问日志**: Nginx访问日志
- **错误监控**: 集成错误追踪
- **性能监控**: 响应时间和资源使用监控

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

如有问题或建议，请：
1. 查看[文档](docs/)
2. 搜索[Issues](issues)
3. 创建新的Issue

---

**PDF章节拆分器** - 让PDF处理变得简单高效 🚀