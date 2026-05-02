"""
YouTube Thumbnail Generator — 山海電台
Creates a professional 1280×720 thumbnail with mountain gradient + text
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

W, H = 1280, 720
OUT = "/home/user/Gulas/assets/thumbnail/thumbnail_vol1.png"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)

# Sky gradient (deep blue → twilight purple → golden amber)
for y in range(H):
    r = y / H
    if r < 0.4:
        t = r / 0.4
        col = (int(10 + 50*t), int(15 + 25*t), int(50 + 40*t))
    elif r < 0.7:
        t = (r - 0.4) / 0.3
        col = (int(60 + 160*t), int(40 + 70*t), int(90 - 20*t))
    else:
        t = (r - 0.7) / 0.3
        col = (int(220 + 20*t), int(110 + 50*t), int(70 - 20*t))
    draw.line([(0, y), (W, y)], fill=col)

# Stars
import random
rng = random.Random(99)
for _ in range(80):
    sx = rng.randint(0, W)
    sy = rng.randint(0, int(H*0.38))
    bright = rng.randint(180, 255)
    draw.ellipse([sx-1, sy-1, sx+1, sy+1], fill=(bright, bright, min(255, bright+20)))

# Moon glow
mx, my = int(W*0.80), int(H*0.20)
for r in range(70, 22, -5):
    a = int(20 * (1 - r/70))
    draw.ellipse([mx-r, my-r, mx+r, my+r], fill=(255, 220, 130))
draw.ellipse([mx-22, my-22, mx+22, my+22], fill=(255, 248, 200))

# Mountain layers
x_arr = list(range(W))

def mt(x, base, amps, freqs, phases):
    y = base
    for a, f, p in zip(amps, freqs, phases):
        y -= a * math.sin(2*math.pi*f*x + p)
    return int(y)

layers = [
    dict(base=H*0.50, amps=[H*0.12, H*0.06, H*0.03], freqs=[0.003,0.008,0.018], phases=[0.0,1.1,2.4], col=(65,50,85)),
    dict(base=H*0.60, amps=[H*0.10, H*0.06, H*0.03], freqs=[0.004,0.010,0.022], phases=[0.9,2.2,0.4], col=(38,50,65)),
    dict(base=H*0.70, amps=[H*0.08, H*0.05, H*0.02], freqs=[0.005,0.013,0.030], phases=[1.6,0.7,3.0], col=(22,32,38)),
    dict(base=H*0.80, amps=[H*0.05, H*0.03],         freqs=[0.006,0.016],       phases=[2.1,1.3],      col=(12,20,25)),
]

for L in layers:
    for x in x_arr:
        y_top = mt(x, L['base'], L['amps'], L['freqs'], L['phases'])
        if y_top < H:
            draw.line([(x, y_top), (x, H)], fill=L['col'])

# Mist bands
for my_band, opacity in [(int(H*0.52), 40), (int(H*0.63), 30)]:
    for dy in range(20):
        alpha = int(opacity * (1 - dy/20))
        draw.line([(0, my_band+dy), (W, my_band+dy)], fill=(180, 190, 200))

# Blur for atmosphere
img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
draw = ImageDraw.Draw(img)

# Dark overlay on left for text readability
overlay = Image.new("RGBA", (W, H), (0,0,0,0))
ov = ImageDraw.Draw(overlay)
for x in range(int(W*0.65)):
    a = int(160 * (1 - x/(W*0.65))**0.5)
    ov.line([(x,0),(x,H)], fill=(0,0,0,a))
img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
draw = ImageDraw.Draw(img)

# Vignette
vig = Image.new("L", (W, H), 255)
vd = ImageDraw.Draw(vig)
for r in range(160):
    vd.ellipse([r, r, W-r, H-r], fill=min(255, int(r*1.4)))
vig = vig.filter(ImageFilter.GaussianBlur(radius=50))
dark = Image.new("RGB", (W, H), (0,0,0))
img = Image.composite(img, dark, vig)
draw = ImageDraw.Draw(img)

# ── Text ──────────────────────────────────────────────────────────────────────
def draw_text_shadow(draw, pos, text, size, color, shadow=(0,0,0)):
    # Use default font (we don't have custom fonts, but PIL has a basic built-in)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except:
        font = ImageFont.load_default()
    x, y = pos
    # Shadow
    for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2),(0,3),(3,0)]:
        draw.text((x+dx, y+dy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=color)
    return font

def draw_text_light(draw, pos, text, size, color=(200,200,220)):
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        font = ImageFont.load_default()
    x, y = pos
    for dx, dy in [(-1,-1),(1,1)]:
        draw.text((x+dx, y+dy), text, font=font, fill=(0,0,0))
    draw.text((x, y), text, font=font, fill=color)

# Channel name
draw_text_shadow(draw, (60, 80), "山海電台", 68, (255, 245, 200), (0,0,0))
draw_text_light(draw, (62, 158), "Taiwan Mountain Radio", 28, (200, 190, 230))

# Divider line
draw.line([(60, 202), (500, 202)], fill=(255, 200, 100, 180), width=2)

# Main title
draw_text_shadow(draw, (60, 222), "太魯閣峽谷晨光", 58, (255, 255, 255), (0,0,0))
draw_text_light(draw, (62, 294), "Taroko Gorge  ·  Dawn Ambience", 26, (200, 215, 240))

# Duration badge
badge_x, badge_y = 60, 360
draw.rounded_rectangle([badge_x, badge_y, badge_x+130, badge_y+44], radius=8, fill=(0,0,0,160))
draw_text_shadow(draw, (badge_x+12, badge_y+8), "▶  1 小時", 24, (255, 220, 100), (0,0,0))

# Genre badge
draw.rounded_rectangle([badge_x+148, badge_y, badge_x+320, badge_y+44], radius=8, fill=(40,60,80,180))
draw_text_light(draw, (badge_x+160, badge_y+8), "Indie Folk · Ambient", 22, (180, 220, 255))

# Bottom tag line
draw_text_light(draw, (60, H-60), "讀書 · 工作 · 療癒放鬆  |  No Copyright", 22, (160, 180, 200))

img.save(OUT, quality=97)
print(f"Thumbnail saved: {OUT}")
print(f"Size: {os.path.getsize(OUT)//1024} KB")
