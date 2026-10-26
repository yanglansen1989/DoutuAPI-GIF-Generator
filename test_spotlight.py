from gif_generator import generate_gif_bytes

def test():
    try:
        generate_gif_bytes("Neon", text_color_param="spotlight", theme="dark", frame_count=30, delay=80)
        print("Success")
    except Exception as e:
        import traceback
        traceback.print_exc()

test()
