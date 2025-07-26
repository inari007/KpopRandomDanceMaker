#!/usr/bin/env python3

from tqdm import tqdm
from pydub import AudioSegment

import configparser
import random

from utils import download_mp3, get_song, load_music_list, is_url

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

# Shuffle order of the songs
if random_order:
    random.shuffle(music_list)

# Gets all music files
for row in tqdm(music_list, desc="Cooking the result"):

    # If URL was uses, download it 
    if is_url(row['name']):
        download_mp3(row, music_folder)
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