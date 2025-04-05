import subprocess
from HighlightExtractor import HighlightExtractor
import os, time, torch, multiprocessing as mp
import zipfile
import smtplib
from dotenv import load_dotenv
from email.message import EmailMessage
from video_download import download_and_merge
import os
import subprocess



load_dotenv()


def process_video_task(youtube_url, start_time, end_time, player_names, email):
    print("Starting job...")
    start_clock = time.time()

    os.environ["CUDA_VISIBLE_DEVICES"] = "6"
    print("CUDA Available:", torch.cuda.is_available())
    video_path = "clipped.mp4"
    # trimmed_path_video = "video_trimmed.mp4"
    temp_path_video = "video_temp.mp4"
    temp_path_audio = "audio_temp.mp4"
    json_log = "player_log.json"
    # mp.set_start_method("spawn", force=True)

    extractor = HighlightExtractor(video_path)
    extractor.delete_files(delete_files=[temp_path_video, video_path, temp_path_audio])
    download_and_merge(youtube_url, start_time, end_time)
    # duration = hhmmss_to_seconds(start_time, end_time)
    # extractor.trim_video(video_path, trimmed_path_video, duration=duration)
    extractor.process_video(video_path, json_log, player_names)
    extractor.split_video_by_speaker_log(video_path, json_log)
    print(f"✅ Job complete in {round(time.time() - start_clock, 2)} sec.")
    create_zip()
    send_email_with_zip(email)


def create_zip(output_zip_path="results.zip"):
    with zipfile.ZipFile(output_zip_path, 'w') as zipf:
        for root, dirs, files in os.walk("clips"):
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, os.path.relpath(filepath, "clips"))
        zipf.write("player_log.json")


def send_email_with_zip(to_email, zip_file_path="results.zip"):
    msg = EmailMessage()
    msg["Subject"] = "🎥 Your Valorant Highlights Are Ready!"
    msg["From"] = "mudit.alwar31@gmail.com"
    msg["To"] = to_email
    msg.set_content("Hi! Your video highlights are ready. The zip is attached.")
    # with open(zip_file_path, "rb") as f:
    #     msg.add_attachment(f.read(), maintype="application", subtype="zip", filename="results.zip")
    with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as smtp:
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        smtp.send_message(msg)
