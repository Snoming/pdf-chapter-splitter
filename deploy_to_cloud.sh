#!/bin/bash

# PDF章节拆分器 - 腾讯云自动部署脚本
# 使用方法: bash deploy_to_cloud.sh

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统环境
check_system() {
    log_info "检查系统环境..."
    echo "=== 系统信息 ==="
    cat /etc/os-release
    echo -e "\n当前用户: $(whoami)"
    echo -e "\n内存使用情况:"
    free -h
    echo -e "\n磁盘使用情况:"
    df -h
    echo -e "\n服务器公网IP:"
    SERVER_IP=$(curl -s ifconfig.me)
    echo $SERVER_IP
    echo "========================"
}

# 更新系统
update_system() {
    log_info "更新系统..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y curl wget git vim htop unzip build-essential pkg-config libssl-dev
    log_success "系统更新完成"
}

# 安装Docker
install_docker() {
    log_info "安装Docker..."
    if command -v docker &> /dev/null; then
        log_warning "Docker已安装，跳过"
        return
    fi
    
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    
    # 安装Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker安装完成"
}

# 创建项目结构
create_project() {
    log_info "创建项目结构..."
    
    mkdir -p ~/pdf-chapter-splitter
    cd ~/pdf-chapter-splitter
    
    # 创建目录结构
    mkdir -p frontend/src/app
    mkdir -p backend/internal/{api,config,models,service}
    mkdir -p ai-service/src/{api,core,models,services}
    mkdir -p pdf-processor/src
    
    log_success "项目结构创建完成"
}

# 创建Docker Compose配置
create_docker_compose() {
    log_info "创建Docker Compose配置..."
    
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8080
    depends_on:
      - backend
    networks:
      - pdf-splitter-network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
      - ENVIRONMENT=production
      - UPLOAD_DIR=/app/uploads
      - TEMP_DIR=/app/temp
      - MAX_FILE_SIZE=52428800
      - AI_SERVICE_URL=http://ai-service:8000
    volumes:
      - ./uploads:/app/uploads
      - ./temp:/app/temp
    depends_on:
      - ai-service
    networks:
      - pdf-splitter-network
    restart: unless-stopped

  ai-service:
    build:
      context: ./ai-service
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - DEBUG=False
      - MAX_FILE_SIZE=52428800
      - TEMP_DIR=/app/temp
    volumes:
      - ./ai-temp:/app/temp
      - ./ai-logs:/app/logs
    networks:
      - pdf-splitter-network
    restart: unless-stopped

networks:
  pdf-splitter-network:
    driver: bridge

volumes:
  uploads:
  temp:
  ai-temp:
  ai-logs:
EOF

    log_success "Docker Compose配置创建完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    sudo apt install -y ufw
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 3000
    sudo ufw allow 8080
    sudo ufw allow 8000
    sudo ufw --force enable
    log_success "防火墙配置完成"
}

# 主函数
main() {
    log_info "开始PDF章节拆分器部署..."
    
    check_system
    update_system
    install_docker
    create_project
    create_docker_compose
    setup_firewall
    
    log_success "基础环境部署完成！"
    log_info "接下来需要创建项目文件，请等待进一步指导..."
    
    SERVER_IP=$(curl -s ifconfig.me)
    echo "=========================================="
    echo "  部署信息"
    echo "=========================================="
    echo "服务器IP: $SERVER_IP"
    echo "项目目录: ~/pdf-chapter-splitter"
    echo "前端端口: 3000"
    echo "后端端口: 8080"
    echo "AI服务端口: 8000"
    echo "=========================================="
}

main "$@"