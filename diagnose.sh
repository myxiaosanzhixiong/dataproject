#!/bin/bash

echo "=========================================="
echo "应用连接性诊断"
echo "=========================================="
echo ""

# 1. 检查应用进程
echo "[1] 应用进程状态:"
if pgrep -f "uvicorn main:app" > /dev/null; then
    echo "    ✓ 应用正在运行"
    ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print "    PID:", $2, "CMD:", $11, $12, $13}'
else
    echo "    ✗ 应用未运行"
    exit 1
fi
echo ""

# 2. 检查端口监听
echo "[2] 80端口监听状态:"
if netstat -tuln 2>/dev/null | grep ":80 " > /dev/null || ss -tuln 2>/dev/null | grep ":80 " > /dev/null; then
    echo "    ✓ 端口 80 正在监听"
    netstat -tuln 2>/dev/null | grep ":80" || ss -tuln 2>/dev/null | grep ":80"
else
    echo "    ✗ 端口 80 未监听"
    exit 1
fi
echo ""

# 3. 检查数据库连接
echo "[3] MySQL数据库状态:"
if mysql -u trader -ptraderpass123 -e "SELECT 1" portfolio_mgmt > /dev/null 2>&1; then
    echo "    ✓ MySQL连接正常"
    mysql -u trader -ptraderpass123 -e "SELECT COUNT(*) as '表数量' FROM information_schema.tables WHERE table_schema='portfolio_mgmt';" portfolio_mgmt 2>/dev/null || true
else
    echo "    ✗ MySQL连接失败"
fi
echo ""

# 4. 检查网络接口
echo "[4] 网络配置:"
echo "    本地IP: $(hostname -I | awk '{print $1}')"
echo "    外部IP: 35.239.55.146"
echo ""

# 5. 检查防火墙规则（如果是GCP）
echo "[5] GCP防火墙规则:"
if command -v gcloud &> /dev/null; then
    echo "    检查是否允许HTTP(80)和HTTPS(443)..."
    gcloud compute firewall-rules list --format="table(name,allowed)" 2>/dev/null | grep -E "allow-http|allow-https" || echo "    ⚠ 未找到允许HTTP/HTTPS的规则"
else
    echo "    gcloud CLI 未安装 (这是可选的)"
fi
echo ""

# 6. 测试本地访问
echo "[6] 本地访问测试:"
if python3 -c "import urllib.request; urllib.request.urlopen('http://localhost/').read()" > /dev/null 2>&1; then
    echo "    ✓ http://localhost 可访问"
else
    echo "    ✗ http://localhost 无法访问"
fi
echo ""

# 7. 应用日志最后几行
echo "[7] 应用日志 (最近5条):"
if [ -f /tmp/app.log ]; then
    tail -5 /tmp/app.log | sed 's/^/    /'
else
    echo "    日志文件未找到"
fi
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果所有检查都通过✓，但外部IP仍无法访问，可能原因："
echo "  1. GCP防火墙规则未配置 → 运行 setup_gcp_firewall.sh"
echo "  2. 规则生效需要10-30秒 → 稍候后重试"
echo "  3. DNS解析问题 → 直接使用IP地址访问"
echo "  4. 云平台安全组配置 → 检查云平台的安全组设置"
echo ""
