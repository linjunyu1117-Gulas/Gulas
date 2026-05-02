#!/usr/bin/env bash
# Build final 1-hour YouTube video
# Loops the 12-sec visual and 3-min music track to exactly 1 hour

set -e
MUSIC="/home/user/Gulas/assets/music/taiwan_folk_ambient.wav"
LOOP_VIDEO="/home/user/Gulas/assets/video/taiwan_mountain_loop.mp4"
OUTPUT="/home/user/Gulas/assets/output/taiwan_mountain_radio_vol1.mp4"

mkdir -p "$(dirname "$OUTPUT")"

DURATION=3600   # 1 hour in seconds

echo "Building 1-hour video..."
echo "  Visual: $LOOP_VIDEO"
echo "  Music:  $MUSIC"
echo "  Output: $OUTPUT"
echo ""

ffmpeg -y \
  -stream_loop -1 -i "$LOOP_VIDEO" \
  -stream_loop -1 -i "$MUSIC" \
  -t $DURATION \
  -c:v libx264 -preset fast -crf 23 \
  -c:a aac -b:a 192k \
  -pix_fmt yuv420p \
  -movflags +faststart \
  -shortest \
  "$OUTPUT"

SIZE=$(du -sh "$OUTPUT" | cut -f1)
echo ""
echo "Done! Output: $OUTPUT ($SIZE)"
echo "Duration: 1 hour"
