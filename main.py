#!/usr/bin/env python3

from tqdm import tqdm
from pydub import AudioSegment

import configparser
import random

from utils import download_mp3, get_song, load_music_list, set_music_list, is_url

# Init audio
final_audio = 0
countdown_audio = []

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

# Loads information about songs
music_list = load_music_list()
column_names = list(music_list[0].keys())

# Shuffle order of the songs
if random_order:
    random.shuffle(music_list)

# Downloading songs
download_occurred = False 
for row in tqdm(music_list, desc="Downloading songs"):

    # If URL was uses, download it 
    if is_url(row['name']):
        download_mp3(row, music_folder)
        download_occurred = True

# Updates CSV file if neccessary (URL->files)
if download_occurred:
    set_music_list(music_list, column_names)

# Gets all music files
for row in tqdm(music_list, desc="Cooking the result"):

    current_song = get_song(row, music_folder)

    # If file exists
    if current_song != None:

        # Puts countdown at the start and in between songs
        if len(countdown_audio) > 0:
            final_audio += countdown_audio
        
        # Adds song to the final audio
        final_audio += current_song

# Export the audio
final_audio.export("random_dance.mp3", format="mp3")

# UwU
print("Random dance was successfully created!")