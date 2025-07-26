from pydub import AudioSegment

import yt_dlp
import os
import csv
import glob
import os
import re

# Downloads audio from youtube video and saves it as mp3
def download_mp3(row, music_folder):

    # Gets only title of the song
    with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
        info = ydl.extract_info(row['name'], download=False)
        title = info.get('title', 'audio')
        sanizedTitle = sanitizeFilename(title)
        filepath = music_folder + sanizedTitle + ".mp3"

    # If was already downloaded
    if os.path.exists(filepath):
        row['name'] = sanizedTitle
        return

    # Download parameters
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
        ydl.download(row['name'])

    row['name'] = sanizedTitle


# Converts filename back to the original title
def unsanitizeFilename(title):
    return title.replace("⧸", "/")


# Makes title of the video saveable on the Windows
def sanitizeFilename(title):
    return title.replace("/", "⧸")


# Parses CSV file
def load_music_list(filepath='./list.csv'):
    with open(filepath, newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))


# Gets audio of the song in the row
def get_song(row, music_folder):
    mp3_files=glob.glob(music_folder + "*.mp3")

    # Finds every song file that matches current row from the list 
    for file in mp3_files:

        filename = os.path.basename(file)
        if filename == (row['name'] + ".mp3"):

            # Loads audio from the file
            audio = AudioSegment.from_mp3(music_folder + filename)

            # Split time string into minutes and seconds
            start_minutes, start_seconds = map(int, row['start'].split(":"))
            end_minutes, end_seconds = map(int, row['end'].split(":"))

            # Convert to total miniseconds
            total_start_time = (start_minutes * 60 + start_seconds) * 1000
            total_end_time = (end_minutes * 60 + end_seconds) * 1000

            return audio[total_start_time:total_end_time]
    return None

# Checks if string is URL 
def is_url(string):
    regex = re.compile(
        r'^(https?://)?' 
        r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        r'(/[^\s]*)?$',
        re.IGNORECASE
    )
    return re.match(regex, string) is not None
