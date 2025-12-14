#!/bin/bash

# PDF章节拆分器 - 腾讯云主机自动化部署脚本
# 使用方法: curl -sSL https://raw.githubusercontent.com/your-repo/pdf-chapter-splitter/main/scripts/setup_tencent_cloud.sh | bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要使用root用户运行此脚本"
        exit 1
    fi
}

# 检查操作系统
check_os() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法检测操作系统版本"
        exit 1
    fi
    
    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_error "此脚本仅支持Ubuntu系统"
        exit 1
    fi
    
    log_info "检测到操作系统: $PRETTY_NAME"
}

# 更新系统
update_system() {
    log_info "更新系统包..."
    sudo apt update && sudo apt upgrade -y
    
    log_info "安装基础工具..."
    sudo apt install -y curl wget git vim htop unzip build-essential pkg-config libssl-dev
    
    log_success "系统更新完成"
}

# 安装Docker
install_docker() {
    log_info "检查Docker是否已安装..."
    if command -v docker &> /dev/null; then
        log_warning "Docker已安装，跳过安装步骤"
        return
    fi
    
    log_info "安装Docker..."
    
    # 卸载旧版本
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # 安装Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加Docker官方APT仓库
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 将当前用户添加到docker组
    sudo usermod -aG docker $USER
    
    log_success "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log_info "检查Docker Compose是否已安装..."
    if command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose已安装，跳过安装步骤"
        return
    fi
    
    log_info "安装Docker Compose..."
    
    # 下载Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 添加执行权限
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_success "Docker Compose安装完成"
}

# 安装Node.js
install_nodejs() {
    log_info "检查Node.js是否已安装..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_warning "Node.js已安装 ($NODE_VERSION)，跳过安装步骤"
        return
    fi
    
    log_info "安装Node.js 18..."
    
    # 使用NodeSource仓库
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt install -y nodejs
    
    log_success "Node.js安装完成"
}

# 安装Go
install_go() {
    log_info "检查Go是否已安装..."
    if command -v go &> /dev/null; then
        GO_VERSION=$(go version)
        log_warning "Go已安装 ($GO_VERSION)，跳过安装步骤"
        return
    fi
    
    log_info "安装Go 1.21..."
    
    # 下载Go
    cd /tmp
    wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
    
    # 解压到/usr/local
    sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
    
    # 添加到PATH
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
    echo 'export GOPATH=$HOME/go' >> ~/.bashrc
    
    log_success "Go安装完成"
}

# 安装Python 3.11
install_python() {
    log_info "检查Python 3.11是否已安装..."
    if command -v python3.11 &> /dev/null; then
        PYTHON_VERSION=$(python3.11 --version)
        log_warning "Python 3.11已安装 ($PYTHON_VERSION)，跳过安装步骤"
        return
    fi
    
    log_info "安装Python 3.11..."
    
    # 添加deadsnakes PPA
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    
    # 安装Python 3.11
    sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
    
    # 创建符号链接
    sudo ln -sf /usr/bin/python3.11 /usr/bin/python3
    
    log_success "Python 3.11安装完成"
}

# 安装Rust
install_rust() {
    log_info "检查Rust是否已安装..."
    if command -v rustc &> /dev/null; then
        RUST_VERSION=$(rustc --version)
        log_warning "Rust已安装 ($RUST_VERSION)，跳过安装步骤"
        return
    fi
    
    log_info "安装Rust..."
    
    # 安装Rust
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    
    # 重新加载环境
    source ~/.cargo/env
    
    log_success "Rust安装完成"
}

# 配置防火墙
setup_firewall() {
    log_info "配置防火墙..."
    
    # 安装ufw
    sudo apt install -y ufw
    
    # 配置防火墙规则
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 3000
    sudo ufw allow 8080
    sudo ufw allow 8000
    sudo ufw allow 80
    sudo ufw allow 443
    
    # 启用防火墙
    sudo ufw --force enable
    
    log_success "防火墙配置完成"
}

