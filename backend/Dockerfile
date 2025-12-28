# 构建阶段
FROM python:3.11-alpine AS builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# 复制requirements文件
COPY requirements.txt ./

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# 运行阶段
FROM python:3.11-alpine

# 安装ca-certificates用于HTTPS请求
RUN apk --no-cache add ca-certificates

# 创建非root用户
RUN adduser -D -s /bin/sh appuser

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制源代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads temp logs && chown -R appuser:appuser /app

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV PORT=8080
ENV ENVIRONMENT=production
ENV UPLOAD_DIR=/app/uploads
ENV TEMP_DIR=/app/temp
ENV MAX_FILE_SIZE=52428800

# 激活虚拟环境并启动应用
CMD ["/opt/venv/bin/python", "main.py"]