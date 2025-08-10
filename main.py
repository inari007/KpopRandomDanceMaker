#!/usr/bin/env python3

from tqdm import tqdm
from pydub import AudioSegment

import configparser
import random

from utils import download_mp3, get_song, load_music_list, set_music_list, is_url

# Init audio
final_audio = AudioSegment.empty()
countdown_audio = AudioSegment.empty()

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

    # Error occured
    if countdown_audio == 0:
        print("Unable to load countdown sound at " + countdown_file_path)
        exit(1)

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

        # If at least one song was downloaded
        if download_mp3(row, music_folder):
            download_occurred = True

# Updates CSV file if neccessary (URL->files)
if download_occurred:
    set_music_list(music_list, column_names)

# Which songs failed to load
error_songs = [] 

# Gets all music files
for row in tqdm(music_list, desc="Cooking the result"):
    current_song, success = get_song(row, music_folder)

    # If file was loaded
    if success:

        # Puts countdown at the start and in between songs
        if len(countdown_audio) > 0:
            final_audio += countdown_audio
        
        # Adds song to the final audio
        final_audio += current_song

    # Error occured
    else:
        error_songs.append(current_song)

# Export the audio
final_audio.export("random_dance.mp3", format="mp3")

# All songs were successfully loaded
if len(error_songs) == 0:

    # UwU
    print("Random dance was successfully created!")

# Any error occured
else:

    # Not UwU
    print("Random dance was created but few songs couldn't be added!")
    print("Failed to add:")
    for error in error_songs:
        print(error)

