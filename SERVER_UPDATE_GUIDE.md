# 服务器端文件未更新问题解决方案

## 问题确认

✅ **本地验证通过**：
- 本地 `gif_generator.py` 已包含新的换行逻辑
- 逻辑测试确认：9个字符应该触发换行

❌ **服务器端问题**：
- 客户端测试未显示换行
- **结论：服务器端的 `gif_generator.py` 文件未真正更新**

---

## 解决步骤

### 步骤1：SSH登录服务器
```bash
ssh user@your-server-ip
```

### 步骤2：进入项目目录
```bash
cd /path/to/imgif  # 替换为实际路径
```

### 步骤3：确认当前文件状态
```bash
# 检查服务器文件是否包含新代码
grep "needs_wrap" gif_generator.py

# 如果没有输出，说明文件未更新
# 如果有输出，说明文件已更新但容器未重载
```

### 步骤4：重新上传文件到服务器

**方法A：使用 SCP（从本地上传）**
```bash
# 在本地Windows PowerShell执行
scp c:\ai\imgif\gif_generator.py user@server-ip:/path/to/imgif/
```

**方法B：使用 FTP/SFTP工具**
- 使用 FileZilla、WinSCP 等工具
- 连接到服务器
- 上传 `c:\ai\imgif\gif_generator.py` 到服务器的 `imgif` 目录

**方法C：直接在服务器上编辑**
```bash
# 在服务器上执行
vim gif_generator.py

# 或者使用 nano
nano gif_generator.py
```

### 步骤5：验证文件已更新
```bash
# 确认关键代码存在
grep -n "needs_wrap" gif_generator.py
grep -n "Auto-enabling wrap" gif_generator.py
grep -n "no_wrap_effects = \['scroll', 'spray'\]" gif_generator.py

# 应该看到类似输出：
# 358:    needs_wrap = auto_wrap
# 370:                logger.info(f"Auto-enabling wrap: {char_count} chars > 8")
# 363:        no_wrap_effects = ['scroll', 'spray']
```

### 步骤6：检查Docker容器内的文件
```bash
# 由于配置了卷挂载，容器内应该自动同步
docker exec gifapi cat /app/gif_generator.py | grep "needs_wrap"

# 如果没有输出，说明卷挂载有问题
```

### 步骤7：重启Docker容器
```bash
# 方法1：简单重启（推荐）
docker-compose restart

# 方法2：完全停止并重启
docker-compose down
docker-compose up -d

# 方法3：强制重建（如果上述方法无效）
docker-compose down
docker-compose up -d --build
```

### 步骤8：查看容器日志
```bash
# 实时查看日志
docker-compose logs -f

# 或
docker logs -f gifapi

# 等待看到：
# INFO:     Application startup complete.
```

### 步骤9：测试换行功能
```bash
# 在服务器上测试
curl "http://localhost:8066/generate?text=嘿嘿嘿丽丽哈哈明天&color=neon" -o test.gif

# 同时查看日志，应该看到：
# INFO:uvicorn:Auto-enabling wrap: 9 chars > 8
```

---

## 常见问题排查

### Q1: 文件上传后容器内还是旧代码
**原因**：卷挂载路径不对
**解决**：
```bash
# 检查 docker-compose.yml 的卷挂载配置
cat docker-compose.yml | grep -A 2 "volumes"

# 应该看到：
# volumes:
#   - ./:/app

# 如果路径不对，修改后重启
vim docker-compose.yml
docker-compose down
docker-compose up -d
```

### Q2: 容器日志中没有 "Auto-enabling wrap" 消息
**原因1**：文件未真正更新
**原因2**：API调用时传了 `wrap=true` 参数（会跳过自动判断）
**解决**：
```bash
# 检查API调用
# 确保URL中没有 wrap=true 参数
# 正确：http://localhost:8066/generate?text=嘿嘿嘿丽丽哈哈明天&color=neon
# 错误：http://localhost:8066/generate?text=嘿嘿嘿丽丽哈哈明天&color=neon&wrap=true
```

### Q3: 重启后还是不换行
**可能原因**：客户端缓存了旧的GIF
**解决**：
1. 清除客户端浏览器缓存
2. 在URL后加时间戳：`?text=xxx&t=123456`
3. 使用隐私/无痕模式测试

---

## 快速检查清单

- [ ] 本地文件已更新（✅ 已确认）
- [ ] 服务器文件已更新（执行步骤3检查）
- [ ] Docker容器内文件已更新（执行步骤6检查）
- [ ] Docker容器已重启（执行步骤7）
- [ ] 日志中出现 "Auto-enabling wrap" （执行步骤9）
- [ ] 客户端看到换行效果

---

## 直接复制执行

在服务器上依次执行：

```bash
# 1. 进入目录
cd /path/to/imgif

# 2. 检查文件
grep "needs_wrap" gif_generator.py || echo "文件未更新！"

# 3. 检查容器内文件
docker exec gifapi grep "needs_wrap" /app/gif_generator.py || echo "容器内文件未更新！"

# 4. 重启容器
docker-compose restart

# 5. 查看日志
docker logs -f gifapi
```

按 `Ctrl+C` 停止日志查看，然后测试生成GIF，观察是否出现 "Auto-enabling wrap" 日志。
