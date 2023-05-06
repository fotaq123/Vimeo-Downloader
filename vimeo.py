import requests
import json
import os
import shutil
import sys
import time

if len(sys.argv) != 2:
    print("Wrong number of arguments")
    print("python3 vimeo.py <url of master.json>")
    exit()

master_json_url = sys.argv[1]
print(master_json_url)


def parse_json(json_text):
    global clip_id, audio_id, video_id, number_of_segments, segment_base_name, segment_base_ext
    json_data = json.loads(json_text)
    clip_id = json_data["clip_id"]
    videos = json_data["video"]
    highest_resolution = 0
    for video in videos:
        if video["height"] == 1080 and video["width"] == 1920 and video["framerate"] >= 20:
            video_id = video["id"]
            audio_id = video["id"]
            segments = video["segments"]
            number_of_segments = len(segments)
            segment_base_name, segment_base_ext = segments[0]["url"].split("1")
            break
        elif video["height"] > highest_resolution and video["width"] > 1919 and video["framerate"] >= 20:
            highest_resolution = video["height"]
            video_id = video["id"]
            audio_id = video["id"]
            segments = video["segments"]
            number_of_segments = len(segments)
            segment_base_name, segment_base_ext = segments[0]["url"].split("1")


base_url = master_json_url.split("video/")[0]
print(base_url)
clip_id = ""
audio_id = ""
video_id = ""
number_of_segments = ""
segment_base_name = ""
segment_base_ext = ""

r = requests.get(master_json_url)

parse_json(r.text)

out_video = "segments_video_" + clip_id
out_audio = "segments_audio_" + clip_id
try:
    shutil.rmtree(out_video)
    shutil.rmtree(out_audio)
except:
    pass

if not os.path.exists(out_video):
    os.mkdir(out_video)
if not os.path.exists(out_audio):
    os.mkdir(out_audio)

print("Clip_ID: " + str(clip_id))
print("Video_ID: " + str(video_id))
print("Audio_ID: " + str(audio_id))
print("Number of Segments: " + str(number_of_segments) )
print()
print("Start Download")

def download_with_retry(url, retries=5, sleep_time=5):
    while retries > 0:
        try:
            r = requests.get(url)
            return r.content
        except requests.exceptions.RequestException:
            print(f"Error downloading segment. Retrying in {sleep_time} seconds.")
            time.sleep(sleep_time)
            retries -= 1
    print("Failed to download segment")
    return None


full_video = b""
full_audio = b""
for i in range(0, number_of_segments+1):
    # video
    current_segment_url = base_url + "video/" + str(video_id) + "/chop/" + segment_base_name + str(i) + segment_base_ext
    segment_content = download_with_retry(current_segment_url)
    if segment_content:
        with open(os.path.join(out_video, "video-" + segment_base_name + str(i+1) + segment_base_ext.split('?')[0]), "wb") as f:
            f.write(segment_content)
        full_video += segment_content

    # audio
    current_segment_url = base_url + "audio/" + str(audio_id) + "/chop/" + segment_base_name + str(i) + segment_base_ext
    segment_content = download_with_retry(current_segment_url)
    if segment_content:
        with open(os.path.join(out_audio, "audio-" + segment_base_name + str(i+1) + segment_base_ext.split('?')[0]), "wb") as f:
            f.write(segment_content)
        full_audio += segment_content

    if i % 2 == 0:
        print(str(i) + "/" + str(number_of_segments) + " downloaded")

with open(video_id + "_final_video.mp4", "wb") as f:
    f.write(full_video)

with open(video_id + "_final_audio.mp4", "wb") as f:
    f.write(full_audio)

print("Merging...")
#print("$ ffmpeg -i " + video_id + "_final_video.mp4" + " -i " + video_id + "_final_audio.mp4" + " -c copy " + clip_id + "final_video.mp4")
os.system(f'ffmpeg -i {video_id}_final_video.mp4 -i {video_id}_final_audio.mp4 -c copy {clip_id}_final_video.mp4&&rm {video_id}_final_video.mp4&&rm {video_id}_final_audio.mp4 ')
# Delete temporary directories
shutil.rmtree(out_video)
shutil.rmtree(out_audio)
