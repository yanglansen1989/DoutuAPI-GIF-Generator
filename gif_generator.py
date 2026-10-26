# gif_generator.py
import os
import io
import json
import string
import logging
import colorsys
import math
import random
from collections import OrderedDict
from functools import lru_cache
import numpy as np
from PIL import ImageFont, Image, ImageDraw, ImageColor, ImageSequence, ImageFilter, ImageChops

# 尝试导入 wand (可选依赖)
try:
    from wand.image import Image as WandImage
    from wand.drawing import Drawing
    from wand.color import Color
    WAND_AVAILABLE = True
except ImportError:
    WAND_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

# --- 全局配置 ---
BASE_LINE_HEIGHT = 100
# 这里修改比例：
# 0.9  = 字号 90px (更大，可能切边)
# 0.85 = 字号 85px (更稳，兼容性好)
FONT_RATIO = 0.86

# 固定画布尺寸：480x480
CANVAS_WIDTH = 480
CANVAS_HEIGHT = 480

# 模板目录
TEMPLATES_DIR = "templates"

# --- 微信表情图片支持 ---
EMOJI_DIR = "emoji"  # 表情图片目录

PREVIEW_FRAME_CAP = int(os.getenv("GIF_PREVIEW_FRAME_CAP", "6"))
PREVIEW_CANVAS_SIZE = int(os.getenv("GIF_PREVIEW_CANVAS_SIZE", "260"))
PREVIEW_AA_SCALE = 1
FULL_AA_SCALE = 2
_RESIZED_GIF_FRAME_CACHE = OrderedDict()
_RESIZED_GIF_FRAME_CACHE_LIMIT = 8
_FAILED_GIF_LOADS = set()
_FONT_FILES_CACHE = None
_EMOJI_IMAGE_CACHE = OrderedDict()
_EMOJI_IMAGE_CACHE_LIMIT = 64

HEART_BLOOM_PATTERN = [
    "..XXX...XXX..",
    ".XXXXX.XXXXX.",
    "XXXXXXXXXXXXX",
    "XXXXXXXXXXXXX",
    ".XXXXXXXXXXX.",
    "..XXXXXXXXX..",
    "...XXXXXXX...",
    "....XXXXX....",
    ".....XXX.....",
    "......X......",
]

AUTO_ADAPTIVE_TEXT_EFFECTS = {
    'rainbow',
    'rainbow_flow',
    'wave',
    'bounce',
    'neon',
    'glitch',
    'shake',
    'extreme_shake',
    'zoom',
    'ktv_sweep',
    'neon_flicker',
    'chromatic_glitch',
    'cinematic_pop',
    'highlighter',
    'prism_sweep',
    'laser_scan',
    'echo_shadow',
    'pixel_burst',
    'hologram_scan',
    'plasma_wave',
    'thunder_crack',
    'vortex_warp',
    'comet_trail',
    'chrome_glass',
    'aurora_ribbon',
    'strobe_cut',
    'sandstorm',
    'magnetic_flip',
    'ink_bleed',
    'solar_flare',
    'pulse_ring',
    'electric_outline',
    'photon_stream',
    'neon_saber',
    'typewriter',
    'dissolve',
    'shining',
    'text_burn',
    'diamond_sparkle',
    'liquid_fill',
    'text_split',
    'jelly_wobble',
    'floating_text_clear',
    'zoom_slide',
    'roller_coaster',
}

PURE_TEXT_EFFECTS = {
    'wave',
    'bounce',
    'neon',
    'glitch',
    'shake',
    'extreme_shake',
    'zoom',
    'zoom_slide',
    'roller_coaster',
    'fly_zoom',
    'spray',
    'scroll',
    'typewriter',
    'marquee',
    'dissolve',
    'shining',
    'floating_text',
    'floating_text_clear',
    'spiral_3d',
    'spotlight',
    'star_wars',
    'ghost_trails',
    'ktv_sweep',
    'neon_flicker',
    'chromatic_glitch',
    'cinematic_pop',
    'highlighter',
    'prism_sweep',
    'laser_scan',
    'echo_shadow',
    'pixel_burst',
    'hologram_scan',
    'plasma_wave',
    'thunder_crack',
    'vortex_warp',
    'comet_trail',
    'chrome_glass',
    'aurora_ribbon',
    'strobe_cut',
    'sandstorm',
    'magnetic_flip',
    'ink_bleed',
    'solar_flare',
    'pulse_ring',
    'electric_outline',
    'photon_stream',
    'neon_saber',
    'heart_bloom',
    'text_burn',
    'diamond_sparkle',
    'liquid_fill',
    'text_split',
    'jelly_wobble',
}

TEXT_EFFECT_PREVIEW_FRAME_CAPS = {
    'neon': 3,
    'glitch': 4,
    'shake': 4,
    'extreme_shake': 4,
    'wave': 5,
    'bounce': 5,
    'zoom': 5,
    'zoom_slide': 5,
    'roller_coaster': 6,
    'floating_text_clear': 6,
    'prism_sweep': 10,
    'laser_scan': 10,
    'echo_shadow': 10,
    'pixel_burst': 10,
    'hologram_scan': 10,
    'plasma_wave': 10,
    'thunder_crack': 10,
    'vortex_warp': 10,
    'comet_trail': 10,
    'chrome_glass': 10,
    'aurora_ribbon': 10,
    'strobe_cut': 10,
    'sandstorm': 10,
    'magnetic_flip': 10,
    'ink_bleed': 10,
    'solar_flare': 10,
    'pulse_ring': 10,
    'electric_outline': 10,
    'photon_stream': 10,
    'neon_saber': 10,
}

TEXT_EFFECT_FULL_FRAME_CAPS = {
    'glitch': 8,
    'shake': 8,
    'extreme_shake': 8,
    'neon': 10,
    'wave': 12,
    'bounce': 12,
    'zoom': 12,
    'zoom_slide': 12,
    'floating_text_clear': 12,
    'rainbow_flow': 14,
    'roller_coaster': 14,
    'chromatic_glitch': 14,
    'shining': 16,
    'ktv_sweep': 16,
    'neon_flicker': 16,
    'cinematic_pop': 16,
    'highlighter': 16,
    'prism_sweep': 16,
    'laser_scan': 16,
    'echo_shadow': 16,
    'pixel_burst': 14,
    'hologram_scan': 16,
    'plasma_wave': 18,
    'thunder_crack': 16,
    'vortex_warp': 16,
    'comet_trail': 16,
    'chrome_glass': 16,
    'aurora_ribbon': 18,
    'strobe_cut': 16,
    'sandstorm': 16,
    'magnetic_flip': 16,
    'ink_bleed': 18,
    'solar_flare': 16,
    'pulse_ring': 16,
    'electric_outline': 16,
    'photon_stream': 16,
    'neon_saber': 16,
    'heart_bloom': 16,
    'text_burn': 16,
    'diamond_sparkle': 16,
    'text_split': 16,
    'jelly_wobble': 16,
    'dissolve': 18,
    'liquid_fill': 18,
    'typewriter': 18,
    'marquee': 20,
    'scroll': 20,
}


def should_auto_use_adaptive_canvas(text_color_param):
    """Pure text effects should default to a tighter, larger-text canvas."""
    if not text_color_param:
        return False
    if text_color_param.startswith('breathing:'):
        return True
    return text_color_param in AUTO_ADAPTIVE_TEXT_EFFECTS


def is_pure_text_effect(effect_type, mode):
    return effect_type in PURE_TEXT_EFFECTS or mode in {'solid', 'rainbow', 'rainbow_flow', 'breathing'}


def cap_text_effect_frames(frame_count, effect_type, mode, text, fast_preview):
    """Keep text-only effects responsive without changing heavy mask/template effects."""
    key = effect_type or mode
    if fast_preview:
        cap = TEXT_EFFECT_PREVIEW_FRAME_CAPS.get(key, PREVIEW_FRAME_CAP)
        return min(max(frame_count, 1), cap)

    if key == 'typewriter':
        visible_steps = min(len(text.strip()) + 1, TEXT_EFFECT_FULL_FRAME_CAPS['typewriter'])
        return min(frame_count, max(2, visible_steps))

    if mode == 'breathing':
        return min(frame_count, 12)

    cap = TEXT_EFFECT_FULL_FRAME_CAPS.get(key)
    if cap:
        return min(frame_count, cap)
    return frame_count

def parse_text_with_emoji(text):
    """
    解析文本，分离文字和表情标记
    
    输入: "你好[呲牙]今天[ok]"
    输出: [
        {'type': 'text', 'content': '你好'},
        {'type': 'emoji', 'content': '[呲牙]'},
        {'type': 'text', 'content': '今天'},
        {'type': 'emoji', 'content': '[ok]'}
    ]
    """
    import re
    
    # 正则匹配 [xxx] 格式的表情
    pattern = r'(\[[^\]]+\])'
    parts = re.split(pattern, text)
    
    result = []
    for part in parts:
        if not part:
            continue
        if part.startswith('[') and part.endswith(']'):
            result.append({'type': 'emoji', 'content': part})
        else:
            result.append({'type': 'text', 'content': part})
    
    return result

def load_emoji_image(emoji_code, target_size):
    """
    加载表情图片并缩放到目标大小
    
    参数:
        emoji_code: 如 "[呲牙]"
        target_size: 目标高度（宽度按比例）
    
    返回:
        PIL Image 对象，或 None（如果加载失败）
    """
    cache_key = (emoji_code, int(target_size))
    cached = _EMOJI_IMAGE_CACHE.get(cache_key)
    if cached is not None:
        _EMOJI_IMAGE_CACHE.move_to_end(cache_key)
        return cached

    # 构造文件路径 - 去掉方括号
    # "[呲牙]" -> "呲牙.png"
    emoji_name = emoji_code.strip('[]')
    filename = f"{emoji_name}.png"
    filepath = os.path.join(EMOJI_DIR, filename)
    
    try:
        if not os.path.exists(filepath):
            logger.warning(f"Emoji image not found: {filepath}")
            return None
        
        img = Image.open(filepath).convert('RGBA')
        
        # 缩放到目标大小（保持宽高比）
        original_width, original_height = img.size
        aspect_ratio = original_width / original_height
        
        new_height = target_size
        new_width = int(new_height * aspect_ratio)
        
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        _EMOJI_IMAGE_CACHE[cache_key] = resized_img
        _EMOJI_IMAGE_CACHE.move_to_end(cache_key)
        while len(_EMOJI_IMAGE_CACHE) > _EMOJI_IMAGE_CACHE_LIMIT:
            _EMOJI_IMAGE_CACHE.popitem(last=False)
        logger.info(f"Loaded emoji: {emoji_code} from {filename}, size: {new_width}x{new_height}")
        
        return resized_img
        
    except Exception as e:
        logger.error(f"Failed to load emoji {emoji_code}: {e}")
        return None


def new_image(width, height, background_color_rgba):
    return Image.new('RGBA', (width, height), background_color_rgba)


def get_resized_gif_frames(gif_path, size):
    """Load and resize GIF frames once per process."""
    if gif_path in _FAILED_GIF_LOADS:
        return []

    cache_key = (gif_path, size)
    cached = _RESIZED_GIF_FRAME_CACHE.get(cache_key)
    if cached is not None:
        _RESIZED_GIF_FRAME_CACHE.move_to_end(cache_key)
        return cached

    try:
        if not os.path.exists(gif_path) or os.path.getsize(gif_path) <= 0:
            raise OSError("missing or empty GIF asset")
        with Image.open(gif_path) as gif:
            frames = []
            for frame_num in range(getattr(gif, "n_frames", 1)):
                gif.seek(frame_num)
                frame = gif.convert('RGB')
                if frame.size != size:
                    frame = frame.resize(size, Image.BILINEAR)
                frames.append(frame.copy())
    except Exception as e:
        if gif_path not in _FAILED_GIF_LOADS:
            logger.warning(f"Failed to load {gif_path}: {e}")
            _FAILED_GIF_LOADS.add(gif_path)
        return []

    _RESIZED_GIF_FRAME_CACHE[cache_key] = frames
    _RESIZED_GIF_FRAME_CACHE.move_to_end(cache_key)
    while len(_RESIZED_GIF_FRAME_CACHE) > _RESIZED_GIF_FRAME_CACHE_LIMIT:
        _RESIZED_GIF_FRAME_CACHE.popitem(last=False)
    return frames


# --- 新增：随机获取字体路径 ---
def get_random_font_from_folder():
    """从 fonts 文件夹中随机选择一个字体文件"""
    global _FONT_FILES_CACHE
    font_dir = "fonts"
    if not os.path.exists(font_dir):
        return None
    
    # 支持的字体后缀
    valid_extensions = ('.ttf', '.ttc', '.otf')
    
    try:
        if _FONT_FILES_CACHE is None:
            _FONT_FILES_CACHE = [
                os.path.join(font_dir, f)
                for f in os.listdir(font_dir)
                if f.lower().endswith(valid_extensions)
            ]
        if not _FONT_FILES_CACHE:
            return None
        
        # 随机选择一个
        full_path = random.choice(_FONT_FILES_CACHE)
        logger.info(f"Randomly selected font: {os.path.basename(full_path)}")
        return full_path
    except Exception as e:
        logger.error(f"Error selecting random font: {e}")
        return None

@lru_cache(maxsize=160)
def _load_font_cached(font_path_key: str, font_size: int):
    font_path = font_path_key or None

    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, font_size)

        fallback_fonts = [
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
            'arial.ttf',
            'msyh.ttc'
        ]
        for f in fallback_fonts:
            try:
                return ImageFont.truetype(f, font_size)
            except OSError:
                continue
    except Exception as e:
        logger.warning(f"Error loading font: {e}")

    return ImageFont.load_default()


# --- 修改：加载字体逻辑 ---
def load_font(font_path: str = None, size_basis: int = 100):
    font_size = max(1, int(size_basis * FONT_RATIO))
    
    # 1. 如果没有指定特定的字体路径，尝试从 fonts 文件夹随机取一个
    if not font_path:
        font_path = get_random_font_from_folder()

    return _load_font_cached(font_path or "", font_size)

def calculate_text_bbox(text_lines, font, dynamic_line_height):
    """
    计算文字的实际边界框（优化版）
    
    参数:
        text_lines: 文本行列表
        font: 字体对象
        dynamic_line_height: 行高
    
    返回:
        (width, height) - 文字实际占用的尺寸
    
    性能优化：使用 1x1 临时画布 + textbbox/textlength 直接计算
    避免创建 3000x3000 大画布，减少内存占用 99.9%
    """
    if not text_lines:
        return (100, 100)
    
    # 创建最小临时画布用于测量（1x1 像素，仅 4 字节）
    temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    
    max_width = 0
    total_height = len(text_lines) * dynamic_line_height
    
    # 逐行测量宽度
    for line in text_lines:
        if not line:  # 跳过空行
            continue
        
        try:
            # 优先使用 textbbox 获取精确边界
            bbox = temp_draw.textbbox((0, 0), line, font=font, anchor='lt')
            line_width = bbox[2] - bbox[0]
        except AttributeError:
            # 回退到 textlength（PIL 8.0+）
            try:
                line_width = temp_draw.textlength(line, font=font)
            except AttributeError:
                # 最终回退到 textsize（旧版 PIL）
                line_width = temp_draw.textsize(line, font=font)[0]
        
        max_width = max(max_width, line_width)
    
    # 添加小幅余量以确保文字不被裁剪（5%）
    max_width = int(max_width * 1.05)
    
    logger.info(f"Text bbox (optimized): {int(max_width)}x{int(total_height)} (from {len(text_lines)} lines)")
    return (int(max_width), int(total_height))

def calculate_adaptive_font_and_canvas(text, font_path=None, is_wrap=False, max_chars_per_line=8, padding=10, effect_type=None):
    """
    自适应画布逻辑：
    1. 根据文字长度动态决定字号（短文本大字号，长文本小字号）
    2. 用实际字号测量文字边界框
    3. 画布 = 文字边界 + 四周 padding
    4. 不再强制正方形，画布形状由文字内容决定
    
    参数:
        text: 输入文本
        font_path: 字体路径
        is_wrap: 是否自动换行
        max_chars_per_line: 每行最多字符数
        padding: 四周边距（像素）
        effect_type: 特效类型（波浪/弹跳等需要额外空间）
    
    返回:
        (font_size, canvas_width, canvas_height, text_lines)
    """
    input_text = ' '.join(text.split())
    char_count = len(input_text.strip())
    
    if char_count == 0:
        return (80, 100, 100, [' '])
    
    # ---- 第一步：根据文字长度确定字号 ----
    # 短文本用大字号，长文本用小字号
    # 字号映射表（字符数 -> 字号）
    if is_wrap:
        # 换行模式：按行数决定字号
        line_count = (char_count + max_chars_per_line - 1) // max_chars_per_line
        effective_chars = max_chars_per_line
    else:
        line_count = 1
        effective_chars = char_count
    
    # 基础字号计算：字号随字符数反比缩放
    # 1个字 -> 200px, 2个字 -> 160px, 4个字 -> 120px, 8个字 -> 80px, 16个字 -> 50px
    if effect_type == 'zoom_slide':
        # Zoom slide 主要用于微信表情包：字号按可视窗口而不是全文长度计算
        effective_chars = min(effective_chars, 4)

    if effective_chars <= 1:
        font_size = 200
    elif effective_chars <= 2:
        font_size = 160
    elif effective_chars <= 4:
        font_size = 120
    elif effective_chars <= 6:
        font_size = 100
    elif effective_chars <= 8:
        font_size = 80
    elif effective_chars <= 12:
        font_size = 60
    elif effective_chars <= 16:
        font_size = 50
    else:
        font_size = 40
    
    # 多行时字号需要适当缩小，防止画布过高
    if line_count > 5:
        font_size = max(35, int(font_size * 0.6))
    elif line_count > 3:
        font_size = max(40, int(font_size * 0.8))
    
    # ---- 第二步：加载字体并分行 ----
    font = load_font(font_path, font_size)
    
    if is_wrap:
        text_lines = split_text_by_char_count(input_text, max_chars_per_line)
    else:
        text_lines = [input_text]
    
    # ---- 第三步：用实际字体测量文字边界 ----
    dynamic_line_height = font_size
    text_width, text_height = calculate_text_bbox(text_lines, font, dynamic_line_height)
    
    # ---- 第四步：画布 = 文字 + padding ----
    canvas_width = text_width + padding * 2
    canvas_height = text_height + padding * 2
    
    # 为特定特效预留额外空间
    if effect_type in ['bounce', 'wave']:
        # 弹跳/波浪需要上下额外空间
        extra_vertical = int(font_size * 0.3)
        canvas_height += extra_vertical * 2
    elif effect_type in ['shake', 'extreme_shake']:
        # 抖动需要四周额外空间
        extra = 10
        if effect_type == 'extreme_shake': extra = 25
        canvas_width += extra * 2
        canvas_height += extra * 2
    elif effect_type == 'zoom':
        # 缩放需要更多空间
        extra = int(font_size * 0.2)
        canvas_width += extra * 2
        canvas_height += extra * 2
    elif effect_type in ['text_split', 'jelly_wobble', 'echo_shadow', 'vortex_warp', 'comet_trail', 'magnetic_flip']:
        extra = int(font_size * 0.18)
        canvas_width += extra * 2
        canvas_height += extra * 2
    elif effect_type in ['text_burn', 'diamond_sparkle', 'liquid_fill', 'prism_sweep', 'laser_scan', 'pixel_burst', 'hologram_scan', 'plasma_wave', 'thunder_crack', 'chrome_glass', 'aurora_ribbon', 'strobe_cut', 'sandstorm', 'ink_bleed', 'solar_flare', 'pulse_ring', 'electric_outline', 'photon_stream', 'neon_saber']:
        extra = int(font_size * 0.12)
        canvas_width += extra * 2
        canvas_height += extra * 2
    elif effect_type == 'zoom_slide':
        # 微信表情包取向：画布尽量紧，首尾不保留大块空白
        canvas_width = min(max(int(font_size * 2.9), 260), 380)
        canvas_height = min(max(int(font_size * 1.45), 150), 300)
    elif effect_type == 'roller_coaster':
        # 过山车保留轨迹高度，但不再使用固定方图，减少微信表情透明留白
        canvas_width = min(max(canvas_width, int(font_size * 3.2)), 520)
        canvas_height = min(max(int(font_size * 2.25), canvas_height + int(font_size * 0.9)), 320)
    elif effect_type == 'fly_zoom':
        # 飞字缩放需要正方形空间
        max_dim = max(canvas_width, canvas_height, 400)
        canvas_width = max_dim
        canvas_height = max_dim
    elif effect_type == 'spray':
        # 喷发需要正方形空间
        max_dim = max(canvas_width, canvas_height)
        spray_size = max(max_dim * 2, 300)
        canvas_width = int(spray_size)
        canvas_height = int(spray_size)
    elif effect_type == 'floating_text':
        # 漂浮字保留满屏大画布
        canvas_width = 480
        canvas_height = 480
    elif effect_type == 'floating_text_clear':
        # 透明版优先走快出图：限制在较紧的自适应画布内
        font_size = min(font_size, 96)
        canvas_width = min(max(canvas_width, 240), 360)
        canvas_height = min(max(canvas_height, 240), 360)
    elif effect_type == 'spiral_3d':
        # 螺旋3D旋转需要正方形画布
        canvas_width = 480
        canvas_height = 480
    elif effect_type == 'star_wars':
        canvas_width = 480
        canvas_height = 480
    elif effect_type == 'ghost_trails':
        # 拖尾效果需要较大的活动空间
        canvas_width = 480
        canvas_height = 480
    
    # 最小尺寸保障
    canvas_width = max(canvas_width, 60)
    canvas_height = max(canvas_height, 60)
    
    # 最大尺寸限制（防止内存溢出）
    canvas_width = min(canvas_width, 1200)
    canvas_height = min(canvas_height, 1200)
    
    logger.info(f"自适应画布: 字数={char_count}, 字号={font_size}px, "
                f"文字尺寸={text_width}x{text_height}, "
                f"画布={canvas_width}x{canvas_height}, padding={padding}")
    
    return (font_size, canvas_width, canvas_height, text_lines)

def calculate_dynamic_font_size_and_canvas(text, is_wrap=False, max_chars_per_line=8, target_canvas_size=None):
    """
    动态计算字体大小
    核心目标：大字号填满画布
    
    逻辑：
    1. 根据文字内容和行数计算最优字号（尽可能大）
    2. 使用画布尺寸限制
    
    参数:
        text: 输入文本
        is_wrap: 是否换行
        max_chars_per_line: 每行最多字符数（默认8）
        target_canvas_size: 目标画布尺寸 (width, height)，可选
    
    返回:
        font_size (int)
    """
    # 使用实际画布尺寸计算字号
    if target_canvas_size:
        # 自适应模式：使用传入的目标尺寸（如800x800）
        MAX_CANVAS_WIDTH, MAX_CANVAS_HEIGHT = target_canvas_size
    else:
        # 固定模式：使用480x480
        MAX_CANVAS_WIDTH = 480
        MAX_CANVAS_HEIGHT = 480
    
    char_count = len(text.strip())
    
    if char_count == 0:
        return int(MAX_CANVAS_HEIGHT * 0.8)
    
    # 计算行数和每行字符数
    if is_wrap:
        chars_per_line = max_chars_per_line
        line_count = (char_count + max_chars_per_line - 1) // max_chars_per_line
    else:
        chars_per_line = char_count
        line_count = 1
    
    # 高度限制（考虑行间距）
    available_height = MAX_CANVAS_HEIGHT * 0.85  # 留15%边距
    
    if is_wrap and line_count > 1:
        # 多行：考虑行间距（1.3倍）
        height_based_size = available_height / (line_count * 1.3)
    else:
        # 单行：使用大部分高度
        height_based_size = available_height
    
    # 宽度限制
    # 字符实际宽度 ≈ font_size * FONT_RATIO
    # 所以：chars_per_line * (font_size * FONT_RATIO) <= available_width
    # 推导：font_size <= available_width / (chars_per_line * FONT_RATIO)
    available_width = MAX_CANVAS_WIDTH * 0.9  # 留10%边距
    width_based_size = available_width / (chars_per_line * FONT_RATIO)
    
    # 取宽度和高度限制中的较小值（确保不超出画布！）
    font_size = int(min(width_based_size, height_based_size))
    
    # 字号范围：根据画布调整
    if target_canvas_size:
        # 自适应模式（800x800）：字号范围40-350px
        font_size = max(40, min(font_size, 350))
    else:
        # 固定模式（480x480）：字号范围40-200px
        font_size = max(40, min(font_size, 200))
    
    logger.info(f"Font calc: {char_count} chars, {line_count} lines, {chars_per_line} chars/line -> {font_size}px (w_limit={int(width_based_size)}, h_limit={int(height_based_size)}, canvas={MAX_CANVAS_WIDTH}x{MAX_CANVAS_HEIGHT})")
    
    return font_size


def get_text_width(draw_obj, txt, fnt):
    try: return draw_obj.textlength(txt, font=fnt)
    except AttributeError: return draw_obj.textsize(txt, font=fnt)[0]

def split_text_by_pixel_width(text, font, max_width):
    temp_img = Image.new('RGBA', (1, 1))
    draw = ImageDraw.Draw(temp_img)
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        w = get_text_width(draw, test_line, font)
        if w <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = char
            else:
                lines.append(char)
                current_line = ""
    if current_line:
        lines.append(current_line)
    return lines

def split_text_by_char_count(text, max_chars_per_line=8):
    """
    按字符数换行，每行最多 max_chars_per_line 个字符
    
    参数:
        text: 输入文本
        max_chars_per_line: 每行最多字符数（默认8个）
    
    返回:
        分行后的文本列表
    """
    lines = []
    current_line = ""
    
    for char in text:
        current_line += char
        if len(current_line) >= max_chars_per_line:
            lines.append(current_line)
            current_line = ""
    
    if current_line:  # 添加最后一行
        lines.append(current_line)
    
    return lines

def create_rainbow_gradient(width, height, phase=0.0, mode='RGBA'):
    width = max(width, 1)
    height = max(height, 1)
    row = np.empty((width, 4), dtype=np.uint8)
    for x in range(width):
        hue = (x / width + phase) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        row[x] = (int(r * 255), int(g * 255), int(b * 255), 255)
    arr = np.repeat(row[np.newaxis, :, :], height, axis=0)
    img = Image.fromarray(arr, 'RGBA')
    return img.convert(mode) if mode != 'RGBA' else img


def create_vertical_gradient(width, height, top_rgb, bottom_rgb, mode='RGB'):
    width = max(width, 1)
    height = max(height, 1)
    top = np.array(top_rgb, dtype=np.float32)
    bottom = np.array(bottom_rgb, dtype=np.float32)
    ratios = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, np.newaxis]
    column = (top + (bottom - top) * ratios).astype(np.uint8)
    arr = np.repeat(column[:, np.newaxis, :], width, axis=1)
    return Image.fromarray(arr, mode)

def process_alpha_threshold(img):
    r, g, b, a = img.split()
    a = a.point(lambda i: 255 if i > 128 else 0)
    return Image.merge('RGBA', (r, g, b, a))

def apply_rainbow_to_text(text_img):
    """
    为文字图层叠加彩虹渐变颜色
    关键：彩虹渐变基于文字的实际边界框，而不是整个画布
    这样整个文字范围都有完整的彩虹色
    
    参数:
        text_img: 带alpha通道的文本图像（RGBA模式）
    
    返回:
        叠加了彩虹颜色的文本图像
    """
    if text_img.mode != 'RGBA':
        text_img = text_img.convert('RGBA')
    
    # 获取文字的边界框（非透明区域）
    bbox = text_img.getbbox()
    
    if bbox is None:
        # 没有内容，直接返回
        return text_img
    
    # 裁剪到文字边界框
    x1, y1, x2, y2 = bbox
    text_crop = text_img.crop(bbox)
    crop_width = x2 - x1
    crop_height = y2 - y1
    
    # 在裁剪区域内创建彩虹渐变（完整的彩虹色）
    rainbow = create_rainbow_gradient(crop_width, crop_height)
    
    # 提取文字的alpha通道
    r, g, b, alpha = text_crop.split()
    
    # 使用彩虹渐变的RGB + 原始alpha
    rainbow_r, rainbow_g, rainbow_b, _ = rainbow.split()
    rainbow_text = Image.merge('RGBA', (rainbow_r, rainbow_g, rainbow_b, alpha))
    
    # 创建结果图像（与原图相同尺寸）
    result = Image.new('RGBA', text_img.size, (0, 0, 0, 0))
    
    # 将彩虹文字粘贴回原位置
    result.paste(rainbow_text, (x1, y1), rainbow_text)
    
    return result

def interpolate_color(color1_rgb, color2_rgb, progress):
    r = int(color1_rgb[0] + (color2_rgb[0] - color1_rgb[0]) * progress)
    g = int(color1_rgb[1] + (color2_rgb[1] - color1_rgb[1]) * progress)
    b = int(color1_rgb[2] + (color2_rgb[2] - color1_rgb[2]) * progress)
    return (r, g, b, 255)

