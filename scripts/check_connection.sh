#!/bin/bash

# SSH连接检查脚本
# 使用方法: ./check_connection.sh <server-ip> [username] [port]

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 参数检查
if [ $# -lt 1 ]; then
    echo -e "${RED}使用方法: $0 <server-ip> [username] [port]${NC}"
    echo "示例: $0 123.456.789.123"
    echo "示例: $0 123.456.789.123 ubuntu 22"
    exit 1
fi

SERVER_IP=$1
USERNAME=${2:-ubuntu}
PORT=${3:-22}

echo -e "${BLUE}=== SSH连接检查工具 ===${NC}"
echo "服务器IP: $SERVER_IP"
echo "用户名: $USERNAME"
echo "端口: $PORT"
echo

# 1. 检查网络连通性
echo -e "${YELLOW}[1/5] 检查网络连通性...${NC}"
if ping -c 3 -W 3 "$SERVER_IP" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 网络连通正常${NC}"
else
    echo -e "${RED}✗ 网络连通失败，请检查IP地址或网络连接${NC}"
    exit 1
fi

# 2. 检查SSH端口
echo -e "${YELLOW}[2/5] 检查SSH端口 $PORT...${NC}"
if timeout 5 bash -c "</dev/tcp/$SERVER_IP/$PORT" 2>/dev/null; then
    echo -e "${GREEN}✓ SSH端口 $PORT 开放${NC}"
else
    echo -e "${RED}✗ SSH端口 $PORT 无法访问${NC}"
    echo "可能原因："
    echo "  - 防火墙阻止了端口 $PORT"
    echo "  - SSH服务未启动"
    echo "  - 端口号不正确"
    exit 1
fi

# 3. 检查SSH服务
echo -e "${YELLOW}[3/5] 检查SSH服务...${NC}"
if timeout 10 ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no "$USERNAME@$SERVER_IP" -p "$PORT" exit 2>/dev/null; then
    echo -e "${GREEN}✓ SSH服务正常，可以使用密钥认证${NC}"
elif timeout 10 ssh -o ConnectTimeout=5 -o PasswordAuthentication=no -o StrictHostKeyChecking=no "$USERNAME@$SERVER_IP" -p "$PORT" exit 2>&1 | grep -q "Permission denied"; then
    echo -e "${YELLOW}⚠ SSH服务正常，但需要密码或密钥认证${NC}"
else
    echo -e "${RED}✗ SSH服务异常${NC}"
    exit 1
fi

# 4. 检查常用密钥文件
echo -e "${YELLOW}[4/5] 检查本地SSH密钥...${NC}"
KEY_FOUND=false

# 检查常见的密钥文件位置
KEY_PATHS=(
    "$HOME/.ssh/id_rsa"
    "$HOME/.ssh/id_ed25519"
    "$HOME/.ssh/tencent-cloud-key.pem"
    "$HOME/.ssh/tencent_cloud_key"
    "$HOME/.ssh/key.pem"
)

for key_path in "${KEY_PATHS[@]}"; do
    if [ -f "$key_path" ]; then
        echo -e "${GREEN}✓ 找到密钥文件: $key_path${NC}"
        
        # 检查密钥文件权限
        perms=$(stat -c "%a" "$key_path" 2>/dev/null || stat -f "%A" "$key_path" 2>/dev/null)
        if [ "$perms" = "600" ] || [ "$perms" = "400" ]; then
            echo -e "${GREEN}  ✓ 密钥文件权限正确 ($perms)${NC}"
        else
            echo -e "${YELLOW}  ⚠ 密钥文件权限不安全 ($perms)，建议执行: chmod 600 $key_path${NC}"
        fi
        
        KEY_FOUND=true
    fi
done

if [ "$KEY_FOUND" = false ]; then
    echo -e "${YELLOW}⚠ 未找到常见的SSH密钥文件${NC}"
    echo "你可能需要："
    echo "  - 生成新的SSH密钥: ssh-keygen -t rsa -b 4096"
    echo "  - 从腾讯云控制台下载密钥文件"
fi

# 5. 尝试连接测试
echo -e "${YELLOW}[5/5] 尝试SSH连接测试...${NC}"

# 尝试使用找到的密钥文件连接
for key_path in "${KEY_PATHS[@]}"; do
    if [ -f "$key_path" ]; then
        echo "测试密钥文件: $key_path"
        if timeout 10 ssh -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=no -i "$key_path" "$USERNAME@$SERVER_IP" -p "$PORT" "echo 'SSH连接成功'" 2>/dev/null; then
            echo -e "${GREEN}✓ 使用密钥 $key_path 连接成功！${NC}"
            echo
            echo -e "${GREEN}=== 连接命令 ===${NC}"
            echo "ssh -i $key_path $USERNAME@$SERVER_IP -p $PORT"
            exit 0
        fi
    fi
done

# 如果密钥连接失败，提示可能需要密码
echo -e "${YELLOW}⚠ 密钥认证失败，可能需要密码认证${NC}"
echo
echo -e "${BLUE}=== 建议的连接方式 ===${NC}"
echo "1. 使用密码连接:"
echo "   ssh $USERNAME@$SERVER_IP -p $PORT"
echo
echo "2. 如果有密钥文件，使用:"
echo "   ssh -i /path/to/your-key.pem $USERNAME@$SERVER_IP -p $PORT"
echo
echo "3. 生成新的SSH密钥对:"
echo "   ssh-keygen -t rsa -b 4096 -C 'your-email@example.com'"
echo "   ssh-copy-id -i ~/.ssh/id_rsa.pub $USERNAME@$SERVER_IP"

echo
echo -e "${BLUE}=== 故障排除建议 ===${NC}"
echo "如果仍然无法连接，请检查："
echo "• 腾讯云安全组是否开放端口 $PORT"
echo "• 云主机是否正在运行"
echo "• 用户名是否正确（Ubuntu系统通常是 'ubuntu'）"
echo "• 密钥文件权限是否正确（应该是 600）"
echo "• 是否需要在腾讯云控制台重置密码"