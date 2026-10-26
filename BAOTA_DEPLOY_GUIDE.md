# 宝塔面板部署指南

本项目是 FastAPI 服务，默认监听 `8066` 端口。服务器有宝塔面板时，推荐使用 Docker Compose 部署，再用宝塔网站反向代理到容器端口。

## 一、服务器准备

1. 登录宝塔面板。
2. 安装软件：
   - Docker 管理器 / Docker
   - Nginx
3. 放行端口：
   - 宝塔安全：放行 `8066`
   - 云服务器安全组：放行 `8066`
   - 如果绑定域名并启用 HTTPS，额外放行 `80` 和 `443`

## 二、上传项目

建议上传到：

```bash
/www/wwwroot/gif-generator
```

上传时至少保留这些文件和目录：

```text
main.py
gif_generator.py
optimized_mask_functions.py
template_compositor.py
requirements.txt
Dockerfile
docker-compose.yml
static/
templates/
fonts/
emoji/
mask_backgrounds/
背景/
```

不需要上传：

```text
.venv/
.uv-cache/
.uv-python/
__pycache__/
test_outputs/
*.log
```

## 三、Docker Compose 启动

在宝塔终端或 SSH 中执行：

```bash
cd /www/wwwroot/gif-generator
docker compose up -d --build
```

如果服务器 Docker 版本较旧，命令可能是：

```bash
docker-compose up -d --build
```

查看运行状态：

```bash
docker ps
docker logs -f gifapi
```

看到 `Application startup complete` 就表示服务已启动。

## 四、访问测试

服务器本机测试：

```bash
curl http://127.0.0.1:8066/health
```

应该返回：

```json
{"status":"ok"}
```

浏览器访问：

```text
http://服务器IP:8066/
```

测试生成接口：

```text
http://服务器IP:8066/generate?text=测试&color=neon
```

## 五、绑定域名和 HTTPS

1. 宝塔面板进入「网站」。
2. 添加站点，例如 `gif.example.com`。
3. 站点设置中打开「反向代理」。
4. 添加代理：
   - 代理名称：`gif-generator`
   - 目标 URL：`http://127.0.0.1:8066`
   - 发送域名：`$host`
5. SSL 菜单里申请 Let's Encrypt 证书。

配置好后访问：

```text
https://gif.example.com/
```

## 六、更新代码

上传新文件后执行：

```bash
cd /www/wwwroot/gif-generator
docker compose restart
```

如果改了 `requirements.txt`、`Dockerfile` 或系统依赖，执行：

```bash
cd /www/wwwroot/gif-generator
docker compose up -d --build
```

## 七、常见问题

### 页面打不开

检查容器是否运行：

```bash
docker ps
docker logs --tail=100 gifapi
```

检查端口是否监听：

```bash
curl http://127.0.0.1:8066/health
```

### 域名能打开但生成慢

GIF 生成比较吃 CPU，可以先把并发调低，避免服务器卡死。编辑 `docker-compose.yml`：

```yaml
environment:
  - GIF_GENERATION_CONCURRENCY=1
```

然后重启：

```bash
docker compose restart
```

### 上传新代码后没生效

执行：

```bash
cd /www/wwwroot/gif-generator
docker compose restart
docker logs -f gifapi
```

### 需要关闭服务

```bash
cd /www/wwwroot/gif-generator
docker compose down
```