# ==========================================
# 主生成函数
# ==========================================
# ==========================================
# 主生成函数
# ==========================================
def generate_gif_bytes(
        text,
        frame_count=None,
        delay=100,
        font_path=None,
        text_color_param=None,
        mask_color_param=None,
        width_pixels=500,
        theme="transparent",
        auto_wrap=False,
        use_adaptive_canvas=False,
        fast_preview=False
    ) -> io.BytesIO:
    if should_auto_use_adaptive_canvas(text_color_param):
        use_adaptive_canvas = True
    logger.info(f"generate_gif_bytes called with text={text}, theme={theme}, color={text_color_param}, mask_color={mask_color_param}, adaptive={use_adaptive_canvas}")

    # 设置默认帧数
    if frame_count is None or frame_count < 1:
        frame_count = 5

    # 1. 主题配置 (默认颜色改为黑色)
    if theme == 'transparent':
        bg_color_rgba = (0, 0, 0, 0)
        default_text_rgb = (0, 0, 0)  # 默认黑色
    elif theme == 'light':
        bg_color_rgba = (255, 255, 255, 255)
        default_text_rgb = (0, 0, 0)
    else: # dark
        bg_color_rgba = (0, 0, 0, 255)
        default_text_rgb = (255, 255, 255)

    # 2. 解析颜色模式
    mode = 'solid'
    solid_color_rgba = (*default_text_rgb, 255)
    breath_colors = []
    
    # 特效参数解析
    effect_type = None # None, 'wave', 'bounce', 'rainbow_flow', 'neon', 'glitch', 'shake', 'zoom'
    
    if text_color_param:
        if text_color_param == 'rainbow':
            mode = 'rainbow'
        elif text_color_param == 'rainbow_flow':
            mode = 'rainbow_flow'
            if frame_count < 10: frame_count = 20
        elif text_color_param == 'wave':
            effect_type = 'wave'
            if frame_count < 10: frame_count = 20
        elif text_color_param == 'bounce':
            effect_type = 'bounce'
            if frame_count < 10: frame_count = 20
        elif text_color_param == 'neon':
            effect_type = 'neon'
            if frame_count < 10: frame_count = 20
        elif text_color_param == 'glitch':
            effect_type = 'glitch'
            # 使用主题默认颜色而不是强制黑色
            if frame_count < 10: frame_count = 10
        elif text_color_param == 'shake':
            effect_type = 'shake'
            # 使用主题默认颜色而不是强制黑色
            if frame_count < 10: frame_count = 10
        elif text_color_param == 'extreme_shake':
            effect_type = 'extreme_shake'
            solid_color_rgba = (0, 0, 0, 255)  # 默认字符颜色强制为黑色
            if frame_count < 10: frame_count = 10
        elif text_color_param == 'zoom':
            effect_type = 'zoom'
            # 使用主题默认颜色而不是强制黑色
            if frame_count < 10: frame_count = 20
        elif text_color_param == 'zoom_slide':
            effect_type = 'zoom_slide'
            if frame_count < 12: frame_count = 20
            if delay > 80: delay = 80
        elif text_color_param == 'roller_coaster':
            effect_type = 'roller_coaster'
            if frame_count < 18: frame_count = 28
            if delay > 55: delay = 55
        elif text_color_param == 'fly_zoom':
            effect_type = 'fly_zoom'
            if frame_count < 15: frame_count = 30  # 飞字缩放需要更多帧
        elif text_color_param == 'spray':
            effect_type = 'spray'
            if frame_count < 15: frame_count = 25  # 喷发效果需要更多帧
        elif text_color_param == 'scroll':
            effect_type = 'scroll'
            if frame_count < 20: frame_count = 30  # 滚动效果需要更多帧
        elif text_color_param == 'typewriter':
            effect_type = 'typewriter'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'marquee':
            effect_type = 'marquee'
            if frame_count < 10: frame_count = 40
        elif text_color_param == 'dissolve':
            effect_type = 'dissolve'
            if frame_count < 10: frame_count = 30  # 溶解效果需要更多帧
        elif text_color_param == 'matrix':
            effect_type = 'template_matrix'
            if frame_count < 10: frame_count = 18
        elif text_color_param == 'neon_flash':
            effect_type = 'template_neon'
            if frame_count < 10: frame_count = 16
        elif text_color_param == 'electric_bg':
            effect_type = 'template_electric'
            if frame_count < 10: frame_count = 16
        elif text_color_param == 'glitch_bg':
            effect_type = 'template_glitch'
            if frame_count < 10: frame_count = 15
        elif text_color_param in ['shining', 'shine']:
            effect_type = 'shining'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'rainbow_mask':
            effect_type = 'rainbow_mask'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'shining_mask':
            effect_type = 'shining_mask'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'emoji_mask':
            effect_type = 'emoji_mask'
            if frame_count < 10: frame_count = 20
        elif text_color_param == 'matrix_mask':
            effect_type = 'matrix_mask'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'fire_mask':
            effect_type = 'fire_mask'
            if frame_count < 10: frame_count = 25
        elif text_color_param == 'stars_mask':
            effect_type = 'stars_mask'
            if frame_count < 10: frame_count = 25
        elif text_color_param == 'snow_mask':
            effect_type = 'snow_mask'
            if frame_count < 10: frame_count = 25
        elif text_color_param == 'hearts_mask':
            effect_type = 'hearts_mask'
        elif text_color_param == 'cute_streamer_mask':
            effect_type = 'cute_streamer_mask'
            if frame_count < 10: frame_count = 25
        elif text_color_param == 'particles_mask':
            effect_type = 'particles_mask'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'music_mask':
            effect_type = 'music_mask'
            if frame_count < 10: frame_count = 25
        elif text_color_param == 'ripple_mask':
            effect_type = 'ripple_mask'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'lightning_mask':
            effect_type = 'lightning_mask'
            if frame_count < 10: frame_count = 25
        elif text_color_param == 'smoke_mask':
            effect_type = 'smoke_mask'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'neon_lines_mask':
            effect_type = 'neon_lines_mask'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'code_mask':
            effect_type = 'code_mask'
            if frame_count < 10: frame_count = 30
        elif text_color_param == 'floating_text':
            effect_type = 'floating_text'
            if frame_count < 20: frame_count = 25
            if delay < 80: delay = 100
        elif text_color_param == 'floating_text_clear':
            effect_type = 'floating_text_clear'
            use_adaptive_canvas = True
            frame_count = min(max(frame_count, 8), 12)
            if delay > 80: delay = 80
        elif text_color_param == 'spiral_3d':
            effect_type = 'spiral_3d'
            if frame_count < 20: frame_count = 30
            if delay < 60: delay = 80
        elif text_color_param == 'spotlight':
            effect_type = 'spotlight'
            if frame_count < 20: frame_count = 30
            if delay < 60: delay = 80
        elif text_color_param == 'star_wars':
            effect_type = 'star_wars'
            if frame_count < 30: frame_count = 40
            if delay < 60: delay = 80
        elif text_color_param == 'ghost_trails':
            effect_type = 'ghost_trails'
            if frame_count < 20: frame_count = 30
            if delay < 60: delay = 80
        elif text_color_param == 'ktv_sweep':
            effect_type = 'ktv_sweep'
            if frame_count < 20: frame_count = 30
        elif text_color_param == 'neon_flicker':
            effect_type = 'neon_flicker'
            if frame_count < 20: frame_count = 30
        elif text_color_param == 'chromatic_glitch':
            effect_type = 'chromatic_glitch'
            if frame_count < 15: frame_count = 20
        elif text_color_param == 'cinematic_pop':
            effect_type = 'cinematic_pop'
            if frame_count < 20: frame_count = 30
            if delay > 50: delay = 50  # 弹入需要顺滑
        elif text_color_param == 'highlighter':
            effect_type = 'highlighter'
            if frame_count < 20: frame_count = 30
        elif text_color_param == 'prism_sweep':
            effect_type = 'prism_sweep'
            if frame_count < 18: frame_count = 28
        elif text_color_param == 'laser_scan':
            effect_type = 'laser_scan'
            if frame_count < 16: frame_count = 24
            if delay > 60: delay = 60
        elif text_color_param == 'echo_shadow':
            effect_type = 'echo_shadow'
            if frame_count < 18: frame_count = 28
        elif text_color_param == 'pixel_burst':
            effect_type = 'pixel_burst'
            if frame_count < 14: frame_count = 24
        elif text_color_param == 'hologram_scan':
            effect_type = 'hologram_scan'
            if frame_count < 18: frame_count = 28
            if delay > 60: delay = 60
        elif text_color_param == 'plasma_wave':
            effect_type = 'plasma_wave'
            if frame_count < 20: frame_count = 32
        elif text_color_param == 'thunder_crack':
            effect_type = 'thunder_crack'
            if frame_count < 16: frame_count = 24
            if delay > 65: delay = 65
        elif text_color_param == 'vortex_warp':
            effect_type = 'vortex_warp'
            if frame_count < 18: frame_count = 28
            if delay > 60: delay = 60
        elif text_color_param == 'comet_trail':
            effect_type = 'comet_trail'
            if frame_count < 18: frame_count = 28
            if delay > 55: delay = 55
        elif text_color_param == 'chrome_glass':
            effect_type = 'chrome_glass'
            if frame_count < 16: frame_count = 24
        elif text_color_param == 'aurora_ribbon':
            effect_type = 'aurora_ribbon'
            if frame_count < 20: frame_count = 32
        elif text_color_param == 'strobe_cut':
            effect_type = 'strobe_cut'
            if frame_count < 16: frame_count = 24
            if delay > 45: delay = 45
        elif text_color_param == 'sandstorm':
            effect_type = 'sandstorm'
            if frame_count < 18: frame_count = 28
            if delay > 60: delay = 60
        elif text_color_param == 'magnetic_flip':
            effect_type = 'magnetic_flip'
            if frame_count < 18: frame_count = 28
            if delay > 55: delay = 55
        elif text_color_param == 'ink_bleed':
            effect_type = 'ink_bleed'
            if frame_count < 20: frame_count = 32
        elif text_color_param == 'solar_flare':
            effect_type = 'solar_flare'
            if frame_count < 18: frame_count = 28
            if delay > 55: delay = 55
        elif text_color_param == 'pulse_ring':
            effect_type = 'pulse_ring'
            if frame_count < 18: frame_count = 28
        elif text_color_param == 'electric_outline':
            effect_type = 'electric_outline'
            if frame_count < 18: frame_count = 28
            if delay > 55: delay = 55
        elif text_color_param == 'photon_stream':
            effect_type = 'photon_stream'
            if frame_count < 18: frame_count = 28
            if delay > 55: delay = 55
        elif text_color_param == 'neon_saber':
            effect_type = 'neon_saber'
            if frame_count < 16: frame_count = 24
            if delay > 50: delay = 50
        elif text_color_param == 'heart_bloom':
            effect_type = 'heart_bloom'
            if frame_count < 15: frame_count = 24
            if delay > 70: delay = 70
        elif text_color_param == 'text_burn':
            effect_type = 'text_burn'
            if frame_count < 20: frame_count = 30
        elif text_color_param == 'diamond_sparkle':
            effect_type = 'diamond_sparkle'
            if frame_count < 15: frame_count = 25
        elif text_color_param == 'liquid_fill':
            effect_type = 'liquid_fill'
            if frame_count < 20: frame_count = 35
        elif text_color_param == 'text_split':
            effect_type = 'text_split'
            if frame_count < 20: frame_count = 30
            if delay > 50: delay = 50
        elif text_color_param == 'jelly_wobble':
            effect_type = 'jelly_wobble'
            if frame_count < 15: frame_count = 25
        elif text_color_param.startswith('breathing:'):
            try:
                parts = text_color_param.split(':')
                if len(parts) == 3:
                    breath_colors = [ImageColor.getrgb(parts[1]), ImageColor.getrgb(parts[2])]
                    mode = 'breathing'
                    if frame_count < 10: frame_count = 20
            except ValueError: pass
        else:
            try: solid_color_rgba = ImageColor.getrgb(text_color_param)
            except ValueError: pass

    impact_static_text_layout = (effect_type is None and mode in ['solid', 'rainbow'])
    if impact_static_text_layout:
        use_adaptive_canvas = True

    pure_text_effect = is_pure_text_effect(effect_type, mode)
    if fast_preview:
        if pure_text_effect:
            use_adaptive_canvas = True
        frame_count = cap_text_effect_frames(frame_count, effect_type, mode, text, fast_preview=True)
        if not pure_text_effect and not should_auto_use_adaptive_canvas(text_color_param) and not impact_static_text_layout:
            use_adaptive_canvas = False
    elif pure_text_effect:
        use_adaptive_canvas = True
        frame_count = cap_text_effect_frames(frame_count, effect_type, mode, text, fast_preview=False)

    # 解析 mask 颜色参数
    mask_color_rgb = None
    if mask_color_param:
        try:
            mask_color_rgb = ImageColor.getrgb(mask_color_param)
            logger.info(f"Mask color parsed: {mask_color_rgb}")
        except ValueError:
            logger.warning(f"Invalid mask color: {mask_color_param}, using default")

    # 3. 字体与换行处理
    input_text = ' '.join(text.split())
    
    # 解析字体路径（如果没有指定则随机选择）
    if not font_path:
        font_path = get_random_font_from_folder()
    
    # ========== 智能换行逻辑 ==========
    # 优先级：
    # 1. 滚动(scroll)和喷发(spray)特效 → 强制不换行
    # 2. 其他特效 → 根据字符数智能判断
    #    - ≤8个字符 → 不换行（显示更大）
    #    - >8个字符 → 自动换行（避免字号过小）
    
    char_count = len(input_text.strip())
    no_wrap_effects = ['scroll', 'spray', 'zoom_slide', 'roller_coaster', 'fly_zoom', 'floating_text', 'floating_text_clear', 'spiral_3d', 'star_wars', 'ghost_trails', 'heart_bloom']
    
    # 判断是否需要换行
    if effect_type in no_wrap_effects:
        # 滚动和喷发特效：强制不换行
        needs_wrap = False
        logger.info(f"Effect {effect_type}: force no wrap")
    elif char_count > 8:
        # 长文本：自动换行以最大化字号
        needs_wrap = True
        logger.info(f"Auto-enabling wrap: {char_count} chars > 8")
    else:
        # 短文本：不换行（显示更大）
        needs_wrap = False
        logger.info(f"Short text ({char_count} chars): no wrap for larger size")
    
    # ========== 画布尺寸计算 ==========
    if use_adaptive_canvas:
        adaptive_text = input_text
        if effect_type == 'floating_text_clear':
            adaptive_text = ''.join(input_text.split())[:5] or input_text[:5]
        elif effect_type == 'roller_coaster':
            adaptive_text = ''.join(input_text.split())[:6] or input_text[:6]
        # 自适应模式：根据文字内容动态计算字号和画布尺寸
        # 画布紧贴文字边界，四周留10px边距，不再强制正方形
        adaptive_result = calculate_adaptive_font_and_canvas(
            text=adaptive_text,
            font_path=font_path,
            is_wrap=needs_wrap,
            max_chars_per_line=8,
            padding=10,
            effect_type=effect_type
        )
        dynamic_line_height, width_pixels, canvas_height, text_lines = adaptive_result
        font = load_font(font_path, dynamic_line_height)
    else:
        # 固定模式：使用标准480x480画布（快速，原始行为）
        target_size = (PREVIEW_CANVAS_SIZE, PREVIEW_CANVAS_SIZE) if fast_preview else None
        dynamic_line_height = calculate_dynamic_font_size_and_canvas(input_text, needs_wrap, target_canvas_size=target_size)
        font = load_font(font_path, dynamic_line_height)
        
        text_lines = []
        if needs_wrap:
            # 按字符数换行：每行最多8个字符
            text_lines = split_text_by_char_count(input_text, max_chars_per_line=8)
            logger.info(f"Split into {len(text_lines)} lines (max 8 chars/line): {text_lines}")
        else:
            text_lines = [input_text]
        
        width_pixels = PREVIEW_CANVAS_SIZE if fast_preview else CANVAS_WIDTH
        canvas_height = PREVIEW_CANVAS_SIZE if fast_preview else CANVAS_HEIGHT
        logger.info(f"Fixed canvas: {width_pixels}x{canvas_height} (fast mode)")


    total_lines = len(text_lines)
    # 为弹跳和波浪预留一些垂直空间
    vertical_padding = int(dynamic_line_height * 0.4) if (effect_type in ['bounce', 'wave']) else 0
    # 注意：保持固定画布高度，不再动态计算
    
    images = []
    render_aa_scale = PREVIEW_AA_SCALE if fast_preview else FULL_AA_SCALE
    text_mask_cache = {}
    aa_font_cache = {}

    def get_centered_text_mask(full_text, mask_font, aa_scale=None):
        scale = max(1, int(aa_scale or render_aa_scale))
        font_path_key = getattr(mask_font, "path", None)
        font_size_key = getattr(mask_font, "size", None)
        cache_key = (full_text, font_path_key, font_size_key, width_pixels, canvas_height, scale)
        cached = text_mask_cache.get(cache_key)
        if cached is not None:
            return cached

        mask_size = (width_pixels * scale, canvas_height * scale)
        text_mask = Image.new('L', mask_size, 0)
        mask_draw = ImageDraw.Draw(text_mask)

        aa_font = mask_font
        if scale > 1 and font_path_key and font_size_key:
            aa_font_key = (font_path_key, font_size_key, scale)
            aa_font = aa_font_cache.get(aa_font_key)
            if aa_font is None:
                try:
                    aa_font = ImageFont.truetype(font_path_key, font_size_key * scale)
                except Exception:
                    aa_font = mask_font
                aa_font_cache[aa_font_key] = aa_font

        bbox = mask_draw.multiline_textbbox((0, 0), full_text, font=aa_font)
        x = (mask_size[0] - (bbox[2] - bbox[0])) // 2
        y = (mask_size[1] - (bbox[3] - bbox[1])) // 2
        mask_draw.multiline_text((x, y), full_text, font=aa_font, fill=255, align='center')

        if scale > 1:
            text_mask = text_mask.resize((width_pixels, canvas_height), Image.LANCZOS)
        text_mask_cache[cache_key] = text_mask
        return text_mask

    def paste_text_mask_effect(canvas_img, effect_bg, text_mask):
        """Composite a texture through the text mask without filling transparent backgrounds."""
        if effect_bg.mode != 'RGBA':
            effect_bg = effect_bg.convert('RGBA')

        if theme == 'transparent':
            layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
            layer.paste(effect_bg, (0, 0), mask=text_mask)
            canvas_img.paste(layer, (0, 0), mask=layer)
            return

        bg_color = (255, 255, 255, 255) if theme == 'light' else (0, 0, 0, 255)
        solid_bg = Image.new('RGBA', (width_pixels, canvas_height), bg_color)
        result = Image.composite(effect_bg, solid_bg, text_mask)
        canvas_img.paste(result, (0, 0))

    # --- 通用混合绘制函数 (支持 Emoji) ---
    def draw_line_mixed(canvas_img, line_text, x, y, font, fill_color, anchor='lm', use_emoji_silhouette=False):
        """
        在指定位置绘制一行混合文本（支持 Emoji）
        """
        segments = parse_text_with_emoji(line_text)
        
        # 1. 计算总宽度和分段信息
        total_width = 0
        segment_infos = [] # (type, content, width, image)
        
        temp_img = new_image(1, 1, (0,0,0,0))
        temp_d = ImageDraw.Draw(temp_img)
        
        emoji_size = int(dynamic_line_height * 0.8)
        
        for seg in segments:
            if seg['type'] == 'text':
                w = get_text_width(temp_d, seg['content'], font)
                segment_infos.append({'type': 'text', 'content': seg['content'], 'width': w})
                total_width += w
            else:
                emoji_img = load_emoji_image(seg['content'], emoji_size)
                if emoji_img:
                    segment_infos.append({'type': 'emoji', 'content': seg['content'], 'width': emoji_img.width, 'image': emoji_img})
                    total_width += emoji_img.width
                else:
                    # Fallback
                    w = get_text_width(temp_d, seg['content'], font)
                    segment_infos.append({'type': 'text', 'content': seg['content'], 'width': w})
                    total_width += w

        # 2. 确定起始 X 坐标
        current_x = x
        if anchor == 'mm':
            current_x = x - (total_width / 2)
        elif anchor == 'rm':
            current_x = x - total_width
        
        # 3. 绘制
        draw_obj = ImageDraw.Draw(canvas_img)
        
        for info in segment_infos:
            if info['type'] == 'text':
                draw_obj.text((current_x, y), info['content'], fill=fill_color, font=font, anchor='lm')
            else:
                # Emoji
                e_img = info['image']
                paste_y = int(y - (e_img.height / 2))
                paste_x = int(current_x)
                
                if canvas_img.mode == 'L':
                    # Mask mode: Paste Alpha as Value
                    mask_val = 255
                    if isinstance(fill_color, int): mask_val = fill_color
                    
                    # Extract alpha
                    alpha = e_img.split()[-1]
                    # Create a solid block of mask_val
                    solid_block = Image.new('L', e_img.size, mask_val)
                    # Paste solid block using alpha as mask
                    canvas_img.paste(solid_block, (paste_x, paste_y), mask=alpha)
                    
                elif use_emoji_silhouette:
                    # Silhouette mode (e.g. Shadow)
                    # Create solid color block
                    solid_block = Image.new('RGBA', e_img.size, fill_color)
                    canvas_img.paste(solid_block, (paste_x, paste_y), mask=e_img)
                else:
                    # Normal mode
                    canvas_img.paste(e_img, (paste_x, paste_y), mask=e_img)
            
            current_x += info['width']
        
        return total_width

    def draw_text_standard(canvas_img, lines, color, offset_x=0, offset_y=0, use_emoji_silhouette=False):
        """标准多行绘制，支持 Emoji - 始终以画布中心为基准居中显示"""
        total_lines = len(lines)
        # 计算所有行的总高度
        total_text_height = total_lines * dynamic_line_height
        # 计算起始Y坐标，使文字垂直居中于画布
        start_y = (canvas_height - total_text_height) // 2
        
        for idx, line in enumerate(lines):
            # 每行的中心Y坐标
            line_base_y = start_y + (idx * dynamic_line_height) + (dynamic_line_height // 2)
            
            # 始终水平居中（以画布中心为基准）
            x = width_pixels // 2 + offset_x
            anchor = 'mm'
                
            draw_line_mixed(canvas_img, line, x, line_base_y + offset_y, font, color, anchor, use_emoji_silhouette)

    def draw_text_extreme_shake(canvas_img, lines, color, frame_idx, total_frames):
        """剧烈抖动效果 - 每个字符完全不规律地上左右下抖动"""
        draw_obj = ImageDraw.Draw(canvas_img)
        
        # 抖动幅度
        intensity = 15
        
        # 计算垂直居中的起始Y
        total_lines = len(lines)
        total_text_height = total_lines * dynamic_line_height
        start_y = (canvas_height - total_text_height) // 2
        
        total_chars = sum(len(parse_text_with_emoji(line)) for line in lines)
        char_index = 0
        progress = frame_idx / max(total_frames - 1, 1)
        
        def pseudo_random(seed):
            return (math.sin(seed * 12.9898 + 78.233) * 43758.5453) % 1.0
        
        for line_idx, line in enumerate(lines):
            line_base_y = start_y + (line_idx * dynamic_line_height) + (dynamic_line_height // 2)
            
            segments = parse_text_with_emoji(line)
            total_width = 0
            segment_data = []
            
            for seg in segments:
                if seg['type'] == 'text':
                    if seg['content']:
                        w = get_text_width(draw_obj, seg['content'], font)
                        segment_data.append({'type': 'text', 'content': seg['content'], 'width': w})
                        total_width += w
                else:
                    emoji_img = load_emoji_image(seg['content'], int(dynamic_line_height * 0.8))
                    if emoji_img:
                        segment_data.append({'type': 'emoji', 'content': seg['content'], 'width': emoji_img.width, 'image': emoji_img})
                        total_width += emoji_img.width
                    else:
                        w = get_text_width(draw_obj, seg['content'], font)
                        segment_data.append({'type': 'text', 'content': seg['content'], 'width': w})
                        total_width += w
            
            start_x = (width_pixels - total_width) // 2
            current_x = start_x
            
            for seg_data in segment_data:
                if seg_data['type'] == 'text':
                    for char in seg_data['content']:
                        char_width = get_text_width(draw_obj, char, font)
                        
                        seed_x = frame_idx * 1.1 + char_index * 2.3
                        seed_y = frame_idx * 1.7 + char_index * 3.1
                        x_offset = (pseudo_random(seed_x) - 0.5) * intensity * 2
                        y_offset = (pseudo_random(seed_y) - 0.5) * intensity * 2
                        
                        if mode == 'rainbow':
                            char_hue = (char_index / max(total_chars, 1) + progress * 0.5) % 1.0
                            r, g, b = colorsys.hsv_to_rgb(char_hue, 1.0, 1.0)
                            char_color = (int(r*255), int(g*255), int(b*255), 255)
                        else:
                            char_color = color
                        
                        draw_obj.text((current_x + x_offset, line_base_y + y_offset), char, fill=char_color, font=font, anchor='lm')
                        current_x += char_width
                        char_index += 1
                else:
                    seed_x = frame_idx * 1.1 + char_index * 2.3
                    seed_y = frame_idx * 1.7 + char_index * 3.1
                    x_offset = (pseudo_random(seed_x) - 0.5) * intensity * 2
                    y_offset = (pseudo_random(seed_y) - 0.5) * intensity * 2
                    
                    paste_y = int(line_base_y + y_offset - (seg_data['image'].height // 2))
                    paste_x = int(current_x + x_offset)
                    canvas_img.paste(seg_data['image'], (paste_x, paste_y), seg_data['image'])
                    current_x += seg_data['width']
                    char_index += 1

    def draw_text_wave(canvas_img, lines, color, frame_idx, total_frames):
        """波浪效果 - 支持emoji图片，以画布中心为基准居中显示，使用彩虹流动颜色"""
        # 波浪参数
        amplitude = 10
        frequency = 0.5
        speed = 2 * math.pi
        
        phase = (frame_idx / total_frames) * speed
        color_phase = frame_idx / total_frames  # 颜色相位
        draw_obj = ImageDraw.Draw(canvas_img)
        
        # 计算垂直居中的起始Y
        total_lines = len(lines)
        total_text_height = total_lines * dynamic_line_height
        start_y = (canvas_height - total_text_height) // 2
        
        # 统计总字符数用于颜色分配
        total_chars = sum(len(parse_text_with_emoji(line)) for line in lines)
        char_index = 0
        
        for line_idx, line in enumerate(lines):
            line_base_y = start_y + (line_idx * dynamic_line_height) + (dynamic_line_height // 2)
            
            # 解析文本和emoji
            segments = parse_text_with_emoji(line)
            
            # 计算总宽度用于居中
            total_width = 0
            segment_data = []  # 存储每段的宽度和类型
            
            for seg in segments:
                if seg['type'] == 'text':
                    if seg['content']:
                        w = get_text_width(draw_obj, seg['content'], font)
                        segment_data.append({'type': 'text', 'content': seg['content'], 'width': w})
                        total_width += w
                else:  # emoji
                    emoji_img = load_emoji_image(seg['content'], int(dynamic_line_height * 0.8))
                    if emoji_img:
                        segment_data.append({'type': 'emoji', 'content': seg['content'], 'width': emoji_img.width, 'image': emoji_img})
                        total_width += emoji_img.width
                    else:
                        # 回退显示文字
                        w = get_text_width(draw_obj, seg['content'], font)
                        segment_data.append({'type': 'text', 'content': seg['content'], 'width': w})
                        total_width += w
            
            # 起始X（居中）
            start_x = (width_pixels - total_width) // 2
            current_x = start_x
            
            # 逐段绘制，应用波浪和彩虹颜色
            for seg_data in segment_data:
                if seg_data['type'] == 'text':
                    # 逐字符绘制文字，应用波浪和彩虹色
                    for char in seg_data['content']:
                        char_width = get_text_width(draw_obj, char, font)
                        x_factor = (current_x - start_x) / 100
                        y_offset = math.sin(x_factor * frequency + phase) * amplitude
                        
                        # 根据 mode 决定颜色
                        if mode == 'rainbow':
                            # 彩虹流动颜色：根据字符位置和帧计算色相
                            char_hue = (char_index / max(total_chars, 1) + color_phase) % 1.0
                            r, g, b = colorsys.hsv_to_rgb(char_hue, 1.0, 1.0)
                            char_color = (int(r*255), int(g*255), int(b*255), 255)
                        else:
                            char_color = color
                        
                        draw_obj.text((current_x, line_base_y + y_offset), char, fill=char_color, font=font, anchor='lm')
                        current_x += char_width
                        char_index += 1
                else:  # emoji
                    # emoji 图片应用波浪
                    x_factor = (current_x - start_x) / 100
                    y_offset = math.sin(x_factor * frequency + phase) * amplitude
                    paste_y = int(line_base_y + y_offset - (seg_data['image'].height // 2))
                    paste_x = int(current_x)
                    canvas_img.paste(seg_data['image'], (paste_x, paste_y), seg_data['image'])
                    current_x += seg_data['width']
                    char_index += 1
    
    def draw_text_spray(canvas_img, lines, frame_idx, total_frames, spray_font_path):
        """喷发效果 - 文字从中心向四周喷发，每个字不同颜色，从小到大，带角度抖动"""
        draw_obj = ImageDraw.Draw(canvas_img)
        
        # 画布中心
        center_x = width_pixels // 2
        center_y = canvas_height // 2
        
        # 合并所有行的字符，限制最大字符数（防止内存过高）
        MAX_CHARS = 20
        all_chars = ''.join(lines)[:MAX_CHARS]
        char_count = len(all_chars)
        
        if char_count == 0:
            return
        
        # 动画进度 (0~1)
        progress = frame_idx / max(total_frames - 1, 1)
        
        # 喷发半径（从0到最大半径）
        max_radius = min(width_pixels, canvas_height) * 0.35
        current_radius = progress * max_radius
        
        # 字体大小（从小到大）- 使用传入的固定字体路径
        min_font_size = 20
        max_font_size = dynamic_line_height
        current_font_size = int(min_font_size + progress * (max_font_size - min_font_size))
        spray_font = ImageFont.truetype(spray_font_path, int(current_font_size * FONT_RATIO))
        
        for i, char in enumerate(all_chars):
            # 每个字符的角度（均匀分布在圆周上）
            base_angle = (2 * math.pi * i / char_count) - (math.pi / 2)  # 从顶部开始
            
            # 字符位置（从中心向外移动）
            char_x = center_x + math.cos(base_angle) * current_radius
            char_y = center_y + math.sin(base_angle) * current_radius
            
            # 颜色：若是rainbow模式则每个字符不同的彩虹颜色，否则使用用户颜色
            if mode == 'rainbow':
                char_hue = (i / char_count + progress * 0.5) % 1.0  # 颜色也随时间流动
                r, g, b = colorsys.hsv_to_rgb(char_hue, 1.0, 1.0)
                char_color = (int(r*255), int(g*255), int(b*255), 255)
            else:
                char_color = current_color
            
            # 角度抖动：喷发后轻微抖动（进度越大抖动越明显）
            shake_intensity = 15  # 最大抖动角度（度）
            shake_offset = math.sin(frame_idx * 0.8 + i * 1.5) * shake_intensity * progress
            rotation_angle = math.degrees(base_angle) + 90 + shake_offset  # 让文字朝外 + 抖动
            
            # 创建单字符临时图像进行旋转
            char_bbox = draw_obj.textbbox((0, 0), char, font=spray_font)
            char_w = char_bbox[2] - char_bbox[0] + 10
            char_h = char_bbox[3] - char_bbox[1] + 10
            
            # 创建透明背景的字符图像
            char_img = Image.new('RGBA', (char_w, char_h), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((char_w // 2, char_h // 2), char, fill=char_color, font=spray_font, anchor='mm')
            
            # 旋转字符
            rotated = char_img.rotate(-rotation_angle, resample=Image.Resampling.BILINEAR, expand=True)
            
            # 粘贴到画布
            paste_x = int(char_x - rotated.width // 2)
            paste_y = int(char_y - rotated.height // 2)
            canvas_img.paste(rotated, (paste_x, paste_y), rotated)
    
    def draw_text_scroll(canvas_img, lines, frame_idx, total_frames, scroll_font, scroll_font_size):
        """滚动效果 - 文字从右到左滚动，使用最大化字号，彩虹叠加"""
        draw_obj = ImageDraw.Draw(canvas_img)
        
        # 合并文字
        text = ''.join(lines)
        
        # 获取文字总宽度
        text_bbox = draw_obj.textbbox((0, 0), text, font=scroll_font)
        text_width = text_bbox[2] - text_bbox[0]
        
        # 滚动范围：从画布右侧到完全离开左侧
        total_travel = width_pixels + text_width
        
        # 当前位置（从右到左）
        progress = frame_idx / max(total_frames - 1, 1)
        current_x = width_pixels - (progress * total_travel)
        
        # Y 居中
        center_y = canvas_height // 2
        
        # 逐字符绘制，每个字符使用不同的彩虹颜色
        char_x = current_x
        for i, char in enumerate(text):
            char_bbox = draw_obj.textbbox((0, 0), char, font=scroll_font)
            char_width = char_bbox[2] - char_bbox[0]
            
            # 颜色：如果是rainbow模式，根据字符位置和帧进度计算彩虹色；否则使用指定的颜色
            if mode == 'rainbow':
                char_hue = (i / max(len(text), 1) + progress) % 1.0
                r, g, b = colorsys.hsv_to_rgb(char_hue, 1.0, 1.0)
                char_color = (int(r*255), int(g*255), int(b*255), 255)
            else:
                char_color = current_color
            
            # 只绘制在画布范围内的字符
            if char_x + char_width > 0 and char_x < width_pixels:
                draw_obj.text((char_x, center_y), char, fill=char_color, font=scroll_font, anchor='lm')
            
            char_x += char_width

    def draw_text_roller_coaster(canvas_img, lines, frame_idx, total_frames, coaster_font):
        """过山车滑行效果 - 限制字数，从左到右爬坡、停顿、俯冲。"""
        coaster_text = ''.join(lines).strip()[:6]
        if not coaster_text:
            return

        draw_obj = ImageDraw.Draw(canvas_img)
        cache_font = coaster_font
        max_track_width = int(width_pixels * 0.72)

        group_bbox = draw_obj.textbbox((0, 0), coaster_text, font=cache_font)
        group_width = max(1, group_bbox[2] - group_bbox[0])
        font_path_key = getattr(coaster_font, 'path', None)
        font_size_key = getattr(coaster_font, 'size', int(dynamic_line_height * FONT_RATIO))
        if group_width > max_track_width and font_path_key:
            shrink_ratio = max_track_width / group_width
            adjusted_size = max(18, int(font_size_key * shrink_ratio))
            try:
                cache_font = ImageFont.truetype(font_path_key, adjusted_size)
                group_bbox = draw_obj.textbbox((0, 0), coaster_text, font=cache_font)
                group_width = max(1, group_bbox[2] - group_bbox[0])
                font_size_key = adjusted_size
            except OSError:
                cache_font = coaster_font

        gap = max(6, int(font_size_key * 0.08))
        char_metrics = []
        running_x = 0
        for char in coaster_text:
            char_bbox = draw_obj.textbbox((0, 0), char, font=cache_font)
            char_w = max(1, char_bbox[2] - char_bbox[0])
            char_h = max(1, char_bbox[3] - char_bbox[1])
            char_metrics.append((char, running_x + char_w / 2.0, char_w, char_h))
            running_x += char_w + gap
        group_width = max(1, running_x - gap)

        progress = frame_idx / max(total_frames - 1, 1)
        edge_visible = max(12, min(width_pixels * 0.18, group_width * 0.45))
        start_x = -group_width + edge_visible
        peak_x = width_pixels * 0.40
        hold_end_x = width_pixels * 0.50
        end_x = width_pixels - edge_visible

        if progress < 0.46:
            local = progress / 0.46
            eased = local * local * (3.0 - 2.0 * local)
            group_x = start_x + (peak_x - start_x) * eased
        elif progress < 0.68:
            local = (progress - 0.46) / 0.22
            eased = 0.5 - 0.5 * math.cos(local * math.pi)
            group_x = peak_x + (hold_end_x - peak_x) * eased
        else:
            local = (progress - 0.68) / 0.32
            fast_t = local ** 0.55
            group_x = hold_end_x + (end_x - hold_end_x) * fast_t

        def track_y(center_x):
            normalized = center_x / max(width_pixels, 1)
            hill = math.exp(-((normalized - 0.46) / 0.16) ** 2)
            downhill = math.exp(-((normalized - 0.76) / 0.10) ** 2)
            return canvas_height * 0.72 - hill * canvas_height * 0.26 + downhill * canvas_height * 0.08

        track_points = []
        for idx in range(0, width_pixels + 1, max(8, width_pixels // 32)):
            track_points.append((idx, track_y(idx)))
        draw_obj.line(track_points, fill=(255, 255, 255, 36), width=max(2, width_pixels // 180))

        if not hasattr(draw_text_roller_coaster, '_char_cache'):
            draw_text_roller_coaster._char_cache = {}

        cache = draw_text_roller_coaster._char_cache
        for char, center_offset, char_w, char_h in char_metrics:
            char_center_x = group_x + center_offset
            if char_center_x < -80 or char_center_x > width_pixels + 80:
                continue

            char_center_y = track_y(char_center_x)
            slope_span = 6
            slope = track_y(char_center_x + slope_span) - track_y(char_center_x - slope_span)
            angle = math.degrees(math.atan2(slope, slope_span * 2)) * 0.9

            cache_key = (char, font_path_key, font_size_key, current_color)
            char_img = cache.get(cache_key)
            if char_img is None:
                char_img = Image.new('RGBA', (char_w + 20, char_h + 20), (0, 0, 0, 0))
                char_draw = ImageDraw.Draw(char_img)
                char_draw.text((char_img.width // 2, char_img.height // 2), char, fill=current_color, font=cache_font, anchor='mm')
                cache[cache_key] = char_img

            rotated = char_img.rotate(-angle, resample=Image.Resampling.BILINEAR, expand=True)
            paste_x = int(char_center_x - rotated.width / 2)
            paste_y = int(char_center_y - rotated.height / 2)
            canvas_img.paste(rotated, (paste_x, paste_y), rotated)
    
    def draw_text_typewriter(canvas_img, lines, frame_idx, total_frames, tw_font, tw_font_size):
        """打字机特效：逐帧增加字符"""
        full_text = ''.join(lines)
        total_chars = len(full_text)
        
        # 计算当前帧应该显示多少个字符
        chars_to_show = int((frame_idx / (total_frames - 1)) * total_chars) if total_frames > 1 else total_chars
        chars_to_show = max(1, min(chars_to_show, total_chars))
        
        # 获取当前应该显示的文本
        current_text = full_text[:chars_to_show]
        
        # 创建临时图层
        temp_img = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 计算文本位置（居中）
        bbox = temp_draw.textbbox((0, 0), current_text, font=tw_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width_pixels - text_width) // 2
        y = (canvas_height - text_height) // 2
        
        # 绘制文字
        if mode == 'rainbow':
            temp_draw.text((x, y), current_text, font=tw_font, fill=(0, 0, 0, 255))
            # 叠加彩虹颜色
            temp_img = apply_rainbow_to_text(temp_img)
        else:
            temp_draw.text((x, y), current_text, font=tw_font, fill=current_color)
            
        canvas_img.paste(temp_img, (0, 0), mask=temp_img)
    
    def draw_text_marquee(canvas_img, lines, frame_idx, total_frames, mq_font, mq_font_size):
        """跑马灯特效：长文本在480宽度内循环滚动"""
        full_text = ''.join(lines)
        
        # 创建临时图层绘制文字（宽度x3，确保滚动空间）
        temp_img = Image.new('RGBA', (width_pixels * 3, canvas_height), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # 计算文本宽度
        bbox = temp_draw.textbbox((0, 0), full_text, font=mq_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算滚动位置（从右到左）
        total_distance = width_pixels + text_width
        progress = (frame_idx / (total_frames - 1)) if total_frames > 1 else 0
        x_offset = width_pixels - int(progress * total_distance)
        
        y = (canvas_height - text_height) // 2
        
        # 绘制文字
        if mode == 'rainbow':
            temp_draw.text((x_offset, y), full_text, font=mq_font, fill=(0, 0, 0, 255))
            # 叠加彩虹颜色
            temp_img = apply_rainbow_to_text(temp_img)
        else:
            temp_draw.text((x_offset, y), full_text, font=mq_font, fill=current_color)
        
        # 裁剪到实际画布大小
        cropped = temp_img.crop((0, 0, width_pixels, canvas_height))
        canvas_img.paste(cropped, (0, 0), mask=cropped)
    
    def draw_text_dissolve(canvas_img, lines, frame_idx, total_frames, ds_font, ds_font_size):
        """像素溶解特效：文字逐渐从像素点拼凑而成"""
        # 先绘制完整文字到临时图层
        temp_img = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        if mode == 'rainbow':
            draw_text_standard(temp_img, lines, (0, 0, 0, 255), 0, 0)
            # 叠加彩虹颜色
            temp_img = apply_rainbow_to_text(temp_img)
        else:
            draw_text_standard(temp_img, lines, current_color, 0, 0)
        
        # 计算溶解进度（0到1）
        dissolve_progress = (frame_idx / (total_frames - 1)) if total_frames > 1 else 1.0
        
        # 性能优化版本：使用块状溶解
        if dissolve_progress >= 1.0:
            canvas_img.paste(temp_img, (0, 0), mask=temp_img)
        else:
            block_size = 8
            blocks_x = width_pixels // block_size
            blocks_y = canvas_height // block_size
            total_blocks = blocks_x * blocks_y
            blocks_to_show = max(1, int(total_blocks * dissolve_progress))
            
            random.seed(42)
            block_order = list(range(total_blocks))
            random.shuffle(block_order)
            random.seed()
            
            result = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
            for i in range(min(blocks_to_show, len(block_order))):
                block_idx = block_order[i]
                bx = (block_idx % blocks_x) * block_size
                by = (block_idx // blocks_x) * block_size
                try:
                    block = temp_img.crop((bx, by, min(bx + block_size, width_pixels), min(by + block_size, canvas_height)))
                    result.paste(block, (bx, by), mask=block)
                except: pass
            canvas_img.paste(result, (0, 0), mask=result)
    
    def draw_text_shining(canvas_img, lines, frame_idx, total_frames, sh_font, sh_font_size):
        """流光字体特效：紫色渐变+光泽扫过"""
        # 1. 创建紫粉色渐变背景
        gradient_bg = create_vertical_gradient(
            width_pixels,
            canvas_height,
            (180, 100, 180),
            (255, 220, 255),
            mode='RGB'
        ).convert('RGBA')
        canvas_img.paste(gradient_bg, (0, 0))
        
        # 2. 创建文字图层
        text_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw_obj = ImageDraw.Draw(text_layer)
        
        # 计算文字位置（居中，支持多行）
        full_text = '\n'.join(lines)
        bbox = draw_obj.multiline_textbbox((0, 0), full_text, font=sh_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width_pixels - text_width) // 2
        y = (canvas_height - text_height) // 2
        
        # 绘制紫色文字
        draw_obj.multiline_text((x, y), full_text, font=sh_font, fill=(150, 0, 200, 255), align='center')
        
        # 3. 添加流光扫过效果
        progress = frame_idx / (total_frames - 1) if total_frames > 1 else 0
        beam_x = int(progress * (width_pixels + 200)) - 100
        
        # 添加白色光泽到文字上
        text_arr = np.array(text_layer)
        x_coords = np.arange(width_pixels)
        intensity = np.clip(1.0 - np.abs(x_coords - beam_x) / 80.0, 0.0, 1.0)
        shine_alpha = (intensity[np.newaxis, :] * 200).astype(np.uint8)
        shine_arr = np.zeros((canvas_height, width_pixels, 4), dtype=np.uint8)
        shine_arr[:, :, :3] = 255
        shine_arr[:, :, 3] = np.where(text_arr[:, :, 3] > 0, shine_alpha, 0)
        shine_layer = Image.fromarray(shine_arr, 'RGBA')
        
        # 4. 合成所有图层
        canvas_rgba = canvas_img.convert('RGBA')
        canvas_rgba = Image.alpha_composite(canvas_rgba, text_layer)
        canvas_rgba = Image.alpha_composite(canvas_rgba, shine_layer)
        canvas_img.paste(canvas_rgba.convert('RGB'), (0, 0))
    
    def draw_text_rainbow_mask(canvas_img, lines, frame_idx, total_frames, rm_font, rm_font_size):
        """彩虹蒙版：文字形状内显示流动彩虹"""
        full_text = '\n'.join(lines)
        
        # 1. 创建彩虹渐变背景
        rainbow_bg = create_rainbow_gradient(
            width_pixels,
            canvas_height,
            frame_idx / max(total_frames, 1),
            mode='RGB'
        )
        
        text_mask = get_centered_text_mask(full_text, rm_font)
        
        paste_text_mask_effect(canvas_img, rainbow_bg, text_mask)
    
    def draw_text_shining_mask(canvas_img, lines, frame_idx, total_frames, sm_font, sm_font_size):
        """流光蒙版：文字形状内显示紫色流光"""
        full_text = '\n'.join(lines)
        
        # 1. 创建紫粉色渐变背景
        shining_bg = create_vertical_gradient(
            width_pixels,
            canvas_height,
            (180, 100, 180),
            (255, 220, 255),
            mode='RGB'
        )
        pixels = shining_bg.load()
        
        # 添加光泽扫过
        progress = frame_idx / (total_frames - 1) if total_frames > 1 else 0
        beam_x = int(progress * (width_pixels + 200)) - 100
        for offset in range(-80, 80, 10):
            x_pos = beam_x + offset
            if 0 <= x_pos < width_pixels:
                intensity = 1.0 - abs(offset) / 80.0
                for y in range(canvas_height):
                    current = pixels[x_pos, y]
                    highlight = int(255 * intensity * 0.6)
                    pixels[x_pos, y] = (
                        min(255, current[0] + highlight),
                        min(255, current[1] + highlight),
                        min(255, current[2] + highlight)
                    )
        
        text_mask = get_centered_text_mask(full_text, sm_font)
        
        paste_text_mask_effect(canvas_img, shining_bg, text_mask)
    
    def draw_text_emoji_mask(canvas_img, lines, frame_idx, total_frames, em_font, em_font_size):
        """Emoji蒙版：文字形状内显示随机emoji表情"""
        full_text = '\n'.join(lines)
        
        # 1. 创建emoji背景
        emoji_list = ['😀', '😁', '😂', '🤣', '😃', '😄', '😅', '😆', '😍', '🥰', '😘', '😎', '🤩', '🔥', '✨', '⚡', '💕', '💖', '💗', '🌟']
        
        emoji_bg = Image.new('RGB', (width_pixels, canvas_height), (255, 255, 255))
        draw_obj = ImageDraw.Draw(emoji_bg)
        
        # 使用中等字号绘制emoji（约40px）
        try:
            emoji_font = ImageFont.truetype(font_path, 40)
        except:
            emoji_font = em_font
        
        random.seed(42 + frame_idx)
        emoji_size = 50
        cols = width_pixels // emoji_size
        rows = canvas_height // emoji_size
        
        for row in range(rows + 1):
            for col in range(cols + 1):
                emoji = random.choice(emoji_list)
                x = col * emoji_size
                y = row * emoji_size
                draw_obj.text((x, y), emoji, font=emoji_font, fill=(0, 0, 0))
        
        random.seed()
        
        text_mask = get_centered_text_mask(full_text, em_font)
        
        paste_text_mask_effect(canvas_img, emoji_bg, text_mask)
    
    def draw_text_matrix_mask(canvas_img, lines, frame_idx, total_frames, mm_font, mm_font_size):
        """矩阵数字雨蒙版：文字形状内显示黑客帝国数字雨"""
        full_text = '\n'.join(lines)
        
        # 1. 创建数字雨背景
        matrix_bg = Image.new('RGB', (width_pixels, canvas_height), (0, 0, 0))
        draw_obj = ImageDraw.Draw(matrix_bg)
        
        # 数字雨字符
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZｱｲｳｴｵｶｷｸｹｺ'
        
        # 使用小字号绘制数字雨
        try:
            matrix_font = ImageFont.truetype(font_path, 20)
        except:
            matrix_font = mm_font
        
        # 列数和雨滴
        num_columns = 24
        column_width = width_pixels // num_columns
        
        random.seed(42 + frame_idx)
        for col_idx in range(num_columns):
            x = col_idx * column_width
            # 每列的雨滴起始位置（随帧变化）
            y_offset = (frame_idx * 15 + col_idx * 30) % (canvas_height + 100)
            
            # 绘制字符串
            for i in range(15):
                char_y = y_offset - canvas_height + i * 20
                if 0 <= char_y < canvas_height:
                    char = random.choice(chars)
                    # 头部亮绿色，尾部暗绿色
                    if i < 2:
                        color = (200, 255, 200)
                    elif i < 5:
                        color = (100, 255, 100)
                    else:
                        brightness = max(50, 200 - i * 15)
                        color = (0, brightness, 0)
                    draw_obj.text((x, char_y), char, font=matrix_font, fill=color)
        
        random.seed()
        
        text_mask = get_centered_text_mask(full_text, mm_font)
        
        paste_text_mask_effect(canvas_img, matrix_bg, text_mask)
    
    def draw_text_fire_mask(canvas_img, lines, frame_idx, total_frames, fm_font, fm_font_size):
        """火焰蒙版：文字形状内显示火焰效果 [NumPy优化-85%提升]"""
        full_text = '\n'.join(lines)
        
        # 1. NumPy批量生成火焰（50%分辨率）
        scale = 0.5
        small_w, small_h = int(width_pixels * scale), int(canvas_height * scale)
        np.random.seed(42 + frame_idx)
        
        y_grid = np.linspace(1.0, 0.0, small_h)[:, np.newaxis]
        y_grid = np.repeat(y_grid, small_w, axis=1)
        noise = np.random.rand(small_h, small_w) * 0.3 - 0.15
        heat = np.clip(y_grid + noise, 0, 1)
        
        r, g, b = (np.zeros((small_h, small_w), dtype=np.uint8) for _ in range(3))
        
        m1 = heat > 0.8
        r[m1], g[m1], b[m1] = 255, (255 * (0.8 + heat[m1] * 0.2)).astype(np.uint8), (100 * heat[m1]).astype(np.uint8)
        
        m2 = (heat > 0.5) & (heat <= 0.8)
        r[m2], g[m2], b[m2] = 255, (200 + heat[m2] * 55).astype(np.uint8), 0
        
        m3 = (heat > 0.2) & (heat <= 0.5)
        r[m3], g[m3], b[m3] = 255, (100 + heat[m3] * 100).astype(np.uint8), 0
        
        m4 = heat <= 0.2
        r[m4], g[m4], b[m4] = (150 * heat[m4] / 0.2).astype(np.uint8), 0, 0
        
        fire_array = np.stack([r, g, b], axis=2)
        fire_bg = Image.fromarray(fire_array, 'RGB').resize((width_pixels, canvas_height), Image.BILINEAR)
        np.random.seed()
        
        text_mask = get_centered_text_mask(full_text, fm_font)
        
        paste_text_mask_effect(canvas_img, fire_bg, text_mask)
    
    def draw_text_stars_mask(canvas_img, lines, frame_idx, total_frames, st_font, st_font_size):
        """星空蒙版：文字形状内显示星空（从GIF加载）"""
        full_text = '\n'.join(lines)
        
        # 1. 加载星空GIF背景
        gif_path = os.path.join('mask_backgrounds', 'stars.gif')
        
        gif_frames = get_resized_gif_frames(gif_path, (width_pixels, canvas_height)) if os.path.exists(gif_path) else []
        if gif_frames:
            stars_bg = gif_frames[frame_idx % len(gif_frames)]
        else:
            # GIF不存在，使用默认密集星空
            stars_bg = Image.new('RGB', (width_pixels, canvas_height), (0, 0, 30))
            pixels = stars_bg.load()
            
            random.seed(42)
            num_stars = 500  # 默认密集星空
            for _ in range(num_stars):
                x = random.randint(0, width_pixels - 1)
                y = random.randint(0, canvas_height - 1)
                brightness = int(random.random() * 255)
                size = random.choice([1, 1, 1, 2])  # 大部分是1像素
                color = (brightness, brightness, min(255, brightness + 50))
                
                if size == 1:
                    pixels[x, y] = color
                else:
                    for dx in range(-size, size + 1):
                        for dy in range(-size, size + 1):
                            if 0 <= x + dx < width_pixels and 0 <= y + dy < canvas_height:
                                dist = (dx*dx + dy*dy) ** 0.5
                                if dist <= size:
                                    pixels[x + dx, y + dy] = color
            random.seed()
        
        text_mask = get_centered_text_mask(full_text, st_font)
        
        paste_text_mask_effect(canvas_img, stars_bg, text_mask)
    

    def draw_text_snow_mask(canvas_img, lines, frame_idx, total_frames, sn_font, sn_font_size):
        """雪花蒙版：文字形状内显示飘落的雪花"""
        full_text = '\n'.join(lines)
        
        # 1. 创建雪花背景
        snow_bg = Image.new('RGB', (width_pixels, canvas_height), (200, 220, 255))  # 淡蓝色
        draw_obj = ImageDraw.Draw(snow_bg)
        
        random.seed(42)
        num_snowflakes = 80  # 优化：减少47%
        snowflakes = []
        for _ in range(num_snowflakes):
            x = random.randint(0, width_pixels)
            y = random.randint(0, canvas_height)
            size = random.randint(2, 6)
            speed = random.uniform(0.5, 2.0)
            drift = random.uniform(-0.5, 0.5)
            snowflakes.append((x, y, size, speed, drift))
        random.seed()
        
        # 绘制雪花
        for x, y, size, speed, drift in snowflakes:
            new_y = (y + frame_idx * speed) % (canvas_height + 20)
            new_x = x + int(frame_idx * drift) % width_pixels
            
            if new_y < canvas_height:
                draw_obj.ellipse([new_x - size//2, new_y - size//2, 
                                 new_x + size//2, new_y + size//2], 
                                fill=(255, 255, 255))
        
        text_mask = get_centered_text_mask(full_text, sn_font)
        
        paste_text_mask_effect(canvas_img, snow_bg, text_mask)
    
    def draw_text_hearts_mask(canvas_img, lines, frame_idx, total_frames, ht_font, ht_font_size):
        """爱心蒙版：文字形状内显示浮动的爱心"""
        full_text = '\n'.join(lines)
        
        # 1. 创建爱心背景
        hearts_bg = Image.new('RGB', (width_pixels, canvas_height), (255, 240, 245))  # 淡粉色
        draw_obj = ImageDraw.Draw(hearts_bg)
        
        # 使用♥符号
        try:
            heart_font_small = ImageFont.truetype(font_path, 30)
            heart_font_large = ImageFont.truetype(font_path, 50)
        except:
            heart_font_small = ht_font
            heart_font_large = ht_font
        
        random.seed(42)
        num_hearts = 30
        hearts = []
        for _ in range(num_hearts):
            x = random.randint(0, width_pixels)
            y = random.randint(0, canvas_height + 100)
            size = random.choice(['small', 'large'])
            speed = random.uniform(1.0, 3.0)
            hearts.append((x, y, size, speed))
        random.seed()
        
        # 绘制爱心
        for x, y, size, speed in hearts:
            new_y = (y - frame_idx * speed) % (canvas_height + 100) - 50
            if -50 < new_y < canvas_height:
                font_to_use = heart_font_large if size == 'large' else heart_font_small
                hue = (x / width_pixels) * 0.1  # 0-0.1范围（红-粉）
                r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
                color = (int(r*255), int(g*255), int(b*255))
                draw_obj.text((x, new_y), '♥', font=font_to_use, fill=color)
        
        text_mask = get_centered_text_mask(full_text, ht_font)
        
        paste_text_mask_effect(canvas_img, hearts_bg, text_mask)
    
    def draw_text_cute_streamer_mask(canvas_img, lines, frame_idx, total_frames, csm_font, csm_font_size):
        """流光爱心蒙版 (Cute Streamer Mask)：文字形状内显示紫色深邃渐变、流动光线条和爱心"""
        full_text = '\n'.join(lines)
        
        # 1. 创建流光深紫渐变背景
        streamer_bg = create_vertical_gradient(
            width_pixels,
            canvas_height,
            (75, 0, 130),
            (200, 0, 200),
            mode='RGB'
        )
        bg_pixels = streamer_bg.load()
                
        draw_obj = ImageDraw.Draw(streamer_bg)
        
        # 2. 绘制流动光线条 (流光)
        random.seed(42)
        num_streamers = 25
        streamers = []
        for _ in range(num_streamers):
            x = random.randint(0, width_pixels)
            width = random.randint(2, 6)
            speed = random.uniform(5.0, 15.0)
            length = random.randint(50, 200)
            opacity = random.randint(100, 220)
            streamers.append((x, width, speed, length, opacity))
            
        for x, width, speed, length, opacity in streamers:
            # 向下流动
            y_pos = (frame_idx * speed) % (canvas_height + length) - length
            if y_pos + length > 0 and y_pos < canvas_height:
                # 绘制带渐变发光的光线条
                for i in range(length):
                    cur_y = int(y_pos + i)
                    if 0 <= cur_y < canvas_height:
                        alpha = int(opacity * math.sin((i / length) * math.pi))
                        # 叠加亮紫色/白色光斑
                        current_color = bg_pixels[x, cur_y]
                        blend_r = min(255, current_color[0] + alpha)
                        blend_g = min(255, current_color[1] + int(alpha*0.5))
                        blend_b = min(255, current_color[2] + alpha)
                        # 画粗细
                        for w_idx in range(width):
                            cur_x = x + w_idx - width//2
                            if 0 <= cur_x < width_pixels:
                                bg_pixels[cur_x, cur_y] = (blend_r, blend_g, blend_b)
        
        # 3. 绘制浮动爱心
        try:
            heart_font = ImageFont.truetype(font_path, 30)
        except:
            heart_font = csm_font
            
        num_hearts = 20
        hearts = []
        for i in range(num_hearts):
            hx = random.randint(0, width_pixels)
            hy = random.randint(0, canvas_height + 100)
            hspeed = random.uniform(1.0, 4.0)
            hearts.append((hx, hy, hspeed))
        
        random.seed()
        
        for hx, hy, hspeed in hearts:
            # 向上浮动
            new_y = (hy - frame_idx * hspeed) % (canvas_height + 100) - 50
            if -50 < new_y < canvas_height:
                draw_obj.text((hx, new_y), '♥', font=heart_font, fill=(255, 180, 255))
        
        text_mask = get_centered_text_mask(full_text, csm_font)
        
        # 5. 合成
        paste_text_mask_effect(canvas_img, streamer_bg, text_mask)
    def draw_text_particles_mask(canvas_img, lines, frame_idx, total_frames, pt_font, pt_font_size):
        """粒子爆炸蒙版：文字形状内显示粒子四散效果"""
        full_text = '\n'.join(lines)
        
        # 1. 创建粒子爆炸背景
        particles_bg = Image.new('RGB', (width_pixels, canvas_height), (20, 20, 40))
        pixels = particles_bg.load()
        
        center_x = width_pixels // 2
        center_y = canvas_height // 2
        
        random.seed(42)
        num_particles = 150  # 优化：减少50%
        particles = []
        for _ in range(num_particles):
            angle = random.random() * 2 * 3.14159
            speed = random.uniform(2, 8)
            hue = random.random()
            size = random.randint(2, 5)
            particles.append((angle, speed, hue, size))
        random.seed()
        
        # 绘制粒子
        progress = frame_idx / total_frames
        for angle, speed, hue, size in particles:
            distance = speed * frame_idx * 3
            x = int(center_x + distance * math.cos(angle))
            y = int(center_y + distance * math.sin(angle))
            
            if 0 <= x < width_pixels and 0 <= y < canvas_height:
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                fade = max(0, 1.0 - progress)
                color = (int(r*255*fade), int(g*255*fade), int(b*255*fade))
                
                for dx in range(-size, size + 1):
                    for dy in range(-size, size + 1):
                        if 0 <= x + dx < width_pixels and 0 <= y + dy < canvas_height:
                            dist = (dx*dx + dy*dy) ** 0.5
                            if dist <= size:
                                alpha = 1.0 - dist / size
                                current = pixels[x + dx, y + dy]
                                pixels[x + dx, y + dy] = (
                                    min(255, current[0] + int(color[0] * alpha)),
                                    min(255, current[1] + int(color[1] * alpha)),
                                    min(255, current[2] + int(color[2] * alpha))
                                )
        
        text_mask = get_centered_text_mask(full_text, pt_font)
        
        paste_text_mask_effect(canvas_img, particles_bg, text_mask)
    
    def draw_text_music_mask(canvas_img, lines, frame_idx, total_frames, ms_font, ms_font_size):
        """音符蒙版：文字形状内显示跳动的音符"""
        full_text = '\n'.join(lines)
        
        # 1. 创建音符背景
        music_bg = Image.new('RGB', (width_pixels, canvas_height), (250, 250, 255))
        draw_obj = ImageDraw.Draw(music_bg)
        
        # 音符符号
        notes = ['♪', '♫', '♬', '♩']
        
        try:
            note_font = ImageFont.truetype(font_path, 40)
        except:
            note_font = ms_font
        
        random.seed(42)
        num_notes = 40
        note_list = []
        for _ in range(num_notes):
            x = random.randint(0, width_pixels)
            y = random.randint(0, canvas_height)
            note = random.choice(notes)
            phase = random.random() * 2 * 3.14159
            amplitude = random.uniform(10, 30)
            note_list.append((x, y, note, phase, amplitude))
        random.seed()
        
        # 绘制跳动的音符
        for x, y, note, phase, amplitude in note_list:
            offset = int(amplitude * math.sin(phase + frame_idx * 0.3))
            new_y = y + offset
            
            # 彩色音符
            hue = (x / width_pixels * 0.8) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 0.6, 0.8)
            color = (int(r*255), int(g*255), int(b*255))
            
            if 0 <= new_y < canvas_height:
                draw_obj.text((x, new_y), note, font=note_font, fill=color)
        
        text_mask = get_centered_text_mask(full_text, ms_font)
        
        paste_text_mask_effect(canvas_img, music_bg, text_mask)
    
    def draw_text_ripple_mask(canvas_img, lines, frame_idx, total_frames, rp_font, rp_font_size):
        """水波纹蒙版：文字形状内显示涟漪效果 [NumPy优化-90%提升]"""
        full_text = '\n'.join(lines)
        
        # 1. NumPy批量生成水波纹（50%分辨率）
        scale = 0.5
        small_w, small_h = int(width_pixels * scale), int(canvas_height * scale)
        
        # 创建距离网格
        x_coords = np.arange(small_w) - small_w // 2
        y_coords = np.arange(small_h) - small_h // 2
        x_grid, y_grid = np.meshgrid(x_coords, y_coords)
        distance = np.sqrt(x_grid**2 + y_grid**2)
        
        # 计算波纹
        wave = np.sin((distance - frame_idx * 10 * scale) / (20 * scale)) * 0.5 + 0.5
        brightness = (150 + wave * 80).astype(np.uint8)
        
        r = (brightness // 2).astype(np.uint8)
        g = brightness
        b = np.minimum(255, brightness + 50).astype(np.uint8)
        
        ripple_array = np.stack([r, g, b], axis=2)
        ripple_bg = Image.fromarray(ripple_array, 'RGB').resize((width_pixels, canvas_height), Image.BILINEAR)
        
        text_mask = get_centered_text_mask(full_text, rp_font)
        
        paste_text_mask_effect(canvas_img, ripple_bg, text_mask)
    
    def draw_text_lightning_mask(canvas_img, lines, frame_idx, total_frames, lt_font, lt_font_size):
        """闪电蒙版：文字形状内显示闪电效果"""
        full_text = '\n'.join(lines)
        
        # 1. 创建闪电背景
        lightning_bg = Image.new('RGB', (width_pixels, canvas_height), (20, 20, 60))
        draw_obj = ImageDraw.Draw(lightning_bg)
        
        # 闪电每5帧出现一次
        if frame_idx % 5 == 0:
            random.seed(42 + frame_idx // 5)
            num_bolts = random.randint(2, 4)
            
            for _ in range(num_bolts):
                # 闪电路径
                x = random.randint(0, width_pixels)
                y = 0
                points = [(x, y)]
                
                for segment in range(8):
                    y += random.randint(40, 80)
                    x += random.randint(-50, 50)
                    x = max(0, min(width_pixels, x))
                    if y < canvas_height:
                        points.append((x, y))
                
                # 绘制闪电主干
                if len(points) > 1:
                    draw_obj.line(points, fill=(200, 220, 255), width=3)
                    # 添加光晕
                    for px, py in points:
                        draw_obj.ellipse([px-10, py-10, px+10, py+10], 
                                        fill=(150, 180, 255))
            
            random.seed()
        
        text_mask = get_centered_text_mask(full_text, lt_font)
        
        paste_text_mask_effect(canvas_img, lightning_bg, text_mask)
    
    def draw_text_smoke_mask(canvas_img, lines, frame_idx, total_frames, sm_font, sm_font_size):
        """彩色烟雾蒙版：文字形状内显示渐变烟雾 [NumPy优化-85%提升]"""
        full_text = '\n'.join(lines)
        
        # 1. NumPy批量生成烟雾（50%分辨率）
        scale = 0.5
        small_w, small_h = int(width_pixels * scale), int(canvas_height * scale)
        
        np.random.seed(42 + frame_idx)
        
        y_grid = 1.0 - np.linspace(0, 1, small_h)[:, np.newaxis]
        y_grid = np.repeat(y_grid, small_w, axis=1)
        noise = np.random.rand(small_h, small_w) * 0.3
        height_ratio = np.clip(y_grid + noise, 0, 1)
        
        x_coords = np.arange(small_w)
        wave = np.sin(x_coords / (30 * scale) + frame_idx / 10) * 0.2
        wave_grid = np.repeat(wave[np.newaxis, :], small_h, axis=0)
        height_with_wave = np.clip(height_ratio + wave_grid, 0, 1)
        
        r, g, b = (np.zeros((small_h, small_w), dtype=np.uint8) for _ in range(3))
        
        m1 = height_with_wave > 0.7
        r[m1], g[m1], b[m1] = 0, (200 * height_with_wave[m1]).astype(np.uint8), (255 * height_with_wave[m1]).astype(np.uint8)
        
        m2 = (height_with_wave > 0.4) & (height_with_wave <= 0.7)
        r[m2], g[m2], b[m2] = (100 * height_with_wave[m2]).astype(np.uint8), (100 * height_with_wave[m2]).astype(np.uint8), (255 * height_with_wave[m2]).astype(np.uint8)
        
        m3 = height_with_wave <= 0.4
        r[m3], g[m3], b[m3] = (150 * height_with_wave[m3]).astype(np.uint8), 0, (200 * height_with_wave[m3]).astype(np.uint8)
        
        smoke_array = np.stack([r, g, b], axis=2)
        smoke_bg = Image.fromarray(smoke_array, 'RGB').resize((width_pixels, canvas_height), Image.BILINEAR)
        np.random.seed()
        
        text_mask = get_centered_text_mask(full_text, sm_font)
        
        paste_text_mask_effect(canvas_img, smoke_bg, text_mask)
    
    def draw_text_neon_lines_mask(canvas_img, lines, frame_idx, total_frames, nl_font, nl_font_size):
        """霓虹灯条蒙版：文字形状内显示动态霓虹灯条"""
        full_text = '\n'.join(lines)
        
        # 1. 创建霓虹灯条背景
        neon_bg = Image.new('RGB', (width_pixels, canvas_height), (10, 10, 20))
        draw_obj = ImageDraw.Draw(neon_bg)
        
        # 霓虹颜色
        colors = [
            (0, 255, 255),    # cyan
            (255, 0, 255),    # magenta
            (255, 255, 0),    # yellow
        ]
        
        random.seed(42)
        num_lines = 15
        lines_data = []
        for _ in range(num_lines):
            orientation = random.choice(['h', 'v'])  # horizontal or vertical
            color = random.choice(colors)
            speed = random.uniform(2, 5)
            offset = random.randint(0, 100)
            lines_data.append((orientation, color, speed, offset))
        random.seed()
        
        # 绘制霓虹灯条
        for orientation, color, speed, offset in lines_data:
            pos = int((frame_idx * speed + offset) % (canvas_height + width_pixels))
            
            if orientation == 'h':
                y = pos % canvas_height
                # 绘制灯条及光晕
                for thickness in range(5, 0, -1):
                    alpha = thickness / 5.0
                    draw_color = tuple(int(c * alpha) for c in color)
                    draw_obj.line([(0, y), (width_pixels, y)], fill=draw_color, width=thickness*2)
            else:
                x = pos % width_pixels
                # 绘制灯条及光晕
                for thickness in range(5, 0, -1):
                    alpha = thickness / 5.0
                    draw_color = tuple(int(c * alpha) for c in color)
                    draw_obj.line([(x, 0), (x, canvas_height)], fill=draw_color, width=thickness*2)
        
        text_mask = get_centered_text_mask(full_text, nl_font)
        
        paste_text_mask_effect(canvas_img, neon_bg, text_mask)
    
    def draw_text_code_mask(canvas_img, lines, frame_idx, total_frames, cd_font, cd_font_size):
        """代码雨蒙版：文字形状内显示编程代码滚动"""
        full_text = '\n'.join(lines)
        
        # 1. 创建代码雨背景
        code_bg = Image.new('RGB', (width_pixels, canvas_height), (30, 30, 30))
        draw_obj = ImageDraw.Draw(code_bg)
        
        # 代码片段
        code_snippets = [
            'def func():', 'import sys', 'return x+y', 
            'for i in range(10):', 'if (x > 0) {', 'console.log(x);',
            '<div class="box">', '} else {', 'const x = 10;',
            'print("hello")', 'while True:', 'let arr = [];'
        ]
        
        try:
            code_font = ImageFont.truetype(font_path, 16)
        except:
            code_font = cd_font
        
        # 列数
        num_columns = 12
        column_width = width_pixels // num_columns
        
        random.seed(42)
        columns_data = []
        for col in range(num_columns):
            speed = random.uniform(10, 25)
            offset = random.randint(0, canvas_height)
            color_hue = random.choice([0.33, 0.5, 0.6])  # 绿/青/蓝
            columns_data.append((speed, offset, color_hue))
        random.seed()
        
        # 绘制代码
        for col_idx, (speed, offset, color_hue) in enumerate(columns_data):
            x = col_idx * column_width
            y_offset = int((frame_idx * speed + offset) % (canvas_height + 200))
            
            for line_idx in range(12):
                y = y_offset - canvas_height + line_idx * 20
                if 0 <= y < canvas_height:
                    code_line = random.choice(code_snippets)
                    # 渐变颜色
                    brightness = max(0.3, 1.0 - line_idx * 0.08)
                    r, g, b = colorsys.hsv_to_rgb(color_hue, 0.8, brightness)
                    color = (int(r*255), int(g*255), int(b*255))
                    draw_obj.text((x, y), code_line, font=code_font, fill=color)
        
        text_mask = get_centered_text_mask(full_text, cd_font)
        
        paste_text_mask_effect(canvas_img, code_bg, text_mask)
    
    def draw_text_floating(canvas_img, lines, frame_idx, total_frames, ft_font_path):
        """漂浮字特效 - 满屏文字从底部向上漂浮，3D立体，带雪花和爱心，前后有层次
        
        性能优化：
        1. 字体按字号缓存，避免重复加载
        2. 粒子数据只在首帧生成，后续帧复用
        3. 使用 stroke_width 替代手动4方向描边
        4. 预渲染贴图后逐帧复用，减少 draw.text 调用
        """
        cw, ch = canvas_img.size
        
        # 限制5个字
        full_text = ''.join(lines)[:5]
        if not full_text:
            return
        
        # === 字体缓存（按字号缓存，避免每帧每粒子都重新加载）===
        if not hasattr(draw_text_floating, '_font_cache'):
            draw_text_floating._font_cache = {}
            draw_text_floating._font_path_cached = None
        
        # 字体路径变化时清空缓存
        if draw_text_floating._font_path_cached != ft_font_path:
            draw_text_floating._font_cache = {}
            draw_text_floating._font_path_cached = ft_font_path
        
        font_cache = draw_text_floating._font_cache
        
        def get_cached_font(size):
            """获取缓存的字体对象"""
            if size not in font_cache:
                try:
                    font_cache[size] = ImageFont.truetype(ft_font_path, int(size * FONT_RATIO))
                except:
                    font_cache[size] = font
            return font_cache[size]
        
        # === 粒子数据只生成一次（用函数属性缓存）===
        font_cache_token = ft_font_path or "__default_font__"
        cache_key = f"{cw}_{ch}_{font_cache_token}_{full_text}"
        if not hasattr(draw_text_floating, '_particles_cache') or draw_text_floating._particles_key != cache_key:
            rng = random.Random(42)
            
            all_items = []
            
            # --- 生成漂浮文字实例（精简数量提升速度）---
            for _ in range(30):
                x = rng.randint(-30, cw - 20)
                y_init = rng.randint(0, ch + 300)
                layer = rng.choices([0, 1, 2], weights=[4, 3, 3])[0]
                if layer == 0:  # 远景 - 仅主体，无阴影无描边
                    fsize = rng.randint(10, 16)
                    alpha = rng.randint(50, 100)
                    speed_cycles = 1
                    has_shadow = False
                    sw = 0
                elif layer == 1:  # 中景 - 仅描边，无阴影
                    fsize = rng.randint(24, 42)
                    alpha = rng.randint(140, 200)
                    speed_cycles = 1
                    has_shadow = False
                    sw = 1
                else:  # 近景 - 1层阴影+描边
                    fsize = rng.randint(70, 120)
                    alpha = rng.randint(230, 255)
                    speed_cycles = 2
                    has_shadow = True
                    sw = 1
                
                hue = rng.random()
                sat = rng.uniform(0.5, 1.0)
                val = rng.uniform(0.8, 1.0)
                r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
                
                all_items.append(('text', {
                    'x': x, 'y_init': y_init, 'fsize': fsize,
                    'speed_cycles': speed_cycles, 'layer': layer,
                    'color': (int(r*255), int(g*255), int(b*255), alpha),
                    'has_shadow': has_shadow, 'sw': sw
                }))
            
            # --- 生成雪花实例（精简）---
            snow_chars = ['❄', '✦', '✧', '☆', '❅', '❆']
            for _ in range(8):
                x = rng.randint(0, cw)
                y_init = rng.randint(0, ch + 200)
                fsize = rng.randint(12, 24)
                alpha = rng.randint(140, 230)
                char = rng.choice(snow_chars)
                snow_hue = rng.choice([0.0, 0.55, 0.75])
                r, g, b = colorsys.hsv_to_rgb(snow_hue, rng.uniform(0.0, 0.25), 1.0)
                all_items.append(('deco', {
                    'x': x, 'y_init': y_init, 'fsize': fsize,
                    'speed_cycles': 1, 'layer': 0,
                    'color': (int(r*255), int(g*255), int(b*255), alpha),
                    'char': char
                }))
            
            # --- 生成爱心实例（精简）---
            heart_chars = ['♡', '♥', '❤']
            for _ in range(5):
                x = rng.randint(0, cw)
                y_init = rng.randint(0, ch + 200)
                fsize = rng.randint(14, 26)
                alpha = rng.randint(160, 255)
                char = rng.choice(heart_chars)
                heart_hue = rng.choice([0.0, 0.9, 0.95])
                r, g, b = colorsys.hsv_to_rgb(heart_hue, rng.uniform(0.5, 1.0), 1.0)
                all_items.append(('deco', {
                    'x': x, 'y_init': y_init, 'fsize': fsize,
                    'speed_cycles': 1, 'layer': 1,
                    'color': (int(r*255), int(g*255), int(b*255), alpha),
                    'char': char
                }))
            
            probe_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            probe_draw = ImageDraw.Draw(probe_img)

            def build_floating_sprite(content, item_font, fill, stroke_width=0, stroke_fill=None, shadow=False):
                shadow_offset = 4 if shadow else 0
                bbox = probe_draw.textbbox((0, 0), content, font=item_font, stroke_width=stroke_width, anchor='lt')
                text_w = max(1, bbox[2] - bbox[0])
                text_h = max(1, bbox[3] - bbox[1])
                pad = max(3, stroke_width + shadow_offset + 2)
                sprite = Image.new('RGBA', (text_w + pad * 2 + shadow_offset, text_h + pad * 2 + shadow_offset), (0, 0, 0, 0))
                sprite_draw = ImageDraw.Draw(sprite)
                base_x = pad
                base_y = pad
                if shadow:
                    sprite_draw.text((base_x + shadow_offset, base_y + shadow_offset), content,
                                     fill=(0, 0, 0, 80), font=item_font, anchor='lt')
                sprite_draw.text(
                    (base_x, base_y),
                    content,
                    fill=fill,
                    font=item_font,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_fill,
                    anchor='lt'
                )
                return sprite

            sprite_cache = {}
            hydrated_items = []
            for item_type, item in all_items:
                content = full_text if item_type == 'text' else item['char']
                stroke_width = item.get('sw', 0) if item_type == 'text' else 0
                stroke_fill = (0, 0, 0, min(item['color'][3], 180)) if item_type == 'text' and stroke_width > 0 else None
                shadow = bool(item.get('has_shadow')) if item_type == 'text' else False
                sprite_key = (item_type, content, item['fsize'], item['color'], stroke_width, stroke_fill, shadow)
                sprite = sprite_cache.get(sprite_key)
                if sprite is None:
                    sprite = build_floating_sprite(content, get_cached_font(item['fsize']), item['color'], stroke_width, stroke_fill, shadow)
                    sprite_cache[sprite_key] = sprite
                enriched = dict(item)
                enriched['sprite'] = sprite
                hydrated_items.append((item_type, enriched))

            all_items = hydrated_items
            # 按layer排序：0(远景) → 1(中景) → 2(近景)
            all_items.sort(key=lambda item: item[1]['layer'])
            
            draw_text_floating._particles_cache = all_items
            draw_text_floating._particles_key = cache_key
        
        all_items = draw_text_floating._particles_cache
        
        # === 逐帧计算位置并绘制 ===
        cycle_height = ch + 350
        progress = frame_idx / total_frames
        
        for item_type, p in all_items:
            # 计算当前y位置
            total_displacement = p['speed_cycles'] * cycle_height
            y_offset = total_displacement * progress
            current_y = int((p['y_init'] - y_offset) % cycle_height - 150)
            sprite = p['sprite']
            paste_x = p['x'] - 3
            paste_y = current_y - 3

            if paste_x >= cw or paste_y >= ch or paste_x + sprite.width <= 0 or paste_y + sprite.height <= 0:
                continue

            canvas_img.paste(sprite, (paste_x, paste_y), sprite)

    def draw_text_floating_clear(canvas_img, lines, frame_idx, total_frames, ft_font_path):
        """漂浮字透明版 - 透明底，白色描边，粉/紫/蓝/白色调，雪花爱心装饰
        
        性能优化：字体缓存 + 粒子数据复用 + 贴图缓存复用
        """
        cw, ch = canvas_img.size
        compact_mode = cw <= 360 or ch <= 360 or total_frames <= 12
        
        # 限制5个字
        full_text = ''.join(lines).replace(' ', '')[:5]
        if not full_text:
            return
        
        # === 字体缓存 ===
        if not hasattr(draw_text_floating_clear, '_font_cache'):
            draw_text_floating_clear._font_cache = {}
            draw_text_floating_clear._font_path_cached = None
        
        if draw_text_floating_clear._font_path_cached != ft_font_path:
            draw_text_floating_clear._font_cache = {}
            draw_text_floating_clear._font_path_cached = ft_font_path
        
        fc = draw_text_floating_clear._font_cache
        
        def get_font(size):
            if size not in fc:
                try:
                    fc[size] = ImageFont.truetype(ft_font_path, int(size * FONT_RATIO))
                except:
                    fc[size] = font
            return fc[size]
        
        # === 粒子数据缓存 ===
        font_cache_token = ft_font_path or "__default_font__"
        cache_key = f"clear_{cw}_{ch}_{font_cache_token}_{full_text}"
        if not hasattr(draw_text_floating_clear, '_particles_cache') or draw_text_floating_clear._particles_key != cache_key:
            rng = random.Random(88)
            all_items = []
            
            # 粉/紫/蓝/白 色调
            color_palette = [
                (255, 105, 180),  # 粉红
                (255, 182, 193),  # 浅粉
                (218, 112, 214),  # 兰花紫
                (186, 85, 211),   # 中紫
                (138, 43, 226),   # 蓝紫
                (100, 149, 237),  # 矢车菊蓝
                (135, 206, 250),  # 浅天蓝
                (255, 255, 255),  # 白
                (240, 230, 255),  # 薰衣草白
            ]

            text_count = 18 if compact_mode else 30
            snow_count = 6 if compact_mode else 12
            heart_count = 4 if compact_mode else 10
            text_size_tiers = (
                (12, 14),
                (28, 32),
                (58, 68),
            ) if compact_mode else (
                (10, 16),
                (24, 42),
                (60, 100),
            )
            
            # --- 漂浮文字 ---
            for _ in range(text_count):
                x = rng.randint(-30, cw - 20)
                y_init = rng.randint(0, ch + 300)
                layer = rng.choices([0, 1, 2], weights=[5, 3, 2] if compact_mode else [4, 3, 3])[0]
                if layer == 0:
                    fsize = rng.choice(text_size_tiers[0])
                    alpha = rng.randint(70, 120) if compact_mode else rng.randint(80, 140)
                    speed_cycles = 1
                    sw = 0 if compact_mode else 1
                elif layer == 1:
                    fsize = rng.choice(text_size_tiers[1])
                    alpha = rng.randint(150, 210) if compact_mode else rng.randint(180, 230)
                    speed_cycles = 1
                    sw = 1
                else:
                    fsize = rng.choice(text_size_tiers[2])
                    alpha = rng.randint(225, 255)
                    speed_cycles = 2
                    sw = 1 if compact_mode else 2
                
                base_color = rng.choice(color_palette)
                color = (base_color[0], base_color[1], base_color[2], alpha)
                
                all_items.append(('text', {
                    'x': x, 'y_init': y_init, 'fsize': fsize,
                    'speed_cycles': speed_cycles, 'layer': layer,
                    'color': color, 'sw': sw
                }))
            
            # --- 雪花+星星 ---
            star_snow_chars = ['❄', '✦', '✧', '☆', '❅', '★', '⭐', '✰', '✩', '✪']
            for _ in range(snow_count):
                x = rng.randint(0, cw)
                y_init = rng.randint(0, ch + 200)
                fsize = rng.choice((12, 16, 18)) if compact_mode else rng.randint(12, 28)
                alpha = rng.randint(150, 230) if compact_mode else rng.randint(150, 245)
                char = rng.choice(star_snow_chars)
                # 白/浅粉/浅紫色
                sc = rng.choice([(255, 255, 255), (255, 230, 240), (230, 210, 255), (200, 220, 255)])
                all_items.append(('deco', {
                    'x': x, 'y_init': y_init, 'fsize': fsize,
                    'speed_cycles': 1, 'layer': 0,
                    'color': (sc[0], sc[1], sc[2], alpha), 'char': char
                }))
            
            # --- 爱心 ---
            heart_chars = ['♡', '♥', '❤', '💕', '💖', '💗']
            for _ in range(heart_count):
                x = rng.randint(0, cw)
                y_init = rng.randint(0, ch + 200)
                fsize = rng.choice((14, 18, 20)) if compact_mode else rng.randint(14, 28)
                alpha = rng.randint(170, 245) if compact_mode else rng.randint(170, 255)
                char = rng.choice(heart_chars)
                hc = rng.choice([(255, 105, 180), (255, 182, 193), (218, 112, 214), (255, 20, 147), (238, 130, 238)])
                all_items.append(('deco', {
                    'x': x, 'y_init': y_init, 'fsize': fsize,
                    'speed_cycles': 1, 'layer': 1,
                    'color': (hc[0], hc[1], hc[2], alpha), 'char': char
                }))
            
            probe_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
            probe_draw = ImageDraw.Draw(probe_img)

            def build_sprite(content, item_font, fill, stroke_width=0, stroke_fill=None):
                bbox = probe_draw.textbbox((0, 0), content, font=item_font, stroke_width=stroke_width, anchor='lt')
                text_w = max(1, bbox[2] - bbox[0])
                text_h = max(1, bbox[3] - bbox[1])
                pad = max(2, stroke_width + 1)
                sprite = Image.new('RGBA', (text_w + pad * 2, text_h + pad * 2), (0, 0, 0, 0))
                sprite_draw = ImageDraw.Draw(sprite)
                sprite_draw.text(
                    (pad, pad),
                    content,
                    fill=fill,
                    font=item_font,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_fill,
                    anchor='lt'
                )
                return sprite

            sprite_cache = {}
            hydrated_items = []
            for item_type, item in all_items:
                content = full_text if item_type == 'text' else item['char']
                stroke_width = item.get('sw', 0) if item_type == 'text' else 0
                stroke_fill = (255, 255, 255, min(item['color'][3], 220)) if item_type == 'text' else None
                sprite_key = (item_type, content, item['fsize'], item['color'], stroke_width, stroke_fill, compact_mode)
                sprite = sprite_cache.get(sprite_key)
                if sprite is None:
                    sprite = build_sprite(content, get_font(item['fsize']), item['color'], stroke_width, stroke_fill)
                    sprite_cache[sprite_key] = sprite
                enriched = dict(item)
                enriched['sprite'] = sprite
                hydrated_items.append((item_type, enriched))

            all_items = hydrated_items
            all_items.sort(key=lambda item: item[1]['layer'])
            draw_text_floating_clear._particles_cache = all_items
            draw_text_floating_clear._particles_key = cache_key
        
        all_items = draw_text_floating_clear._particles_cache
        
        # === 绘制 ===
        cycle_height = ch + 350
        progress = frame_idx / total_frames
        
        for item_type, p in all_items:
            total_displacement = p['speed_cycles'] * cycle_height
            y_offset = total_displacement * progress
            current_y = int((p['y_init'] - y_offset) % cycle_height - 150)
            sprite = p['sprite']
            paste_x = p['x'] - 2
            paste_y = current_y - 2

            if paste_x >= cw or paste_y >= ch or paste_x + sprite.width <= 0 or paste_y + sprite.height <= 0:
                continue

            canvas_img.paste(sprite, (paste_x, paste_y), sprite)

    def draw_text_spiral_3d(canvas_img, lines, frame_idx, total_frames, ft_font_path):
        """螺旋3D旋转 - 每个字符沿螺旋路径从底部旋转上升到顶部
        
        3D效果：cos控制x偏移，sin控制缩放和透明度（前大后小）
        每个字符使用随机字体和随机颜色
        """
        draw_obj = ImageDraw.Draw(canvas_img)
        cw, ch = canvas_img.size
        
        # 限制6个字
        full_text = ''.join(lines)[:6]
        if not full_text:
            return
        char_count = len(full_text)
        
        # === 缓存：字体和粒子数据 ===
        cache_key = f"spiral_{cw}_{ch}_{full_text}"
        if not hasattr(draw_text_spiral_3d, '_cache') or draw_text_spiral_3d._cache_key != cache_key:
            rng = random.Random(77)
            
            # 获取可用字体列表
            font_dir = "fonts"
            valid_ext = ('.ttf', '.ttc', '.otf')
            try:
                all_fonts = [os.path.join(font_dir, f) for f in os.listdir(font_dir) if f.lower().endswith(valid_ext)]
            except:
                all_fonts = [ft_font_path]
            if not all_fonts:
                all_fonts = [ft_font_path]
            
            # 为每个字符生成属性
            chars_data = []
            for idx, char in enumerate(full_text):
                # 随机字体
                char_font_path = rng.choice(all_fonts)
                
                # 随机颜色（高饱和高亮度）
                hue = rng.random()
                sat = rng.uniform(0.6, 1.0)
                val = rng.uniform(0.85, 1.0)
                r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
                color = (int(r*255), int(g*255), int(b*255))
                
                # 每个字符在螺旋上的相位偏移（均匀分布在一圈上）
                phase_offset = (idx / char_count) * 2 * math.pi
                
                chars_data.append({
                    'char': char,
                    'font_path': char_font_path,
                    'color': color,
                    'phase_offset': phase_offset,
                })
            
            draw_text_spiral_3d._cache = chars_data
            draw_text_spiral_3d._cache_key = cache_key
            draw_text_spiral_3d._font_cache = {}
        
        chars_data = draw_text_spiral_3d._cache
        font_cache = draw_text_spiral_3d._font_cache
        
        def get_font(font_path, size):
            key = (font_path, size)
            if key not in font_cache:
                try:
                    font_cache[key] = ImageFont.truetype(font_path, int(size * FONT_RATIO))
                except:
                    font_cache[key] = font
            return font_cache[key]
        
        # === 动画参数 ===
        center_x = cw // 2
        radius_x = int(cw * 0.28)         # 水平旋转半径
        base_font_size = 60                # 基础字号
        min_scale = 0.35                   # 最远处缩放
        max_scale = 1.2                    # 最近处缩放
        
        # 动画进度 [0, 1)
        progress = frame_idx / total_frames
        # 旋转角度（1圈/循环，保证无缝）
        base_angle = progress * 2 * math.pi
        
        # y轴：从底部到顶部循环（1个完整周期）
        total_y_range = ch + 200  # 上下各留余量
        
        # === 计算每个字符的位置和深度，然后按深度排序绘制 ===
        render_list = []
        
        for cd in chars_data:
            # 当前字符的旋转角度
            angle = base_angle + cd['phase_offset']
            
            # 3D投影
            # cos(angle) 控制 x 偏移（左右摆动）
            # sin(angle) 控制深度（>0 = 前面/大，<0 = 后面/小）
            cos_val = math.cos(angle)
            sin_val = math.sin(angle)
            
            # x位置：中心 + 旋转偏移
            x = center_x + int(radius_x * cos_val)
            
            # y位置：随进度从底部向上移动（加上相位产生螺旋分布）
            y_progress = (progress + cd['phase_offset'] / (2 * math.pi)) % 1.0
            y = int(ch + 100 - y_progress * total_y_range)
            
            # 缩放：sin控制，前面大后面小
            depth = (sin_val + 1) / 2  # 0~1, 1=最前
            scale = min_scale + depth * (max_scale - min_scale)
            
            # 透明度：前面不透明，后面半透明
            alpha = int(80 + depth * 175)  # 80~255
            
            fsize = int(base_font_size * scale)
            if fsize < 8:
                fsize = 8
            
            render_list.append({
                'char': cd['char'],
                'font_path': cd['font_path'],
                'color': cd['color'],
                'x': x, 'y': y,
                'fsize': fsize,
                'alpha': alpha,
                'depth': depth,
            })
        
        # 按深度排序：先画远的（depth小），后画近的（depth大）
        render_list.sort(key=lambda r: r['depth'])
        
        # === 绘制 ===
        for item in render_list:
            char_font = get_font(item['font_path'], item['fsize'])
            
            # 计算字符尺寸用于居中
            try:
                bbox = char_font.getbbox(item['char'])
                char_w = bbox[2] - bbox[0]
            except:
                char_w = item['fsize']
            
            draw_x = item['x'] - char_w // 2
            draw_y = item['y']
            
            r, g, b = item['color']
            alpha = item['alpha']
            
            # 描边 + 主体（1次draw call + stroke_width）
            stroke_alpha = min(alpha, 200)
            draw_obj.text(
                (draw_x, draw_y), item['char'],
                fill=(r, g, b, alpha),
                font=char_font,
                stroke_width=2,
                stroke_fill=(0, 0, 0, stroke_alpha)
            )

    def draw_text_spotlight(canvas_img, lines, frame_idx, total_frames, font):
        """暗夜聚光灯特效 - 黑色暗影字 + 高亮霓虹字组合，通过移动的光束遮罩显现高亮部分"""
        cw, ch = canvas_img.size
        full_text = '\n'.join(lines)
        
        # === 数据和图层缓存 ===
        cache_key = f"spotlight_{cw}_{ch}_{full_text}_{getattr(font, 'path', '')}_{getattr(font, 'size', '')}"
        if not hasattr(draw_text_spotlight, '_cache_key') or draw_text_spotlight._cache_key != cache_key:
            # 1. 预先绘制暗色图层
            dark_layer = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
            draw_dark = ImageDraw.Draw(dark_layer)
            
            # 计算居中坐标
            try:
                line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines]
                total_height = sum(line_heights) + 10 * (len(lines) - 1)
            except:
                total_height = font.size * len(lines)
            
            start_y = (ch - total_height) // 2
            current_y = start_y
            
            # 暗光颜色和高亮颜色
            dark_color = (30, 30, 30, 255)
            dark_stroke = (10, 10, 10, 255)
            
            bright_color = (0, 255, 255, 255)      # 青色核心
            bright_stroke = (0, 150, 255, 255)     # 蓝色边缘
            
            for line in lines:
                try:
                    w = font.getbbox(line)[2] - font.getbbox(line)[0]
                except:
                    w = font.size * len(line)
                cx = (cw - w) // 2
                
                # 画暗层
                draw_dark.text((cx, current_y), line, fill=dark_color, font=font, 
                              stroke_width=2, stroke_fill=dark_stroke)
                current_y += font.size + 10
            
            # 2. 绘制高亮图层 + 发光模糊
            bright_base = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
            draw_bright = ImageDraw.Draw(bright_base)
            current_y = start_y
            for line in lines:
                try:
                    w = font.getbbox(line)[2] - font.getbbox(line)[0]
                except:
                    w = font.size * len(line)
                cx = (cw - w) // 2
                draw_bright.text((cx, current_y), line, fill=bright_color, font=font,
                                stroke_width=3, stroke_fill=bright_stroke)
                current_y += font.size + 10
            
            # 高亮层加上辉光
            bright_glow = bright_base.filter(ImageFilter.GaussianBlur(8))
            bright_layer = Image.alpha_composite(bright_glow, bright_base)
            
            # 3. 生成聚光灯遮罩模版 (径向渐变)
            spot_r = int(min(cw, ch) * 0.45)
            spot_d = spot_r * 2
            spot_mask_template = Image.new('L', (spot_d, spot_d), 0)
            
            # 创建渐变
            for r in range(spot_r, 0, -1):
                # 越靠近中心越亮，边缘平滑衰减
                val = int(255 * ((r) / spot_r) ** 1.5)
                ImageDraw.Draw(spot_mask_template).ellipse(
                    ((spot_r - r), (spot_r - r), (spot_r + r), (spot_r + r)),
                    fill=val
                )
            
            draw_text_spotlight._dark_layer = dark_layer
            draw_text_spotlight._bright_layer = bright_layer
            draw_text_spotlight._spot_template = spot_mask_template
            draw_text_spotlight._spot_r = spot_r
            draw_text_spotlight._cache_key = cache_key
            
        dark_layer = draw_text_spotlight._dark_layer
        bright_layer = draw_text_spotlight._bright_layer
        spot_template = draw_text_spotlight._spot_template
        spot_r = draw_text_spotlight._spot_r
        
        # === 逐帧绘制 ===
        # 1. 始终叠加暗层
        canvas_img.alpha_composite(dark_layer)
        
        # 2. 计算聚光灯位置 (8字型/无限大轨迹)
        progress = frame_idx / total_frames
        angle = progress * 2 * math.pi
        
        # 运动范围
        range_x = int(cw * 0.45)
        range_y = int(ch * 0.35)
        
        # 典型的 Lissajous 曲线 (a=1, b=2) 形成 8 字型
        center_x = cw // 2 + int(math.sin(angle) * range_x)
        center_y = ch // 2 + int(math.sin(angle * 2) * range_y)
        
        # 3. 把聚光灯帖到全屏遮罩上
        full_mask = Image.new('L', (cw, ch), 0)
        paste_x = center_x - spot_r
        paste_y = center_y - spot_r
        
        # 由于可能超出边界，直接糊到满屏尺寸 mask 上，利用 PIL 自动裁剪处理或透明保护
        full_mask.paste(spot_template, (paste_x, paste_y))
        
        # 4. 用遮罩画高亮层
        canvas_img.paste(bright_layer, (0, 0), full_mask)

    def draw_text_star_wars(canvas_img, lines, frame_idx, total_frames, font):
        """星际史诗透视特效 - 文本沿 3D 透视平面向远方滚动"""
        cw, ch = canvas_img.size
        
        # === 缓存星空背景和梯形变换矩阵 ===
        full_text_key = '\n'.join(lines)
        cache_key = f"starwars_{cw}_{ch}_{full_text_key}_{getattr(font, 'path', '')}_{getattr(font, 'size', '')}"
        if not hasattr(draw_text_star_wars, '_cache_key') or draw_text_star_wars._cache_key != cache_key:
            # 1. 生成星空背景
            stars_bg = Image.new('RGBA', (cw, ch), (0, 0, 0, 255))
            draw_stars = ImageDraw.Draw(stars_bg)
            rng = random.Random(101)
            
            # 星空点缀
            for _ in range(80):
                sx = rng.randint(0, cw)
                sy = rng.randint(0, ch)
                s_size = rng.choice([1, 1, 2, 2, 3])
                s_alpha = rng.randint(80, 255)
                draw_stars.ellipse((sx, sy, sx+s_size, sy+s_size), fill=(255, 255, 255, s_alpha))
                
            # 2. 计算透视变换矩阵 (利用 numpy)
            # 目标多边形（梯形：上边短，且位于画面靠上）
            top_y = int(ch * 0.15)
            # 源坐标系
            pa = [(0, 0), (cw, 0), (cw, ch), (0, ch)]
            # 目标坐标系
            pb = [(int(cw * 0.3), top_y), (int(cw * 0.7), top_y), (cw, ch), (0, ch)]
            
            matrix = []
            for p1, p2 in zip(pa, pb):
                matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
                matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
            
            A = np.matrix(matrix, dtype=float)
            B = np.array(pb).reshape(8)
            coeffs = np.linalg.solve(A, B).flatten().tolist()
            
            # 3. 绘制所有的文字图层(超长画布)
            line_heights = []
            for line in lines:
                try:
                    h = font.getbbox(line)[3] - font.getbbox(line)[1]
                except:
                    h = font.size
                line_heights.append(h)
            
            total_text_h = sum(line_heights) + int(font.size * 0.8) * (len(lines) - 1)
            scroll_length = ch + total_text_h + ch // 2  # 整个滚动的位移总量
            
            text_img = Image.new('RGBA', (cw, total_text_h), (0, 0, 0, 0))
            draw_text = ImageDraw.Draw(text_img)
            
            sw_color = (255, 232, 31, 255)  # 星战黄
            
            cy = 0
            for i, line in enumerate(lines):
                try:
                    w = font.getbbox(line)[2] - font.getbbox(line)[0]
                except:
                    w = font.size * len(line)
                draw_text.text(((cw - w) // 2, cy), line, fill=sw_color, font=font)
                cy += line_heights[i] + int(font.size * 0.8)
                
            draw_text_star_wars._stars_bg = stars_bg
            draw_text_star_wars._coeffs = coeffs
            draw_text_star_wars._text_img = text_img
            draw_text_star_wars._total_text_h = total_text_h
            draw_text_star_wars._scroll_length = scroll_length
            draw_text_star_wars._cache_key = cache_key
            
        stars_bg = draw_text_star_wars._stars_bg
        coeffs = draw_text_star_wars._coeffs
        text_img = draw_text_star_wars._text_img
        scroll_length = draw_text_star_wars._scroll_length
        total_text_h = draw_text_star_wars._total_text_h
        
        # === 逐帧合并 ===
        # 1. 铺底星空
        canvas_img.alpha_composite(stars_bg)
        
        # 2. 从 text_img 滚动画布
        progress = frame_idx / total_frames
        
        # 当前滑动偏移的 Y (起始：文字在下方屏幕外；结束：文字在透视消失点上)
        current_y_offset = int(ch - progress * scroll_length)
        
        # 把文字贴在一个新的全屏透明画板上，代表这一帧变换前的原始视角
        flat_view = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
        flat_view.paste(text_img, (0, current_y_offset), text_img)
        
        # 3. 梯形透视变换
        perspective_view = flat_view.transform((cw, ch), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
        
        # 4. 根据 Y 坐标加一个高度渐隐 (上面消失在星空)
        # 优化：通过透明度遮罩让顶部稍微淡出
        fade_mask = Image.new('L', (cw, ch), 255)
        fade_draw = ImageDraw.Draw(fade_mask)
        fade_top = int(ch * 0.15)
        fade_h = int(ch * 0.1)
        for y in range(fade_top, fade_top + fade_h):
            alpha = int(255 * ((y - fade_top) / fade_h))
            fade_draw.line((0, y, cw, y), fill=alpha)
        fade_draw.rectangle((0, 0, cw, fade_top), fill=0)
        
        # 应用透明度渐变
        perspective_view.putalpha(ImageChops.multiply(perspective_view.split()[3], fade_mask))
        
        canvas_img.alpha_composite(perspective_view)


    def draw_text_ghost_trails(canvas_img, lines, frame_idx, total_frames, font):
        """流萤残影特效 - 元素在屏幕内以 Lissajous 曲线游走，身后带有多个透明度和颜色渐变的残影。
        因为是预渲染，直接通过数学公式读取历史/未来帧的位置，不需要状态缓存。
        """
        cw, ch = canvas_img.size
        draw_obj = ImageDraw.Draw(canvas_img)
        
        # 将文字合并
        full_text = '\n'.join(lines)
        
        # 运动范围
        # 由于我们中心点不能太靠近边缘导致文字切断，需要结合文字大小
        try:
            w = font.getbbox(lines[0])[2] - font.getbbox(lines[0])[0]
            h = sum(font.getbbox(l)[3] - font.getbbox(l)[1] for l in lines)
        except:
            w = font.size * len(lines[0])
            h = font.size * len(lines)
            
        range_x = max(10, (cw - w) // 2 - 20)
        range_y = max(10, (ch - h) // 2 - 50)
        
        center_x = cw // 2
        center_y = ch // 2
        
        # 拖尾参数
        trail_count = 15     # 残影数量
        tail_length = 0.2    # 拖尾总占动画周期的比例 (0~1)
        
        # 获取当前时间相位 [0, 1)
        # 从最后面的残影开始画，最后画本体，这样本体在最上层
        # 这里 t_offset = 1代表过去，0代表现在
        for i in range(trail_count, -1, -1):
            # i 越大，表示越老的残影
            progress_offset = (i / trail_count) * tail_length
            
            # 当前这个影子对应的动画进度
            # 加上 1.0 确保对负数取模依然在 [0, 1)
            t = (frame_idx / total_frames - progress_offset + 1.0) % 1.0
            
            # Lissajous 曲线 (a=3, b=2 保证平滑无缝且充满边界)
            angle_x = t * 2 * math.pi * 3
            angle_y = t * 2 * math.pi * 2
            
            x = center_x + int(range_x * math.sin(angle_x))
            y = center_y + int(range_y * math.cos(angle_y))
            
            # 中心对齐排版
            current_y = y - h // 2
            
            if i == 0:
                # 本体：最高亮度，白色/青色
                main_color = (0, 255, 255, 255)
                stroke_color = (255, 255, 255, 255)
                sw = 2
            else:
                # 残影：透明度递减，颜色向紫/深蓝偏移
                # hue 从 0.5 (青色) 变到 0.8 (紫色)
                hue = 0.5 + 0.3 * (i / trail_count)
                alpha = int(200 * (1 - i / trail_count))
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                main_color = (int(r*255), int(g*255), int(b*255), alpha)
                stroke_color = (int(r*150), int(g*150), int(b*150), alpha // 2)
                sw = 1
                
            for line in lines:
                try:
                    line_w = font.getbbox(line)[2] - font.getbbox(line)[0]
                    line_h = font.getbbox(line)[3] - font.getbbox(line)[1]
                except:
                    line_w = font.size * len(line)
                    line_h = font.size
                
                cx = x - line_w // 2
                draw_obj.text((cx, current_y), line, fill=main_color, font=font, 
                             stroke_width=sw, stroke_fill=stroke_color)
                current_y += line_h + 10

    def draw_text_ktv_sweep(canvas_img, lines, frame_idx, total_frames):
        """KTV 卡拉OK变色 - 从左到右扫光"""
        base_color = (150, 150, 150, 255) if theme == 'dark' else (200, 200, 200, 255)
        highlight_color = current_color
        
        base_layer = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
        highlight_layer = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
        
        draw_text_standard(base_layer, lines, base_color, 0, 0)
        if mode == 'rainbow':
            draw_text_standard(highlight_layer, lines, (0,0,0,255), 0, 0)
            highlight_layer = apply_rainbow_to_text(highlight_layer)
        else:
            draw_text_standard(highlight_layer, lines, highlight_color, 0, 0)
            
        progress = frame_idx / max(total_frames - 1, 1)
        
        draw_obj = ImageDraw.Draw(canvas_img)
        full_text = '\n'.join(lines)
        bbox = draw_obj.multiline_textbbox((0, 0), full_text, font=font)
        text_width = bbox[2] - bbox[0]
        x_start = (width_pixels - text_width) // 2
        
        sweep_x = int(x_start + text_width * progress)
        
        mask = Image.new('L', (width_pixels, canvas_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rectangle([0, 0, sweep_x, canvas_height], fill=255)
        
        canvas_img.paste(base_layer, (0, 0), mask=base_layer)
        highlight_layer_cropped = Image.composite(highlight_layer, Image.new('RGBA', highlight_layer.size, (0,0,0,0)), mask)
        canvas_img.paste(highlight_layer_cropped, (0, 0), mask=highlight_layer_cropped)

    def draw_text_neon_flicker(canvas_img, lines, frame_idx, total_frames):
        """霓虹灯故障闪烁 - 前期闪烁，后期常亮并发光"""
        progress = frame_idx / max(total_frames - 1, 1)
        is_flicker_phase = progress < 0.3
        
        opacity = 255
        if is_flicker_phase:
            random.seed(42 + frame_idx)
            if random.random() < 0.5:
                opacity = random.randint(20, 80)
            else:
                opacity = 255
            random.seed()
            
        text_color = (*current_color[:3], opacity) if mode != 'rainbow' else (255, 255, 255, opacity)
        
        temp_img = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
        if mode == 'rainbow':
            draw_text_standard(temp_img, lines, (0,0,0,opacity), 0, 0)
            temp_img = apply_rainbow_to_text(temp_img)
            if opacity < 255:
                alpha = temp_img.split()[3]
                alpha = alpha.point(lambda p: int(p * (opacity / 255.0)))
                temp_img.putalpha(alpha)
        else:
            draw_text_standard(temp_img, lines, text_color, 0, 0)
            
        if opacity > 150:
            glow = temp_img.filter(ImageFilter.GaussianBlur(radius=10))
            canvas_img.paste(glow, (0, 0), mask=glow)
            glow2 = temp_img.filter(ImageFilter.GaussianBlur(radius=3))
            canvas_img.paste(glow2, (0, 0), mask=glow2)
            
        canvas_img.paste(temp_img, (0, 0), mask=temp_img)

    def draw_text_chromatic_glitch(canvas_img, lines, frame_idx, total_frames):
        """赛博RGB色差分离 - 剧烈分离与抖动"""
        random.seed(42 + frame_idx * 10)
        is_major_glitch = random.random() < 0.15
        
        if is_major_glitch:
            offset_r = (random.randint(-15, 15), random.randint(-5, 5))
            offset_g = (random.randint(-5, 5), random.randint(-10, 10))
            offset_b = (random.randint(-15, 15), random.randint(-5, 5))
        else:
            offset_r = (random.randint(-3, 3), random.randint(-1, 1))
            offset_g = (0, 0)
            offset_b = (random.randint(-3, 3), random.randint(-1, 1))
        random.seed()
        
        layer_r = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
        layer_g = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
        layer_b = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
        
        draw_text_standard(layer_r, lines, (255, 0, 0, 255), offset_r[0], offset_r[1])
        draw_text_standard(layer_g, lines, (0, 255, 0, 255), offset_g[0], offset_g[1])
        draw_text_standard(layer_b, lines, (0, 0, 255, 255), offset_b[0], offset_b[1])
        
        arr_r = np.array(layer_r)
        arr_g = np.array(layer_g)
        arr_b = np.array(layer_b)
        
        merged_arr = np.maximum(np.maximum(arr_r, arr_g), arr_b)
        merged_img = Image.fromarray(merged_arr, 'RGBA')
        
        if is_major_glitch:
            w, h = merged_img.size
            slice_y = random.randint(0, h - 20)
            slice_h = random.randint(10, 30)
            slice_x_offset = random.randint(-20, 20)
            slice_img = merged_img.crop((0, slice_y, w, slice_y + slice_h))
            merged_img.paste(slice_img, (slice_x_offset, slice_y))
            
        canvas_img.paste(merged_img, (0, 0), mask=merged_img)

    def draw_text_cinematic_pop(canvas_img, lines, frame_idx, total_frames):
        """电影级果冻弹入 - 从0放大到1.2再回弹到1.0"""
        progress = frame_idx / max(total_frames - 1, 1)
        
        def ease_out_back(x):
            c1 = 1.70158
            c3 = c1 + 1
            return 1 + c3 * math.pow(x - 1, 3) + c1 * math.pow(x - 1, 2)
            
        if progress < 0.6:
            p = progress / 0.6
            scale = max(0.01, ease_out_back(p))
        else:
            scale = 1.0
            
        temp_img = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
        if mode == 'rainbow':
            draw_text_standard(temp_img, lines, (0,0,0,255), 0, 0)
            temp_img = apply_rainbow_to_text(temp_img)
        else:
            draw_text_standard(temp_img, lines, current_color, 0, 0)
            
        if abs(scale - 1.0) > 0.01 and scale > 0:
            new_w = int(width_pixels * scale)
            new_h = int(canvas_height * scale)
            new_w = min(new_w, width_pixels * 3)
            new_h = min(new_h, canvas_height * 3)
            if new_w > 0 and new_h > 0:
                resized = temp_img.resize((new_w, new_h), Image.LANCZOS)
                paste_x = (width_pixels - new_w) // 2
                paste_y = (canvas_height - new_h) // 2
                canvas_img.paste(resized, (paste_x, paste_y), mask=resized)
        else:
            canvas_img.paste(temp_img, (0, 0), mask=temp_img)

    def draw_text_highlighter(canvas_img, lines, frame_idx, total_frames):
        """马克笔划线高亮 - 背景从左到右长出高亮色带"""
        progress = frame_idx / max(total_frames - 1, 1)
        draw_obj = ImageDraw.Draw(canvas_img)
        full_text = '\n'.join(lines)
        bbox = draw_obj.multiline_textbbox((0, 0), full_text, font=font)
        
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x_start = (width_pixels - text_width) // 2
        y_start = (canvas_height - text_height) // 2
        
        padding_x = 15
        padding_y = 5
        
        hl_color = (255, 215, 0, 200)
        if mode != 'solid':
            hl_color = (*current_color[:3], 200)
            
        current_hl_width = int((text_width + padding_x * 2) * progress)
        
        if current_hl_width > 0:
            hl_rect = [
                x_start - padding_x,
                y_start - padding_y,
                x_start - padding_x + current_hl_width,
                y_start + text_height + padding_y
            ]
            bg_layer = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
            bg_draw = ImageDraw.Draw(bg_layer)
            bg_draw.rounded_rectangle(hl_rect, radius=8, fill=hl_color)
            canvas_img.paste(bg_layer, (0, 0), mask=bg_layer)
            
        temp_img = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
        if mode == 'rainbow':
            draw_text_standard(temp_img, lines, (0,0,0,255), 0, 0)
            temp_img = apply_rainbow_to_text(temp_img)
        else:
            draw_text_standard(temp_img, lines, current_color, 0, 0)
            
        canvas_img.paste(temp_img, (0, 0), mask=temp_img)

    def make_standard_text_layer(lines, color=None):
        text_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        if mode == 'rainbow':
            draw_text_standard(text_layer, lines, (0, 0, 0, 255), 0, 0)
            return apply_rainbow_to_text(text_layer)
        draw_text_standard(text_layer, lines, color or current_color, 0, 0)
        return text_layer

    def draw_text_prism_sweep(canvas_img, lines, frame_idx, total_frames):
        """棱镜扫光：文字内流动的斜向彩色光谱，并叠加白色高光。"""
        progress = frame_idx / max(total_frames - 1, 1)
        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]
        if not text_mask.getbbox():
            return

        spectrum = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        spectrum_draw = ImageDraw.Draw(spectrum)
        band_width = max(16, width_pixels // 5)
        offset = int(progress * (width_pixels + band_width * 2)) - band_width
        colors = [
            (255, 55, 110, 255),
            (255, 210, 70, 255),
            (70, 255, 180, 255),
            (60, 180, 255, 255),
            (190, 90, 255, 255),
        ]
        for x in range(-band_width * 2, width_pixels + band_width * 2, max(8, band_width // 2)):
            color = colors[((x - offset) // max(1, band_width // 2)) % len(colors)]
            spectrum_draw.polygon(
                [
                    (x + offset, 0),
                    (x + offset + band_width, 0),
                    (x + offset - band_width, canvas_height),
                    (x + offset - band_width * 2, canvas_height),
                ],
                fill=color
            )
        spectrum.putalpha(text_mask)

        glow = spectrum.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 16)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * 0.35))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)
        canvas_img.paste(spectrum, (0, 0), mask=spectrum)

        shine = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        shine_draw = ImageDraw.Draw(shine)
        shine_x = int(progress * (width_pixels + band_width * 2)) - band_width
        shine_draw.polygon(
            [
                (shine_x, 0),
                (shine_x + max(8, band_width // 4), 0),
                (shine_x - band_width, canvas_height),
                (shine_x - band_width - max(8, band_width // 4), canvas_height),
            ],
            fill=(255, 255, 255, 160)
        )
        shine.putalpha(ImageChops.multiply(shine.split()[3], text_mask))
        canvas_img.paste(shine, (0, 0), mask=shine)

    def draw_text_laser_scan(canvas_img, lines, frame_idx, total_frames):
        """激光扫描：红色扫描线切过文字，命中区域出现热亮边缘。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base = make_standard_text_layer(lines, (*current_color[:3], 110))
        canvas_img.paste(base, (0, 0), mask=base)

        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]
        bbox = text_mask.getbbox()
        if not bbox:
            return

        scan_y = int(bbox[1] - dynamic_line_height * 0.25 + progress * ((bbox[3] - bbox[1]) + dynamic_line_height * 0.5))
        band_h = max(8, dynamic_line_height // 5)
        band_mask = Image.new('L', (width_pixels, canvas_height), 0)
        band_draw = ImageDraw.Draw(band_mask)
        band_draw.rectangle((0, scan_y - band_h, width_pixels, scan_y + band_h), fill=255)
        band_mask = ImageChops.multiply(band_mask.filter(ImageFilter.GaussianBlur(max(2, band_h // 3))), text_mask)

        hot_layer = Image.new('RGBA', (width_pixels, canvas_height), (255, 40, 40, 0))
        hot_layer.putalpha(band_mask.point(lambda p: min(255, int(p * 1.45))))
        canvas_img.paste(hot_layer, (0, 0), mask=hot_layer)

        laser = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        laser_draw = ImageDraw.Draw(laser)
        laser_draw.line((bbox[0] - 20, scan_y, bbox[2] + 20, scan_y), fill=(255, 245, 180, 240), width=max(2, dynamic_line_height // 22))
        laser_draw.line((bbox[0] - 20, scan_y + 2, bbox[2] + 20, scan_y + 2), fill=(255, 40, 40, 190), width=max(1, dynamic_line_height // 28))
        laser_glow = laser.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 18)))
        canvas_img.paste(laser_glow, (0, 0), mask=laser_glow)
        canvas_img.paste(laser, (0, 0), mask=laser)

    def draw_text_echo_shadow(canvas_img, lines, frame_idx, total_frames):
        """回声残影：多层彩色拖影绕着文字呼吸移动。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base_radius = max(3, dynamic_line_height // 12)
        echo_specs = [
            (255, 70, 120),
            (70, 230, 255),
            (255, 220, 70),
            (160, 100, 255),
        ]
        for idx, rgb in enumerate(echo_specs):
            phase = progress * math.pi * 2 + idx * math.pi / 2
            offset = int(base_radius * (1.4 + idx * 0.45))
            dx = int(math.cos(phase) * offset)
            dy = int(math.sin(phase) * offset)
            alpha = max(45, 140 - idx * 22)
            echo_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
            draw_text_standard(echo_layer, lines, (*rgb, alpha), dx, dy)
            echo_layer = echo_layer.filter(ImageFilter.GaussianBlur(0.5 + idx * 0.35))
            canvas_img.paste(echo_layer, (0, 0), mask=echo_layer)

        base = make_standard_text_layer(lines, current_color)
        canvas_img.paste(base, (0, 0), mask=base)

    def draw_text_pixel_burst(canvas_img, lines, frame_idx, total_frames):
        """像素爆散：文字像素块从中心炸开，再回到完整文字。"""
        progress = frame_idx / max(total_frames - 1, 1)
        burst = math.sin(progress * math.pi)
        base = make_standard_text_layer(lines, current_color)
        bbox = base.getbbox()
        if not bbox:
            return

        if burst < 0.08:
            canvas_img.paste(base, (0, 0), mask=base)
            return

        pixel_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        pixel_draw = ImageDraw.Draw(pixel_layer)
        rng = random.Random(11400)
        step = max(6, dynamic_line_height // 8)
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        alpha_scale = 1.0 - burst * 0.25
        base_alpha = base.split()[3]

        for y in range(bbox[1], bbox[3], step):
            for x in range(bbox[0], bbox[2], step):
                sample_box = (
                    max(0, x),
                    max(0, y),
                    min(width_pixels, x + step),
                    min(canvas_height, y + step)
                )
                if not base_alpha.crop(sample_box).getbbox():
                    continue
                angle = math.atan2(y - cy, x - cx)
                distance = rng.uniform(step * 0.5, step * 4.2) * burst
                jitter_angle = angle + rng.uniform(-0.65, 0.65)
                px = int(x + math.cos(jitter_angle) * distance)
                py = int(y + math.sin(jitter_angle) * distance)
                size = max(3, int(step * (1.0 - burst * 0.35)))
                hue = (progress + (x + y) / max(width_pixels + canvas_height, 1)) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
                alpha = int(230 * alpha_scale)
                pixel_draw.rectangle((px, py, px + size, py + size), fill=(int(r * 255), int(g * 255), int(b * 255), alpha))

        ghost_alpha = base_alpha.point(lambda p: int(p * (1.0 - burst) * 0.45))
        ghost = base.copy()
        ghost.putalpha(ghost_alpha)
        canvas_img.paste(ghost, (0, 0), mask=ghost)
        canvas_img.paste(pixel_layer, (0, 0), mask=pixel_layer)

    def draw_text_hologram_scan(canvas_img, lines, frame_idx, total_frames):
        """全息扫描：青紫色偏移、扫描线和短促横向数据撕裂。"""
        progress = frame_idx / max(total_frames - 1, 1)
        rng = random.Random(13100 + frame_idx)
        base = make_standard_text_layer(lines, (180, 255, 255, 190))
        bbox = base.getbbox()
        if not bbox:
            return

        glow = base.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 14)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * 0.5))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)

        cyan = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        magenta = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        jitter = 2 + int(4 * math.sin(progress * math.pi * 2) ** 2)
        draw_text_standard(cyan, lines, (40, 255, 255, 190), -jitter, 0)
        draw_text_standard(magenta, lines, (255, 70, 210, 150), jitter, rng.randint(-1, 1))
        canvas_img.paste(cyan, (0, 0), mask=cyan)
        canvas_img.paste(magenta, (0, 0), mask=magenta)
        canvas_img.paste(base, (0, 0), mask=base)

        scan = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        scan_draw = ImageDraw.Draw(scan)
        for y in range(bbox[1] - 8, bbox[3] + 8, max(4, dynamic_line_height // 18)):
            alpha = 45 + int(40 * math.sin(progress * math.pi * 2 + y * 0.2))
            scan_draw.line((bbox[0] - 12, y, bbox[2] + 12, y), fill=(160, 255, 255, max(20, alpha)), width=1)

        sweep_y = int(bbox[1] + progress * max(1, bbox[3] - bbox[1]))
        scan_draw.rectangle((bbox[0] - 18, sweep_y - 4, bbox[2] + 18, sweep_y + 4), fill=(255, 255, 255, 125))
        scan.putalpha(ImageChops.multiply(scan.split()[3], base.split()[3].filter(ImageFilter.GaussianBlur(1))))
        canvas_img.paste(scan, (0, 0), mask=scan)

        for _ in range(3):
            y = rng.randint(bbox[1], max(bbox[1], bbox[3] - 3))
            h = rng.randint(2, max(3, dynamic_line_height // 14))
            x_shift = rng.randint(-18, 18)
            stripe = base.crop((bbox[0], y, bbox[2], min(canvas_height, y + h)))
            canvas_img.paste(stripe, (bbox[0] + x_shift, y), mask=stripe)

    def draw_text_plasma_wave(canvas_img, lines, frame_idx, total_frames):
        """等离子流体：文字内部流动热色云团，外缘带电光晕。"""
        progress = frame_idx / max(total_frames - 1, 1)
        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]
        if not text_mask.getbbox():
            return

        plasma = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        plasma_draw = ImageDraw.Draw(plasma)
        step = max(3, width_pixels // 80)
        for y in range(0, canvas_height, step):
            for x in range(0, width_pixels, step):
                v = (
                    math.sin(x * 0.045 + progress * math.pi * 4) +
                    math.sin(y * 0.055 - progress * math.pi * 3) +
                    math.sin((x + y) * 0.032 + progress * math.pi * 2)
                ) / 3.0
                hue = (0.72 + v * 0.18 + progress * 0.28) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
                plasma_draw.rectangle((x, y, x + step, y + step), fill=(int(r * 255), int(g * 255), int(b * 255), 255))

        plasma = plasma.filter(ImageFilter.GaussianBlur(1.2))
        plasma.putalpha(text_mask)
        glow = plasma.filter(ImageFilter.GaussianBlur(max(3, dynamic_line_height // 10)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * 0.42))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)
        canvas_img.paste(plasma, (0, 0), mask=plasma)

        edge = text_mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.5))
        edge_layer = Image.new('RGBA', (width_pixels, canvas_height), (255, 255, 255, 0))
        edge_layer.putalpha(edge.point(lambda p: min(180, p * 2)))
        canvas_img.paste(edge_layer, (0, 0), mask=edge_layer)

    def draw_text_thunder_crack(canvas_img, lines, frame_idx, total_frames):
        """雷裂闪电：文字上闪现裂纹和电弧。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base = make_standard_text_layer(lines, (*current_color[:3], 190))
        bbox = base.getbbox()
        if not bbox:
            return

        glow = base.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 16)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * 0.32))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)
        canvas_img.paste(base, (0, 0), mask=base)

        flash = math.sin(progress * math.pi * 4) > 0.15
        crack_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        crack_draw = ImageDraw.Draw(crack_layer)
        rng = random.Random(15100 + int(progress * 6))
        bolt_count = 3 if flash else 2
        for bolt_idx in range(bolt_count):
            x = rng.randint(bbox[0], bbox[2])
            y = bbox[1] - rng.randint(0, max(2, dynamic_line_height // 8))
            points = [(x, y)]
            segments = 7
            for seg in range(segments):
                y = bbox[1] + int((bbox[3] - bbox[1]) * (seg + 1) / segments)
                x += rng.randint(-max(8, dynamic_line_height // 5), max(8, dynamic_line_height // 5))
                x = max(bbox[0] - 10, min(bbox[2] + 10, x))
                points.append((x, y))
            crack_draw.line(points, fill=(150, 235, 255, 210), width=max(1, dynamic_line_height // 30))
            if flash:
                crack_draw.line(points, fill=(255, 255, 255, 255), width=max(1, dynamic_line_height // 45))
        crack_glow = crack_layer.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 18)))
        canvas_img.paste(crack_glow, (0, 0), mask=crack_glow)
        canvas_img.paste(crack_layer, (0, 0), mask=crack_layer)

    def draw_text_vortex_warp(canvas_img, lines, frame_idx, total_frames):
        """漩涡扭曲：把文字横向切片，按螺旋波形错位。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base = make_standard_text_layer(lines, current_color)
        bbox = base.getbbox()
        if not bbox:
            return

        warped = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        slice_h = max(3, dynamic_line_height // 18)
        center_y = (bbox[1] + bbox[3]) / 2
        for y in range(0, canvas_height, slice_h):
            distance = (y - center_y) / max(1, (bbox[3] - bbox[1]))
            twist = math.sin(progress * math.pi * 2 + distance * math.pi * 5)
            envelope = max(0.15, 1.0 - abs(distance) * 1.2)
            dx = int(twist * envelope * dynamic_line_height * 0.24)
            stripe = base.crop((0, y, width_pixels, min(canvas_height, y + slice_h)))
            warped.paste(stripe, (dx, y), mask=stripe)

        rgb_echo = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw_text_standard(rgb_echo, lines, (50, 220, 255, 130), -max(2, dynamic_line_height // 30), 0)
        draw_text_standard(rgb_echo, lines, (255, 60, 180, 120), max(2, dynamic_line_height // 30), 0)
        rgb_echo = rgb_echo.filter(ImageFilter.GaussianBlur(0.8))
        canvas_img.paste(rgb_echo, (0, 0), mask=rgb_echo)
        glow = warped.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 16)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * 0.36))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)
        canvas_img.paste(warped, (0, 0), mask=warped)

    def draw_text_comet_trail(canvas_img, lines, frame_idx, total_frames):
        """彗星拖尾：文字从左侧飞入，身后留下发光残影。"""
        progress = frame_idx / max(total_frames - 1, 1)
        ease = 1 - math.pow(1 - min(progress / 0.72, 1.0), 3)
        start_x = -int(width_pixels * 0.65)
        offset_x = int(start_x * (1 - ease))
        offset_y = int(math.sin(progress * math.pi * 2) * dynamic_line_height * 0.08 * (1 - ease))
        trail_steps = 7

        for idx in range(trail_steps, 0, -1):
            trail_progress = idx / trail_steps
            dx = offset_x - int(trail_progress * dynamic_line_height * 0.42)
            dy = offset_y + int(math.sin(progress * math.pi * 3 + idx) * dynamic_line_height * 0.035)
            alpha = int(135 * (1 - trail_progress * 0.75))
            hue = (0.55 + trail_progress * 0.18 + progress * 0.12) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 0.9, 1.0)
            trail = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
            draw_text_standard(trail, lines, (int(r * 255), int(g * 255), int(b * 255), alpha), dx, dy)
            trail = trail.filter(ImageFilter.GaussianBlur(0.6 + trail_progress * 1.4))
            canvas_img.paste(trail, (0, 0), mask=trail)

        main_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw_text_standard(main_layer, lines, (255, 255, 255, 255), offset_x, offset_y)
        if progress > 0.72:
            pulse = 0.55 + 0.45 * math.sin((progress - 0.72) / 0.28 * math.pi)
            burst = main_layer.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 15)))
            burst_alpha = burst.split()[3].point(lambda p: int(p * 0.35 * pulse))
            burst.putalpha(burst_alpha)
            canvas_img.paste(burst, (0, 0), mask=burst)
        canvas_img.paste(main_layer, (0, 0), mask=main_layer)

    def draw_text_chrome_glass(canvas_img, lines, frame_idx, total_frames):
        """液态铬玻璃：银色镜面渐变、边缘高光和移动反射带。"""
        progress = frame_idx / max(total_frames - 1, 1)
        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]
        bbox = text_mask.getbbox()
        if not bbox:
            return

        wobble_dx = int(math.sin(progress * math.pi * 2) * max(3, dynamic_line_height // 18))
        shadow_a = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        shadow_b = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw_text_standard(shadow_a, lines, (80, 220, 255, 150), -wobble_dx - 2, 0)
        draw_text_standard(shadow_b, lines, (255, 255, 255, 120), wobble_dx + 2, 0)
        shadow_a = shadow_a.filter(ImageFilter.GaussianBlur(1.0))
        shadow_b = shadow_b.filter(ImageFilter.GaussianBlur(1.0))
        canvas_img.paste(shadow_a, (0, 0), mask=shadow_a)
        canvas_img.paste(shadow_b, (0, 0), mask=shadow_b)

        chrome = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        chrome_draw = ImageDraw.Draw(chrome)
        for y in range(canvas_height):
            t = y / max(canvas_height - 1, 1)
            wave = 0.5 + 0.5 * math.sin(t * math.pi * 10 + progress * math.pi * 4)
            shade = int(55 + 145 * (1 - abs(0.5 - t) * 1.5) + 70 * wave)
            shade = max(35, min(245, shade))
            cool_shift = int(30 * math.sin(progress * math.pi * 2 + y * 0.04))
            chrome_draw.line(
                (0, y, width_pixels, y),
                fill=(max(30, shade - cool_shift), min(255, shade + 8), min(255, shade + 24 + cool_shift), 255)
            )

        reflection = Image.new('L', (width_pixels, canvas_height), 0)
        ref_draw = ImageDraw.Draw(reflection)
        band_w = max(14, width_pixels // 8)
        x0 = int(progress * (width_pixels + band_w * 2)) - band_w
        ref_draw.polygon(
            [(x0, 0), (x0 + band_w, 0), (x0 - band_w, canvas_height), (x0 - band_w * 2, canvas_height)],
            fill=165
        )
        chrome.putalpha(text_mask)
        canvas_img.paste(chrome, (wobble_dx, 0), mask=chrome)

        highlight = Image.new('RGBA', (width_pixels, canvas_height), (255, 255, 255, 0))
        highlight.putalpha(ImageChops.multiply(reflection.filter(ImageFilter.GaussianBlur(1)), text_mask))
        canvas_img.paste(highlight, (0, 0), mask=highlight)

        blade = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        blade_draw = ImageDraw.Draw(blade)
        blade_x = int((1 - progress) * (width_pixels + band_w * 2)) - band_w
        blade_draw.rectangle((blade_x, bbox[1] - 8, blade_x + max(5, band_w // 3), bbox[3] + 8), fill=(120, 230, 255, 190))
        blade = blade.filter(ImageFilter.GaussianBlur(1.5))
        blade.putalpha(ImageChops.multiply(blade.split()[3], text_mask))
        canvas_img.paste(blade, (0, 0), mask=blade)

        liquid_lines = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        liquid_draw = ImageDraw.Draw(liquid_lines)
        for line_idx in range(4):
            y = int(bbox[1] + (bbox[3] - bbox[1]) * ((progress + line_idx * 0.23) % 1.0))
            alpha = 90 + line_idx * 24
            liquid_draw.line((bbox[0] - 8, y, bbox[2] + 8, y), fill=(255, 255, 255, alpha), width=max(1, dynamic_line_height // 34))
        liquid_lines = liquid_lines.filter(ImageFilter.GaussianBlur(0.8))
        liquid_lines.putalpha(ImageChops.multiply(liquid_lines.split()[3], text_mask))
        canvas_img.paste(liquid_lines, (0, 0), mask=liquid_lines)

        edge = text_mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.4))
        edge_layer = Image.new('RGBA', (width_pixels, canvas_height), (245, 255, 255, 0))
        edge_layer.putalpha(edge.point(lambda p: min(210, p * 2)))
        canvas_img.paste(edge_layer, (0, 0), mask=edge_layer)

    def draw_text_aurora_ribbon(canvas_img, lines, frame_idx, total_frames):
        """极光丝带：文字内部流动极光色带，外侧有柔和光晕。"""
        progress = frame_idx / max(total_frames - 1, 1)
        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]
        if not text_mask.getbbox():
            return

        aurora = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(aurora)
        step = max(3, canvas_height // 70)
        for y in range(-step, canvas_height + step, step):
            band = 0.5 + 0.5 * math.sin(y * 0.055 + progress * math.pi * 4)
            hue = (0.42 + band * 0.26 + progress * 0.14) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 0.82, 1.0)
            left_wave = int(math.sin(y * 0.035 + progress * math.pi * 3) * dynamic_line_height * 0.18)
            right_wave = int(math.sin(y * 0.028 - progress * math.pi * 2) * dynamic_line_height * 0.22)
            draw.polygon(
                [
                    (left_wave, y),
                    (width_pixels + right_wave, y + step),
                    (width_pixels - right_wave, y + step * 5),
                    (-left_wave, y + step * 4),
                ],
                fill=(int(r * 255), int(g * 255), int(b * 255), 215),
            )

        aurora = aurora.filter(ImageFilter.GaussianBlur(1.4))
        aurora.putalpha(text_mask)
        glow = aurora.filter(ImageFilter.GaussianBlur(max(3, dynamic_line_height // 10)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * 0.46))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)
        canvas_img.paste(aurora, (0, 0), mask=aurora)

        edge = text_mask.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.4))
        edge_layer = Image.new('RGBA', (width_pixels, canvas_height), (220, 255, 245, 0))
        edge_layer.putalpha(edge.point(lambda p: min(175, p * 2)))
        canvas_img.paste(edge_layer, (0, 0), mask=edge_layer)

    def draw_text_strobe_cut(canvas_img, lines, frame_idx, total_frames):
        """频闪切片：快速横向切片、白闪和RGB错位。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base = make_standard_text_layer(lines, current_color)
        bbox = base.getbbox()
        if not bbox:
            return

        rng = random.Random(17100 + frame_idx)
        cut_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        slice_h = max(3, dynamic_line_height // 12)
        for y in range(bbox[1] - slice_h, bbox[3] + slice_h, slice_h):
            shift = rng.randint(-max(5, dynamic_line_height // 8), max(5, dynamic_line_height // 8))
            stripe = base.crop((0, max(0, y), width_pixels, min(canvas_height, y + slice_h)))
            cut_layer.paste(stripe, (shift, max(0, y)), mask=stripe)

        rgb = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        flash_strength = 0.5 + 0.5 * math.sin(progress * math.pi * 8)
        draw_text_standard(rgb, lines, (255, 30, 90, int(120 + 90 * flash_strength)), -3, 0)
        draw_text_standard(rgb, lines, (40, 235, 255, int(120 + 90 * (1 - flash_strength))), 3, 0)
        canvas_img.paste(rgb, (0, 0), mask=rgb)
        canvas_img.paste(cut_layer, (0, 0), mask=cut_layer)

        if frame_idx % 4 == 1:
            flash = Image.new('RGBA', (width_pixels, canvas_height), (255, 255, 255, 0))
            flash.putalpha(base.split()[3].point(lambda p: int(p * 0.42)))
            canvas_img.paste(flash, (0, 0), mask=flash)

    def draw_text_sandstorm(canvas_img, lines, frame_idx, total_frames):
        """沙暴聚散：文字颗粒从四周聚合，再随风散开。"""
        progress = frame_idx / max(total_frames - 1, 1)
        scatter = math.sin(progress * math.pi)
        base = make_standard_text_layer(lines, (240, 218, 150, 235))
        alpha = base.split()[3]
        bbox = alpha.getbbox()
        if not bbox:
            return

        ghost_alpha = alpha.point(lambda p: int(p * (1 - scatter) * 0.45))
        ghost = base.copy()
        ghost.putalpha(ghost_alpha)
        canvas_img.paste(ghost, (0, 0), mask=ghost)

        particles = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(particles)
        rng = random.Random(18100)
        step = max(5, dynamic_line_height // 10)
        wind = int(math.sin(progress * math.pi * 2) * dynamic_line_height * 0.22)
        for y in range(bbox[1], bbox[3], step):
            for x in range(bbox[0], bbox[2], step):
                sample = alpha.crop((x, y, min(width_pixels, x + step), min(canvas_height, y + step)))
                if not sample.getbbox():
                    continue
                angle = math.atan2(y - (bbox[1] + bbox[3]) / 2, x - (bbox[0] + bbox[2]) / 2)
                distance = rng.uniform(step * 0.6, step * 5.0) * scatter
                px = int(x + math.cos(angle) * distance + wind * scatter + rng.uniform(-2, 2))
                py = int(y + math.sin(angle) * distance * 0.55 + rng.uniform(-2, 2))
                size = max(2, int(step * (0.45 + rng.random() * 0.55)))
                color_jitter = rng.randint(-20, 30)
                draw.rectangle(
                    (px, py, px + size, py + size),
                    fill=(max(90, 218 + color_jitter), max(70, 178 + color_jitter), max(35, 95 + color_jitter), 210),
                )
        particles = particles.filter(ImageFilter.GaussianBlur(0.35))
        canvas_img.paste(particles, (0, 0), mask=particles)

    def draw_text_magnetic_flip(canvas_img, lines, frame_idx, total_frames):
        """磁场翻折：文字切片被磁场吸引，左右摆动并产生极性色影。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base = make_standard_text_layer(lines, current_color)
        bbox = base.getbbox()
        if not bbox:
            return

        field = math.sin(progress * math.pi * 2)
        slice_h = max(4, dynamic_line_height // 10)
        warped = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        center_y = (bbox[1] + bbox[3]) / 2
        for y in range(0, canvas_height, slice_h):
            distance = (y - center_y) / max(1, (bbox[3] - bbox[1]))
            flip = math.sin(progress * math.pi * 2 + distance * math.pi * 3)
            dx = int(flip * dynamic_line_height * 0.16)
            scale_x = 1.0 + abs(flip) * 0.16
            stripe = base.crop((0, y, width_pixels, min(canvas_height, y + slice_h)))
            new_w = max(1, int(width_pixels * scale_x))
            resized = stripe.resize((new_w, stripe.height), Image.Resampling.BICUBIC)
            paste_x = dx - (new_w - width_pixels) // 2
            warped.paste(resized, (paste_x, y), mask=resized)

        pole = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw_text_standard(pole, lines, (255, 70, 120, 135), int(-field * 8) - 3, 0)
        draw_text_standard(pole, lines, (60, 230, 255, 135), int(field * 8) + 3, 0)
        pole = pole.filter(ImageFilter.GaussianBlur(0.8))
        canvas_img.paste(pole, (0, 0), mask=pole)
        glow = warped.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 18)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * 0.34))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)
        canvas_img.paste(warped, (0, 0), mask=warped)

    def draw_text_ink_bleed(canvas_img, lines, frame_idx, total_frames):
        """墨水晕染：文字由湿墨扩散成形，边缘有墨滴渗出。"""
        progress = frame_idx / max(total_frames - 1, 1)
        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]
        bbox = text_mask.getbbox()
        if not bbox:
            return

        blur_radius = max(0.4, (1 - progress) * dynamic_line_height * 0.16)
        bleed_mask = text_mask.filter(ImageFilter.GaussianBlur(blur_radius))
        threshold = int(60 + progress * 85)
        bleed_mask = bleed_mask.point(lambda p: 255 if p > threshold else int(p * 0.6))

        ink = Image.new('RGBA', (width_pixels, canvas_height), (12, 18, 30, 0))
        ink.putalpha(bleed_mask.point(lambda p: min(245, int(p * (0.72 + progress * 0.35)))))
        canvas_img.paste(ink, (0, 0), mask=ink)

        inner = Image.new('RGBA', (width_pixels, canvas_height), (40, 70, 110, 0))
        inner.putalpha(text_mask.point(lambda p: int(p * min(1.0, progress * 1.4))))
        canvas_img.paste(inner, (0, 0), mask=inner)

        rng = random.Random(19100)
        drops = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(drops)
        drop_count = 10 if fast_preview else 18
        for idx in range(drop_count):
            x = rng.randint(bbox[0], max(bbox[0], bbox[2] - 1))
            base_y = bbox[3] - rng.randint(0, max(1, (bbox[3] - bbox[1]) // 3))
            fall = int(((progress + idx * 0.07) % 1.0) * dynamic_line_height * 0.38)
            radius = rng.randint(2, max(3, dynamic_line_height // 20))
            alpha_val = int(170 * (1 - ((progress + idx * 0.07) % 1.0) * 0.45))
            draw.ellipse((x - radius, base_y + fall, x + radius, base_y + fall + radius * 2), fill=(8, 14, 26, alpha_val))
        drops = drops.filter(ImageFilter.GaussianBlur(0.4))
        canvas_img.paste(drops, (0, 0), mask=drops)

    def draw_text_solar_flare(canvas_img, lines, frame_idx, total_frames):
        """太阳耀斑：热光球横穿文字，带径向闪光和暖色辉光。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base = make_standard_text_layer(lines, (255, 230, 150, 230))
        bbox = base.getbbox()
        if not bbox:
            return

        glow = base.filter(ImageFilter.GaussianBlur(max(4, dynamic_line_height // 8)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * 0.48))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)

        flare_x = int(bbox[0] - dynamic_line_height * 0.4 + progress * ((bbox[2] - bbox[0]) + dynamic_line_height * 0.8))
        flare_y = int((bbox[1] + bbox[3]) / 2 + math.sin(progress * math.pi * 2) * dynamic_line_height * 0.12)
        flare = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(flare)
        radius = max(8, dynamic_line_height // 4)
        for ring in range(5, 0, -1):
            r = radius * ring / 2
            alpha = int(36 + 38 * (6 - ring))
            draw.ellipse((flare_x - r, flare_y - r, flare_x + r, flare_y + r), fill=(255, 155, 45, alpha))
        draw.line((bbox[0] - 30, flare_y, bbox[2] + 30, flare_y), fill=(255, 245, 180, 170), width=max(1, dynamic_line_height // 26))
        draw.line((flare_x, bbox[1] - 20, flare_x, bbox[3] + 20), fill=(255, 210, 90, 130), width=max(1, dynamic_line_height // 34))
        flare = flare.filter(ImageFilter.GaussianBlur(1.0))
        canvas_img.paste(flare, (0, 0), mask=flare)

        hot = Image.new('RGBA', (width_pixels, canvas_height), (255, 120, 30, 0))
        band = Image.new('L', (width_pixels, canvas_height), 0)
        band_draw = ImageDraw.Draw(band)
        band_draw.rectangle((flare_x - radius, 0, flare_x + radius, canvas_height), fill=210)
        hot.putalpha(ImageChops.multiply(band.filter(ImageFilter.GaussianBlur(radius // 2)), base.split()[3]))
        canvas_img.paste(base, (0, 0), mask=base)
        canvas_img.paste(hot, (0, 0), mask=hot)

    def draw_text_pulse_ring(canvas_img, lines, frame_idx, total_frames):
        """脉冲环：扩散圆环从文字中心向外传播，文字同步发光。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base = make_standard_text_layer(lines, current_color)
        bbox = base.getbbox()
        if not bbox:
            return

        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        max_radius = max(bbox[2] - bbox[0], bbox[3] - bbox[1]) * 0.7
        rings = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(rings)
        for idx in range(3):
            phase = (progress + idx / 3) % 1.0
            radius = max_radius * phase
            alpha = int(210 * (1 - phase))
            if alpha <= 0:
                continue
            color = (80 + idx * 50, 210, 255, alpha)
            width = max(2, dynamic_line_height // 28)
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=color, width=width)
        rings = rings.filter(ImageFilter.GaussianBlur(0.7))
        canvas_img.paste(rings, (0, 0), mask=rings)

        pulse = 0.55 + 0.45 * math.sin(progress * math.pi * 2)
        glow = base.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 12)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * (0.28 + pulse * 0.35)))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)
        canvas_img.paste(base, (0, 0), mask=base)

    def draw_text_electric_outline(canvas_img, lines, frame_idx, total_frames):
        """电光描边：文字边缘闪烁电弧，随机火花沿轮廓跳动。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base = make_standard_text_layer(lines, (*current_color[:3], 150))
        alpha = base.split()[3]
        bbox = alpha.getbbox()
        if not bbox:
            return

        edge = alpha.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(0.6))
        edge_layer = Image.new('RGBA', (width_pixels, canvas_height), (90, 225, 255, 0))
        flicker = 0.7 + 0.3 * math.sin(progress * math.pi * 10)
        edge_layer.putalpha(edge.point(lambda p: min(255, int(p * 2.5 * flicker))))
        edge_glow = edge_layer.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 16)))
        glow_alpha = edge_glow.split()[3].point(lambda p: int(p * 0.45))
        edge_glow.putalpha(glow_alpha)
        canvas_img.paste(edge_glow, (0, 0), mask=edge_glow)
        canvas_img.paste(base, (0, 0), mask=base)
        canvas_img.paste(edge_layer, (0, 0), mask=edge_layer)

        rng = random.Random(20100 + frame_idx)
        sparks = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(sparks)
        for _ in range(10 if fast_preview else 18):
            x = rng.randint(bbox[0], bbox[2])
            y = rng.randint(bbox[1], bbox[3])
            if alpha.getpixel((min(width_pixels - 1, x), min(canvas_height - 1, y))) < 20:
                continue
            length = rng.randint(max(5, dynamic_line_height // 16), max(8, dynamic_line_height // 7))
            angle = rng.uniform(0, math.pi * 2)
            x2 = x + int(math.cos(angle) * length)
            y2 = y + int(math.sin(angle) * length)
            draw.line((x, y, x2, y2), fill=(210, 255, 255, rng.randint(130, 240)), width=1)
        sparks = sparks.filter(ImageFilter.GaussianBlur(0.4))
        canvas_img.paste(sparks, (0, 0), mask=sparks)

    def draw_text_photon_stream(canvas_img, lines, frame_idx, total_frames):
        """光子流：细密光线穿过字形内部，像粒子束沿文字流动。"""
        progress = frame_idx / max(total_frames - 1, 1)
        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]
        bbox = text_mask.getbbox()
        if not bbox:
            return

        stream = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(stream)
        spacing = max(10, dynamic_line_height // 7)
        travel = int(progress * spacing * 2)
        for y in range(bbox[1] - spacing, bbox[3] + spacing, spacing):
            for idx in range(-2, 8):
                x = bbox[0] + idx * spacing * 2 + travel
                y2 = y + int(math.sin(progress * math.pi * 2 + idx) * dynamic_line_height * 0.04)
                draw.line((x, y2, x + spacing * 2, y2 - spacing), fill=(120, 240, 255, 180), width=max(1, dynamic_line_height // 40))
                draw.ellipse((x + spacing * 2 - 2, y2 - spacing - 2, x + spacing * 2 + 3, y2 - spacing + 3), fill=(255, 255, 255, 220))
        stream = stream.filter(ImageFilter.GaussianBlur(0.5))
        stream.putalpha(ImageChops.multiply(stream.split()[3], text_mask))

        base = make_standard_text_layer(lines, (35, 120, 180, 100))
        canvas_img.paste(base, (0, 0), mask=base)
        glow = stream.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 14)))
        glow_alpha = glow.split()[3].point(lambda p: int(p * 0.5))
        glow.putalpha(glow_alpha)
        canvas_img.paste(glow, (0, 0), mask=glow)
        canvas_img.paste(stream, (0, 0), mask=stream)

    def draw_text_neon_saber(canvas_img, lines, frame_idx, total_frames):
        """霓虹光剑：高能斜向光刃扫过并逐步点亮文字。"""
        progress = frame_idx / max(total_frames - 1, 1)
        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]
        bbox = text_mask.getbbox()
        if not bbox:
            return

        dim = make_standard_text_layer(lines, (40, 70, 100, 90))
        canvas_img.paste(dim, (0, 0), mask=dim)

        reveal = Image.new('L', (width_pixels, canvas_height), 0)
        reveal_draw = ImageDraw.Draw(reveal)
        saber_x = int(bbox[0] - dynamic_line_height * 0.6 + progress * ((bbox[2] - bbox[0]) + dynamic_line_height * 1.2))
        reveal_draw.polygon(
            [
                (bbox[0] - 30, 0),
                (saber_x + dynamic_line_height // 3, 0),
                (saber_x - dynamic_line_height // 3, canvas_height),
                (bbox[0] - 30, canvas_height),
            ],
            fill=255,
        )
        revealed_mask = ImageChops.multiply(reveal, text_mask)
        bright = Image.new('RGBA', (width_pixels, canvas_height), (120, 255, 255, 0))
        bright.putalpha(revealed_mask)
        canvas_img.paste(bright, (0, 0), mask=bright)

        saber = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(saber)
        draw.line(
            (saber_x + dynamic_line_height // 4, bbox[1] - 30, saber_x - dynamic_line_height // 4, bbox[3] + 30),
            fill=(255, 255, 255, 245),
            width=max(3, dynamic_line_height // 16),
        )
        draw.line(
            (saber_x + dynamic_line_height // 4 + 5, bbox[1] - 30, saber_x - dynamic_line_height // 4 + 5, bbox[3] + 30),
            fill=(0, 220, 255, 190),
            width=max(4, dynamic_line_height // 12),
        )
        saber_glow = saber.filter(ImageFilter.GaussianBlur(max(3, dynamic_line_height // 10)))
        canvas_img.paste(saber_glow, (0, 0), mask=saber_glow)
        canvas_img.paste(saber, (0, 0), mask=saber)

    def draw_text_burn(canvas_img, lines, frame_idx, total_frames):
        """燃烧字：文字内部火焰渐变，边缘发光并喷出小火星。"""
        progress = frame_idx / max(total_frames - 1, 1)
        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]

        glow_mask = text_mask.filter(ImageFilter.GaussianBlur(max(3, dynamic_line_height // 12)))
        glow_layer = Image.new('RGBA', (width_pixels, canvas_height), (255, 80, 0, 0))
        glow_layer.putalpha(glow_mask.point(lambda p: min(180, int(p * 0.75))))
        canvas_img.paste(glow_layer, (0, 0), mask=glow_layer)

        fire_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        fire_draw = ImageDraw.Draw(fire_layer)
        for y in range(canvas_height):
            t = y / max(canvas_height - 1, 1)
            wave = 0.5 + 0.5 * math.sin(progress * math.pi * 2 + y * 0.08)
            r = 255
            g = int(220 - 150 * t + 25 * wave)
            b = int(30 * (1 - t))
            fire_draw.line((0, y, width_pixels, y), fill=(r, max(40, g), max(0, b), 255))
        fire_layer.putalpha(text_mask)
        canvas_img.paste(fire_layer, (0, 0), mask=fire_layer)

        bbox = text_mask.getbbox()
        if not bbox:
            return

        rng = random.Random(7100 + frame_idx)
        ember_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        ember_draw = ImageDraw.Draw(ember_layer)
        ember_count = 10 if fast_preview else 18
        for idx in range(ember_count):
            x = rng.randint(bbox[0], max(bbox[0], bbox[2] - 1))
            rise = (frame_idx * 9 + idx * 17) % max(1, (bbox[3] - bbox[1]) + 40)
            y = bbox[3] - rise
            if y < bbox[1] - 25:
                continue
            size = rng.randint(2, 5)
            alpha = rng.randint(90, 220)
            ember_draw.ellipse((x, y, x + size, y + size), fill=(255, rng.randint(120, 230), 30, alpha))
        ember_layer = ember_layer.filter(ImageFilter.GaussianBlur(0.6))
        canvas_img.paste(ember_layer, (0, 0), mask=ember_layer)

    def draw_text_diamond_sparkle(canvas_img, lines, frame_idx, total_frames):
        """钻石闪耀：文字叠加冷色高光和周期闪钻。"""
        progress = frame_idx / max(total_frames - 1, 1)
        base_layer = make_standard_text_layer(lines, current_color)
        glow = base_layer.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 18)))
        canvas_img.paste(glow, (0, 0), mask=glow)
        canvas_img.paste(base_layer, (0, 0), mask=base_layer)

        bbox = base_layer.getbbox()
        if not bbox:
            return

        sparkle_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        sparkle_draw = ImageDraw.Draw(sparkle_layer)
        rng = random.Random(9200)
        sparkle_count = 12 if fast_preview else 20
        for idx in range(sparkle_count):
            x = rng.randint(bbox[0], max(bbox[0], bbox[2] - 1))
            y = rng.randint(bbox[1], max(bbox[1], bbox[3] - 1))
            phase = (progress * 2 * math.pi + idx * 0.85) % (2 * math.pi)
            intensity = max(0.0, math.sin(phase))
            if intensity <= 0.15:
                continue
            radius = int((3 + (idx % 4)) * intensity)
            alpha = int(255 * intensity)
            color = (210, 245, 255, alpha)
            sparkle_draw.line((x - radius, y, x + radius, y), fill=color, width=1)
            sparkle_draw.line((x, y - radius, x, y + radius), fill=color, width=1)
            sparkle_draw.polygon(
                [(x, y - radius), (x + radius, y), (x, y + radius), (x - radius, y)],
                fill=(255, 255, 255, min(180, alpha))
            )
        canvas_img.paste(sparkle_layer, (0, 0), mask=sparkle_layer)

    def draw_text_liquid_fill(canvas_img, lines, frame_idx, total_frames):
        """液体填充：文字轮廓内水位上升并产生波纹。"""
        progress = frame_idx / max(total_frames - 1, 1)
        mask_source = make_standard_text_layer(lines, (255, 255, 255, 255))
        text_mask = mask_source.split()[3]

        outline = make_standard_text_layer(lines, (*current_color[:3], 92))
        canvas_img.paste(outline, (0, 0), mask=outline)

        wave_mask = Image.new('L', (width_pixels, canvas_height), 0)
        wave_draw = ImageDraw.Draw(wave_mask)
        fill_top = canvas_height * (0.82 - 0.62 * progress)
        amplitude = max(4, dynamic_line_height * 0.08)
        points = []
        step = max(4, width_pixels // 48)
        for x in range(-step, width_pixels + step * 2, step):
            y = fill_top + math.sin(x * 0.055 + progress * math.pi * 4) * amplitude
            points.append((x, y))
        polygon = [(-step, canvas_height + step)] + points + [(width_pixels + step, canvas_height + step)]
        wave_draw.polygon(polygon, fill=255)

        fill_mask = ImageChops.multiply(text_mask, wave_mask)
        liquid = create_vertical_gradient(
            width_pixels,
            canvas_height,
            (60, 240, 255),
            (20, 80, 255),
            mode='RGB'
        ).convert('RGBA')
        liquid.putalpha(fill_mask)
        canvas_img.paste(liquid, (0, 0), mask=liquid)

        crest = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        crest_draw = ImageDraw.Draw(crest)
        for x, y in points:
            if 0 <= x < width_pixels:
                crest_draw.ellipse((x - 1, y - 1, x + 2, y + 2), fill=(230, 255, 255, 170))
        crest.putalpha(ImageChops.multiply(crest.split()[3], text_mask))
        canvas_img.paste(crest, (0, 0), mask=crest)

    def draw_text_split(canvas_img, lines, frame_idx, total_frames):
        """文字分裂：左右半边错位拉开再合拢。"""
        progress = frame_idx / max(total_frames - 1, 1)
        split_amount = int(math.sin(progress * math.pi) * max(8, width_pixels * 0.12))
        vertical_jitter = int(math.sin(progress * math.pi * 2) * max(2, canvas_height * 0.025))
        base_layer = make_standard_text_layer(lines, current_color)

        shadow_left = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        shadow_right = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
        draw_text_standard(shadow_left, lines, (255, 30, 80, 150), -split_amount - 2, vertical_jitter)
        draw_text_standard(shadow_right, lines, (30, 230, 255, 150), split_amount + 2, -vertical_jitter)
        canvas_img.paste(shadow_left, (0, 0), mask=shadow_left)
        canvas_img.paste(shadow_right, (0, 0), mask=shadow_right)

        mid = width_pixels // 2
        left = base_layer.crop((0, 0, mid, canvas_height))
        right = base_layer.crop((mid, 0, width_pixels, canvas_height))
        canvas_img.paste(left, (-split_amount, vertical_jitter), mask=left)
        canvas_img.paste(right, (mid + split_amount, -vertical_jitter), mask=right)

    def draw_text_jelly_wobble(canvas_img, lines, frame_idx, total_frames):
        """果冻摇摆：文字整体弹性挤压并带轻微拖影。"""
        progress = frame_idx / max(total_frames - 1, 1)
        wobble = math.sin(progress * math.pi * 4)
        damp = 0.45 + 0.55 * math.sin(progress * math.pi)
        scale_x = 1.0 + wobble * 0.16 * damp
        scale_y = 1.0 - wobble * 0.12 * damp

        base_layer = make_standard_text_layer(lines, current_color)
        shadow = base_layer.filter(ImageFilter.GaussianBlur(max(2, dynamic_line_height // 18)))
        shadow_alpha = shadow.split()[3].point(lambda p: int(p * 0.38))
        shadow.putalpha(shadow_alpha)
        canvas_img.paste(shadow, (0, 0), mask=shadow)

        new_w = max(1, int(width_pixels * scale_x))
        new_h = max(1, int(canvas_height * scale_y))
        resized = base_layer.resize((new_w, new_h), Image.Resampling.BICUBIC)
        paste_x = (width_pixels - new_w) // 2
        paste_y = (canvas_height - new_h) // 2
        canvas_img.paste(resized, (paste_x, paste_y), mask=resized)

    def draw_text_heart_bloom(canvas_img, lines, frame_idx, total_frames, hb_font):
        """心花怒放：心形文字整体旋转并放大"""
        source_text = ''.join(lines).strip()
        if not source_text:
            return

        cw, ch = canvas_img.size
        pattern = HEART_BLOOM_PATTERN
        rows = len(pattern)
        cols = max(len(row) for row in pattern)

        active_cells = []
        for row_idx, row in enumerate(pattern):
            for col_idx, cell in enumerate(row):
                if cell == 'X':
                    active_cells.append((row_idx, col_idx))

        if not active_cells:
            return

        cache_key = (
            source_text, cw, ch,
            getattr(hb_font, 'path', ''),
            getattr(hb_font, 'size', 0)
        )
        if not hasattr(draw_text_heart_bloom, '_cache'):
            draw_text_heart_bloom._cache = {}

        cached = draw_text_heart_bloom._cache.get(cache_key)
        if cached is None:
            usable_w = cw * 0.72
            usable_h = ch * 0.70
            cell_w = usable_w / cols
            cell_h = usable_h / rows
            cell_size = max(14, int(min(cell_w, cell_h)))

            try:
                heart_font = ImageFont.truetype(hb_font.path, max(12, int(cell_size * FONT_RATIO)))
            except Exception:
                heart_font = hb_font

            base_layer = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
            glow_layer = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
            draw_base = ImageDraw.Draw(base_layer)
            draw_glow = ImageDraw.Draw(glow_layer)
            offset_x = (cw - cols * cell_w) / 2.0
            offset_y = (ch - rows * cell_h) / 2.0 - cell_h * 0.12
            text_len = len(source_text)

            for idx, (row_idx, col_idx) in enumerate(active_cells):
                char = source_text[idx % text_len]
                center_x = offset_x + (col_idx + 0.5) * cell_w
                center_y = offset_y + (row_idx + 0.5) * cell_h
                bbox = draw_base.textbbox((0, 0), char, font=heart_font)
                char_w = bbox[2] - bbox[0]
                char_h = bbox[3] - bbox[1]
                draw_x = int(center_x - char_w / 2)
                draw_y = int(center_y - char_h / 2)
                draw_glow.text((draw_x, draw_y), char, font=heart_font, fill=(255, 90, 130, 120))
                draw_base.text((draw_x, draw_y), char, font=heart_font, fill=(220, 20, 60, 255))

            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(6))
            composite = Image.alpha_composite(glow_layer, base_layer)
            draw_text_heart_bloom._cache[cache_key] = composite
            cached = composite

        progress = frame_idx / max(total_frames - 1, 1)
        angle = math.sin(progress * 2 * math.pi) * 14
        scale = 0.72 + 0.38 * math.sin(progress * math.pi)

        scaled_w = max(1, int(cw * scale))
        scaled_h = max(1, int(ch * scale))
        scaled = cached.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
        rotated = scaled.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)

        paste_x = (cw - rotated.width) // 2
        paste_y = (ch - rotated.height) // 2
        canvas_img.paste(rotated, (paste_x, paste_y), rotated)

    def apply_glitch(base_img):
        # 1. 色彩错位 (RGB Split)
        r, g, b, a = base_img.split()
        
        # 随机偏移 R 和 B 通道
        offset_r = random.randint(-5, 5)
        offset_b = random.randint(-5, 5)
        
        # 使用 ImageChops 或简单的 crop/paste 移动通道
        def shift_channel(channel, x_offset):
            w, h = channel.size
            new_ch = Image.new('L', (w, h), 0)
            if x_offset > 0:
                data = channel.crop((0, 0, w - x_offset, h))
                new_ch.paste(data, (x_offset, 0))
            elif x_offset < 0:
                data = channel.crop((-x_offset, 0, w, h))
                new_ch.paste(data, (0, 0))
            else:
                return channel
            return new_ch

        r = shift_channel(r, offset_r)
        b = shift_channel(b, offset_b)
        
        glitched = Image.merge('RGBA', (r, g, b, a))
        
        # 2. 切片错位 (Slice Offset)
        w, h = glitched.size
        num_slices = random.randint(0, 3)
        for _ in range(num_slices):
            slice_h = random.randint(5, 20)
            slice_y = random.randint(0, h - slice_h)
            slice_offset = random.randint(-10, 10)
            
            slice_img = glitched.crop((0, slice_y, w, slice_y + slice_h))
            # 粘贴回去，带偏移
            glitched.paste(slice_img, (slice_offset, slice_y))
            
        return glitched

    # --- 核心生成循环 ---
    
    # 场景 A: 静态 / 呼吸 / 霓虹 / 弹跳 / 波浪 / 彩虹流动 / 故障 / 抖动 / 缩放 / 缩放滑动 / 喷发 / 滚动 / 打字机 / 跑马灯 / 像素溶解 / 模板特效
    # 这些特效有自己的专用绘制逻辑，必须进入is_static_layout分支
    template_effects = ['template_matrix', 'template_neon', 'template_electric', 'template_glitch']
    mask_effects = ['rainbow_mask', 'shining_mask', 'emoji_mask', 'matrix_mask', 'fire_mask',
                    'stars_mask', 'snow_mask', 'hearts_mask', 'cute_streamer_mask', 'particles_mask', 'music_mask',
                    'ripple_mask', 'lightning_mask', 'smoke_mask', 'neon_lines_mask', 'code_mask']
    is_static_layout = (needs_wrap or 
                        impact_static_text_layout or
                        effect_type in ['wave', 'bounce', 'neon', 'glitch', 'shake', 'extreme_shake', 'zoom', 'zoom_slide', 'roller_coaster', 'fly_zoom', 'spray', 'scroll', 'typewriter', 'marquee', 'dissolve', 'shining', 'floating_text', 'floating_text_clear', 'spiral_3d', 'spotlight', 'star_wars', 'ghost_trails', 'ktv_sweep', 'neon_flicker', 'chromatic_glitch', 'cinematic_pop', 'highlighter', 'prism_sweep', 'laser_scan', 'echo_shadow', 'pixel_burst', 'hologram_scan', 'plasma_wave', 'thunder_crack', 'vortex_warp', 'comet_trail', 'chrome_glass', 'aurora_ribbon', 'strobe_cut', 'sandstorm', 'magnetic_flip', 'ink_bleed', 'solar_flare', 'pulse_ring', 'electric_outline', 'photon_stream', 'neon_saber', 'text_burn', 'diamond_sparkle', 'liquid_fill', 'text_split', 'jelly_wobble', 'heart_bloom'] + template_effects + mask_effects or 
                        mode in ['breathing', 'rainbow_flow'])

    
    if is_static_layout:
        loop_frames = frame_count
        # 强制修正：如果 needs_wrap=False 且无特效，且 mode=solid，应该去滚动
        if not needs_wrap and mode == 'solid' and not effect_type and not impact_static_text_layout:
             is_static_layout = False
        elif impact_static_text_layout:
            loop_frames = 1


    if is_static_layout:
        for i in range(loop_frames):
            img = new_image(width_pixels, canvas_height, bg_color_rgba)
            d = ImageDraw.Draw(img) # 某些旧逻辑可能还需要 d，但主要使用 img
            
            # 1. 计算颜色
            current_color = solid_color_rgba
            if mode == 'breathing':
                progress = math.sin((i / (loop_frames - 1)) * math.pi) if loop_frames > 1 else 0
                current_color = interpolate_color(breath_colors[0], breath_colors[1], progress)
            elif effect_type == 'neon':
                hue = (i / loop_frames)
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                current_color = (int(r*255), int(g*255), int(b*255), 255)
                shadow_color = (int(r*100), int(g*100), int(b*100), 100)
                # 绘制阴影 (Emoji 也会有阴影)
                draw_text_standard(img, text_lines, shadow_color, 2, 2, use_emoji_silhouette=True)
            
            # 2. 计算位移/缩放等
            offset_x, offset_y = 0, 0
            if effect_type == 'bounce':
                bounce_progress = (i / (loop_frames - 1)) if loop_frames > 1 else 0
                bounce_offset = math.sin(bounce_progress * math.pi * 2) * 15
                offset_y = int(bounce_offset)
            elif effect_type == 'shake':
                shake_offset_x = (random.random() - 0.5) * 10
                shake_offset_y = (random.random() - 0.5) * 10
                offset_x, offset_y = int(shake_offset_x), int(shake_offset_y)
            
            # 3. 绘制 (rainbow_flow 使用专用逻辑)
            if mode == 'rainbow_flow':
                mask_img = Image.new('L', (width_pixels, canvas_height), 0)
                draw_text_standard(mask_img, text_lines, 255, offset_x, offset_y)
                
                grad_w, grad_h = width_pixels, canvas_height
                phase_shift = i / loop_frames
                gradient_img = create_rainbow_gradient(grad_w, grad_h, phase_shift)
                
                final_layer = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
                final_layer.paste(gradient_img, (0,0), mask=mask_img)
                img.paste(final_layer, (0,0), mask=final_layer)
                
            elif effect_type == 'wave':
                draw_text_wave(img, text_lines, current_color, i, loop_frames)
            
            elif effect_type == 'extreme_shake':
                draw_text_extreme_shake(img, text_lines, current_color, i, loop_frames)
            
            elif effect_type == 'glitch':
                # 先画文字到临时图层
                temp_img = new_image(width_pixels, canvas_height, (0,0,0,0))
                if mode == 'rainbow':
                    draw_text_standard(temp_img, text_lines, (0,0,0,255), 0, 0)
                    temp_img = apply_glitch(temp_img)
                    # 叠加彩虹颜色
                    temp_img = apply_rainbow_to_text(temp_img)
                else:
                    draw_text_standard(temp_img, text_lines, current_color, 0, 0)
                    # 应用故障效果
                    temp_img = apply_glitch(temp_img)
                img.paste(temp_img, (0,0), mask=temp_img)
            
            elif effect_type == 'zoom':
                # 先画文字到临时图层
                temp_img = new_image(width_pixels, canvas_height, (0,0,0,0))
                if mode == 'rainbow':
                    draw_text_standard(temp_img, text_lines, (0,0,0,255), 0, 0)
                else:
                    draw_text_standard(temp_img, text_lines, current_color, 0, 0)
                
                # 计算缩放比例 (1.0 ~ 1.2)
                scale_progress = (math.sin((i / loop_frames) * 2 * math.pi) + 1) / 2 # 0~1
                scale = 1.0 + (scale_progress * 0.2)
                
                # 缩放
                new_w = int(width_pixels * scale)
                new_h = int(canvas_height * scale)
                resized = temp_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
                
                if mode == 'rainbow':
                    # 叠加彩虹颜色（在缩放后）
                    resized = apply_rainbow_to_text(resized)
                
                # 居中裁剪/粘贴
                paste_x = (width_pixels - new_w) // 2
                paste_y = (canvas_height - new_h) // 2
                
                img.paste(resized, (paste_x, paste_y), mask=resized)

            elif effect_type == 'ktv_sweep':
                draw_text_ktv_sweep(img, text_lines, i, loop_frames)
            
            elif effect_type == 'neon_flicker':
                draw_text_neon_flicker(img, text_lines, i, loop_frames)
            
            elif effect_type == 'chromatic_glitch':
                draw_text_chromatic_glitch(img, text_lines, i, loop_frames)
            
            elif effect_type == 'cinematic_pop':
                draw_text_cinematic_pop(img, text_lines, i, loop_frames)
            
            elif effect_type == 'highlighter':
                draw_text_highlighter(img, text_lines, i, loop_frames)

            elif effect_type == 'prism_sweep':
                draw_text_prism_sweep(img, text_lines, i, loop_frames)

            elif effect_type == 'laser_scan':
                draw_text_laser_scan(img, text_lines, i, loop_frames)

            elif effect_type == 'echo_shadow':
                draw_text_echo_shadow(img, text_lines, i, loop_frames)

            elif effect_type == 'pixel_burst':
                draw_text_pixel_burst(img, text_lines, i, loop_frames)

            elif effect_type == 'hologram_scan':
                draw_text_hologram_scan(img, text_lines, i, loop_frames)

            elif effect_type == 'plasma_wave':
                draw_text_plasma_wave(img, text_lines, i, loop_frames)

            elif effect_type == 'thunder_crack':
                draw_text_thunder_crack(img, text_lines, i, loop_frames)

            elif effect_type == 'vortex_warp':
                draw_text_vortex_warp(img, text_lines, i, loop_frames)

            elif effect_type == 'comet_trail':
                draw_text_comet_trail(img, text_lines, i, loop_frames)

            elif effect_type == 'chrome_glass':
                draw_text_chrome_glass(img, text_lines, i, loop_frames)

            elif effect_type == 'aurora_ribbon':
                draw_text_aurora_ribbon(img, text_lines, i, loop_frames)

            elif effect_type == 'strobe_cut':
                draw_text_strobe_cut(img, text_lines, i, loop_frames)

            elif effect_type == 'sandstorm':
                draw_text_sandstorm(img, text_lines, i, loop_frames)

            elif effect_type == 'magnetic_flip':
                draw_text_magnetic_flip(img, text_lines, i, loop_frames)

            elif effect_type == 'ink_bleed':
                draw_text_ink_bleed(img, text_lines, i, loop_frames)

            elif effect_type == 'solar_flare':
                draw_text_solar_flare(img, text_lines, i, loop_frames)

            elif effect_type == 'pulse_ring':
                draw_text_pulse_ring(img, text_lines, i, loop_frames)

            elif effect_type == 'electric_outline':
                draw_text_electric_outline(img, text_lines, i, loop_frames)

            elif effect_type == 'photon_stream':
                draw_text_photon_stream(img, text_lines, i, loop_frames)

            elif effect_type == 'neon_saber':
                draw_text_neon_saber(img, text_lines, i, loop_frames)

            elif effect_type == 'text_burn':
                draw_text_burn(img, text_lines, i, loop_frames)

            elif effect_type == 'diamond_sparkle':
                draw_text_diamond_sparkle(img, text_lines, i, loop_frames)

            elif effect_type == 'liquid_fill':
                draw_text_liquid_fill(img, text_lines, i, loop_frames)

            elif effect_type == 'text_split':
                draw_text_split(img, text_lines, i, loop_frames)

            elif effect_type == 'jelly_wobble':
                draw_text_jelly_wobble(img, text_lines, i, loop_frames)

            elif effect_type == 'heart_bloom':
                draw_text_heart_bloom(img, text_lines, i, loop_frames, font)

            elif effect_type == 'roller_coaster':
                draw_text_roller_coaster(img, text_lines, i, loop_frames, font)

            elif effect_type == 'zoom_slide':
                # 滑动缩放：逐字渲染，每个字的字号由其x位置决定
                # 靠近画布中心的字最大，靠近两边的字最小
                draw_obj = ImageDraw.Draw(img)
                all_chars = ''.join(text_lines)
                char_count = len(all_chars)
                if char_count == 0:
                    continue
                
                # 动画进度 (0~1)，控制整体文字从左滚到右
                progress = i / max(loop_frames - 1, 1)
                
                # 基础字号和范围
                max_font_size = dynamic_line_height
                min_font_size = max(24, int(max_font_size * 0.5))
                
                # 计算每个字符所需的间距（用最大字号估算）
                try:
                    max_f = ImageFont.truetype(font_path, int(max_font_size * FONT_RATIO))
                except:
                    max_f = font
                sample_bbox = draw_obj.textbbox((0, 0), all_chars[0], font=max_f, anchor='lt')
                sample_char_width = sample_bbox[2] - sample_bbox[0]
                char_spacing = max(int(sample_char_width * 0.98), int(max_font_size * 0.82))
                
                # 整体文字块的总长度
                total_text_width = char_spacing * char_count
                
                # 整体滚动范围：从右侧边缘内侧 -> 左侧边缘内侧
                edge_margin = max(12, int(char_spacing * 0.55))
                start_x = width_pixels - edge_margin - char_spacing / 2
                end_x = edge_margin - total_text_width + char_spacing / 2
                group_x = start_x + (end_x - start_x) * progress
                
                center_x = width_pixels / 2.0
                
                for ci, char in enumerate(all_chars):
                    # 当前字符的中心x坐标
                    char_center_x = group_x + ci * char_spacing + char_spacing / 2
                    
                    # 根据字符与画布中心的距离计算缩放
                    # 距离中心越近，字号越大
                    dist_ratio = abs(char_center_x - center_x) / (width_pixels / 2.0)
                    dist_ratio = min(dist_ratio, 1.0)
                    # 钟形曲线：中心=1.0, 边缘=0.0
                    scale_factor = math.cos(dist_ratio * math.pi / 2) ** 2
                    
                    cur_font_size = int(min_font_size + scale_factor * (max_font_size - min_font_size))
                    cur_font_size = max(min_font_size, min(max_font_size, cur_font_size))
                    
                    try:
                        cur_font = ImageFont.truetype(font_path, int(cur_font_size * FONT_RATIO))
                    except:
                        cur_font = font
                    
                    # 彩虹颜色
                    char_hue = (ci / char_count + progress * 0.3) % 1.0
                    r, g, b = colorsys.hsv_to_rgb(char_hue, 1.0, 1.0)
                    char_color = (int(r*255), int(g*255), int(b*255), 255)
                    
                    # 绘制字符（垂直居中）
                    char_bbox = draw_obj.textbbox((0, 0), char, font=cur_font, anchor='lt')
                    char_w = char_bbox[2] - char_bbox[0]
                    char_h = char_bbox[3] - char_bbox[1]
                    draw_x = int(char_center_x - char_w / 2)
                    draw_y = int((canvas_height - char_h) / 2)
                    
                    # 只绘制在画布可见范围内的字符
                    if draw_x + char_w > 0 and draw_x < width_pixels:
                        draw_obj.text((draw_x, draw_y), char, fill=char_color, font=cur_font)

            elif effect_type == 'fly_zoom':
                # 飞字缩放效果：中间逐字放大 + 两侧斜飞文字
                draw_obj = ImageDraw.Draw(img)
                all_chars = ''.join(text_lines)[:5]  # 限制3个字符
                char_count = len(all_chars)
                if char_count == 0:
                    continue
                full_text = ''.join(text_lines)[:5]
                
                # 文字颜色：深绿色
                text_color = (0, 100, 0, 255)
                
                # === 1. 两侧斜飞文字 ===
                try:
                    fly_font = ImageFont.truetype(font_path, int(28 * FONT_RATIO))
                except:
                    fly_font = font
                
                # 生成多条斜飞文字轨迹
                random.seed(42)
                num_fly = 8  # 每侧飞行文字数量
                fly_items = []
                for fi in range(num_fly):
                    start_y = random.randint(-100, canvas_height)
                    speed = random.uniform(3.0, 8.0)
                    x_offset = random.randint(0, int(width_pixels * 0.3))
                    fly_items.append((start_y, speed, x_offset))
                random.seed()
                
                for start_y, speed, x_offset in fly_items:
                    # 左侧：从左上往左下飘
                    fly_y = (start_y + i * speed) % (canvas_height + 200) - 100
                    fly_x_left = x_offset - int(fly_y * 0.30)  # 倾斜角度
                    if -50 < fly_y < canvas_height + 50:
                        draw_obj.text((fly_x_left, int(fly_y)), full_text, fill=text_color, font=fly_font)
                    
                    # 右侧：从右上往右下飘
                    fly_x_right = width_pixels - x_offset - 80 + int(fly_y * 0.35)
                    if -50 < fly_y < canvas_height + 50:
                        draw_obj.text((fly_x_right, int(fly_y)), full_text, fill=text_color, font=fly_font)
                
                # === 2. 中间逐字放大 ===
                # 将动画分为 char_count 个阶段，每阶段一个字放大
                progress = i / max(loop_frames - 1, 1)  # 0~1
                char_phase = progress * char_count  # 0~3
                current_char_idx = min(int(char_phase), char_count - 1)
                char_progress = char_phase - current_char_idx  # 当前字符的放大进度 0~1
                
                # 当前字符
                current_char = all_chars[current_char_idx]
                
                # 字号：从小到画布高度的80%
                min_size = max(20, int(canvas_height * 0.05))
                max_size = int(canvas_height * 0.75)
                cur_size = int(min_size + char_progress * (max_size - min_size))
                
                try:
                    zoom_font = ImageFont.truetype(font_path, int(cur_size * FONT_RATIO))
                except:
                    zoom_font = font
                
                # 居中绘制
                char_bbox = draw_obj.textbbox((0, 0), current_char, font=zoom_font)
                char_w = char_bbox[2] - char_bbox[0]
                char_h = char_bbox[3] - char_bbox[1]
                cx = (width_pixels - char_w) // 2
                cy = (canvas_height - char_h) // 2
                
                # 透明度随放大增加（用颜色亮度模拟）
                alpha_factor = min(1.0, char_progress * 1.5)
                zoom_color = (0, int(100 * alpha_factor), 0, int(255 * alpha_factor))
                draw_obj.text((cx, cy), current_char, fill=zoom_color, font=zoom_font)

            elif effect_type == 'spray':
                # 喷发效果 - 传入固定字体路径
                draw_text_spray(img, text_lines, i, loop_frames, font_path)

            elif effect_type == 'scroll':
                # 滚动效果 - 使用最大化字号（已有彩虹）
                draw_text_scroll(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'typewriter':
                # 打字机特效 - 逐帧增加字符
                draw_text_typewriter(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'marquee':
                # 跑马灯特效 - 循环滚动
                draw_text_marquee(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'dissolve':
                # 像素溶解特效 - 逐渐拼凑
                draw_text_dissolve(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type in template_effects:
                # 模板特效 - 使用预渲染背景
                template_map = {
                    'template_matrix': 'templates/matrix_rain1.gif',
                    'template_neon': 'templates/neon_flash.gif',
                    'template_electric': 'templates/electric1.gif',
                    'template_glitch': 'templates/glitch_bg.gif'
                }
                
                template_path = template_map.get(effect_type)
                if template_path and os.path.exists(template_path):
                    if i == 0:
                        global template_frames_cache
                        if 'template_frames_cache' not in globals():
                            template_frames_cache = {}
                        
                        template_cache_key = (template_path, width_pixels, canvas_height, loop_frames)
                        if template_cache_key not in template_frames_cache:
                            cached_frames = []
                            with Image.open(template_path) as template_img:
                                source_frames = getattr(template_img, "n_frames", 1)
                                wanted_frames = min(loop_frames, source_frames)
                                if wanted_frames <= 1:
                                    frame_indices = [0]
                                else:
                                    frame_indices = [
                                        min(source_frames - 1, round(idx * (source_frames - 1) / (wanted_frames - 1)))
                                        for idx in range(wanted_frames)
                                    ]

                                for frame_index in frame_indices:
                                    template_img.seek(frame_index)
                                    cached_frame = template_img.convert('RGBA')
                                    if cached_frame.size != (width_pixels, canvas_height):
                                        cached_frame = cached_frame.resize((width_pixels, canvas_height), Image.BILINEAR)
                                    cached_frames.append(cached_frame.copy())
                            template_frames_cache[template_cache_key] = cached_frames
                    
                    # 获取对应的模板帧（循环使用）
                    template_cache_key = (template_path, width_pixels, canvas_height, loop_frames)
                    cached_frames = template_frames_cache.get(template_cache_key, [])
                    if cached_frames:
                        template_frame = cached_frames[i % len(cached_frames)]
                        
                        # 复制模板帧作为背景
                        img.paste(template_frame.convert('RGB'), (0, 0))
                        
                        # 绘制文字到临时图层
                        text_layer = Image.new('RGBA', (width_pixels, canvas_height), (0, 0, 0, 0))
                        draw_text_standard(text_layer, text_lines, (255, 255, 255, 255), 0, 0)
                        
                        # 叠加文字
                        img_rgba = img.convert('RGBA')
                        img_rgba = Image.alpha_composite(img_rgba, text_layer)
                        img.paste(img_rgba.convert('RGB'), (0, 0))
            
            elif effect_type == 'shining':
                # 流光字体特效 - 紫色渐变+光泽扫过
                draw_text_shining(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'rainbow_mask':
                # 彩虹蒙版特效 - 文字形状内显示彩虹
                draw_text_rainbow_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'shining_mask':
                # 流光蒙版特效 - 文字形状内显示流光
                draw_text_shining_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'emoji_mask':
                # Emoji蒙版特效 - 文字形状内显示emoji
                draw_text_emoji_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'matrix_mask':
                # 矩阵数字雨蒙版 - 文字形状内显示数字雨
                draw_text_matrix_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'fire_mask':
                # 火焰蒙版 - 文字形状内显示火焰
                draw_text_fire_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'stars_mask':
                # 星空蒙版 - 文字形状内显示闪烁星星
                draw_text_stars_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'snow_mask':
                # 雪花蒙版 - 文字形状内显示飘落雪花
                draw_text_snow_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'hearts_mask':
                # 爱心蒙版 - 文字形状内显示浮动爱心
                draw_text_hearts_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'cute_streamer_mask':
                # 可爱流光蒙版
                draw_text_cute_streamer_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'particles_mask':
                # 粒子爆炸蒙版 - 文字形状内显示粒子四散
                draw_text_particles_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'music_mask':
                # 音符蒙版 - 文字形状内显示跳动音符
                draw_text_music_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'ripple_mask':
                # 水波纹蒙版 - 文字形状内显示涟漪效果
                draw_text_ripple_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'lightning_mask':
                # 闪电蒙版 - 文字形状内显示闪电
                draw_text_lightning_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'smoke_mask':
                # 彩色烟雾蒙版 - 文字形状内显示渐变烟雾
                draw_text_smoke_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'neon_lines_mask':
                # 霓虹灯条蒙版 - 文字形状内显示霓虹灯条
                draw_text_neon_lines_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)
            
            elif effect_type == 'code_mask':
                # 代码雨蒙版 - 文字形状内显示代码滚动
                draw_text_code_mask(img, text_lines, i, loop_frames, font, dynamic_line_height)

            elif effect_type == 'floating_text':
                # 漂浮字特效 - 满屏文字从底部漂浮向上，3D立体+雪花+爱心
                draw_text_floating(img, text_lines, i, loop_frames, font_path)

            elif effect_type == 'floating_text_clear':
                # 漂浮字透明版 - 白色描边，粉紫蓝白色调
                draw_text_floating_clear(img, text_lines, i, loop_frames, font_path)

            elif effect_type == 'spiral_3d':
                # 螺旋3D旋转 - 每个字符沿螺旋路径旋转上升
                draw_text_spiral_3d(img, text_lines, i, loop_frames, font_path)

            elif effect_type == 'spotlight':
                # 暗夜聚光灯 - 扫射光束效果
                draw_text_spotlight(img, text_lines, i, loop_frames, font)

            elif effect_type == 'star_wars':
                # 星际史诗 - 3D向远方滚动字幕
                draw_text_star_wars(img, text_lines, i, loop_frames, font)

            elif effect_type == 'ghost_trails':
                # 流萤残影 - 8字游走带拖尾
                draw_text_ghost_trails(img, text_lines, i, loop_frames, font)

            else:
                # 标准绘制 (Bounce, Shake, Solid, Neon, Breathing)
                # 判断是否需要彩虹颜色
                if mode == 'breathing' or effect_type == 'neon':
                    # Breathing和Neon使用自己的颜色逻辑
                    draw_text_standard(img, text_lines, current_color, offset_x, offset_y)
                elif mode == 'rainbow':
                    # 只有选择了rainbow才使用彩虹颜色
                    temp_img = new_image(width_pixels, canvas_height, (0,0,0,0))
                    draw_text_standard(temp_img, text_lines, (0,0,0,255), offset_x, offset_y)
                    # 叠加彩虹颜色
                    temp_img = apply_rainbow_to_text(temp_img)
                    img.paste(temp_img, (0,0), mask=temp_img)
                else:
                    # Bounce, Shake, Solid等默认使用各自的颜色(current_color)
                    draw_text_standard(img, text_lines, current_color, offset_x, offset_y)
            
            images.append(img)

    # 场景 B: 滚动 (Scrolling)
    # 仅当 auto_wrap=False 且无特殊静态特效时触发
    else: 
        line = text_lines[0]
        # 计算总宽度 (包含 Emoji)
        temp_img = new_image(1, 1, bg_color_rgba)
        d_temp = ImageDraw.Draw(temp_img)
        
        # 使用 draw_line_mixed 计算宽度 (通过 mm 锚点反推，或者直接用 get_mixed_text_width 逻辑)
        # 这里我们简单调用 draw_line_mixed 模拟绘制来获取宽度，或者复用 get_mixed_text_width
        # 为了代码复用，我们直接用 draw_line_mixed 的逻辑
        # 但 draw_line_mixed 需要一个 img。
        # 我们可以直接用 get_mixed_text_width 逻辑，但它在外部。
        # 让我们把 get_mixed_text_width 逻辑内联或者简化。
        # 其实 draw_line_mixed 返回 total_width。
        
        text_w = draw_line_mixed(temp_img, line, 0, 0, font, (0,0,0,0))
        
        start_x = width_pixels
        total_distance = width_pixels + text_w
        step = total_distance / (frame_count - 1)
        
        for i in range(frame_count):
            img = new_image(width_pixels, canvas_height, bg_color_rgba)
            curr_x = start_x - (step * i)
            
            if mode == 'rainbow':
                mask_img = Image.new('L', (width_pixels, canvas_height), 0)
                # 绘制 Mask (支持 Emoji Alpha)
                draw_line_mixed(mask_img, line, curr_x, BASE_LINE_HEIGHT // 2, font, 255, anchor='lm')
                
                gradient_img = create_rainbow_gradient(width_pixels, canvas_height)
                res_layer = Image.new('RGBA', (width_pixels, canvas_height), (0,0,0,0))
                res_layer.paste(gradient_img, (0,0), mask=mask_img)
                img.paste(res_layer, (0,0), mask=res_layer)
            else:
                draw_line_mixed(img, line, curr_x, BASE_LINE_HEIGHT // 2, font, solid_color_rgba, anchor='lm')
            
            images.append(img)

    if not images: return None
    if theme == 'transparent':
        images = [process_alpha_threshold(img) for img in images]

    # ========== 自适应画布：不再强制缩放，保持原始尺寸 ==========
    if use_adaptive_canvas and images:
        current_w, current_h = images[0].size
        logger.info(f"自适应画布最终尺寸: {current_w}x{current_h}")

    output_buffer = io.BytesIO()
    duration_val = delay if len(images) > 1 else 1000
    
    # 打字机特效：最后一帧延迟1000ms
    if effect_type == 'typewriter' and len(images) > 1:
        # 创建每帧的延迟列表：除最后一帧外使用delay，最后一帧使用1000ms
        durations = [delay] * (len(images) - 1) + [1000]
        images[0].save(fp=output_buffer, format='GIF', append_images=images[1:], save_all=True, duration=durations, loop=0, transparency=0, disposal=2)
    else:
        images[0].save(fp=output_buffer, format='GIF', append_images=images[1:], save_all=len(images)>1, duration=duration_val, loop=0, transparency=0, disposal=2)
    
    output_buffer.seek(0)
    return output_buffer


# ==========================================
# 模板特效生成器 (高级版)
# ==========================================

# --- Wand 辅助函数 ---
def wand_make_text_mask(size, text_lines, cfg, font_path):
    """生成文字遮罩 (白字黑底)"""
    if not WAND_AVAILABLE:
        return None
    mask = WandImage(width=size[0], height=size[1], background=Color("black"))
    with Drawing() as draw:
        draw.font = font_path
        draw.font_size = cfg.get("font_size", 52)
        draw.fill_color = Color("white")
        draw.stroke_width = 0
        y = cfg.get("y_start", 80)
        for line in text_lines:
            draw.text(60, int(y), line)
            y += cfg.get("font_size", 52) + cfg.get("line_gap", 10)
        draw(mask)
    return mask

def wand_apply_fire_mask(fire_img, mask_img):
    """
    火焰穿字：用遮罩裁剪火焰，火焰只在文字区域可见
    
    原理：
    1. 创建透明底图
    2. 将遮罩（白字黑底）作为火焰的 alpha 通道
    3. 火焰只在白色（文字）区域可见
    """
    # 克隆火焰
    fire = fire_img.clone()
    
    # 克隆遮罩并确保是灰度
    mask = mask_img.clone()
    
    # 使用 DstIn 合成模式：保留 fire 在 mask 白色区域的像素
    # 或者手动设置 alpha
    try:
        # 方法1: 尝试使用 composite 的 dst_in 模式
        fire.composite(mask, left=0, top=0, operator='dst_in')
    except Exception:
        try:
            # 方法2: 使用 copy_opacity
            fire.composite(mask, left=0, top=0, operator='copy_opacity')
        except Exception:
            # 方法3: 回退 - 直接返回火焰（不裁剪）
            pass
    
    mask.close()
    return fire

def wand_draw_multiglow(text_lines, size, cfg, font_path):
    """多层发光 (橙→黄→白)"""
    if not WAND_AVAILABLE:
        return None
    base = WandImage(width=size[0], height=size[1], background=Color("transparent"))
    
    glow_layers = cfg.get("glow_layers", [
        {"color": [255, 80, 0], "stroke": 7, "blur": 3.0},
        {"color": [255, 180, 50], "stroke": 4, "blur": 2.0},
        {"color": [255, 255, 255], "stroke": 1, "blur": 0.8}
    ])
    
    jitter = cfg.get("jitter", 2)
    if isinstance(jitter, list):
        jitter = random.randint(jitter[0], jitter[1])
    dx = random.randint(-jitter, jitter)
    dy = random.randint(-jitter, jitter)
    
    y_start = cfg.get("y_start", 80)
    
    for layer in glow_layers:
        glow = WandImage(width=size[0], height=size[1], background=Color("transparent"))
        with Drawing() as draw:
            draw.font = font_path
            draw.font_size = cfg.get("font_size", 52)
            color = layer["color"]
            draw.fill_color = Color(f"rgb({color[0]},{color[1]},{color[2]})")
            draw.stroke_color = draw.fill_color
            draw.stroke_width = layer.get("stroke", 3) + random.choice([-1, 0, 1])
            
            y = y_start
            for line in text_lines:
                # 单字级亮度变化
                cursor_x = 60 + dx
                for ch in line:
                    brightness = random.uniform(0.85, 1.15)
                    r = min(255, int(color[0] * brightness))
                    g = min(255, int(color[1] * brightness))
                    b = min(255, int(color[2] * brightness))
                    draw.fill_color = Color(f"rgb({r},{g},{b})")
                    draw.text(int(cursor_x), int(y + dy), ch)
                    cursor_x += cfg.get("font_size", 52)
                y += cfg.get("font_size", 52) + cfg.get("line_gap", 10)
            draw(glow)
        
        blur_val = layer.get("blur", 2.0) + random.uniform(0, 0.8)
        glow.blur(0, blur_val)
        
        # 内白层偶尔更亮
        if layer["color"] == [255, 255, 255]:
            glow.modulate(brightness=random.uniform(105, 120))
        
        base.composite(glow, 0, 0, "over")
        glow.close()
    
    return base

def wand_make_inner_highlight(mask, texture_path):
    """内部高光纹理"""
    if not WAND_AVAILABLE or not texture_path or not os.path.exists(texture_path):
        return None
    
    tex = WandImage(filename=texture_path)
    
    # 随机缩放
    scale = random.uniform(1.0, 1.3)
    tex.resize(int(tex.width * scale), int(tex.height * scale))
    
    # 随机裁剪区域
    x = random.randint(0, max(0, tex.width - mask.width))
    y = random.randint(0, max(0, tex.height - mask.height))
    tex.crop(x, y, width=mask.width, height=mask.height)
    
    # 用文字遮罩裁剪
    tex.composite(mask, 0, 0, "copy_opacity")
    tex.modulate(brightness=random.uniform(120, 150))
    
    return tex

def wand_make_weight_mask(size, text_lines, cfg, font_path):
    """笔画粗细权重遮罩"""
    if not WAND_AVAILABLE:
        return None
    
    def make_stroke_mask(stroke_width):
        img = WandImage(width=size[0], height=size[1], background=Color("black"))
        with Drawing() as draw:
            draw.font = font_path
            draw.font_size = cfg.get("font_size", 52)
            draw.fill_color = Color("white")
            draw.stroke_color = Color("white")
            draw.stroke_width = stroke_width
            y = cfg.get("y_start", 80)
            for line in text_lines:
                draw.text(60, int(y), line)
                y += cfg.get("font_size", 52) + cfg.get("line_gap", 10)
            draw(img)
        return img
    
    thick = make_stroke_mask(stroke_width=8)
    thin = make_stroke_mask(stroke_width=1)
    
    thick.composite(thin, 0, 0, operator="minus")
    thick.blur(0, 2)
    
    thin.close()
    return thick

def generate_template_gif(
        text,
        template_name="fire_spark",
        font_path=None,
        delay=100,
        frame_count=None,
        fast_preview=False
    ) -> io.BytesIO:
    """
    使用预制模板生成 GIF (Wand 高级版)
    
    核心效果:
    1. 火焰穿透文字 - 火焰只在文字区域可见
    2. 文字自动缩放居中 - 占满画布
    3. 透明背景 - 无多余背景
    4. 多层发光边缘效果
    """
    if not WAND_AVAILABLE:
        logger.warning("Wand not available, using Pillow fallback")
        return generate_template_gif_pillow(text, template_name, font_path, delay, frame_count, fast_preview)
    
    template_dir = os.path.join(TEMPLATES_DIR, template_name)
    config_path = os.path.join(template_dir, "config.json")
    effect_dir = os.path.join(template_dir, "effect")
    
    if not os.path.exists(config_path):
        logger.error(f"Template config not found: {config_path}")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    # 字体路径
    if not font_path:
        font_path = get_random_font_from_folder()
    if not font_path or not os.path.exists(font_path):
        font_path = os.path.join(template_dir, "fonts", cfg.get("font", "default.ttf"))
        if not os.path.exists(font_path):
            font_path = "fonts/default.ttf" if os.path.exists("fonts/default.ttf") else None
    
    # 获取文本行
    text_lines = text.strip().split('\n') if '\n' in text else [text.strip()]
    
    # ========== 动态计算字号，使文字占满画布 ==========
    max_chars_per_line = max(len(line) for line in text_lines)
    num_lines = len(text_lines)
    
    target_width = CANVAS_WIDTH * 0.90
    width_based_size = target_width / max(max_chars_per_line, 1)
    
    target_height = CANVAS_HEIGHT * 0.70
    line_gap = cfg.get("line_gap", 10)
    height_based_size = (target_height - (num_lines - 1) * line_gap) / max(num_lines, 1)
    
    font_size = int(min(width_based_size, height_based_size))
    font_size = max(font_size, 40)
    font_size = min(font_size, 300)
    
    logger.info(f"Wand template font size: {font_size}px for {max_chars_per_line} chars x {num_lines} lines")
    
    # 计算居中 Y 位置
    total_text_height = num_lines * font_size + (num_lines - 1) * line_gap
    start_y = (CANVAS_HEIGHT - total_text_height) // 2 + font_size  # Wand 用基线，需要加字号
    
    # 火焰/特效帧
    effect_frames = []
    if os.path.exists(effect_dir):
        effect_frames = sorted([f for f in os.listdir(effect_dir) if f.endswith('.png')])
    
    total_frames = frame_count or len(effect_frames) or 10
    if total_frames < 5:
        total_frames = 10
    if fast_preview:
        total_frames = min(total_frames, PREVIEW_FRAME_CAP)
    
    frames = []
    size = (CANVAS_WIDTH, CANVAS_HEIGHT)
    
    # 发光层配置
    glow_layers = cfg.get("glow_layers", [
        {"color": [255, 80, 0], "stroke": 7, "blur": 3.0},
        {"color": [255, 180, 50], "stroke": 4, "blur": 2.0},
        {"color": [255, 255, 255], "stroke": 1, "blur": 0.8}
    ])
    
    for i in range(total_frames):
        # 抖动偏移
        jitter = cfg.get("jitter", 2)
        if isinstance(jitter, list):
            jitter = random.randint(jitter[0], jitter[1])
        dx = random.randint(-jitter, jitter)
        dy = random.randint(-jitter, jitter)
        
        # ========== 1. 创建透明画布 ==========
        bg = WandImage(width=size[0], height=size[1], background=Color('transparent'))
        
        # ========== 2. 加载火焰帧 ==========
        fire = None
        if effect_frames:
            effect_file = effect_frames[i % len(effect_frames)]
            fire_path = os.path.join(effect_dir, effect_file)
            fire = WandImage(filename=fire_path)
            if fire.width != size[0] or fire.height != size[1]:
                fire.resize(size[0], size[1])
            
            # 火焰亮度抖动
            fire_brightness = cfg.get("fire_brightness", [90, 115])
            if isinstance(fire_brightness, list):
                brightness = random.uniform(fire_brightness[0], fire_brightness[1])
            else:
                brightness = fire_brightness
            fire.modulate(brightness=brightness, saturation=100, hue=100)
        
        # ========== 3. 创建文字遮罩（居中） ==========
        mask = WandImage(width=size[0], height=size[1], background=Color("black"))
        with Drawing() as draw:
            if font_path:
                draw.font = font_path
            draw.font_size = font_size
            draw.fill_color = Color("white")
            draw.stroke_width = 0
            draw.text_alignment = 'center'  # 居中对齐
            
            for line_idx, line in enumerate(text_lines):
                x = size[0] // 2 + dx
                y = start_y + line_idx * (font_size + line_gap) + dy
                draw.text(x, int(y), line)
            draw(mask)
        mask.blur(0, 1.2)
        
        # ========== 4. 火焰穿透文字 ==========
        # 关键：火焰只在文字区域可见，其他区域透明
        fire_text = None
        if fire and mask:
            fire_text = fire.clone()
            # 将遮罩转为灰度并应用到火焰的 alpha 通道
            mask_gray = mask.clone()
            mask_gray.type = 'grayscale'
            
            # 使用 composite_channel 或 copy_opacity 应用遮罩
            try:
                # 方法1: 直接设置 alpha 通道
                fire_text.composite_channel('alpha', mask_gray, 'copy')
            except Exception:
                try:
                    # 方法2: copy_opacity
                    fire_text.composite(mask_gray, left=0, top=0, operator='copy_opacity')
                except Exception:
                    try:
                        # 方法3: dst_in
                        fire_text.composite(mask_gray, left=0, top=0, operator='dst_in')
                    except Exception:
                        # 回退：不裁剪
                        logger.warning("Fire mask composite failed, using unmasked fire")
            mask_gray.close()
        
        # ========== 5. 多层发光边缘（居中） ==========
        glow_img = WandImage(width=size[0], height=size[1], background=Color("transparent"))
        for layer in glow_layers:
            layer_img = WandImage(width=size[0], height=size[1], background=Color("transparent"))
            with Drawing() as draw:
                if font_path:
                    draw.font = font_path
                draw.font_size = font_size
                
                color = layer["color"]
                draw.fill_color = Color(f"rgb({color[0]},{color[1]},{color[2]})")
                draw.stroke_color = draw.fill_color
                draw.stroke_width = layer.get("stroke", 3) + random.choice([-1, 0, 1])
                draw.text_alignment = 'center'
                
                for line_idx, line in enumerate(text_lines):
                    x = size[0] // 2 + dx
                    y = start_y + line_idx * (font_size + line_gap) + dy
                    draw.text(x, int(y), line)
                draw(layer_img)
            
            blur_val = layer.get("blur", 2.0) + random.uniform(0, 0.8)
            layer_img.blur(0, blur_val)
            
            glow_img.composite(layer_img, 0, 0, "over")
            layer_img.close()
        
        # ========== 6. 合成（透明底 → 火焰穿字 → 发光） ==========
        frame = bg.clone()
        
        if fire_text:
            frame.composite(fire_text, 0, 0, "over")
            fire_text.close()
        
        frame.composite(glow_img, 0, 0, "over")
        glow_img.close()
        
        # 转换为 PIL
        frame.format = 'png'
        pil_img = Image.open(io.BytesIO(frame.make_blob())).convert('RGBA')
        frames.append(pil_img)
        
        # 清理
        frame.close()
        bg.close()
        if fire:
            fire.close()
        mask.close()
    
    if not frames:
        return None
    
    # 帧延迟随机化
    delay_jitter = cfg.get("delay_jitter", False)
    duration = delay
    if delay_jitter:
        duration = [random.choice([delay-10, delay, delay+10]) for _ in frames]
    
    output_buffer = io.BytesIO()
    frames[0].save(
        fp=output_buffer,
        format='GIF',
        append_images=frames[1:],
        save_all=True,
        duration=duration,
        loop=0,
        transparency=0,
        disposal=2
    )
    output_buffer.seek(0)
    return output_buffer


def generate_template_gif_pillow(
        text,
        template_name="fire_spark",
        font_path=None,
        delay=100,
        frame_count=None,
        fast_preview=False
    ) -> io.BytesIO:
    """
    Pillow 回退实现 (当 Wand 不可用时)
    
    核心效果:
    1. 火焰穿透文字 - 火焰只在文字区域可见
    2. 文字自动缩放居中 - 占满画布
    3. 透明背景 - 无多余背景
    4. 多层发光边缘效果
    """
    template_dir = os.path.join(TEMPLATES_DIR, template_name)
    config_path = os.path.join(template_dir, "config.json")
    effect_dir = os.path.join(template_dir, "effect")
    
    if not os.path.exists(config_path):
        logger.error(f"Template config not found: {config_path}")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    # 获取文本行
    text_lines = text.strip().split('\n') if '\n' in text else [text.strip()]
    
    # ========== 动态计算字号，使文字占满画布 ==========
    # 目标：文字宽度占画布 90%，高度占画布 70%
    max_chars_per_line = max(len(line) for line in text_lines)
    num_lines = len(text_lines)
    
    # 根据宽度计算（每字占据的宽度 ≈ 字号）
    target_width = CANVAS_WIDTH * 0.90
    width_based_size = target_width / max(max_chars_per_line, 1)
    
    # 根据高度计算（包含行间距）
    target_height = CANVAS_HEIGHT * 0.70
    line_gap = cfg.get("line_gap", 10)
    height_based_size = (target_height - (num_lines - 1) * line_gap) / max(num_lines, 1)
    
    # 取较小值确保不超出
    font_size = int(min(width_based_size, height_based_size))
    font_size = max(font_size, 40)  # 最小 40px
    font_size = min(font_size, 300)  # 最大 300px
    
    logger.info(f"Template font size: {font_size}px for {max_chars_per_line} chars x {num_lines} lines")
    
    font = load_font(font_path, font_size)
    
    # 加载火焰帧
    effect_frames = []
    if os.path.exists(effect_dir):
        effect_frames = sorted([f for f in os.listdir(effect_dir) if f.endswith('.png')])
    
    total_frames = frame_count or len(effect_frames) or 10
    if total_frames < 5:
        total_frames = 10
    if fast_preview:
        total_frames = min(total_frames, PREVIEW_FRAME_CAP)
    
    # 发光层配置
    glow_layers = cfg.get("glow_layers", [
        {"color": [255, 80, 0], "stroke": 7},
        {"color": [255, 180, 50], "stroke": 4},
        {"color": [255, 255, 255], "stroke": 1}
    ])
    
    frames = []
    
    for i in range(total_frames):
        # ========== 1. 创建透明画布 ==========
        img = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # ========== 2. 计算文字居中位置 ==========
        # 计算总文字高度
        total_text_height = num_lines * font_size + (num_lines - 1) * line_gap
        start_y = (CANVAS_HEIGHT - total_text_height) // 2
        
        # 抖动偏移
        jitter = cfg.get("jitter", 2)
        if isinstance(jitter, list):
            jitter = random.randint(jitter[0], jitter[1])
        dx = random.randint(-jitter, jitter)
        dy = random.randint(-jitter, jitter)
        
        # ========== 3. 加载火焰帧 ==========
        fire_img = None
        if effect_frames:
            effect_file = effect_frames[i % len(effect_frames)]
            fire_path = os.path.join(effect_dir, effect_file)
            fire_img = Image.open(fire_path).convert('RGBA')
            fire_img = fire_img.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
        
        # ========== 4. 创建文字遮罩（白字黑底，用于火焰穿透） ==========
        mask_img = Image.new('L', (CANVAS_WIDTH, CANVAS_HEIGHT), 0)
        mask_draw = ImageDraw.Draw(mask_img)
        
        for line_idx, line in enumerate(text_lines):
            # 计算每行居中的 X 位置
            try:
                bbox = font.getbbox(line)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * font_size
            
            x = (CANVAS_WIDTH - text_width) // 2 + dx
            y = start_y + line_idx * (font_size + line_gap) + dy
            
            mask_draw.text((x, y), line, font=font, fill=255)
        
        # ========== 5. 火焰穿透文字效果 ==========
        if fire_img:
            # 用遮罩裁剪火焰：火焰只在文字区域可见
            fire_masked = fire_img.copy()
            fire_masked.putalpha(mask_img)
            img.paste(fire_masked, (0, 0), fire_masked)
        
        # ========== 6. 多层发光边缘 ==========
        for layer in glow_layers:
            color = layer["color"]
            stroke = layer.get("stroke", 3)
            
            for line_idx, line in enumerate(text_lines):
                try:
                    bbox = font.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                except:
                    text_width = len(line) * font_size
                
                x = (CANVAS_WIDTH - text_width) // 2 + dx
                y = start_y + line_idx * (font_size + line_gap) + dy
                
                # 单字绘制发光
                cursor_x = x
                for ch in line:
                    try:
                        ch_bbox = font.getbbox(ch)
                        ch_width = ch_bbox[2] - ch_bbox[0]
                    except:
                        ch_width = font_size
                    
                    # 随机亮度变化
                    brightness = random.uniform(0.85, 1.15)
                    r = min(255, int(color[0] * brightness))
                    g = min(255, int(color[1] * brightness))
                    b = min(255, int(color[2] * brightness))
                    fill = (r, g, b, 255)
                    
                    # 绘制描边（四个方向）
                    for offset in range(1, stroke + 1):
                        draw.text((cursor_x - offset, y), ch, font=font, fill=fill)
                        draw.text((cursor_x + offset, y), ch, font=font, fill=fill)
                        draw.text((cursor_x, y - offset), ch, font=font, fill=fill)
                        draw.text((cursor_x, y + offset), ch, font=font, fill=fill)
                    
                    cursor_x += ch_width
        
        # ========== 7. 内层白色文字（最亮层） ==========
        for line_idx, line in enumerate(text_lines):
            try:
                bbox = font.getbbox(line)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * font_size
            
            x = (CANVAS_WIDTH - text_width) // 2 + dx
            y = start_y + line_idx * (font_size + line_gap) + dy
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        
        frames.append(img)
    
    if not frames:
        return None
    
    # ========== 保存 GIF ==========
    output_buffer = io.BytesIO()
    frames[0].save(
        fp=output_buffer,
        format='GIF',
        append_images=frames[1:],
        save_all=True,
        duration=delay,
        loop=0,
        transparency=0,
        disposal=2
    )
    output_buffer.seek(0)
    return output_buffer
