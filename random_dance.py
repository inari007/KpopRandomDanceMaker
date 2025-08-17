#!/usr/bin/env python3

from tqdm import tqdm
from pydub import AudioSegment

import configparser
import random

from utils import download_mp3, get_song, load_music_list, set_music_list, is_url, printable_loop

class KpopRandomDanceMaker():

    # Init audio
    def __init__(self, enable_printing):
        self.final_audio = AudioSegment.empty()
        self.error_songs = [] 
        self.enable_printing = enable_printing

        self.readConfig()
        self.readSongs()

    # Parses configuration file
    def readConfig(self):
        config = configparser.ConfigParser()
        config.read('config.ini')

        self.config = {
            'countdown_enable' : config['countdown'].getboolean('enable'),
            'countdown_file' : config['countdown']['sound_file'],
            'random_order' : config['general'].getboolean('random_order'),
            'music_folder' : config['general']['music_folder']
        }

        self.countdown_audio = AudioSegment.from_mp3(self.config['countdown_file']) if self.config['countdown_enable'] else AudioSegment.empty()

    def writeConfig(self):
        config = configparser.ConfigParser()

        config['countdown'] = {
            'enable': str(self.config['countdown_enable']),
            'sound_file': self.config['countdown_file']
        }

        config['general'] = {
            'random_order': str(self.config['random_order']),
            'music_folder': self.config['music_folder']
        }

        with open('config.ini', 'w') as configfile:
            config.write(configfile)

        # Reopen and inject comments
        with open('config.ini', 'r') as f:
            lines = f.readlines()

        with open('config.ini', 'w') as f:
            f.write("### Settings ###\n\n")
            for line in lines:
                if line.strip().startswith("enable"):
                    f.write("# Enable countdown (True -> Enable, False -> Disable)\n")
                elif line.strip().startswith("sound_file"):
                    f.write("# Path to the countdown sound file, that you want to put in between songs\n")
                elif line.strip().startswith("random_order"):
                    f.write("# Randomize order of the songs (True -> Enable, False -> Disable)\n")
                elif line.strip().startswith("music_folder"):
                    f.write("# Path to the folder with songs\n")
                f.write(line)

    def getConfig(self):
        return self.config

    def readSongs(self):
        self.music_list = load_music_list()
        self.column_names = list(self.music_list[0].keys())

    def getSongs(self):
        return self.music_list

    # Updates CSV file if neccessary (URL->files)
    def writeSongs(self):
        set_music_list(self.music_list, self.column_names)

    def getErrorSongs(self):
        return self.error_songs

    def downloadSongs(self):
        if self.config['random_order']:
            random.shuffle(self.music_list)

        download_occurred = False 
        for row in printable_loop(self.music_list, self.enable_printing, desc="Downloading songs"):

            # If URL was uses, download it 
            if is_url(row['name']):

                # If at least one song was downloaded
                if download_mp3(row, self.config['music_folder']):
                    download_occurred = True

        if download_occurred:
            self.writeSongs()

    def cookRandomDance(self):
        for row in printable_loop(self.music_list, self.enable_printing, desc="Cooking the result"):
            current_song, success = get_song(row, self.config['music_folder'])

            if success:

                # Adds countdown
                if len(self.countdown_audio) > 0:
                    self.final_audio += self.countdown_audio
                
                # Adds song
                self.final_audio += current_song

            # Error occured
            else:
                self.error_songs.append(current_song)

        self.final_audio.export("random_dance.mp3", format="mp3")


if __name__ == '__main__':
    engine = KpopRandomDanceMaker(enable_printing=True)
    engine.downloadSongs()
    engine.cookRandomDance()

    error_songs = engine.getErrorSongs()

    if len(error_songs) == 0:
        # UwU
        print("Random dance was successfully created!")

    else:
        # Not UwU
        print("Random dance was created but few songs couldn't be added!")
        print("Failed to add:")
        for error in error_songs:
            print(error)


