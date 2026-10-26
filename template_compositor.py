#!/usr/bin/env python3
"""
模板合成系统 - 将文字叠加到预渲染动态背景上
"""
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import os

def composite_text_with_template(text, template_path, font_path, font_size, output_path=None):
    """
    将文字叠加到模板GIF上
    
    参数:
        text: 要显示的文字
        template_path: 模板GIF路径
        font_path: 字体路径
        font_size: 字号
        output_path: 输出路径（可选）
    
    返回:
        frames列表
    """
    # 1. 加载模板
    template = Image.open(template_path)
    width, height = template.size
    
    # 2. 创建文字图层（透明背景）
    text_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    
    # 3. 加载字体
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    
    # 4. 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 5. 绘制白色文字（稍后可以添加更多样式）
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # 6. 逐帧合成
    frames = []
    for frame in ImageSequence.Iterator(template):
        # 复制背景帧
        new_frame = frame.copy().convert('RGBA')
        
        # 叠加文字层
        new_frame = Image.alpha_composite(new_frame, text_layer)
        
        # 转换回RGB（如果需要）
        new_frame = new_frame.convert('RGB')
        
        frames.append(new_frame)
    
    # 7. 保存（如果指定了输出路径）
    if output_path:
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=template.info.get('duration', 50),
            loop=0
        )
    
    return frames


def test_template_composite():
    """测试模板合成"""
    print("=" * 60)
    print("测试模板合成系统")
    print("=" * 60)
    
    templates = {
        'matrix': 'templates/matrix_rain.gif',
        'neon': 'templates/neon_flash.gif',
        'electric': 'templates/electric.gif',
        'glitch': 'templates/glitch_bg.gif'
    }
    
    # 测试字体（使用系统默认或随机字体）
    import glob
    fonts = glob.glob('fonts/*.ttf') + glob.glob('fonts/*.otf')
    font_path = fonts[0] if fonts else None
    
    for name, template_path in templates.items():
        if os.path.exists(template_path):
            print(f"\n测试: {name}")
            output = f'test_template_{name}.gif'
            
            if font_path:
                composite_text_with_template(
                    text=f'{name.upper()}',
                    template_path=template_path,
                    font_path=font_path,
                    font_size=120,
                    output_path=output
                )
            else:
                # 使用默认字体
                frames = []
                template = Image.open(template_path)
                for frame in ImageSequence.Iterator(template):
                    new_frame = frame.copy().convert('RGBA')
                    draw = ImageDraw.Draw(new_frame)
                    draw.text((100, 200), name.upper(), fill=(255, 255, 255))
                    frames.append(new_frame.convert('RGB'))
                
                frames[0].save(output, save_all=True, append_images=frames[1:], duration=50, loop=0)
            
            print(f"✓ 生成: {output}")
        else:
            print(f"✗ 模板不存在: {template_path}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)


if __name__ == '__main__':
    test_template_composite()
