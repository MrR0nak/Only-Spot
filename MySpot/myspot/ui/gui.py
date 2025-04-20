import os
import sys
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path

from ..audio.player import AudioPlayer
from ..playlist.playlist import PlaylistManager
from ..config.config import ConfigManager

logger = logging.getLogger(__name__)

class GUIPlayer:
    """Graphical user interface for MySpot audio player."""
    
    def __init__(self, root=None):
        self.config = ConfigManager()
        self.player = AudioPlayer(volume=self.config.get('volume', 0.5))
        self.playlist = PlaylistManager(self.config.get('music_directory'))
        
        # Create root window if not provided
        self.root = root or tk.Tk()
        self.root.title("MySpot Player")
        self.root.geometry("500x350")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set theme
        self.theme = self.config.get('theme', 'dark')
        self._apply_theme()
        
        # Create UI elements
        self._create_ui()
        
        # Set up polling for track end detection
        self.polling = True
        self.poll_thread = threading.Thread(target=self._poll_playback_status, daemon=True)
        self.poll_thread.start()
        
        # Load initial directory if needed
        if not self.playlist.tracks:
            self.open_directory()
    
    def _apply_theme(self):
        """Apply the selected theme to the UI."""
        if self.theme == 'dark':
            self.bg_color = "#222222"
            self.fg_color = "#EEEEEE"
            self.accent_color = "#1DB954"  # Spotify green
            self.button_bg = "#333333"
        else:
            self.bg_color = "#FFFFFF"
            self.fg_color = "#222222"
            self.accent_color = "#1DB954"  # Spotify green
            self.button_bg = "#EEEEEE"
        
        self.root.configure(bg=self.bg_color)
    
    def _create_ui(self):
        """Create the user interface elements."""
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Track info
        self.track_var = tk.StringVar(value="No track playing")
        self.track_label = tk.Label(
            main_frame, 
            textvariable=self.track_var,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 12, "bold"),
            wraplength=460
        )
        self.track_label.pack(pady=(10, 5))
        
        self.track_info_var = tk.StringVar(value="")
        self.track_info_label = tk.Label(
            main_frame, 
            textvariable=self.track_info_var,
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Arial", 10)
        )
        self.track_info_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_frame = tk.Frame(main_frame, bg=self.bg_color)
        self.progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            orient=tk.HORIZONTAL,
            length=480,
            mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(pady=10)
        
        # Previous button
        self.prev_button = tk.Button(
            button_frame, 
            text="⏮️",
            font=("Arial", 16),
            command=self.previous_track,
            bg=self.button_bg,
            fg=self.fg_color,
        )
        self.prev_button.pack(side=tk.LEFT, padx=5)
        
        # Play/Pause button
        self.play_button = tk.Button(
            button_frame, 
            text="▶️",
            font=("Arial", 16),
            command=self.toggle_play_pause,
            bg=self.button_bg,
            fg=self.fg_color,
        )
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        # Next button
        self.next_button = tk.Button(
            button_frame, 
            text="⏭️",
            font=("Arial", 16),
            command=self.next_track,
            bg=self.button_bg,
            fg=self.fg_color,
        )
        self.next_button.pack(side=tk.LEFT, padx=5)
        
        # Volume control
        volume_frame = tk.Frame(main_frame, bg=self.bg_color)
        volume_frame.pack(pady=10, fill=tk.X)
        
        # Mute button
        self.mute_button = tk.Button(
            volume_frame, 
            text="🔊",
            font=("Arial", 14),
            command=self.toggle_mute,
            bg=self.button_bg,
            fg=self.fg_color,
        )
        self.mute_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Volume slider
        self.volume_var = tk.DoubleVar(value=self.player.get_volume())
        self.volume_slider = ttk.Scale(
            volume_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.volume_var,
            command=self.set_volume
        )
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Menu
        self._create_menu()
        
        # Keyboard shortcuts
        self.root.bind("<space>", lambda e: self.toggle_play_pause())
        self.root.bind("n", lambda e: self.next_track())
        self.root.bind("p", lambda e: self.previous_track())
        self.root.bind("m", lambda e: self.toggle_mute())
        self.root.bind("q", lambda e: self.on_close())
        self.root.bind("<plus>", lambda e: self.increase_volume())
        self.root.bind("<minus>", lambda e: self.decrease_volume())
    
    def _create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Music Folder", command=self.open_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Theme menu
        theme_menu = tk.Menu(menubar, tearoff=0)
        theme_menu.add_command(label="Light", command=lambda: self.change_theme('light'))
        theme_menu.add_command(label="Dark", command=lambda: self.change_theme('dark'))
        menubar.add_cascade(label="Theme", menu=theme_menu)
        
        self.root.config(menu=menubar)
    
    def open_directory(self):
        """Open a directory dialog to select music folder."""
        directory = filedialog.askdirectory(
            title="Select Music Directory",
            initialdir=self.config.get('music_directory', os.path.expanduser("~/Music"))
        )
        
        if directory:
            if self.playlist.scan_directory(directory):
                self.config.set('music_directory', directory)
                self._play_current_track()
                self.update_track_info()
    
    def _play_current_track(self):
        """Play the current track from the playlist."""
        current = self.playlist.get_current_track()
        if current:
            self.player.play(current)
            self.update_ui()
    
    def toggle_play_pause(self):
        """Toggle play/pause status."""
        current = self.playlist.get_current_track()
        
        if not current:
            return
        
        status = self.player.toggle_play_pause()
        
        # Update play button text
        if status == "playing":
            self.play_button.config(text="⏸️")
        else:
            self.play_button.config(text="▶️")
    
    def next_track(self):
        """Play the next track."""
        next_track = self.playlist.next_track()
        if next_track:
            self.player.play(next_track)
            self.update_ui()
    
    def previous_track(self):
        """Play the previous track."""
        prev_track = self.playlist.previous_track()
        if prev_track:
            self.player.play(prev_track)
            self.update_ui()
    
    def toggle_mute(self):
        """Toggle mute status."""
        is_muted = self.player.toggle_mute()
        
        # Update mute button text
        if is_muted:
            self.mute_button.config(text="🔇")
        else:
            self.mute_button.config(text="🔊")
    
    def set_volume(self, value):
        """Set the volume from slider."""
        try:
            volume = float(value)
            self.player.set_volume(volume)
            self.config.set('volume', volume)
        except ValueError:
            pass
    
    def increase_volume(self):
        """Increase volume by 5%."""
        new_vol = self.player.increase_volume(0.05)
        self.volume_var.set(new_vol)
        self.config.set('volume', new_vol)
    
    def decrease_volume(self):
        """Decrease volume by 5%."""
        new_vol = self.player.decrease_volume(0.05)
        self.volume_var.set(new_vol)
        self.config.set('volume', new_vol)
    
    def update_track_info(self):
        """Update the track information display."""
        track_info = self.playlist.get_current_track_info()
        
        if not track_info:
            self.track_var.set("No track playing")
            self.track_info_var.set("")
            return
        
        # Update track name
        self.track_var.set(track_info['filename'])
        
        # Update track position info
        self.track_info_var.set(f"Track {track_info['index']} of {track_info['total']}")
    
    def update_ui(self):
        """Update all UI elements based on current state."""
        # Update track info
        self.update_track_info()
        
        # Update play/pause button
        if self.player.is_playing():
            self.play_button.config(text="⏸️")
        else:
            self.play_button.config(text="▶️")
        
        # Update mute button
        if self.player.is_muted():
            self.mute_button.config(text="🔇")
        else:
            self.mute_button.config(text="🔊")
        
        # Update volume slider
        self.volume_var.set(self.player.get_volume())
    
    def change_theme(self, theme):
        """Change the UI theme."""
        self.theme = theme
        self.config.set('theme', theme)
        self._apply_theme()
        
        # Update UI elements
        self.track_label.config(bg=self.bg_color, fg=self.fg_color)
        self.track_info_label.config(bg=self.bg_color, fg=self.fg_color)
        self.progress_frame.config(bg=self.bg_color)
        self.prev_button.config(bg=self.button_bg, fg=self.fg_color)
        self.play_button.config(bg=self.button_bg, fg=self.fg_color)
        self.next_button.config(bg=self.button_bg, fg=self.fg_color)
        self.mute_button.config(bg=self.button_bg, fg=self.fg_color)
    
    def _poll_playback_status(self):
        """Check if the current track has ended and play next if needed."""
        while self.polling:
            # Verifica se há uma faixa carregada mas não está tocando E não está pausada
            if (self.player.current_track and not self.player.is_playing()):
                if self.player.is_paused == "false":
                    self.next_track()
            
            import time
            time.sleep(0.5)
    
    def on_close(self):
        """Handle application close."""
        # Save current state
        self.config.set('volume', self.player.get_volume())
        current = self.playlist.get_current_track()
        if current:
            self.config.set('last_played', current)
        
        # Stop threads
        self.polling = False
        
        # Stop playback
        self.player.stop()
        
        # Close window
        self.root.destroy()
    
    def start(self):
        """Start the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for GUI player."""
    root = tk.Tk()
    app = GUIPlayer(root)
    app.start()


if __name__ == "__main__":
    main()
