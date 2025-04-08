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
from file_upload import upload_to_gofile


load_dotenv()

def process_video_task(youtube_url, start_time, end_time, player_names, email):
    print("Starting job...")
    start_clock = time.time()
    os.environ["CUDA_VISIBLE_DEVICES"] = "2"
    print("CUDA Available:", torch.cuda.is_available())
    video_path = "clipped.mp4"
    # trimmed_path_video = "video_trimmed.mp4"
    temp_path_video = "video_temp.mp4"
    temp_path_audio = "audio_temp.mp4"
    json_log = "player_log.json"
    extractor = HighlightExtractor(video_path)
    extractor.delete_files(delete_files=[temp_path_video, video_path, temp_path_audio])
    download_and_merge(youtube_url, start_time, end_time)
    # duration = hhmmss_to_seconds(start_time, end_time)
    # extractor.trim_video(video_path, trimmed_path_video, duration=duration)
    extractor.process_video(video_path, json_log, player_names)
    extractor.split_video_by_speaker_log(video_path, json_log)
    print(f"✅ Job complete in {round(time.time() - start_clock, 2)} sec.")
    zip_file_location = create_zip()
    gofile_response = upload_to_gofile(zip_file_location,os.getenv("GOFILE_TOKEN"))
    # "downloadPage": file_info["downloadPage"],
    #         "fileId": file_info["id"],
    #         "fileName": file_info["name"],
    #         "folderId": file_info["parentFolder"],
    send_email_with_zip_link(email,gofile_response["downloadPage"])


def create_zip(output_zip_path="results.zip"):
    with zipfile.ZipFile(output_zip_path, 'w') as zipf:
        for root, dirs, files in os.walk("clips"):
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, os.path.relpath(filepath, "clips"))
        zipf.write("player_log.json")

    return os.path.abspath(output_zip_path)



def send_email_with_zip_link(to_email, zip_download_url):
    msg = EmailMessage()
    msg["Subject"] = "🎥 Your Valorant Highlights Are Ready!"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = to_email

    msg.set_content(f"""\
        Hi!

        Your Valorant highlights are ready. 🎮

        🔗 Download your ZIP file from the link below:
        {zip_download_url}

        Enjoy!
        """)
    with smtplib.SMTP_SSL(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as smtp:
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        smtp.send_message(msg)
    print(f"Email with download link sent to {to_email}")