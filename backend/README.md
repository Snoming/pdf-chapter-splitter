# PDF章节拆分器 - Python后端

基于FastAPI的统一后端服务，提供文件管理、智能章节识别、文本分析和PDF拆分功能。

## 技术栈

- **Python 3.11** - 现代化的编程语言
- **FastAPI** - 高性能的异步Web框架
- **PyMuPDF** - 强大的PDF处理库
- **Loguru** - 结构化日志库
- **Pydantic** - 数据验证和序列化
- **CORS** - 跨域资源共享支持

## 项目结构

```
backend/
├── main.py                    # 应用入口点
├── requirements.txt           # Python依赖
├── Dockerfile                 # Docker构建文件
├── README.md                  # 项目文档
└── src/                       # 源代码
    ├── api/                   # API路由
    │   └── routes.py          # 路由配置和端点定义
    ├── core/                  # 核心配置
    │   └── config.py          # 配置结构和加载
    ├── models/                # 数据模型
    │   └── schemas.py         # Pydantic模型定义
    └── services/              # 业务逻辑服务
        ├── file_service.py    # 文件处理服务
        ├── pdf_analyzer.py    # PDF章节分析服务
        ├── pdf_splitter.py    # PDF拆分服务
        └── task_service.py    # 任务管理服务
```

## 功能特性

### API端点

- `POST /api/upload` - 文件上传（最大50MB）
- `POST /api/analyze` - PDF章节分析
- `POST /api/split` - PDF拆分处理
- `GET /api/download/:file_id` - 文件下载
- `GET /api/task/:task_id` - 任务状态查询
- `POST /api/validate-chapters` - 章节验证
- `GET /api/pdf-info/:file_id` - PDF信息获取
- `GET /health` - 健康检查

### 核心功能

- 📁 **文件上传管理** - 支持大文件上传，文件格式验证
- 🔍 **智能章节识别** - 基于PyMuPDF的章节自动识别
- ✂️ **PDF拆分** - 高效的PDF拆分处理
- 📊 **任务管理** - 异步任务处理和进度跟踪
- 💾 **文件存储** - 安全的文件存储和访问控制
- 🔒 **错误处理** - 完善的错误处理和日志记录

## 开发环境设置

### 前置要求

- Python 3.11+
- Git

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动开发服务器

```bash
python main.py
```

服务将在 http://localhost:8080 启动

### 构建生产版本

```bash
# 使用uvicorn直接运行
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
```

## 环境变量配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `PORT` | `8080` | 服务端口 |
| `ENVIRONMENT` | `development` | 运行环境 |
| `UPLOAD_DIR` | `./uploads` | 上传文件目录 |
| `TEMP_DIR` | `./temp` | 临时文件目录 |
| `MAX_FILE_SIZE` | `52428800` | 最大文件大小（50MB） |
| `DEBUG` | `True` | 调试模式开关 |

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
export DEBUG=False
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
pytest
```

### 运行特定测试

```bash
pytest tests/test_file_service.py -v
```

## 日志

应用使用结构化日志记录，支持不同级别：

- `DEBUG` - 详细调试信息
- `INFO` - 一般信息
- `WARNING` - 警告信息
- `ERROR` - 错误信息
- `CRITICAL` - 严重错误信息

日志格式：
```
2023-01-01 00:00:00.000 | INFO     | main:lifespan:28 - PDF章节拆分器后端服务启动中...
```

## 性能优化

- 使用FastAPI的异步特性提高并发处理能力
- 文件流处理减少内存占用
- 合理的任务队列管理
- 高效的PDF处理算法

## 安全考虑

- 文件类型和大小验证
- 路径遍历攻击防护
- CORS配置限制跨域访问
- 结构化错误响应避免信息泄露
- 安全的文件存储路径
