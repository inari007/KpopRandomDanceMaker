from pydub import AudioSegment

import yt_dlp
import os
import csv
import glob
import os
import re
import time

# Downloads audio from youtube video and saves it as mp3
def download_mp3(row, music_folder):

    # Gets only title of the song
    sanizedTitle = get_video_safely(get_video_title, row['name'], music_folder)
    if sanizedTitle == False:
        return

    # If was already downloaded
    filepath = music_folder + sanizedTitle + ".mp3"
    if os.path.exists(filepath):
        row['name'] = sanizedTitle
        return
    
    # Gets content of the song
    if get_video_safely(get_video_content, row['name'], music_folder) == False:
        return
    
    # Set title instead of URL
    row['name'] = sanizedTitle


# Tries 3 times and ensures that downloading doesn't kill the process
def get_video_safely(get_vid_func, url, music_folder, attempts=3):
    while attempts > 0:
        try:
            return get_vid_func(url, music_folder)
        except:
            attempts = attempts - 1
            time.sleep(2)
    return False

# Gets title of the song
def get_video_title(url, music_folder):
    with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'audio')
        sanizedTitle = sanitizeFilename(title)
        return sanizedTitle
    
# Gets content of the song (downloads mp3)
def get_video_content(url, music_folder):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{music_folder}%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
    }

    # Downloads the video
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return True

# Removes sussy characters
def removeIllegalCharacters(title):
    return title.replace('\u00A0', ' ').replace('\uFF1A', ':')


# Makes title of the video saveable on the Windows
def sanitizeFilename(title):
    return title.replace("/", "⧸").replace('\uFF1A', ':')


# Parses CSV file
def load_music_list(filepath='./list.csv'):
    with open(filepath, newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))


# Sets CSV file
def set_music_list(music_list, column_names, filepath='./list.csv'):
    with open(filepath, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=column_names)
        writer.writeheader()
        writer.writerows(music_list)


# Gets audio of the song in the row
def get_song(row, music_folder):
    mp3_files=glob.glob(music_folder + "*.mp3")
    current_song = row['name'] + ".mp3"

    # Finds every song file that matches current row from the list 
    for file in mp3_files:

        filename = os.path.basename(file)
        if filename == current_song:

            # Loads audio from the file
            audio = AudioSegment.from_mp3(music_folder + filename)

            # Split time string into minutes and seconds
            start_minutes, start_seconds = map(int, row['start'].split(":"))
            end_minutes, end_seconds = map(int, row['end'].split(":"))

            # Convert to total miniseconds
            total_start_time = (start_minutes * 60 + start_seconds) * 1000
            total_end_time = (end_minutes * 60 + end_seconds) * 1000

            return audio[total_start_time:total_end_time], True
    return row['name'], False


# Checks if string is URL 
def is_url(string):
    regex = re.compile(
        r'^(https?://)?' 
        r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        r'(/[^\s]*)?$',
        re.IGNORECASE
    )
    return re.match(regex, string) is not None
