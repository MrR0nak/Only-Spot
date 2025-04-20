import os
import sys
import msvcrt
import logging
import threading
import time
from pathlib import Path

from ..audio.player import AudioPlayer
from ..playlist.playlist import PlaylistManager
from ..config.config import ConfigManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CLIPlayer:
    """Command-line interface for MySpot audio player on Windows."""
    
    KEY_MAPPINGS = {
        b' ': 'toggle_play_pause',
        b'n': 'next_track',
        b'p': 'previous_track',
        b'm': 'toggle_mute',
        b'+': 'increase_volume',
        b'-': 'decrease_volume',
        b'q': 'quit'
    }
    
    def __init__(self):
        self.config = ConfigManager()
        self.player = AudioPlayer(volume=self.config.get('volume', 0.5))
        self.playlist = PlaylistManager(self.config.get('music_directory'))
        
        if not self.playlist.tracks:
            print("No music files found. Please specify a valid music directory.")
            music_dir = input("Enter music directory path: ")
            self.playlist.scan_directory(music_dir)
            self.config.set('music_directory', music_dir)
        
        self.running = False
        self.status_thread = None
    
    def start(self):
        """Start the CLI player."""
        self.running = True
        
        # Start with the first track
        self._play_current_track()
        
        # Start status display thread
        self.status_thread = threading.Thread(target=self._status_display, daemon=True)
        self.status_thread.start()
        
        print("\nMySpot CLI Player")
        print("Controls: Space=Play/Pause, n=Next, p=Previous, m=Mute, +=Volume Up, -=Volume Down, q=Quit")
        
        try:
            self._input_loop()
        except KeyboardInterrupt:
            print("\nExiting MySpot...")
        finally:
            self.running = False
            self._save_state()
    
    def _input_loop(self):
        """Handle keyboard input using msvcrt for Windows."""
        while self.running:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                
                if ch in self.KEY_MAPPINGS:
                    action = self.KEY_MAPPINGS[ch]
                    self._handle_action(action)
            
            # Small delay to prevent CPU hogging
            time.sleep(0.1)
    
    def _handle_action(self, action):
        """Handle player actions."""
        if action == 'toggle_play_pause':
            status = self.player.toggle_play_pause()
            logger.info(f"Playback {status}")
        
        elif action == 'next_track':
            next_track = self.playlist.next_track()
            if next_track:
                self.player.play(next_track)
        
        elif action == 'previous_track':
            prev_track = self.playlist.previous_track()
            if prev_track:
                self.player.play(prev_track)
        
        elif action == 'toggle_mute':
            muted = self.player.toggle_mute()
            logger.info(f"Audio {'muted' if muted else 'unmuted'}")
        
        elif action == 'increase_volume':
            new_vol = self.player.increase_volume(0.05)
            self.config.set('volume', new_vol)
        
        elif action == 'decrease_volume':
            new_vol = self.player.decrease_volume(0.05)
            self.config.set('volume', new_vol)
        
        elif action == 'quit':
            self.running = False
            self._save_state()
            sys.exit(0)
    
    def _play_current_track(self):
        """Play the current track from playlist."""
        current = self.playlist.get_current_track()
        if current:
            self.player.play(current)
            logger.info(f"Playing: {Path(current).name}")
    
    def _status_display(self):
        """Update the status display in a separate thread."""
        while self.running:
                # Auto-advance to next track when current one finishes

            
            # Display current status every second
            self._print_status()
            time.sleep(1)
    
    def _print_status(self):
        """Print the current playback status."""
        track_info = self.playlist.get_current_track_info()
        
        if track_info:
            status = "▶️ " if self.player.is_playing() else "⏸️ "
            volume = int(self.player.get_volume() * 100)
            volume_display = f"🔇 {volume}%" if self.player.is_muted() else f"🔊 {volume}%"
            
            # Clear line and print status
            print(f"\r{status} {track_info['filename']} | {track_info['index']}/{track_info['total']} | {volume_display}", end="", flush=True)
    
    def _save_state(self):
        """Save current state to config."""
        current = self.playlist.get_current_track()
        if current:
            self.config.set('last_played', current)
        self.config.set('volume', self.player.get_volume())


def main():
    """Main entry point for CLI player."""
    cli = CLIPlayer()
    cli.start()


if __name__ == "__main__":
    main()