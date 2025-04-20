import os
import random
import logging
from pathlib import Path
from . import utils

logger = logging.getLogger(__name__)

class PlaylistManager:
    """Manages playlists of audio files."""
    
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.flac', '.ogg', '.m4a']
    
    def __init__(self, music_dir=None):
        """Initialize with optional music directory."""
        self.music_dir = music_dir
        self.current_index = -1
        self.tracks = []
        self.shuffled_tracks = []
        
        if music_dir:
            self.scan_directory(music_dir)
    
    def scan_directory(self, directory):
        """Scan directory for audio files and add to playlist."""
        if not os.path.isdir(directory):
            logger.error(f"Directory not found: {directory}")
            return False
        
        self.music_dir = directory
        self.tracks = utils.scan_audio_files(directory, self.SUPPORTED_FORMATS)
        
        if not self.tracks:
            logger.warning(f"No supported audio files found in {directory}")
            return False
        
        logger.info(f"Found {len(self.tracks)} audio files in {directory}")
        self.shuffle()
        return True
    
    def shuffle(self):
        """Shuffle the playlist."""
        if not self.tracks:
            logger.warning("No tracks to shuffle")
            return False
        
        self.shuffled_tracks = self.tracks.copy()
        random.shuffle(self.shuffled_tracks)
        self.current_index = 0
        
        logger.info(f"Playlist shuffled with {len(self.shuffled_tracks)} tracks")
        return True
    
    def get_current_track(self):
        """Get the current track path."""
        if not self.shuffled_tracks or self.current_index < 0:
            return None
        
        return self.shuffled_tracks[self.current_index]
    
    def get_current_track_info(self):
        """Get information about the current track."""
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
        except Exception as e:
            logger.error(f"Error getting track info: {e}")
            return None
    
    def next_track(self):
        """Move to the next track and return its path."""
        if not self.shuffled_tracks:
            logger.warning("Playlist is empty")
            return None
        
        if self.current_index >= len(self.shuffled_tracks) - 1:
            # End of playlist, loop back to beginning
            self.current_index = 0
        else:
            self.current_index += 1
            
        logger.info(f"Moving to next track: {Path(self.shuffled_tracks[self.current_index]).name}")
        return self.shuffled_tracks[self.current_index]
    
    def previous_track(self):
        """Move to the previous track and return its path."""
        if not self.shuffled_tracks:
            logger.warning("Playlist is empty")
            return None
            
        if self.current_index <= 0:
            # Beginning of playlist, loop to end
            self.current_index = len(self.shuffled_tracks) - 1
        else:
            self.current_index -= 1
            
        logger.info(f"Moving to previous track: {Path(self.shuffled_tracks[self.current_index]).name}")
        return self.shuffled_tracks[self.current_index]
    
    def total_tracks(self):
        """Return the total number of tracks."""
        return len(self.tracks)