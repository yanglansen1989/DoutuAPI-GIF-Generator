# 星空GIF转换命令示例

## 场景1：从视频转换星空GIF

### 基本转换
```bash
ffmpeg -i starry_sky.mp4 \
  -vf "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2,fps=20" \
  -loop 0 \
  c:\ai\imgif\mask_backgrounds\stars.gif
```

### 高质量转换（推荐）
```bash
ffmpeg -i starry_sky.mp4 \
  -ss 00:00:05 -t 00:00:03 \
  -vf "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2:color=black,fps=24,split[s0][s1];[s0]palettegen=max_colors=256[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5" \
  -loop 0 \
  c:\ai\imgif\mask_backgrounds\stars.gif
```

参数说明：
- `-ss 00:00:05`: 从第5秒开始
- `-t 00:00:03`: 提取3秒
- `fps=24`: 24帧/秒
- `max_colors=256`: 调色板颜色数
- `bayer_scale=5`: 抖动级别

### 压缩版本
```bash
ffmpeg -i starry_sky.mp4 \
  -vf "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2,fps=15" \
  -loop 0 \
  c:\ai\imgif\mask_backgrounds\stars.gif
```

---

## 场景2：从图片序列制作

```bash
# 假设有 star001.jpg, star002.jpg, ...
ffmpeg -framerate 20 -i star%03d.jpg \
  -vf "scale=480:480" \
  -loop 0 \
  c:\ai\imgif\mask_backgrounds\stars.gif
```

---

## 场景3：优化已有GIF

### 压缩GIF
```bash
ffmpeg -i large_stars.gif \
  -vf "scale=480:480,fps=15" \
  -loop 0 \
  c:\ai\imgif\mask_backgrounds\stars.gif
```

### 减少帧数
```bash
ffmpeg -i original_stars.gif \
  -vf "fps=12" \
  -loop 0 \
  c:\ai\imgif\mask_backgrounds\stars.gif
```

### 使用Gifsiclepython (更好的压缩)
```bash
# 安装
pip install gifsicle

# 压缩
gifsicle --optimize=3 --scale 0.5 original.gif -o c:\ai\imgif\mask_backgrounds\stars.gif
```

---

## 场景4：在线下载的GIF处理

假设从Pexels下载了stars.gif：

```bash
# 调整大小并优化
ffmpeg -i downloads\pexels_stars.gif \
  -vf "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2,fps=20" \
  -loop 0 \
  c:\ai\imgif\mask_backgrounds\stars.gif
```

---

## Windows PowerShell命令

在PowerShell中使用（注意路径）：

```powershell
# 基本转换
ffmpeg -i "D:\videos\starry_sky.mp4" `
  -vf "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2,fps=20" `
  -loop 0 `
  "c:\ai\imgif\mask_backgrounds\stars.gif"

# 高质量
ffmpeg -i "D:\videos\starry_sky.mp4" `
  -ss 00:00:05 -t 00:00:03 `
  -vf "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2:color=black,fps=24" `
  -loop 0 `
  "c:\ai\imgif\mask_backgrounds\stars.gif"
```

---

## 快速测试

转换后立即测试：

```powershell
# 转换
ffmpeg -i your_video.mp4 -vf "scale=480:480,fps=20" -loop 0 c:\ai\imgif\mask_backgrounds\stars.gif

# 测试
cd c:\ai\imgif
python test_stars_with_gif.py
```

---

## 推荐素材来源

### 免费视频网站
1. **Pexels** (https://www.pexels.com/search/videos/starry%20sky/)
2. **Pixabay** (https://pixabay.com/videos/search/stars/)
3. **Videvo** (https://www.videvo.net)

### 搜索关键词
- "starry night time lapse"
- "milky way stars"
- "night sky stars"
- "galaxy animation"
- "space stars loop"

### 推荐参数
- **时长**: 2-5秒（足够循环）
- **分辨率**: 1080p或更高
- **类型**: 延时摄影、循环动画

---

## 常用参数对照表

| 用途 | FPS | 大小估算 | 推荐场景 |
|------|-----|---------|---------|
| 高质量 | 24 | ~2-5MB | 作品展示 |
| 标准 | 20 | ~1-3MB | 日常使用 |
| 压缩 | 15 | ~500KB-1MB | 快速加载 |
| 极简 | 10 | ~300-500KB | 性能优先 |

---

## 检查结果

转换完成后检查：

```powershell
# 查看文件信息
ffprobe c:\ai\imgif\mask_backgrounds\stars.gif

# 快速预览
start c:\ai\imgif\mask_backgrounds\stars.gif
```

---

**准备好GIF后，放到 `c:\ai\imgif\mask_backgrounds\stars.gif`，重新生成即可看到效果！** ✨
