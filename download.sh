#!/bin/bash

# Usage:
# ./yt_clip_merge.sh "https://www.youtube.com/watch?v=dXYllcjtR-o" "00:10:00" "00:15:00"

URL="$1"
START="$2"
END="$3"

VIDEO_FORMAT="311"  # 720p video-only DASH format (check with yt-dlp -F <url>)
AUDIO_FORMAT="234"  # audio-only format (replace with 233 or 140 if not available)

VIDEO_FILE="$(pwd)/video_temp.mp4"
AUDIO_FILE="$(pwd)/audio_temp.mp4"
OUTPUT_FILE="$(pwd)/clipped.mp4"
echo "FFmpeg is running from: $(pwd)"
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

# ✅ FIXED: Add missing fi
if [ ! -f "$VIDEO_FILE" ] || [ ! -f "$AUDIO_FILE" ]; then
    echo "❌ Error: One or both files failed to download."
    exit 1
fi

# Check if files are valid media (using ffprobe)
if ! ffprobe -v error -i "$VIDEO_FILE" > /dev/null; then
    echo "❌ Invalid video file format or unreadable: $VIDEO_FILE"
    exit 1
fi

if ! ffprobe -v error -i "$AUDIO_FILE" > /dev/null; then
    echo "❌ Invalid audio file format or unreadable: $AUDIO_FILE"
    exit 1
fi

# ls -lh "$VIDEO_FILE"
# ls -lh "$AUDIO_FILE"


# echo "✅ Files are valid. Proceeding to merge..."

# echo "🎬 Merging video and audio..."
# ffmpeg -y -loglevel debug -i "$VIDEO_FILE" -i "$AUDIO_FILE" -c copy "$OUTPUT_FILE"

# echo "🧹 Cleaning up..."
# rm -f "$VIDEO_FILE" "$AUDIO_FILE"

# echo "✅ Done! Saved as $OUTPUT_FILE"
