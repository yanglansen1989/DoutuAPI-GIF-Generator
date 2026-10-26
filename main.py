# main.py
import asyncio
import os
from collections import OrderedDict
from enum import Enum
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from gif_generator import generate_gif_bytes, generate_template_gif, should_auto_use_adaptive_canvas
from starlette.concurrency import run_in_threadpool

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Text to GIF API (Word Wrap Edition)",
    version="1.7.0"
)

# 允许跨域请求 (CORS)，方便其他客户端（如小程序、前端网页）调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

PREVIEW_WIDTH_CAP = int(os.getenv("GIF_PREVIEW_WIDTH_CAP", "260"))
PREVIEW_FRAME_CAP = int(os.getenv("GIF_PREVIEW_FRAME_CAP", "6"))
FULL_WIDTH_CAP = int(os.getenv("GIF_FULL_WIDTH_CAP", "1200"))
FULL_FRAME_CAP = int(os.getenv("GIF_FULL_FRAME_CAP", "60"))
GENERATION_CONCURRENCY = max(1, int(os.getenv("GIF_GENERATION_CONCURRENCY", "2")))
RESPONSE_CACHE_ITEMS = max(0, int(os.getenv("GIF_RESPONSE_CACHE_ITEMS", "128")))

_generation_semaphore = asyncio.Semaphore(GENERATION_CONCURRENCY)
_response_cache = OrderedDict()


class ThemeEnum(str, Enum):
    transparent = "transparent"
    dark = "dark"
    light = "light"


def _get_cached_response(cache_key):
    if RESPONSE_CACHE_ITEMS <= 0:
        return None
    cached = _response_cache.get(cache_key)
    if cached is not None:
        _response_cache.move_to_end(cache_key)
    return cached


def _set_cached_response(cache_key, data):
    if RESPONSE_CACHE_ITEMS <= 0:
        return
    _response_cache[cache_key] = data
    _response_cache.move_to_end(cache_key)
    while len(_response_cache) > RESPONSE_CACHE_ITEMS:
        _response_cache.popitem(last=False)


@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/generate")
async def get_gif(
    text: str = Query(..., min_length=1),
    frame_count: int = Query(20, ge=1, le=120),
    delay: int = Query(100, ge=20),
    color: str = Query(None, description="Color name, hex code, effect ('rainbow', 'wave', 'neon', etc), or template ('template:fire_spark')"),
    width_pixels: int = Query(500, ge=1, le=1200),
    theme: ThemeEnum = Query(ThemeEnum.transparent),
    wrap: bool = Query(False, description="Auto wrap text to new lines if it exceeds width. Disables scrolling."),
    font: str = Query(None, description="Font filename from fonts/ directory (e.g., 'jiying.ttf'). If not specified, a random font will be selected."),
    mask_color: str = Query(None, description="Custom color for mask effects (hex like '%23FF5733' or color name like 'red'). Only works with mask effects (fire_mask, lightning_mask, etc)."),
    adaptive_canvas: bool = Query(False, description="Enable adaptive canvas sizing for better text fit (slower). Default is fixed 480x480 for faster performance."),
    preview: bool = Query(False, description="Fast preview mode: caps size/frames and skips slower quality work."),
    cache_bust: str = Query(None, alias="_ts", description="Ignored cache-busting token for browser previews.")
):
    try:
        impact_plain_mode = color is None or color == "rainbow"
        if impact_plain_mode:
            adaptive_canvas = True
            frame_count = 1

        auto_adaptive_canvas = should_auto_use_adaptive_canvas(color)
        pure_text_mode = (
            impact_plain_mode
            or auto_adaptive_canvas
            or color in {
                "scroll", "marquee", "fly_zoom", "spray", "heart_bloom",
                "prism_sweep", "laser_scan", "echo_shadow", "pixel_burst",
                "hologram_scan", "plasma_wave", "thunder_crack", "vortex_warp",
                "comet_trail", "chrome_glass",
                "aurora_ribbon", "strobe_cut", "sandstorm", "magnetic_flip", "ink_bleed",
                "solar_flare", "pulse_ring", "electric_outline", "photon_stream", "neon_saber"
            }
            or (color and color.startswith("breathing:"))
        )
        if pure_text_mode:
            adaptive_canvas = True

        rich_preview_effects = {
            "prism_sweep", "laser_scan", "echo_shadow", "pixel_burst",
            "hologram_scan", "plasma_wave", "thunder_crack", "vortex_warp",
            "comet_trail", "chrome_glass",
            "aurora_ribbon", "strobe_cut", "sandstorm", "magnetic_flip", "ink_bleed",
            "solar_flare", "pulse_ring", "electric_outline", "photon_stream", "neon_saber"
        }

        if preview:
            width_pixels = min(width_pixels, PREVIEW_WIDTH_CAP)
            preview_frame_cap = 10 if color in rich_preview_effects else PREVIEW_FRAME_CAP
            frame_count = min(frame_count, preview_frame_cap)
            if not pure_text_mode:
                adaptive_canvas = False
        else:
            width_pixels = min(width_pixels, FULL_WIDTH_CAP)
            frame_count = min(frame_count, FULL_FRAME_CAP)

        # 处理字体参数：如果只提供文件名，则添加 fonts/ 前缀
        font_path_param = None
        if font:
            if not os.path.isabs(font):
                font_path_param = os.path.join("fonts", font)
            else:
                font_path_param = font

        cache_key = (
            text, frame_count, delay, color, width_pixels, theme.value, wrap,
            font_path_param, mask_color, adaptive_canvas, preview
        )
        response_headers = (
            {"Cache-Control": "no-store, max-age=0"}
            if preview
            else {"Cache-Control": "public, max-age=300"}
        )
        use_response_cache = not preview and not cache_bust

        cached = _get_cached_response(cache_key) if use_response_cache else None
        if cached is not None:
            return Response(
                content=cached,
                media_type="image/gif",
                headers=response_headers
            )
        
        async with _generation_semaphore:
            cached = _get_cached_response(cache_key) if use_response_cache else None
            if cached is not None:
                return Response(
                    content=cached,
                    media_type="image/gif",
                    headers=response_headers
                )

            # 检查是否使用模板特效
            if color and color.startswith('template:'):
                template_name = color.split(':', 1)[1]
                gif_buffer = await run_in_threadpool(
                    generate_template_gif,
                    text=text,
                    template_name=template_name,
                    font_path=font_path_param,
                    delay=delay,
                    frame_count=frame_count,
                    fast_preview=preview
                )
            else:
                # 呼吸灯逻辑检查
                if color and color.startswith('breathing:') and frame_count < 20 and not preview:
                    frame_count = 20
                
                gif_buffer = await run_in_threadpool(
                    generate_gif_bytes,
                    text=text,
                    frame_count=frame_count,
                    delay=delay,
                    font_path=font_path_param,
                    text_color_param=color,
                    mask_color_param=mask_color,
                    width_pixels=width_pixels,
                    theme=theme.value,
                    auto_wrap=wrap,
                    use_adaptive_canvas=adaptive_canvas,
                    fast_preview=preview
                )

        if not gif_buffer:
            raise HTTPException(status_code=400, detail="Failed to generate GIF.")

        data = gif_buffer.getvalue()
        if use_response_cache:
            _set_cached_response(cache_key, data)
        return Response(
            content=data,
            media_type="image/gif",
            headers=response_headers
        )
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8066, reload=True)
