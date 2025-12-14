# PDF章节拆分器 - Go后端

基于Gin框架的高性能PDF章节拆分工具后端API服务。

## 技术栈

- **Go 1.21** - 现代化的编程语言
- **Gin** - 高性能的HTTP Web框架
- **Logrus** - 结构化日志库
- **UUID** - 唯一标识符生成
- **CORS** - 跨域资源共享支持

## 项目结构

```
backend/
├── main.go                    # 应用入口点
├── go.mod                     # Go模块定义
├── go.sum                     # 依赖校验和
├── Dockerfile                 # Docker构建文件
├── README.md                  # 项目文档
└── internal/                  # 内部包
    ├── api/                   # API路由和处理器
    │   ├── router.go         # 路由配置
    │   └── handlers.go       # HTTP处理器
    ├── config/                # 配置管理
    │   └── config.go         # 配置结构和加载
    ├── models/                # 数据模型
    │   └── models.go         # 数据结构定义
    └── service/               # 业务逻辑服务
        ├── file_service.go   # 文件处理服务
        └── pdf_service.go    # PDF处理服务
```

## 功能特性

### API端点

- `POST /api/upload` - 文件上传（最大50MB）
- `POST /api/analyze` - PDF章节分析
- `POST /api/split` - PDF拆分处理
- `GET /api/download/:file_id` - 文件下载
- `GET /api/task/:task_id` - 任务状态查询
- `GET /api/health` - 健康检查

### 核心功能

- 📁 **文件上传管理** - 支持大文件上传，文件格式验证
- 🔍 **章节分析** - 集成AI服务进行智能章节识别
- ✂️ **PDF拆分** - 调用Rust引擎进行高效PDF拆分
- 📊 **任务管理** - 异步任务处理和进度跟踪
- 💾 **文件存储** - 安全的文件存储和访问控制
- 🔒 **错误处理** - 完善的错误处理和日志记录

## 开发环境设置

### 前置要求

- Go 1.21+
- Git

### 安装依赖

```bash
go mod download
```

### 启动开发服务器

```bash
go run main.go
```

服务将在 http://localhost:8080 启动

### 构建生产版本

```bash
go build -o pdf-splitter-backend
./pdf-splitter-backend
```

## 环境变量配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `PORT` | `8080` | 服务端口 |
| `ENVIRONMENT` | `development` | 运行环境 |
| `UPLOAD_DIR` | `./uploads` | 上传文件目录 |
| `TEMP_DIR` | `./temp` | 临时文件目录 |
| `MAX_FILE_SIZE` | `52428800` | 最大文件大小（50MB） |
| `AI_SERVICE_URL` | `http://localhost:8000` | AI服务地址 |

### 环境配置示例

```bash
# 开发环境
export PORT=8080
export ENVIRONMENT=development
export UPLOAD_DIR=./uploads
export TEMP_DIR=./temp

# 生产环境
export PORT=8080
export ENVIRONMENT=production
export UPLOAD_DIR=/app/uploads
export TEMP_DIR=/app/temp
export MAX_FILE_SIZE=52428800
```

## Docker部署

### 构建镜像

```bash
docker build -t pdf-splitter-backend .
```

### 运行容器

```bash
docker run -d \
  --name pdf-splitter-backend \
  -p 8080:8080 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/temp:/app/temp \
  -e ENVIRONMENT=production \
  pdf-splitter-backend
```

## API文档

### 文件上传

```http
POST /api/upload
Content-Type: multipart/form-data

file: [PDF文件]
```

**响应:**
```json
{
  "file_id": "uuid",
  "filename": "document.pdf",
  "file_size": 1024000,
  "message": "文件上传成功"
}
```

### 章节分析

```http
POST /api/analyze
Content-Type: application/json

{
  "file_id": "uuid"
}
```

**响应:**
```json
{
  "chapters": [
    {
      "title": "第一章 引言",
      "start_page": 1,
      "end_page": 10,
      "page_count": 10
    }
  ],
  "total_pages": 40
}
```

### PDF拆分

```http
POST /api/split
Content-Type: application/json

{
  "file_id": "uuid",
  "chapters": [
    {
      "title": "第一章 引言",
      "start_page": 1,
      "end_page": 10,
      "page_count": 10
    }
  ]
}
```

**响应:**
```json
{
  "task_id": "uuid",
  "status": "pending"
}
```

### 任务状态查询

```http
GET /api/task/{task_id}
```

**响应:**
```json
{
  "task_id": "uuid",
  "file_id": "uuid",
  "status": "processing",
  "progress": 50,
  "created_at": "2023-01-01T00:00:00Z"
}
```

## 测试

### 运行测试

```bash
go test ./...
```

### 运行基准测试

```bash
go test -bench=. ./...
```

## 日志

应用使用结构化日志记录，支持不同级别：

- `DEBUG` - 详细调试信息
- `INFO` - 一般信息
- `WARN` - 警告信息
- `ERROR` - 错误信息

日志格式：
```
time="2023-01-01T00:00:00Z" level=info msg="服务器启动在端口 8080"
```

## 性能优化

- 使用Gin框架提供高性能HTTP处理
- 异步任务处理避免阻塞请求
- 文件流式处理减少内存占用
- 合理的错误处理和资源清理

## 安全考虑

- 文件类型和大小验证
- 路径遍历攻击防护
- CORS配置限制跨域访问
- 结构化错误响应避免信息泄露