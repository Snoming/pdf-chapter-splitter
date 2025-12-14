# 多阶段构建 - 构建阶段
FROM rust:1.70-alpine AS builder

WORKDIR /app

# 安装必要的工具
RUN apk add --no-cache musl-dev

# 复制 Cargo 文件
COPY Cargo.toml Cargo.lock ./

# 创建虚拟源文件以缓存依赖
RUN mkdir src && echo "fn main() {}" > src/main.rs && echo "" > src/lib.rs

# 构建依赖
RUN cargo build --release
RUN rm -rf src

# 复制实际源代码
COPY src ./src

# 构建应用
RUN cargo build --release

# 生产阶段
FROM alpine:latest

# 安装运行时依赖
RUN apk --no-cache add ca-certificates

WORKDIR /root/

# 从构建阶段复制二进制文件
COPY --from=builder /app/target/release/pdf-processor .
COPY --from=builder /app/target/release/libpdf_processor.so .

# 暴露端口（如果需要）
EXPOSE 8001

# 运行应用
CMD ["./pdf-processor"]