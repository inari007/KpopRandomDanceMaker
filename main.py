#!/usr/bin/env python3

from tqdm import tqdm
from pydub import AudioSegment
import csv
import glob
import os
import configparser
import random

# Init audio
final_audio = 0
countdown_audio = 0

# Parses configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Get config values
countdown_enable = config['countdown'].getboolean('enable')
random_order = config['general'].getboolean('random_order')
music_folder = config['general']['music_folder']

# Gets countdown sound
if countdown_enable:
    countdown_file_path = config['countdown']['sound_file']
    countdown_audio = AudioSegment.from_mp3(countdown_file_path)

# Parses CSV file
def load_music_list(filepath='./list.csv'):
    with open(filepath, newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))

# Gets audio of the song in the row
def get_song(row):
    mp3_files=glob.glob(music_folder + "*.mp3")

    # Finds every song file that matches current row from the list 
    for file in mp3_files:
        if os.path.basename(file) == (row['name'] + ".mp3"):

            # Loads audio from the file
            audio = AudioSegment.from_mp3(music_folder + row['name'] + ".mp3")

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

# Shuffle order of the songs
if random_order:
    random.shuffle(music_list)

# Gets all music files
for row in tqdm(music_list, desc="Cooking the result"):
    current_song = get_song(row)

    # If file exists
    if current_song != None:

        # Puts countdown at the start and in between songs
        if len(countdown_audio) > 0:
            final_audio += countdown_audio
        
        # Adds song to the final audio
        final_audio += current_song

# Export the audio
final_audio.export("random_dance.mp3", format="mp3")