import os
import subprocess
import sys
def download_and_merge(url: str, start: str, end: str):
    # Constants
    VIDEO_FORMAT = "311"
    AUDIO_FORMAT = "234"
    VIDEO_FILE = os.path.abspath("video_temp.mp4")
    AUDIO_FILE = os.path.abspath("audio_temp.mp4")
    OUTPUT_FILE = os.path.abspath("clipped.mp4")
    print("📂 FFmpeg is running from:", os.getcwd())
    # Download video
    print(f"📥 Downloading video from {start} to {end}...")
    video_cmd = [
        "yt-dlp", "--quiet", "--no-warnings",
        "--no-part",
        "--download-sections", f"*{start}-{end}",
        "-f", VIDEO_FORMAT,
        "-o", VIDEO_FILE,
        url
    ]
    subprocess.run(video_cmd, check=True)

    # Download audio
    print(f"🎧 Downloading audio from {start} to {end}...")
    audio_cmd = [
        "yt-dlp", "--quiet", "--no-warnings",
        "--no-part",
        "--download-sections", f"*{start}-{end}",
        "-f", AUDIO_FORMAT,
        "-o", AUDIO_FILE,
        url
    ]
    subprocess.run(audio_cmd, check=True)

    # Validate files exist
    if not os.path.isfile(VIDEO_FILE) or not os.path.isfile(AUDIO_FILE):
        print("❌ Error: One or both files failed to download.")
        sys.exit(1)

    # Validate media with ffprobe
    for f in [VIDEO_FILE, AUDIO_FILE]:
        if subprocess.run(["ffprobe", "-v", "error", "-i", f], stdout=subprocess.DEVNULL).returncode != 0:
            print(f"❌ Invalid or unreadable file: {f}")
            sys.exit(1)

    print("✅ Files are valid. Proceeding to merge...")

    # Merge video and audio
    print("🎬 Merging video and audio...")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", VIDEO_FILE,
        "-i", AUDIO_FILE,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k",
        OUTPUT_FILE
    ]
    subprocess.run(ffmpeg_cmd, check=True, stdin=subprocess.DEVNULL)

    # Clean up
    print("🧹 Cleaning up...")
    os.remove(VIDEO_FILE)
    os.remove(AUDIO_FILE)

    print(f"✅ Done! Saved as {OUTPUT_FILE}")