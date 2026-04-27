#!/bin/bash

# GCP防火墙快速配置脚本

echo "=========================================="
echo "GCP Firewall Configuration"
echo "=========================================="
echo ""
echo "当前配置："
echo "  外部IP: 35.239.55.146"
echo "  内部IP: 192.168.52.114"
echo "  应用端口: 80"
echo ""

# 检查是否安装了gcloud
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI 未安装"
    echo "请访问: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✓ gcloud CLI 已检测到"
echo ""
echo "执行防火墙配置..."
echo ""

# 配置HTTP防火墙规则
echo "1. 创建HTTP允许规则..."
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --description="Allow HTTP traffic on port 80" 2>/dev/null || echo "   (规则可能已存在)"

echo "✓ HTTP规则已配置"
echo ""

# 配置HTTPS防火墙规则
echo "2. 创建HTTPS允许规则..."
gcloud compute firewall-rules create allow-https \
  --allow=tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --description="Allow HTTPS traffic on port 443" 2>/dev/null || echo "   (规则可能已存在)"

echo "✓ HTTPS规则已配置"
echo ""

# 列出防火墙规则
echo "=========================================="
echo "当前防火墙规则:"
echo "=========================================="
gcloud compute firewall-rules list --format="table(name,direction,priority,sourceRanges[].list():label=SOURCE_RANGES,allowed[].map().firewall_rule().list():label=ALLOW)"

echo ""
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "现在可以通过以下地址访问应用:"
echo "  http://35.239.55.146"
echo ""
echo "等待10-30秒规则生效..."
