#!/usr/bin/env bash
# Build 山水鋼琴 — 1-hour ambient video
# Loops the 16-sec ink landscape visual + 3-min piano track

set -e
MUSIC="/home/user/Gulas/assets/music/piano_shanshui.wav"
LOOP_VIDEO="/home/user/Gulas/assets/video/shanshui_loop.mp4"
OUTPUT="/home/user/Gulas/assets/output/shanshui_piano_vol1.mp4"

mkdir -p "$(dirname "$OUTPUT")"

DURATION=3600   # 1 hour

echo "========================================="
echo "  山水鋼琴 — Shanshui Piano Video Build"
echo "========================================="
echo "  Visual : $LOOP_VIDEO"
echo "  Music  : $MUSIC"
echo "  Output : $OUTPUT"
echo ""

# Step 1: Generate piano music
echo "[1/3] Generating piano music..."
python3 /home/user/Gulas/generate_music_piano.py

# Step 2: Generate ink landscape visual
echo "[2/3] Generating ink landscape visuals..."
python3 /home/user/Gulas/generate_visual_shanshui.py

# Step 3: Combine into 1-hour video
echo "[3/3] Assembling 1-hour video..."
ffmpeg -y \
  -stream_loop -1 -i "$LOOP_VIDEO" \
  -stream_loop -1 -i "$MUSIC" \
  -t $DURATION \
  -c:v libx264 -preset fast -crf 22 \
  -c:a aac -b:a 192k \
  -pix_fmt yuv420p \
  -movflags +faststart \
  -shortest \
  "$OUTPUT"

SIZE=$(du -sh "$OUTPUT" | cut -f1)
echo ""
echo "========================================="
echo "  Done! Output: $OUTPUT  ($SIZE)"
echo "  Duration: 1 hour"
echo "========================================="
