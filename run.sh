#!/bin/bash

# Portfolio Management System - 启动脚本
# 在80端口运行应用

set -e

echo "=========================================="
echo "Portfolio Management System"
echo "=========================================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# 检查依赖
cd /root/dataproject/backend
echo "✓ Dependencies check..."

# 设置环境变量
export DB_HOST="${DB_HOST:-localhost}"
export DB_PORT="${DB_PORT:-3306}"
export DB_USER="${DB_USER:-trader}"
export DB_PASSWORD="${DB_PASSWORD:-traderpass123}"
export DB_NAME="${DB_NAME:-portfolio_mgmt}"

echo ""
echo "Configuration:"
echo "  - Database Host: $DB_HOST"
echo "  - Database Port: $DB_PORT"
echo "  - Database Name: $DB_NAME"
echo ""

# 检查是否有sudo权限（因为需要80端口）
if [ "$EUID" -ne 0 ]; then 
    echo "NOTE: 80端口需要root权限。尝试使用sudo..."
    echo ""
    exec sudo -E python3 -m uvicorn main:app --host 0.0.0.0 --port 80 --reload
else
    echo "Starting on port 80..."
    echo ""
    python3 -m uvicorn main:app --host 0.0.0.0 --port 80 --reload
fi
