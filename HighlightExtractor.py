import concurrent
import subprocess
import cv2
import numpy as np
import os
import easyocr
import json
import torch.multiprocessing as mp
from rapidfuzz import fuzz, process
from collections import defaultdict


class HighlightExtractor:
    def __init__(self, video_path ,output_folder="speaker_boxes"):
        self.video_path = video_path
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        self.reader = easyocr.Reader(['en'], gpu = True)
        self.player_log = []

    def merge_player_intervals(self):
        if not self.player_log:
            return []
        merged = []
        current_player = self.player_log[0]["player"]
        start_time = self.player_log[0]["timestamp"]
        end_time = self.player_log[0]["timestamp"]
        for entry in self.player_log[1:]:
            if entry["player"] == current_player:
                end_time = entry["timestamp"]
            else:
                merged.append({
                    "player": current_player,
                    "start": round(start_time, 2),
                    "end": round(end_time, 2)
                })
                current_player = entry["player"]
                start_time = entry["timestamp"]
                end_time = entry["timestamp"]
        merged.append({
            "player": current_player,
            "start": round(start_time, 2),
            "end": round(end_time, 2)
        })
        self.player_log = merged

    def detect_player_container(self, frame, frame_count):
        """Returns bounding box of the player container ROI"""
        # print(f"Extracting player name ROI at frame {frame_count}...")
        height, width, _ = frame.shape
        roi_top = int(height * 0.88)
        roi_bottom = int(height * 0.925)
        roi_left = int(width * 0.274)
        roi_right = int(width * 0.4)
        return (roi_left, roi_top, roi_right - roi_left, roi_bottom - roi_top)

    def extract_frames(self, video_path):
        """Extracts every 11th frame from the video (i.e., skips 10 frames after each read)."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print("Error: Unable to open video file")
            return [], []
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        print(f"FPS: {fps}")
        print(f"Total frames: {frame_count}")
        print(f"Video duration (s): {duration}")
        frames, timestamps = [], []
        i = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
            timestamps.append(round(i / fps, 2))
            for _ in range(5):
                cap.read()
                i += 1
            i += 1
        cap.release()
        return frames, timestamps

    def match_player_name(self, ocr_name, known_names, threshold=80):
        lowercase_map = {name.lower(): name for name in known_names}
        lowercase_names = list(lowercase_map.keys())
        ocr_name_lower = ocr_name.lower()
        match = process.extractOne(ocr_name_lower, lowercase_names, scorer=fuzz.ratio)
        if match and match[1] >= threshold:
            return lowercase_map[match[0]]
        return None

    def delete_files(self, delete_files):
        if delete_files:
            for file in delete_files:
                local_path = os.path.join(os.getcwd(), file)  # Force local dir
                if os.path.exists(local_path) and os.path.isfile(local_path):
                    os.remove(local_path)
                    print(f"Deleted: {file}")

        print("files deleted successfully")

    def trim_video(self, input_file, output_file, duration=1):
        command = [
            "ffmpeg",
            "-i", input_file,
            "-t", str(duration), 
            "-c:a", "copy",
            "-c:v", "copy",
            output_file
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("files cropped successfully")

    def save_player_log_to_json(self, json_path):
        try:
            with open(json_path, 'w') as f:
                json.dump(self.player_log, f, indent=4)
            print(f"Speaker log saved to {json_path}")
        except Exception as e:
            print(f"Failed to save speaker log: {e}")

    def split_video_by_speaker_log(self, video_path, speaker_json_path, output_dir="clips"):
        # Load the speaker log
        with open(speaker_json_path, 'r') as f:
            speaker_log = json.load(f)

        os.makedirs(output_dir, exist_ok=True)
        VIDEO_FILE = os.path.abspath(video_path)

        # Group entries by player
        player_intervals = defaultdict(list)
        for entry in speaker_log:
            player = entry["player"]
            if player is not None:
                player_intervals[player].append((entry["start"], entry["end"]))

        # For each player, extract all their clips
        for player, intervals in player_intervals.items():
            safe_player = player.replace(" ", "_")  # For file naming
            temp_files = []

            print(f"🎬 Processing {player}...")

            for idx, (start, end) in enumerate(intervals):
                duration = round(end - start, 2)
                temp_clip = os.path.abspath(os.path.join(output_dir, f"{safe_player}_part{idx}.mp4"))
                print(temp_clip)
                temp_files.append(temp_clip)
                print(temp_files)
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss", str(start),
                    "-i", VIDEO_FILE,
                    "-t", str(duration),
                    "-c:v", "copy",
                    "-c:a", "copy",
                    temp_clip
                ]
                subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
                print("video saved successfully")

            # Merge all parts into one video using ffmpeg concat
            if len(temp_files) == 1:
                os.rename(temp_files[0], os.path.join(output_dir, f"{safe_player}.mp4"))
            else:
                list_file = os.path.abspath(os.path.join(output_dir, f"{safe_player}_list.txt"))
                with open(list_file, "w") as f:
                    for clip in temp_files:
                        f.write(f"file '{os.path.abspath(clip)}'\n")

                merged_path =  os.path.abspath(os.path.join(output_dir, f"{safe_player}.mp4"))
                print(f"Merging {len(temp_files)} parts into {merged_path}...")
                subprocess.run([
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
                    "-c", "copy", merged_path
                ],  check=True, stdin=subprocess.DEVNULL)

                # Clean up
                os.remove(list_file)
                for clip in temp_files:
                    os.remove(clip)

            print(f"✅ Saved: {safe_player}.mp4")

    # def process_video(self, video_path):
    #     """ Process video and extract speaker names in parallel """
    #     frames, timestamps = self.extract_frames(video_path)

    #     with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
    #         future_to_index = {
    #             executor.submit(self.process_frame, frame, timestamps[i], i): i
    #             for i, frame in enumerate(frames)
    #         }
    #         for future in concurrent.futures.as_completed(future_to_index):
    #             i = future_to_index[future]
    #             try:
    #                 result = future.result()
    #                 if result and result["speaker"]:
    #                     if self.player_log and self.player_log[-1]["timestamp"] == result["timestamp"]:
    #                         combined_speakers = self.player_log[-1]["speaker"] + result["speaker"]
    #                         self.player_log[-1]["speaker"] = self.get_unique_speaker_names(combined_speakers)
    #                     else:
    #                         self.player_log.append(result)
    #             except Exception as e:
    #                 print(f"Error processing frame {i}: {e}")
        
    #     print(self.player_log)
                    
    #     executor.shutdown(wait=True)


    def keep_text_regions_only(self, roi, padding=5, confidence_threshold=0.4):
        results = self.reader.readtext(roi, detail=1)
        mask = np.zeros_like(roi)
        for (bbox, text, conf) in results:
            if conf < confidence_threshold:
                continue
            x_coords = [int(p[0]) for p in bbox]
            y_coords = [int(p[1]) for p in bbox]
            x_min = max(min(x_coords) - padding, 0)
            x_max = min(max(x_coords) + padding, roi.shape[1])
            y_min = max(min(y_coords) - padding, 0)
            y_max = min(max(y_coords) + padding, roi.shape[0])
            mask[y_min:y_max, x_min:x_max] = roi[y_min:y_max, x_min:x_max]
        gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        coords = cv2.findNonZero(gray)
        if coords is not None:
            x, y, w, h = cv2.boundingRect(coords)
            return (x, y, w, h), results
        else:
            return None, results

    # def process_video(self, video_path, player_json, known_players=[]):
    #     """ Process video and extract speaker names sequentially (no multiprocessing). """
    #     frames, timestamps = self.extract_frames(video_path)
    #     for i, frame in enumerate(frames):
    #         try:
    #             result = self.process_frame(frame, timestamps[i], i)
    #             if result and result.get("player"):
    #                 if self.match_player_name(result['player'], known_players, 50) is None:
    #                     print(f"Unrecognized player: {result['player']}")
    #                     # result = self.detect_player_container(frame, 0)
    #                     # if result is None:
    #                     #     return None
    #                     # x, y, w, h = result
    #                     # roi_x_start = x
    #                     # roi_x_end = x + w
    #                     # roi_y_start = y
    #                     # roi_y_end = y + h
    #                     # roi = frame[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
    #                     # result, text = self.keep_text_regions_only(roi)
    #                     # cv2.imshow("Merged Text Mask", result)
    #                     # key = cv2.waitKey(0) & 0xFF
    #                     # if key == ord('q'):
    #                     #     cv2.destroyAllWindows()
    #                     #     exit()
    #                 self.player_log.append({
    #                     "timestamp": result["timestamp"],
    #                     "player": self.match_player_name(result['player'], known_players, 50)
    #                 })
    #         except Exception as e:
    #             print(f"Error processing frame {i}: {e}")
    #     self.merge_player_intervals()
    #     self.save_player_log_to_json(player_json)


    def process_video(self, video_path, player_json, known_players=[]):
        """Process video and extract speaker names using multiprocessing (10 workers)."""
        frames, timestamps = self.extract_frames(video_path)

        mp.set_start_method("spawn", force=True)
        with concurrent.futures.ProcessPoolExecutor(max_workers=10) as executor:
            future_to_index = {
                executor.submit(self.process_frame, frame, timestamps[i], i): i
                for i, frame in enumerate(frames)
            }

            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    result = future.result()
                    if result and result.get("player"):
                        matched_name = self.match_player_name(result["player"], known_players, 50)

                        if matched_name is None:
                            print(f"Unrecognized player: {result['player']}")
                            # Optional debug visualization (uncomment to use)
                            # result = self.detect_player_container(frames[i], i)
                            # if result is not None:
                            #     x, y, w, h = result
                            #     roi = frames[i][y:y+h, x:x+w]
                            #     result, text = self.keep_text_regions_only(roi)
                            #     cv2.imshow("Unrecognized Player ROI", roi)
                            #     if cv2.waitKey(0) & 0xFF == ord('q'):
                            #         cv2.destroyAllWindows()
                            #         exit()
                        else:
                            self.player_log.append({
                                "timestamp": result["timestamp"],
                                "player": matched_name
                            })
                except Exception as e:
                    print(f"Error processing frame {i}: {e}")

        self.merge_player_intervals()
        self.save_player_log_to_json(player_json)
        executor.shutdown(wait=True)

    def process_frame(self, frame, timestamp, frame_index):
        """Process a single frame and extract speaker names."""
        result = self.detect_player_container(frame, frame_index)
        if result is None:
            return None
        x, y, w, h = result
        roi_x_start = x
        roi_x_end = x + w
        roi_y_start = y
        roi_y_end = y + h
        roi = frame[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
        result_final, text = self.keep_text_regions_only(roi)
        if result_final is None:
            return None
        x, y, w, h = result_final
        texts = [text for (_, text, conf) in text if conf >= 0.4]
        final_name = " ".join(texts).strip() if texts else None
        # print(final_name)
        # print(result_final)
        # cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # print(f"Detected bbox: {result}")
        # print(self.extract_speaker_name(frame, result))
        # cv2.imshow("Detected Player Container", frame)
        # if cv2.waitKey(0) & 0xFF == ord('q'):
        #     cv2.destroyAllWindows()
        # print(self.extract_speaker_name(frame, result_final))
        return {"timestamp": timestamp, "player": final_name}


# if __name__ == "__main__":
#     print("CPU Count : ", os.cpu_count()) 
#     # mp.set_start_method("spawn", force=True)
#     video_path = "clipped.mp4"
#     trimmed_video_path = "trimmed_video.mp4"
#     image_path = "image1.png"
#     player_json_path = "player_json.json"
#     known_players = [
#     "T1 stax",
#     "T1 iZu",
#     "T1 Sylvan",
#     "T1 Meteor",
#     "T1 BuZz",
#     "EDG Smoggy",
#     "EDG CHICHOO",
#     "EDG ZmjjKK",
#     "EDG nobody",
#     "EDG Jieni7"
#     ]
#     # frame = cv2.imread(image_path)
#     extractor = HighlightExtractor(video_path)
#     extractor.trim_video(video_path,trimmed_video_path, duration=300, delete_files=[trimmed_video_path])
#     extractor.process_video(trimmed_video_path, player_json_path, known_players)
#     extractor.split_video_by_speaker_log(video_path, player_json_path)
#     # extractor.process_frame(frame, 0, 0)
