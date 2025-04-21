import os
import subprocess
import sys
import logging


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def download_and_merge(url: str, start: str, end: str):
    VIDEO_FORMAT = "311"
    AUDIO_FORMAT = "234"
    VIDEO_FILE = os.path.abspath("video_temp.mp4")
    AUDIO_FILE = os.path.abspath("audio_temp.mp4")
    OUTPUT_FILE = os.path.abspath("clipped.mp4")
    print("FFmpeg is running from:", os.getcwd())
    # Download video
    logger.info(f"Downloading video from {start} to {end}...")
    video_cmd = [
        "yt-dlp", "--quiet", "--no-warnings",
        "--no-part",
        "--download-sections", f"*{start}-{end}",
        "-f", VIDEO_FORMAT,
        "-o", VIDEO_FILE,
        url
    ]
    subprocess.run(video_cmd, check=True, stdout=subprocess.DEVNULL)
    print(f"Downloading audio from {start} to {end}...")
    audio_cmd = [
        "yt-dlp",
        "--no-part",
        "--download-sections", f"*{start}-{end}",
        "-f", AUDIO_FORMAT,
        "-o", AUDIO_FILE,
        url
    ]
    subprocess.run(audio_cmd, check=True)
    if not os.path.isfile(VIDEO_FILE) or not os.path.isfile(AUDIO_FILE):
        print("Error: One or both files failed to download.")
        sys.exit(1)
    for f in [VIDEO_FILE, AUDIO_FILE]:
        if subprocess.run(["ffprobe", "-v", "error", "-i", f], stdout=subprocess.DEVNULL).returncode != 0:
            print(f"Invalid or unreadable file: {f}")
            sys.exit(1)
    print("Files are valid. Proceeding to merge...")
    print("Merging video and audio...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", VIDEO_FILE,
        "-i", AUDIO_FILE,
        "-c", "copy",
        OUTPUT_FILE
    ]
    subprocess.run(ffmpeg_cmd, check=True, stdin=subprocess.DEVNULL)
    print("Cleaning up...")
    os.remove(VIDEO_FILE)
    os.remove(AUDIO_FILE)
    print(f"Done! Saved as {OUTPUT_FILE}")