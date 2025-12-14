# PDF章节拆分器 - AI服务

基于FastAPI的智能PDF章节识别服务，使用PyMuPDF进行PDF解析和文本分析。

## 技术栈

- **FastAPI** - 现代化的Python Web框架
- **PyMuPDF (fitz)** - 高性能PDF处理库
- **PyPDF2** - PDF操作辅助库
- **Pydantic** - 数据验证和设置管理
- **Loguru** - 现代化日志库
- **Uvicorn** - ASGI服务器

## 功能特性

### 智能章节识别

- 📖 **书签提取** - 从PDF书签自动提取章节结构
- 🔍 **文本模式识别** - 基于正则表达式识别章节标题
- 📊 **默认分割建议** - 当无法识别章节时提供平均分割方案
- ✅ **章节验证** - 验证章节信息的完整性和有效性

### API端点

- `POST /api/analyze` - 分析指定路径的PDF文件
- `POST /api/upload-and-analyze` - 上传并分析PDF文件
- `GET /api/pdf-info` - 获取PDF基本信息
- `POST /api/validate-chapters` - 验证章节信息有效性
- `GET /health` - 健康检查

## 项目结构

```
ai-service/
├── main.py                    # 应用入口点
├── requirements.txt           # Python依赖
├── Dockerfile                 # Docker构建文件
├── README.md                  # 项目文档
└── src/                       # 源代码目录
    ├── api/                   # API路由
    │   └── routes.py         # 路由定义
    ├── core/                  # 核心配置
    │   └── config.py         # 配置管理
    ├── models/                # 数据模型
    │   └── schemas.py        # Pydantic模型
    └── services/              # 业务服务
        └── pdf_analyzer.py   # PDF分析服务
```

## 开发环境设置

### 前置要求

- Python 3.11+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动开发服务器

```bash
python main.py
```

服务将在 http://localhost:8000 启动

### 查看API文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境变量配置

创建 `.env` 文件：

```env
# 服务配置
HOST=0.0.0.0
PORT=8000
DEBUG=True

# 文件处理配置
MAX_FILE_SIZE=52428800
TEMP_DIR=./temp

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/ai-service.log
```

## API使用示例

### 分析PDF文件

```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/document.pdf",
    "auto_detect": true,
    "min_pages_per_chapter": 1
  }'
```

**响应:**
```json
{
  "success": true,
  "chapters": [
    {
      "title": "第一章 引言",
      "start_page": 1,
      "end_page": 10,
      "page_count": 10
    },
    {
      "title": "第二章 基础概念",
      "start_page": 11,
      "end_page": 25,
      "page_count": 15
    }
  ],
  "total_pages": 40,
  "message": "成功识别 2 个章节"
}
```

### 上传并分析PDF

```bash
curl -X POST "http://localhost:8000/api/upload-and-analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### 验证章节信息

```bash
curl -X POST "http://localhost:8000/api/validate-chapters?total_pages=40" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "title": "第一章",
      "start_page": 1,
      "end_page": 20,
      "page_count": 20
    },
    {
      "title": "第二章",
      "start_page": 21,
      "end_page": 40,
      "page_count": 20
    }
  ]'
```

## 章节识别算法

### 1. 书签提取

优先从PDF书签（目录）提取章节信息：
- 提取顶级书签作为章节
- 自动计算页码范围
- 验证书签的有效性

### 2. 文本模式识别

当PDF没有书签时，使用正则表达式识别章节标题：

```python
CHAPTER_PATTERNS = [
    r"第[一二三四五六七八九十\d]+章",  # 中文章节
    r"Chapter\s+\d+",                    # 英文章节
    r"第\d+章",                          # 数字章节
    r"CHAPTER\s+\d+",                    # 大写英文
]
```

### 3. 默认分割建议

当无法识别章节时，提供智能分割建议：
- 根据总页数决定章节数量
- 平均分配页面
- 确保每个章节至少有一页

### 4. 章节验证

验证章节信息的完整性：
- 检查页码范围有效性
- 确保章节覆盖所有页面
- 防止章节重叠或间隙
- 自动修正边界问题

## Docker部署

### 构建镜像

```bash
docker build -t pdf-splitter-ai-service .
```

### 运行容器

```bash
docker run -d \
  --name pdf-ai-service \
  -p 8000:8000 \
  -v $(pwd)/temp:/app/temp \
  -v $(pwd)/logs:/app/logs \
  pdf-splitter-ai-service
```

## 测试

### 运行测试

```bash
pytest tests/ -v
```

### 测试覆盖率

```bash
pytest --cov=src tests/
```

## 性能优化

- 使用PyMuPDF进行高效PDF处理
- 异步API设计支持并发请求
- 智能缓存减少重复计算
- 临时文件自动清理

## 日志记录

应用使用Loguru进行结构化日志记录：

```python
logger.info("PDF分析完成", extra={
    "file_path": file_path,
    "chapters_count": len(chapters),
    "total_pages": total_pages
})
```

日志文件位置：`logs/ai-service.log`

## 错误处理

完善的错误处理机制：
- 文件不存在或格式错误
- PDF损坏或无法解析
- 内存不足或处理超时
- 网络连接问题

所有错误都会返回标准化的错误响应格式。