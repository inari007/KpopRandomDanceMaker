#!/usr/bin/env python3

from pydub import AudioSegment
import csv
import glob
import os

# Parses CSV file
def load_music_list(filepath='./list.csv'):
    with open(filepath, newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))

# Gets audio of the song in the row
def get_song(row):
    mp3_files=glob.glob("./music/*.mp3")

    # Finds every song file that matches current row from the list 
    for file in mp3_files:
        if os.path.basename(file) == (row['name'] + ".mp3"):

            # Loads audio from the file
            audio = AudioSegment.from_mp3("music/" + row['name'] + ".mp3")

            # Split time string into minutes and seconds
            start_minutes, start_seconds = map(int, row['start'].split(":"))
            end_minutes, end_seconds = map(int, row['end'].split(":"))

            # Convert to total miniseconds
            total_start_time = (start_minutes * 60 + start_seconds) * 1000
            total_end_time = (end_minutes * 60 + end_seconds) * 1000

            return audio[total_start_time:total_end_time]
    return None

# Loads information about songs
music_list = load_music_list()

# Init audio
final_audio = AudioSegment.empty()

# Gets all music files
for row in music_list:
    current_song = get_song(row)

    # If file exists
    if current_song != None:
        final_audio += current_song

# Export the audio
final_audio.export("random_dance.mp3", format="mp3")