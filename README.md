# PDF分析与知识图谱可视化系统

一个现代化的PDF分析平台，专注于PDF内容的深度分析、自然语言交互和知识图谱构建，帮助用户更高效地理解和利用PDF文档中的知识。

## 项目概述

本系统由最初的PDF章节拆分器转型而来，现专注于PDF内容的智能分析、对话式交互和知识图谱可视化。系统支持"书-章-节-知识点"四层知识架构体系，能够自动提取PDF内容中的关键信息，构建可视化知识图谱，并支持用户通过自然语言提问获取准确回答。

## 技术架构

### 前端 (Next.js)
- **框架**: Next.js 14 + TypeScript
- **UI库**: Tailwind CSS
- **状态管理**: Zustand
- **可视化库**: D3.js
- **功能**: 文件上传、PDF预览、对话交互、知识图谱可视化

### 后端 (Python)
- **框架**: FastAPI + PyMuPDF
- **图数据库**: Neo4j（用于知识图谱存储和查询）
- **大模型集成**: 支持千问等大模型API
- **功能**: 统一的API服务，包括文件管理、智能内容分析、知识图谱构建、大模型服务集成

## 核心功能

### 🚀 核心功能
- 📁 **文件上传**: 支持拖拽上传，最大50MB PDF文件
- 👀 **PDF预览**: 浏览器内预览，支持页面导航和缩放
- 💬 **智能对话**: 基于PDF内容的自然语言问答，支持上下文理解
- 🧠 **知识图谱**: 自动构建交互式知识图谱，可视化展示知识点关联
- 🔍 **内容分析**: 深度提取PDF中的关键信息和实体关系

### 🎯 技术特色
- **简洁架构**: 前后端分离，后端统一服务，易于维护和扩展
- **响应式设计**: 支持桌面和移动设备
- **实时反馈**: 操作后立即给予用户反馈
- **安全可靠**: 文件验证、大小限制、路径安全
- **可扩展设计**: 支持多种大模型集成，易于功能扩展

## 快速开始

### 使用Docker Compose（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd pdf-analyzer

# 启动所有服务
docker-compose up -d

# 访问应用
# 前端: http://localhost:3000
# 后端API: http://localhost:8080
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
pip install -r requirements.txt
python main.py
```

## 项目结构

```
pdf-analyzer/
├── frontend/                  # Next.js前端应用
│   ├── src/
│   │   ├── app/              # App Router页面
│   │   ├── components/       # React组件
│   │   ├── lib/              # 工具函数
│   │   └── store/            # 状态管理
│   ├── package.json
│   └── Dockerfile
├── backend/                   # Python后端服务
│   ├── src/
│   │   ├── api/              # FastAPI路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据模型
│   │   └── services/         # 业务服务
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── .kiro/                     # 项目规格文档
├── docker-compose.yml         # Docker编排配置
└── README.md                  # 项目说明文档
```

## API文档

### 后端API (Port 8080)
- **文件管理**
  - `POST /api/upload` - 文件上传
  - `GET /api/pdf-info/:id` - PDF信息获取
  
- **内容分析**
  - `POST /api/analyze` - PDF内容分析
  
- **知识图谱**
  - `POST /api/knowledge-graph` - 构建知识图谱
  - `GET /api/knowledge-graph/:file_id` - 获取知识图谱
  - `GET /api/knowledge-graph/:file_id/nodes` - 获取知识图谱节点
  - `GET /api/knowledge-graph/:file_id/edges` - 获取知识图谱边
  - `GET /api/knowledge-graph/:file_id/visualize` - 获取知识图谱可视化数据
  - `POST /api/knowledge-points` - 管理知识点
  - `GET /api/knowledge-graph/:file_id/search` - 搜索知识点

## 开发指南

### 环境要求
- **前端**: Node.js 18+
- **后端**: Python 3.11+
- **容器化**: Docker & Docker Compose

### 大模型配置
1. 在 `.env` 文件中配置大模型API密钥和参数
2. 支持的模型: 千问模型
3. 配置示例:
   ```
   LLM_API_KEY=your_api_key
   LLM_API_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
   LLM_MODEL_NAME=qwen-turbo
   LLM_TEMPERATURE=0.7
   ```

### 代码规范
- **前端**: ESLint + Prettier
- **后端**: Black + isort + flake8

### 测试
```bash
# 前端测试
cd frontend && npm test

# 后端测试
cd backend && pytest

# 集成测试
cd backend && python test_integration.py
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

#### 后端环境变量
| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| `LLM_API_KEY` | 大模型API密钥 | 空 |
| `LLM_API_ENDPOINT` | 大模型API端点 | https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions |
| `LLM_MODEL_NAME` | 大模型名称 | qwen-turbo |
| `LLM_TEMPERATURE` | 生成温度 | 0.7 |
| `LLM_MAX_TOKENS` | 最大生成 tokens | 2048 |
| `LLM_RETRY_COUNT` | API调用重试次数 | 3 |
| `LLM_TIMEOUT` | API调用超时时间（秒） | 30 |
| `NEO4J_URI` | Neo4j连接地址 | bolt://localhost:7687 |
| `NEO4J_USER` | Neo4j用户名 | neo4j |
| `NEO4J_PASSWORD` | Neo4j密码 | password |
| `NEO4J_DATABASE` | Neo4j数据库名 | neo4j |

#### 前端环境变量
| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端API地址 | http://localhost:8080 |

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

**PDF分析与知识图谱可视化系统** - 让PDF知识探索变得简单高效 🚀
