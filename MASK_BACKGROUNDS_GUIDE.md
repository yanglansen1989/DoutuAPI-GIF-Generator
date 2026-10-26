# 蒙版背景GIF使用指南

## 📁 目录结构

```
c:\ai\imgif\
├── mask_backgrounds\          # 蒙版背景GIF目录
│   ├── stars.gif             # 星空蒙版背景
│   ├── fire.gif              # 火焰蒙版背景（可选）
│   ├── smoke.gif             # 烟雾蒙版背景（可选）
│   └── ...                   # 其他蒙版背景
```

## ⭐ 星空蒙版 (stars_mask)

### 使用方法

1. **准备GIF文件**
   - 分辨率：建议480x480（会自动缩放）
   - 内容：密集星空、闪烁星星、星系等
   - 格式：GIF（支持动画）
   - 示例：真实星空延时摄影、动画星空等

2. **放置文件**
   ```
   c:\ai\imgif\mask_backgrounds\stars.gif
   ```

3. **使用效果**
   - 访问：http://localhost:8066
   - 选择：星空蒙版 (Stars Mask)
   - 输入文字，生成GIF

### 素材要求

**推荐素材类型：**
- ✅ 密集星空（银河系）
- ✅ 闪烁星星动画
- ✅ 星云、星团
- ✅ 流星雨效果
- ✅ 太空延时摄影

**技术要求：**
- 分辨率：480x480或更大（自动缩放）
- 帧数：10-30帧
- 循环：支持循环播放
- 背景：深色背景（黑色、深蓝）

**不推荐：**
- ❌ 白天天空
- ❌ 云层（建议用smoke_mask）
- ❌ 过亮背景

### 备用方案

如果没有GIF文件，系统会自动使用**默认星空**：
- 500颗随机星星
- 深蓝夜空背景
- 星星大小和亮度随机

## 🎨 效果对比

### 使用外部GIF
```
优点：
  ✅ 真实星空效果
  ✅ 密集星光
  ✅ 专业质感
  ✅ 动画流畅

缺点：
  ⚠️ 需要准备素材
  ⚠️ 文件可能较大
```

### 使用默认星空
```
优点：
  ✅ 无需额外文件
  ✅ 即开即用
  ✅ 文件小

缺点：
  ⚠️ 程序化生成
  ⚠️ 效果相对简单
```

## 🔧 高级配置

### 扩展其他蒙版

可以为其他蒙版也添加GIF背景：

**火焰蒙版：**
```
mask_backgrounds/fire.gif
→ 真实火焰视频转GIF
```

**烟雾蒙版：**
```
mask_backgrounds/smoke.gif
→ 彩色烟雾效果
```

**水波纹蒙版：**
```
mask_backgrounds/ripple.gif
→ 水波纹动画
```

### 修改代码支持

在`gif_generator.py`中找到对应的蒙版函数，参考stars_mask的实现：

```python
# 示例：修改火焰蒙版
gif_path = os.path.join('mask_backgrounds', 'fire.gif')
if os.path.exists(gif_path):
    # 加载GIF
    gif = Image.open(gif_path)
    # ... 处理逻辑
else:
    # 使用默认生成
    # ... 原有代码
```

## 📊 GIF制作建议

### 使用FFmpeg转换

```bash
# 从视频提取并转换为GIF
ffmpeg -i starry_sky.mp4 \
  -vf "scale=480:480:force_original_aspect_ratio=decrease,pad=480:480:(ow-iw)/2:(oh-ih)/2,fps=20" \
  -loop 0 \
  c:\ai\imgif\mask_backgrounds\stars.gif

# 压缩GIF
ffmpeg -i stars.gif \
  -vf "split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  -loop 0 \
  stars_optimized.gif
```

### 在线工具

- EZGif (https://ezgif.com)
- CloudConvert (https://cloudconvert.com)
- 视频转GIF在线工具

### 推荐设置

- **分辨率**：480x480
- **帧率**：15-24fps
- **时长**：2-5秒（循环播放）
- **大小**：<2MB

## 🎯 测试效果

修改完成后测试：

```bash
cd c:\ai\imgif
python test_stars_with_gif.py
```

或访问：
```
http://localhost:8066/generate?text=星空测试&color=stars_mask
```

## 📝 注意事项

1. **文件命名**：必须是`stars.gif`（小写）
2. **路径正确**：放在`mask_backgrounds`文件夹
3. **权限**：确保文件可读
4. **重启服务**：修改后服务会自动重载（--reload模式）
5. **性能**：GIF文件不要太大（建议<5MB）

## ❓ 常见问题

**Q: GIF不显示怎么办？**
A: 检查文件路径和名称，查看服务器日志

**Q: 可以用MP4吗？**
A: 不可以，必须先转换为GIF

**Q: GIF太大怎么办？**
A: 使用FFmpeg或在线工具压缩

**Q: 支持透明背景吗？**
A: 支持，但建议用深色背景

## 🌟 推荐资源

**免费星空素材：**
- Pexels (https://www.pexels.com)
- Pixabay (https://pixabay.com)
- Unsplash (https://unsplash.com)

搜索关键词：
- starry sky time lapse
- milky way
- stars animation
- space background

---

**现在把您的星空GIF放到 `mask_backgrounds/stars.gif`，就可以看到效果了！** ✨
