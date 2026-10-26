# Docker 部署重启指南

## 问题诊断

✅ **好消息**：您的 `docker-compose.yml` 已配置卷挂载：
```yaml
volumes:
  - ./:/app  # 本地文件已映射到容器
```

❌ **问题**：虽然文件已映射，但容器内的 `uvicorn --reload` 可能没有检测到文件变化，或者Python已缓存旧模块。

---

## 解决方案（按推荐顺序）

### 方案1：重启Docker容器（最快，推荐）

```bash
# 进入项目目录
cd c:\ai\imgif

# 重启容器
docker-compose restart

# 或者使用容器名重启
docker restart gifapi
```

**验证：**
```bash
# 查看容器日志，确认重启成功
docker logs -f gifapi
```

---

### 方案2：停止并重新启动容器（更彻底）

```bash
cd c:\ai\imgif

# 停止容器
docker-compose down

# 重新启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

### 方案3：强制重新构建镜像（如果上述方案无效）

```bash
cd c:\ai\imgif

# 停止并删除容器
docker-compose down

# 重新构建镜像并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f
```

> ⚠️ **注意**：由于配置了卷挂载，通常不需要重新构建镜像

---

### 方案4：进入容器手动重启uvicorn

```bash
# 进入容器
docker exec -it gifapi bash

# 查看进程
ps aux | grep uvicorn

# 杀掉uvicorn进程
pkill -f uvicorn

# 退出容器（容器会自动重启uvicorn）
exit
```

---

## 验证换行功能是否生效

重启后，访问以下URL测试（替换为您的服务器地址）：

```
http://localhost:8066/generate?text=这是一段很长的测试文本&color=neon
```

**查看容器日志，应该看到：**
```
INFO:uvicorn:Auto-enabling wrap: 11 chars > 8
```

如果看到这条日志，说明新代码已生效！✅

---

## 常用Docker命令

```bash
# 查看运行中的容器
docker ps

# 查看容器日志（实时）
docker logs -f gifapi

# 查看容器详情
docker inspect gifapi

# 进入容器调试
docker exec -it gifapi bash

# 查看容器内的文件（确认是否更新）
docker exec gifapi cat /app/gif_generator.py | grep "Auto-enabling wrap"
```

---

## 故障排查

### 如果重启后仍不生效：

1. **确认文件确实已更新：**
   ```bash
   docker exec gifapi cat /app/gif_generator.py | grep "needs_wrap"
   ```
   应该能看到 `needs_wrap` 变量

2. **检查卷挂载是否正常：**
   ```bash
   docker inspect gifapi | grep -A 10 "Mounts"
   ```

3. **确认容器使用的是正确的代码路径：**
   ```bash
   docker exec gifapi pwd
   docker exec gifapi ls -la /app/gif_generator.py
   ```

---

## 推荐操作

执行以下命令即可：

```bash
cd c:\ai\imgif
docker-compose restart
docker-compose logs -f
```

等待看到 "Application startup complete" 后，测试换行功能。
