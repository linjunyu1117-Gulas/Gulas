"""
山水水墨 — Shanshui Ink Landscape Visual Generator
Chinese ink-wash painting style: layered misty mountains, calm water reflection.
Outputs PNG frames → ffmpeg encodes to looping MP4.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import os, math

WIDTH, HEIGHT = 1920, 1080
FPS = 24
LOOP_SEC = 16        # 16-second seamless loop
N_FRAMES = FPS * LOOP_SEC
OUT_DIR = "/home/user/Gulas/assets/video/shanshui_frames"
OUT_MP4 = "/home/user/Gulas/assets/video/shanshui_loop.mp4"

os.makedirs(OUT_DIR, exist_ok=True)

# ── Colour palette — ink wash (水墨) ──────────────────────────────────────────
# Paper: warm pale grey, like aged xuan paper
PAPER      = (242, 238, 228)
# Ink tones: from faint wash to deep black
INK_FAINT  = (190, 185, 175)
INK_LIGHT  = (148, 143, 132)
INK_MID    = (98,  94,  86)
INK_DEEP   = (52,  50,  44)
INK_BLACK  = (22,  20,  16)
# Water tint: silvery reflection
WATER_PALE = (220, 218, 212)
WATER_DARK = (140, 138, 132)
# Mist: near-white with blue hint
MIST_COL   = (235, 232, 226)


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return int(a + (b - a) * t)


def lerp_color(c1, c2, t):
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))


# ── Sky gradient ──────────────────────────────────────────────────────────────
def sky_color(y_norm, phase):
    """
    Ink-wash sky: nearly white paper at horizon, pale blue-grey overhead.
    A subtle luminance pulse breathes gently through the loop.
    """
    pulse = 0.5 + 0.5 * math.sin(phase * 2 * math.pi)
    # top → bottom: pale blue-grey → warm paper white
    top    = (200, 198, 194)
    mid    = (225, 222, 216)
    bottom = (238, 235, 228)

    if y_norm < 0.5:
        c = lerp_color(top, mid, y_norm / 0.5)
    else:
        c = lerp_color(mid, bottom, (y_norm - 0.5) / 0.5)

    # very gentle luminance breath
    bright = int(4 * pulse)
    return tuple(min(255, v + bright) for v in c)


# ── Mountain profile ──────────────────────────────────────────────────────────
def mountain_y(x_arr, w, h, layer, phase, drift=0.0):
    """
    Mountain silhouette for a given layer.
    layer 0 = farthest (tallest, palest)
    layer 3 = nearest foreground
    """
    configs = [
        # layer 0 — distant jagged peaks
        dict(base=0.42, amps=[0.18, 0.10, 0.06, 0.035, 0.018],
             freqs=[0.0025, 0.006, 0.013, 0.026, 0.050],
             phases=[0.0, 1.2, 2.5, 0.8, 3.6]),
        # layer 1 — mid-range ridge
        dict(base=0.56, amps=[0.15, 0.09, 0.05, 0.028],
             freqs=[0.0030, 0.008, 0.017, 0.038],
             phases=[0.5, 2.0, 1.0, 2.9]),
        # layer 2 — near hills
        dict(base=0.68, amps=[0.12, 0.07, 0.04, 0.020],
             freqs=[0.0040, 0.010, 0.022, 0.048],
             phases=[1.1, 0.4, 3.2, 1.7]),
        # layer 3 — foreground dark shore / rocks
        dict(base=0.80, amps=[0.08, 0.05, 0.03],
             freqs=[0.005,  0.013, 0.030],
             phases=[2.0, 1.5, 0.3]),
    ]
    cfg = configs[layer]
    # slow horizontal drift (parallax: far layers drift less)
    speed = [0.006, 0.012, 0.020, 0.030][layer]
    x_shift = drift * w * speed * math.sin(phase * 2 * math.pi)
    x_eff = (x_arr + x_shift) % w

    y = np.full_like(x_arr, cfg['base'] * h, dtype=float)
    for amp, freq, ph in zip(cfg['amps'], cfg['freqs'], cfg['phases']):
        y -= amp * h * np.sin(2 * math.pi * freq * x_eff + ph)
    return np.clip(y, 0, h - 1).astype(int)


# ── Pine tree silhouettes ─────────────────────────────────────────────────────
PINE_POSITIONS = [(320, 0.72), (580, 0.74), (840, 0.73), (1100, 0.71),
                  (1380, 0.73), (1620, 0.75), (200, 0.76), (1780, 0.72)]

def draw_pine(draw, cx, base_y, height=90, ink_col=INK_BLACK):
    """Stylised ink-brush pine: stacked triangles."""
    levels = 4
    for lvl in range(levels):
        frac   = lvl / levels
        w_half = int(height * 0.38 * (1 - frac * 0.55))
        tip_y  = int(base_y - height * (1 - frac * 0.22))
        base_l = int(base_y - height * frac * 0.22)
        # Simple triangle with slight ink brush wobble
        pts = [cx, tip_y, cx - w_half, base_l, cx + w_half, base_l]
        # Vary darkness per level
        shade = tuple(min(255, v + lvl * 6) for v in ink_col)
        draw.polygon(pts, fill=shade)
    # trunk
    draw.rectangle([cx - 3, base_y - int(height * 0.15), cx + 3, base_y], fill=ink_col)


# ── Water reflection ──────────────────────────────────────────────────────────
WATER_LINE = int(HEIGHT * 0.78)   # y where water begins

def water_color(y, h, phase):
    """Calm water: pale ink, gentle shimmer."""
    depth = (y - WATER_LINE) / (h - WATER_LINE)
    shimmer = 0.02 * math.sin(phase * 2 * math.pi * 2 + depth * 8)
    t = max(0, min(1, depth + shimmer))
    return lerp_color(WATER_PALE, WATER_DARK, t)


def draw_ripple(draw, w, h, phase):
    """Sparse horizontal ripple lines on water surface."""
    for k in range(6):
        y_base = WATER_LINE + int((h - WATER_LINE) * (k + 1) / 8)
        # breathing amplitude: ripples gently widen and narrow
        amp = 2 + k
        freq = 0.003 + k * 0.0007
        phase_off = phase * 2 * math.pi + k * 1.1
        pts = []
        step = 8
        for x in range(0, w, step):
            ry = y_base + int(amp * math.sin(freq * x * w / w * 6 + phase_off))
            pts.append((x, ry))
        if len(pts) > 1:
            alpha = 60 - k * 6
            col = (160, 158, 150, alpha)
            for i in range(len(pts) - 1):
                draw.line([pts[i], pts[i+1]], fill=(160, 158, 150), width=1)


# ── Mist bands ────────────────────────────────────────────────────────────────
def draw_mist(img, layer_y_values, phase):
    """Translucent white mist that drifts slowly between mountain layers."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    for ly in layer_y_values:
        mist_h = int(HEIGHT * 0.055)
        drift  = int(25 * math.sin(phase * 2 * math.pi + ly * 0.01))
        for dy in range(mist_h):
            frac = dy / mist_h
            alpha = int(85 * (1 - frac) * (0.6 + 0.4 * math.sin(phase * 2 * math.pi)))
            y = ly + dy + drift
            if 0 <= y < HEIGHT:
                r, g, b = MIST_COL
                od.line([(0, y), (WIDTH, y)], fill=(r, g, b, alpha))

    img_rgba = img.convert("RGBA")
    return Image.alpha_composite(img_rgba, overlay).convert("RGB")


