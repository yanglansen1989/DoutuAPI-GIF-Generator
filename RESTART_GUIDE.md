# 服务器重启问题和解决方案

## 问题原因

**Python模块缓存问题：** 服务器启动时会将 `gif_generator.py` 加载到内存中。即使您替换了文件，已运行的服务器仍然使用旧代码。

## 解决方案

### 方案1：手动重启服务器（推荐）

如果服务器正在运行窗口中运行：
1. 切换到运行服务器的终端窗口
2. 按 `Ctrl + C` 停止服务器
3. 重新运行启动命令：
   ```bash
   python main.py
   ```
   或
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8066 --reload
   ```

### 方案2：使用PowerShell杀掉进程并重启

找到服务器进程ID（通常是最近启动的Python进程）：
```powershell
# 查看所有Python进程
Get-Process python | Select-Object Id, StartTime, Path

# 杀掉特定进程（替换 <PID> 为实际进程ID）
Stop-Process -Id <PID>

# 重新启动服务器
cd c:\ai\imgif
python main.py
```

### 方案3：重启所有imgif相关的Python进程（谨慎使用）

```powershell
# 这会杀掉路径包含 'imgif' 的所有Python进程
Get-Process python | Where-Object {$_.Path -like '*imgif*'} | Stop-Process -Force
```

## 验证重启是否成功

重启后，查看服务器日志，应该会看到类似：
```
INFO:     Uvicorn running on http://0.0.0.0:8066
INFO:     Application startup complete.
```

然后测试一个超过8个字符的文本，例如：
```
http://localhost:8066/generate?text=这是一段很长的测试文本&color=neon
```

如果看到日志中出现 **"Auto-enabling wrap: XX chars > 8"**，说明新代码已生效！

## 注意事项

⚠️ `uvicorn` 的 `reload=True` 选项应该会自动重载，但有时会失败
⚠️ 如果使用了多进程或Docker，需要重启整个容器
⚠️ 重启后需要等待几秒让服务器完全启动
