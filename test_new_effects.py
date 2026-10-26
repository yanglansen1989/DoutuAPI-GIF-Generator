import os
from gif_generator import generate_gif_bytes

effects = [
    'ktv_sweep',
    'neon_flicker',
    'chromatic_glitch',
    'cinematic_pop',
    'highlighter',
    'roller_coaster'
]

os.makedirs('test_outputs', exist_ok=True)

for effect in effects:
    print(f"Testing {effect}...")
    try:
        gif_bytes = generate_gif_bytes(
            text=f"Test {effect}",
            text_color_param=effect,
            frame_count=20,
            delay=50,
            width_pixels=480,
            theme="dark",
            auto_wrap=False,
            use_adaptive_canvas=True
        )
        
        with open(f"test_outputs/{effect}.gif", "wb") as f:
            f.write(gif_bytes.getvalue())
        print(f"Success: {effect}.gif generated.")
    except Exception as e:
        print(f"Failed {effect}: {e}")