# ── Moon ──────────────────────────────────────────────────────────────────────
def draw_moon(draw, phase):
    mx = int(WIDTH * 0.78)
    my = int(HEIGHT * 0.14)
    r  = 26
    # soft outer glow (several translucent rings)
    for gr in range(60, r, -3):
        frac  = 1 - (gr - r) / (60 - r)
        alpha = int(22 * frac * (0.75 + 0.25 * math.sin(phase * 2 * math.pi)))
        col   = tuple(lerp(PAPER[i], (255, 252, 245)[i], frac) for i in range(3))
        draw.ellipse([mx - gr, my - gr, mx + gr, my + gr], fill=col)
    # moon disc
    draw.ellipse([mx - r, my - r, mx + r, my + r], fill=(252, 250, 244))


# ── Single frame render ────────────────────────────────────────────────────────
def generate_frame(frame_idx):
    phase = frame_idx / N_FRAMES   # 0.0 → <1.0

    img  = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    x_arr = np.arange(WIDTH)

    # 1. Sky
    for y in range(WATER_LINE):
        col = sky_color(y / WATER_LINE, phase)
        draw.line([(0, y), (WIDTH, y)], fill=col)

    # 2. Moon
    draw_moon(draw, phase)

    # 3. Mountain layers (far → near)
    layer_ink = [INK_FAINT, INK_LIGHT, INK_MID, INK_DEEP]
    mist_ys   = []
    all_my    = []
    for layer in range(4):
        my_arr = mountain_y(x_arr, WIDTH, HEIGHT, layer, phase, drift=1.0)
        all_my.append(my_arr)
        col = layer_ink[layer]
        # Each layer: draw silhouette column by column, with ink softening
        for x in range(WIDTH):
            yt = my_arr[x]
            if yt < WATER_LINE:
                draw.line([(x, yt), (x, min(WATER_LINE, HEIGHT))], fill=col)
        # Collect mist anchor y (top of each layer at centre)
        mist_ys.append(int(np.mean(my_arr)) - 12)

    # 4. Pine silhouettes on layer-2 ridgeline
    for cx, base_frac in PINE_POSITIONS:
        ridge_y = all_my[2][min(cx, WIDTH - 1)]
        base_y  = ridge_y
        draw_pine(draw, cx, base_y, height=int(HEIGHT * 0.075), ink_col=INK_BLACK)

    # 5. Water surface
    for y in range(WATER_LINE, HEIGHT):
        col = water_color(y, HEIGHT, phase)
        draw.line([(0, y), (WIDTH, y)], fill=col)

    # Reflected mountain silhouettes in water (flipped, lighter)
    for layer in range(3, -1, -1):
        my_arr = all_my[layer]
        r_col  = tuple(lerp(layer_ink[layer][i], WATER_PALE[i], 0.55) for i in range(3))
        for x in range(WIDTH):
            ref_top = WATER_LINE + (WATER_LINE - my_arr[x])
            ref_top = max(WATER_LINE, min(HEIGHT - 1, ref_top))
            if ref_top < HEIGHT:
                draw.line([(x, ref_top), (x, HEIGHT)], fill=r_col)

    # Ripple lines
    draw_ripple(draw, WIDTH, HEIGHT, phase)

    # 6. Mist overlay
    img = draw_mist(img, mist_ys[:3], phase)

    # 7. Light ink texture blur (simulate paper absorbency)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.7))

    # 8. Subtle desaturation to push toward ink-wash monochrome
    img = ImageEnhance.Color(img).enhance(0.55)

    # 9. Vignette (heavier corners for scroll-painting feel)
    vig = Image.new("L", (WIDTH, HEIGHT), 255)
    vd  = ImageDraw.Draw(vig)
    for rr in range(250):
        alpha = int(rr * 0.95)
        vd.ellipse([rr, rr, WIDTH - rr, HEIGHT - rr], fill=min(255, alpha))
    vig = vig.filter(ImageFilter.GaussianBlur(radius=55))
    dark = Image.new("RGB", (WIDTH, HEIGHT), (10, 9, 8))
    img  = Image.composite(img, dark, vig)

    return img


# ── Render all frames ─────────────────────────────────────────────────────────
print(f"Generating {N_FRAMES} frames ({LOOP_SEC}s loop at {FPS}fps)...")
for i in range(N_FRAMES):
    frame = generate_frame(i)
    frame.save(f"{OUT_DIR}/frame_{i:04d}.png")
    if i % (FPS * 2) == 0:
        print(f"  Frame {i}/{N_FRAMES}  ({100 * i // N_FRAMES}%)")

print("Frames done. Encoding MP4...")
os.system(
    f'ffmpeg -y -framerate {FPS} -i "{OUT_DIR}/frame_%04d.png" '
    f'-c:v libx264 -pix_fmt yuv420p -crf 17 -preset slow '
    f'"{OUT_MP4}" 2>&1 | tail -5'
)
print(f"Video: {OUT_MP4}")
