#!/bin/bash

# Usage:
# ./yt_clip_merge.sh "https://www.youtube.com/watch?v=dXYllcjtR-o" "00:10:00" "00:15:00"

URL="$1"
START="$2"
END="$3"

VIDEO_FORMAT="311"  # 720p video-only DASH format (check with yt-dlp -F <url>)
AUDIO_FORMAT="234"  # audio-only format (replace with 233 or 140 if not available)

VIDEO_FILE="video_temp.mp4"
AUDIO_FILE="audio_temp.mp4"
OUTPUT_FILE="clipped.mp4"

# Validate arguments
if [ $# -ne 3 ]; then
    echo "Usage: $0 <YouTube URL> <Start Time HH:MM:SS> <End Time HH:MM:SS>"
    exit 1
fi

echo "📥 Downloading video from $START to $END..."
yt-dlp --quiet --no-warnings \
  --download-sections "*$START-$END" \
  -f "$VIDEO_FORMAT" \
  -o "$VIDEO_FILE" "$URL"

echo "🎧 Downloading audio from $START to $END..."
yt-dlp --quiet --no-warnings \
  --download-sections "*$START-$END" \
  -f "$AUDIO_FORMAT" \
  -o "$AUDIO_FILE" "$URL"

# Check if files exist
if [ ! -f "$VIDEO_FILE" ] || [ ! -f "$AUDIO_FILE" ]; then
    echo "❌ Error: One or both files failed to download."
    exit 1
fi

echo "🎬 Merging video and audio..."
ffmpeg -y -i "$VIDEO_FILE" -i "$AUDIO_FILE" -c copy "$OUTPUT_FILE"

echo "🧹 Cleaning up..."
rm -f "$VIDEO_FILE" "$AUDIO_FILE"

echo "✅ Done! Saved as $OUTPUT_FILE"