# 克隆项目
clone_project() {
    log_info "准备项目目录..."
    
    PROJECT_DIR="$HOME/pdf-chapter-splitter"
    
    if [[ -d "$PROJECT_DIR" ]]; then
        log_warning "项目目录已存在，是否要重新克隆？(y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
        else
            log_info "跳过项目克隆"
            return
        fi
    fi
    
    log_info "请输入Git仓库地址（或按Enter跳过）:"
    read -r repo_url
    
    if [[ -n "$repo_url" ]]; then
        git clone "$repo_url" "$PROJECT_DIR"
        log_success "项目克隆完成"
    else
        log_warning "跳过项目克隆，请手动上传项目文件到 $PROJECT_DIR"
    fi
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    PROJECT_DIR="$HOME/pdf-chapter-splitter"
    
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_warning "项目目录不存在，跳过环境变量配置"
        return
    fi
    
    cd "$PROJECT_DIR"
    
    # 获取服务器IP
    SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "localhost")
    
    # 创建环境变量文件
    cat > .env << EOF
# 服务器配置
HOST=0.0.0.0
FRONTEND_PORT=3000
BACKEND_PORT=8080
AI_SERVICE_PORT=8000

# 文件存储
UPLOAD_DIR=/app/uploads
TEMP_DIR=/app/temp
MAX_FILE_SIZE=52428800

# 服务URL
NEXT_PUBLIC_API_URL=http://${SERVER_IP}:8080
AI_SERVICE_URL=http://ai-service:8000

# 生产环境配置
ENVIRONMENT=production
DEBUG=false
EOF
    
    log_success "环境变量配置完成"
    log_info "服务器IP: $SERVER_IP"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    PROJECT_DIR="$HOME/pdf-chapter-splitter"
    
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_error "项目目录不存在，无法启动服务"
        return 1
    fi
    
    cd "$PROJECT_DIR"
    
    # 检查docker-compose.yml是否存在
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "docker-compose.yml文件不存在"
        return 1
    fi
    
    # 启动服务
    docker-compose up -d
    
    log_success "服务启动完成"
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    docker-compose ps
}

# 显示访问信息
show_access_info() {
    SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "localhost")
    
    log_success "部署完成！"
    echo
    echo "=========================================="
    echo "  PDF章节拆分器 - 访问信息"
    echo "=========================================="
    echo "前端应用:    http://${SERVER_IP}:3000"
    echo "后端API:     http://${SERVER_IP}:8080/api"
    echo "AI服务文档:  http://${SERVER_IP}:8000/docs"
    echo "=========================================="
    echo
    log_info "请确保腾讯云安全组已开放端口: 3000, 8080, 8000"
    log_info "如需配置域名和SSL，请参考文档: docs/TENCENT_CLOUD_SETUP.md"
}

# 主函数
main() {
    log_info "开始PDF章节拆分器腾讯云部署..."
    
    check_root
    check_os
    
    # 安装基础软件
    update_system
    install_docker
    install_docker_compose
    
    # 安装开发工具（可选）
    log_info "是否安装开发工具？(Node.js, Go, Python, Rust) (y/N)"
    read -r install_dev_tools
    if [[ "$install_dev_tools" =~ ^[Yy]$ ]]; then
        install_nodejs
        install_go
        install_python
        install_rust
    fi
    
    # 配置防火墙
    setup_firewall
    
    # 项目设置
    clone_project
    setup_environment
    
    # 启动服务
    log_info "是否立即启动服务？(y/N)"
    read -r start_now
    if [[ "$start_now" =~ ^[Yy]$ ]]; then
        start_services
        show_access_info
    else
        log_info "跳过服务启动，你可以稍后手动启动："
        log_info "cd ~/pdf-chapter-splitter && docker-compose up -d"
    fi
    
    log_success "部署脚本执行完成！"
    log_warning "请重新登录或执行 'newgrp docker' 以使Docker组权限生效"
}

# 执行主函数
main "$@"