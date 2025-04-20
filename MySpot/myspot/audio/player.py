import pygame
import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)
class AudioPlayer:
    def __init__(self, volume=0.5):
        pygame.mixer.init()
        self._volume = 0.0
        self._is_muted = False
        self._muted_volume = 0.0
        self.set_volume(volume)
        self.current_track = None
        self.is_paused = False
        logger.info("AudioPlayer initialized with volume %.2f", volume)
    def play(self, file_path):
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.current_track = Path(file_path).name
            logger.info(f"Playing: {self.current_track}")
            return True
        except pygame.error as e:
            logger.error(f"Cannot play file {file_path}: {e}")
            return False
    def pause(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_paused = True
            logger.info("Playback paused")
            return True
        return False
    def unpause(self):
        try:
            pygame.mixer.music.unpause()
            self.is_paused = False
            logger.info("Playback resumed")
            return True
        except:
            logger.error("Cannot unpause - no music loaded or playing")
            return False
    def toggle_play_pause(self):
        if pygame.mixer.music.get_busy():
            self.pause()
            return "paused"
        else:
            if self.current_track:
                self.unpause()
                return "playing"
            return "no track loaded"
    def stop(self):
        pygame.mixer.music.stop()
        logger.info("Playback stopped")
    def is_playing(self):
        return pygame.mixer.music.get_busy()
    def set_volume(self, volume):
        volume = max(0.0, min(1.0, volume))
        self._volume = volume
        if not self._is_muted:
            pygame.mixer.music.set_volume(volume)
            logger.debug(f"Volume set to {volume:.2f}")
        return volume
    def get_volume(self):
        return self._volume
    def increase_volume(self, increment=0.05):
        return self.set_volume(self._volume + increment)
    def decrease_volume(self, decrement=0.05):
        return self.set_volume(self._volume - decrement)
    def toggle_mute(self):
        if self._is_muted:
            pygame.mixer.music.set_volume(self._muted_volume)
            self._is_muted = False
            logger.info(f"Audio unmuted, volume restored to {self._muted_volume:.2f}")
            return False
        else:
            self._muted_volume = self._volume
            pygame.mixer.music.set_volume(0)
            self._is_muted = True
            logger.info("Audio muted")
            return True
    def is_muted(self):
        return self._is_muted
    def __del__(self):
        try:
            pygame.mixer.quit()
        except Exception:
            pass