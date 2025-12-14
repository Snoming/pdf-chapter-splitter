# 腾讯云主机开发环境配置指南

本指南将帮助你在腾讯云主机上配置PDF章节拆分器的开发环境。

## 前置要求

### 腾讯云主机配置建议
- **操作系统**: Ubuntu 20.04 LTS 或 Ubuntu 22.04 LTS
- **CPU**: 2核心或以上
- **内存**: 4GB或以上
- **存储**: 40GB或以上
- **网络**: 公网IP，开放必要端口

### 需要开放的端口
在腾讯云控制台的安全组中开放以下端口：
- `22` - SSH连接
- `3000` - Next.js前端服务
- `8080` - Go后端API服务
- `8000` - Python AI服务
- `80` - HTTP (可选)
- `443` - HTTPS (可选)

## 步骤1: 连接到腾讯云主机

### 使用SSH连接
```bash
# 替换为你的腾讯云主机公网IP
ssh ubuntu@your-server-ip

# 如果使用密钥文件
ssh -i /path/to/your-key.pem ubuntu@your-server-ip
```

### Windows用户可以使用
- **PuTTY** - 图形化SSH客户端
- **Windows Terminal** - 内置SSH支持
- **VS Code Remote SSH** - 直接在VS Code中连接

## 步骤2: 系统更新和基础软件安装

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y curl wget git vim htop unzip

# 安装构建工具
sudo apt install -y build-essential pkg-config libssl-dev
```

## 步骤3: 安装Docker和Docker Compose

### 安装Docker
```bash
# 卸载旧版本Docker（如果存在）
sudo apt remove docker docker-engine docker.io containerd runc

# 安装Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker官方APT仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新包索引并安装Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到docker组（避免每次使用sudo）
sudo usermod -aG docker $USER

# 重新登录或执行以下命令使组权限生效
newgrp docker
```

### 安装Docker Compose
```bash
# 下载Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

## 步骤4: 安装开发工具（可选，用于本地开发）

### 安装Node.js
```bash
# 使用NodeSource仓库安装Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# 验证安装
node --version
npm --version
```

### 安装Go
```bash
# 下载Go 1.21
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# 解压到/usr/local
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# 添加到PATH
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
echo 'export GOPATH=$HOME/go' >> ~/.bashrc
source ~/.bashrc

# 验证安装
go version
```

### 安装Python 3.11
```bash
# 添加deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# 安装Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# 创建符号链接
sudo ln -sf /usr/bin/python3.11 /usr/bin/python3

# 验证安装
python3 --version
pip3 --version
```

### 安装Rust
```bash
# 安装Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 重新加载环境
source ~/.cargo/env

# 验证安装
rustc --version
cargo --version
```

## 步骤5: 克隆项目代码

```bash
# 克隆项目（替换为你的仓库地址）
git clone https://github.com/your-username/pdf-chapter-splitter.git
cd pdf-chapter-splitter

# 或者如果你要从本地上传代码
# 可以使用scp命令上传项目文件
```

## 步骤6: 配置环境变量

```bash
# 创建环境变量文件
cp .env.example .env

# 编辑环境变量
vim .env
```

### 环境变量配置示例
```env
# 服务器配置
HOST=0.0.0.0
FRONTEND_PORT=3000
BACKEND_PORT=8080
AI_SERVICE_PORT=8000

# 文件存储
UPLOAD_DIR=/app/uploads
TEMP_DIR=/app/temp
MAX_FILE_SIZE=52428800

# 服务URL（使用腾讯云主机的公网IP）
NEXT_PUBLIC_API_URL=http://your-server-ip:8080
AI_SERVICE_URL=http://ai-service:8000

# 生产环境配置
ENVIRONMENT=production
DEBUG=false
```

## 步骤7: 启动服务

### 使用Docker Compose启动所有服务
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务的日志
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f ai-service
```

### 验证服务运行状态
```bash
# 检查端口是否正在监听
sudo netstat -tlnp | grep -E ':(3000|8080|8000)'

