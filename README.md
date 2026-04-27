# Portfolio Management System - 启动指南

## 项目结构
```
dataproject/
├── backend/           # FastAPI Python后端
├── frontend/          # HTML前端界面
├── sql/               # 数据库初始化脚本
├── docker-compose.yml # Docker Compose配置
├── run.sh            # 启动脚本
└── start_server.sh   # 备选启动脚本
```

## 运行方式

### 方式1: 直接运行（推荐快速测试）
在8000端口运行（无需sudo）：
```bash
cd /root/dataproject/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

然后在浏览器访问: http://localhost:8000

### 方式2: 在80端口运行（需要root权限）
```bash
cd /root/dataproject
sudo bash run.sh
```

或：
```bash
cd /root/dataproject/backend
sudo python3 -m uvicorn main:app --host 0.0.0.0 --port 80
```

然后在浏览器访问: http://localhost

### 方式3: 使用Docker Compose（完整环境 - 需要安装Docker）
```bash
cd /root/dataproject
docker-compose up -d
```

这将启动：
- MySQL数据库 (port 3307)
- FastAPI后端 (port 8080)

## 数据库配置

项目使用MySQL数据库。环境变量配置：
- `DB_HOST`: localhost (默认)
- `DB_PORT`: 3306 (默认)
- `DB_USER`: trader
- `DB_PASSWORD`: traderpass123
- `DB_NAME`: portfolio_mgmt

如果要使用本地MySQL，请确保MySQL服务正在运行。

## 前端访问

应用启动后，访问根路径(/)即可看到前端界面。

默认登录凭证：
- Username: admin
- Password: admin123

## 应用特性

- 📊 投资组合管理系统
- 📈 实时资产跟踪
- 🔐 JWT认证
- 📱 响应式Web界面
- 🗄️ MySQL数据库存储

## 故障排查

**问题：连接数据库失败**
- 确保MySQL服务正在运行（如果使用本地MySQL）
- 检查数据库凭证是否正确
- 检查网络连接

**问题：权限拒绝（Port 80）**
- 使用8000或其他端口代替
- 或使用`sudo`运行脚本
- 或使用Docker Compose处理权限问题

**问题：模块未找到**
- 确保已安装依赖：`pip install -r backend/requirements.txt`
