# GCP防火墙配置指南

## 问题
外部IP (35.239.55.146) 无法访问运行在80端口的应用

## 原因
GCP默认防火墙规则阻止了HTTP (80) 和 HTTPS (443) 端口的入站流量

## 解决方案

### 方案A: 使用gcloud CLI配置防火墙

```bash
# 允许HTTP流量
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80 \
  --source-ranges=0.0.0.0/0 \
  --description="Allow HTTP traffic"

# 允许HTTPS流量
gcloud compute firewall-rules create allow-https \
  --allow=tcp:443 \
  --source-ranges=0.0.0.0/0 \
  --description="Allow HTTPS traffic"

# 允许SSH（用于管理）
gcloud compute firewall-rules create allow-ssh \
  --allow=tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --description="Allow SSH traffic"
```

### 方案B: 使用GCP Console（Web界面）

1. 打开 GCP Console
2. 导航到 VPC > Firewall > Create Firewall Rule
3. 配置如下：
   - **Name**: allow-http
   - **Direction of traffic**: Ingress
   - **Priority**: 1000
   - **Action on match**: Allow
   - **Source IPv4 ranges**: 0.0.0.0/0
   - **Specified protocols and ports**:
     - TCP: 80, 443
   - Click Create

### 方案C: 仅允许特定IP范围（更安全）

如果你只需要特定IP访问，修改source-ranges：

```bash
# 仅允许特定IP段
gcloud compute firewall-rules create allow-http-restricted \
  --allow=tcp:80 \
  --source-ranges=YOUR_IP/32 \
  --description="Allow HTTP from specific IP"
```

## 验证配置

配置完成后，访问应该立即可用：
```
http://35.239.55.146
```

## 应用状态

- **运行进程**: /usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 80
- **内部IP**: 192.168.52.114:80 ✓ (已测试)
- **外部IP**: 35.239.55.146 (需要防火墙规则)
- **数据库**: MySQL (localhost:3306) ✓ 已配置