# 或使用ss命令
ss -tlnp | grep -E ':(3000|8080|8000)'
```

## 步骤8: 配置防火墙（如果需要）

```bash
# 安装ufw防火墙
sudo apt install -y ufw

# 配置防火墙规则
sudo ufw allow ssh
sudo ufw allow 3000
sudo ufw allow 8080
sudo ufw allow 8000

# 启用防火墙
sudo ufw enable

# 查看防火墙状态
sudo ufw status
```

## 步骤9: 配置域名和SSL（可选）

### 使用Nginx反向代理
```bash
# 安装Nginx
sudo apt install -y nginx

# 创建Nginx配置文件
sudo vim /etc/nginx/sites-available/pdf-splitter
```

### Nginx配置示例
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端代理
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/pdf-splitter /etc/nginx/sites-enabled/

# 测试Nginx配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 使用Let's Encrypt配置SSL
```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 步骤10: 监控和维护

### 设置日志轮转
```bash
# 创建Docker日志轮转配置
sudo vim /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
# 重启Docker服务
sudo systemctl restart docker
```

### 设置系统监控
```bash
# 安装htop和iotop
sudo apt install -y htop iotop

# 查看系统资源使用情况
htop
iotop
df -h
free -h
```

### 备份脚本
```bash
# 创建备份脚本
vim ~/backup.sh
```

```bash
#!/bin/bash
# PDF章节拆分器备份脚本

BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/home/ubuntu/pdf-chapter-splitter"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份项目文件
tar -czf $BACKUP_DIR/pdf-splitter-$DATE.tar.gz -C $PROJECT_DIR .

# 备份Docker数据卷
docker run --rm -v pdf-chapter-splitter_uploads:/data -v $BACKUP_DIR:/backup alpine tar czf /backup/uploads-$DATE.tar.gz -C /data .

# 清理7天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $DATE"
```

```bash
# 添加执行权限
chmod +x ~/backup.sh

# 设置定时备份
crontab -e
# 添加以下行（每天凌晨2点备份）：
# 0 2 * * * /home/ubuntu/backup.sh >> /home/ubuntu/backup.log 2>&1
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看端口占用情况
   sudo lsof -i :3000
   sudo lsof -i :8080
   sudo lsof -i :8000
   
   # 杀死占用端口的进程
   sudo kill -9 <PID>
   ```

2. **Docker服务无法启动**
   ```bash
   # 检查Docker服务状态
   sudo systemctl status docker
   
   # 重启Docker服务
   sudo systemctl restart docker
   
   # 查看Docker日志
   sudo journalctl -u docker.service
   ```

3. **内存不足**
   ```bash
   # 查看内存使用情况
   free -h
   
   # 清理Docker缓存
   docker system prune -a
   
   # 重启服务释放内存
   docker-compose restart
   ```

4. **磁盘空间不足**
   ```bash
   # 查看磁盘使用情况
   df -h
   
   # 清理Docker镜像和容器
   docker system prune -a --volumes
   
   # 清理日志文件
   sudo journalctl --vacuum-time=7d
   ```

### 性能优化

1. **调整Docker资源限制**
   ```yaml
   # 在docker-compose.yml中添加资源限制
   services:
     frontend:
       deploy:
         resources:
           limits:
             memory: 512M
           reservations:
             memory: 256M
   ```

2. **启用Gzip压缩**
   ```nginx
   # 在Nginx配置中添加
   gzip on;
   gzip_vary on;
   gzip_min_length 1024;
   gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
   ```

## 访问应用

配置完成后，你可以通过以下地址访问应用：

- **前端应用**: `http://your-server-ip:3000` 或 `https://your-domain.com`
- **后端API**: `http://your-server-ip:8080/api`
- **AI服务**: `http://your-server-ip:8000/docs` (API文档)

## 安全建议

1. **定期更新系统和软件包**
2. **使用强密码和SSH密钥认证**
3. **配置防火墙规则**
4. **启用SSL/TLS加密**
5. **定期备份重要数据**
6. **监控系统日志和资源使用情况**
7. **限制不必要的网络访问**

---

如果在配置过程中遇到问题，请检查日志文件或联系技术支持。