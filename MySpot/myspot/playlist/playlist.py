import os
import random
from pathlib import Path
from . import utils
class PlaylistManager:
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
    def __init__(self, music_dir=None):
        self.music_dir = music_dir
        self.current_index = 0
        self.tracks = []
        self.shuffled_tracks = []
        if music_dir:
            self.scan_directory(music_dir)
    def scan_directory(self, directory):
        if not os.path.isdir(directory):
            return False
        self.music_dir = directory
        self.tracks = utils.scan_audio_files(directory, self.SUPPORTED_FORMATS)
        if not self.tracks:
            return False
        self.shuffle()
        return True
    def shuffle(self):
        if not self.tracks:
            return False
        self.shuffled_tracks = self.tracks.copy()
        random.shuffle(self.shuffled_tracks)
        self.current_index = 0
        return True
    def get_current_track(self):
        if not self.shuffled_tracks or self.current_index < 0:
            return None
        return self.shuffled_tracks[self.current_index]
    def get_current_track_info(self):
        track = self.get_current_track()
        if not track:
            return None
        try:
            return {
                'path': track,
                'filename': Path(track).name,
                'index': self.current_index + 1,
                'total': len(self.shuffled_tracks)
            }
        except Exception:
            return None
    def next_track(self):
        if not self.shuffled_tracks:
            return None
        if self.current_index >= len(self.shuffled_tracks) - 1:
            self.current_index = 0
        else:
            self.current_index += 1
        return self.shuffled_tracks[self.current_index]
    def previous_track(self):
        if not self.shuffled_tracks:
            return None
        if self.current_index <= 0:
            self.current_index = len(self.shuffled_tracks) - 1
        else:
            self.current_index -= 1
        return self.shuffled_tracks[self.current_index]
    def total_tracks(self):
        return len(self.tracks)