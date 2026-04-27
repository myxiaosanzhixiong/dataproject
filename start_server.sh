#!/bin/bash

# 设置环境变量
export DB_HOST="localhost"
export DB_PORT="3306"
export DB_USER="trader"
export DB_PASSWORD="traderpass123"
export DB_NAME="portfolio_mgmt"

# 进入后端目录
cd /root/dataproject/backend

# 使用uvicorn在80端口启动FastAPI应用
echo "Starting application on port 80..."
sudo python3 -m uvicorn main:app --host 0.0.0.0 --port 80
