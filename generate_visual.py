"""
Taiwan Mountain Landscape Visual Generator
Creates a looping ambient visual: mountain silhouette + aurora-style gradient sky
Outputs PNG frames → ffmpeg encodes to looping MP4
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import os, math

WIDTH, HEIGHT = 1920, 1080
FPS = 24
LOOP_SEC = 12       # 12-second smooth loop
N_FRAMES = FPS * LOOP_SEC
OUT_DIR = "/home/user/Gulas/assets/video/frames"
OUT_MP4 = "/home/user/Gulas/assets/video/taiwan_mountain_loop.mp4"

os.makedirs(OUT_DIR, exist_ok=True)

def lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def sky_gradient(y, h, phase):
    """Taiwan mountain golden hour sky — transitions from deep blue to warm amber."""
    sky_ratio = y / h
    # Base colors: deep night blue → twilight purple → golden amber horizon
    night   = (15, 20, 45)
    twilight= (60, 40, 90)
    gold    = (220, 120, 40)
    horizon = (255, 180, 80)

    pulse = 0.5 + 0.5 * math.sin(phase * 2 * math.pi)  # 0→1→0

    if sky_ratio < 0.35:
        t = sky_ratio / 0.35
        base = lerp_color(night, twilight, t)
    elif sky_ratio < 0.65:
        t = (sky_ratio - 0.35) / 0.30
        warm = lerp_color(
            (int(220 + 20 * pulse), int(100 + 30 * pulse), int(30 + 20 * pulse)),
            gold, t
        )
        base = lerp_color(twilight, warm, t)
    else:
        t = (sky_ratio - 0.65) / 0.35
        base = lerp_color(gold, horizon, t)

    # Subtle warmth pulse
    r = min(255, base[0] + int(15 * pulse * (1 - sky_ratio)))
    g = min(255, base[1] + int(8 * pulse * sky_ratio))
    b = base[2]
    return (r, g, b)

def mountain_silhouette(x_arr, w, h, layer):
    """Generate mountain ridge profile using sum of sine waves."""
    if layer == 0:   # far mountains (lighter)
        amps   = [0.22, 0.09, 0.05, 0.03]
        freqs  = [0.003, 0.007, 0.015, 0.025]
        phases = [0.0, 1.1, 2.4, 0.7]
        base_y = 0.52  # fraction from top
    elif layer == 1: # mid mountains
        amps   = [0.19, 0.10, 0.06, 0.02]
        freqs  = [0.004, 0.009, 0.018, 0.035]
        phases = [0.8, 2.1, 0.3, 3.1]
        base_y = 0.62
    else:            # foreground hills (darkest)
        amps   = [0.14, 0.08, 0.05]
        freqs  = [0.005, 0.012, 0.028]
        phases = [1.5, 0.6, 2.8]
        base_y = 0.74

    y = np.full_like(x_arr, base_y * h, dtype=float)
    for amp, freq, ph in zip(amps, freqs, phases):
        y -= amp * h * np.sin(2 * math.pi * freq * x_arr + ph)
    return y.astype(int)

def mist_layer(draw, w, h, phase, layer_y, opacity):
    """Draw soft horizontal mist bands between mountain layers."""
    mist_h = int(h * 0.035)
    shift = int(15 * math.sin(phase * 2 * math.pi + layer_y))
    for dy in range(mist_h):
        alpha = opacity * (1 - dy / mist_h) * 0.6
        col = int(200 + 40 * math.sin(phase * math.pi))
        draw.line(
            [(0, layer_y + dy + shift), (w, layer_y + dy + shift)],
            fill=(col, col, col + 20, int(alpha * 60))
        )

def generate_frame(frame_idx):
    phase = frame_idx / N_FRAMES  # 0.0 → 1.0 smoothly

    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # 1. Sky gradient
    x_arr = np.arange(WIDTH)
    for y in range(HEIGHT):
        color = sky_gradient(y, HEIGHT, phase)
        draw.line([(0, y), (WIDTH, y)], fill=color)

    # 2. Stars (only in upper sky, fade out near horizon)
    rng = np.random.default_rng(42)  # fixed seed for stable stars
    n_stars = 120
    sx = rng.integers(0, WIDTH, n_stars)
    sy = rng.integers(0, int(HEIGHT * 0.45), n_stars)
    twinkle = 0.4 + 0.6 * np.sin(2 * math.pi * (phase * 3 + rng.random(n_stars)))
    for i in range(n_stars):
        alpha = int(180 * twinkle[i] * (1 - sy[i] / (HEIGHT * 0.45) * 0.5))
        bright = 200 + rng.integers(0, 55)
        size = 1 if rng.random() > 0.15 else 2
        draw.ellipse(
            [sx[i]-size, sy[i]-size, sx[i]+size, sy[i]+size],
            fill=(bright, bright, min(255, bright + 30))
        )

    # 3. Moon / sun glow
    moon_x = int(WIDTH * 0.72)
    moon_y = int(HEIGHT * 0.18)
    moon_r = 28
    glow_col = (255, 230, 150)
    for r in range(80, moon_r, -4):
        alpha = int(30 * (1 - r / 80) * (0.7 + 0.3 * math.sin(phase * 2 * math.pi)))
        draw.ellipse(
            [moon_x-r, moon_y-r, moon_x+r, moon_y+r],
            fill=(glow_col[0], glow_col[1], glow_col[2])
        )
    draw.ellipse(
        [moon_x-moon_r, moon_y-moon_r, moon_x+moon_r, moon_y+moon_r],
        fill=(255, 245, 200)
    )

    # 4. Mountain layers (back to front)
    layer_colors = [
        (70, 55, 90),    # far — dusky purple
        (45, 55, 70),    # mid — deep blue-grey
        (25, 35, 40),    # near — dark forest
        (15, 22, 28),    # foreground — near black
    ]

    for layer in range(3):
        mountain_y = mountain_silhouette(x_arr, WIDTH, HEIGHT, layer)
        col = layer_colors[layer + 1]
        # slight color warmth shift on horizon edge
        for x in range(WIDTH):
            y_top = mountain_y[x]
            if y_top >= HEIGHT: continue
            draw.line([(x, y_top), (x, HEIGHT)], fill=col)

    # 5. Mist between layers (RGBA overlay)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    m0_y = mountain_silhouette(x_arr, WIDTH, HEIGHT, 0)
    m1_y = mountain_silhouette(x_arr, WIDTH, HEIGHT, 1)
    mist_layer(ov_draw, WIDTH, HEIGHT, phase, int(np.mean(m0_y)) - 10, 0.8)
    mist_layer(ov_draw, WIDTH, HEIGHT, phase, int(np.mean(m1_y)) - 8, 0.6)

    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, overlay)
    img = img_rgba.convert("RGB")

    # 6. Slight blur for cinematic feel
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

    # 7. Vignette
    vignette = Image.new("L", (WIDTH, HEIGHT), 255)
    vd = ImageDraw.Draw(vignette)
    for r in range(200):
        alpha = int(r * 1.1)
        vd.ellipse([r, r, WIDTH-r, HEIGHT-r], fill=min(255, alpha))
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=60))
    vig_dark = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    img = Image.composite(img, vig_dark, vignette)

    return img

print(f"Generating {N_FRAMES} frames ({LOOP_SEC}s loop at {FPS}fps)...")
for i in range(N_FRAMES):
    frame = generate_frame(i)
    frame.save(f"{OUT_DIR}/frame_{i:04d}.png")
    if i % (FPS * 2) == 0:
        print(f"  Frame {i}/{N_FRAMES} ({100*i//N_FRAMES}%)")

print("Frames done. Encoding to MP4 with ffmpeg...")
os.system(
    f'ffmpeg -y -framerate {FPS} -i "{OUT_DIR}/frame_%04d.png" '
    f'-c:v libx264 -pix_fmt yuv420p -crf 18 -preset slow '
    f'"{OUT_MP4}" 2>&1 | tail -5'
)
print(f"Video: {OUT_MP4}")
