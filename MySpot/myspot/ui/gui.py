import os
import sys
import logging
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import pygame
from PIL import Image, ImageTk
import io

from ..audio.player import AudioPlayer
from ..playlist.playlist import PlaylistManager
from ..config.config import ConfigManager

logger = logging.getLogger(__name__)

class ModernUI:
    """Custom UI elements with modern styling."""
    
    @staticmethod
    def create_button(parent, text, command, size=12, width=None, hover_color="#333333"):
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", size),
            bg="#3D3D3D",
            fg="#FFFFFF",
            activebackground="#444444",
            activeforeground="#FFFFFF",
            borderwidth=0,
            padx=10,
            pady=5,
            width=width,
            cursor="hand2",
            command=command
        )
        
        btn.bind("<Enter>", lambda e: btn.config(background=hover_color))
        btn.bind("<Leave>", lambda e: btn.config(background="#3D3D3D"))
        
        return btn
    
    @staticmethod
    def setup_styles():
        """Set up ttk styles."""
        style = ttk.Style()
        
        # Configure the progress bar
        style.configure(
            "MySpot.Horizontal.TProgressbar",
            troughcolor="#222222",
            background="#1DB954",
            thickness=8,
            borderwidth=0
        )
        
        # Configure volume slider
        style.configure(
            "MySpot.Horizontal.TScale",
            background="#1E1E1E",
            troughcolor="#333333",
            sliderwidth=15,
            sliderlength=15
        )
        
        return style

class GUIPlayer:
    """Modern graphical user interface for MySpot audio player."""
    
    def __init__(self, root=None):
        self.config = ConfigManager()
        self.player = AudioPlayer(volume=self.config.get('volume', 0.5))
        self.playlist = PlaylistManager(self.config.get('music_directory'))
        
        # Create root window if not provided
        self.root = root or tk.Tk()
        self.root.title("MySpot Player")
        self.root.geometry("550x400")
        self.root.minsize(500, 350)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Set dark theme
        self.bg_color = "#1E1E1E"
        self.fg_color = "#E6E6E6"
        self.accent_color = "#1DB954"  # Spotify green
        self.button_bg = "#3D3D3D"
        self.secondary_color = "#333333"
        
        self.root.configure(bg=self.bg_color)
        
        # Set up ttk styles
        self.style = ModernUI.setup_styles()
        
        # Create UI elements
        self._create_ui()
        
        # Set up polling for track end detection
        self.polling = True
        self.poll_thread = threading.Thread(target=self._poll_playback_status, daemon=True)
        self.poll_thread.start()
        # Load initial directory if needed
        if not self.playlist.tracks:
            self.open_directory()
        
    def _create_ui(self):
        """Create the user interface elements."""
        # Main frame with padding
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Header with logo
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(
            header_frame,
            text="MySpot",
            bg=self.bg_color,
            fg=self.accent_color,
            font=("Segoe UI", 20, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Folder button in header
        folder_btn = ModernUI.create_button(
            header_frame,
            text="📁",
            command=self.open_directory,
            size=14
        )
        folder_btn.pack(side=tk.RIGHT)
        
        # Track container
        track_frame = tk.Frame(main_frame, bg=self.secondary_color, padx=15, pady=15)
        track_frame.pack(fill=tk.X, pady=10)
        
        # Now playing label
        now_playing = tk.Label(
            track_frame,
            text="NOW PLAYING",
            bg=self.secondary_color,
            fg=self.accent_color,
            font=("Segoe UI", 9),
            anchor=tk.W
        )
        now_playing.pack(fill=tk.X)
        
        # Track info
        self.track_var = tk.StringVar(value="No track playing")
        self.track_label = tk.Label(
            track_frame, 
            textvariable=self.track_var,
            bg=self.secondary_color,
            fg=self.fg_color,
            font=("Segoe UI", 12, "bold"),
            anchor=tk.W,
            wraplength=490
        )
        self.track_label.pack(fill=tk.X, pady=(5, 10))
        
        self.track_info_var = tk.StringVar(value="")
        self.track_info_label = tk.Label(
            track_frame, 
            textvariable=self.track_info_var,
            bg=self.secondary_color,
            fg="#AAAAAA",
            font=("Segoe UI", 9),
            anchor=tk.W
        )
        self.track_info_label.pack(fill=tk.X)
        
        # Progress bar
        progress_frame = tk.Frame(main_frame, bg=self.bg_color)
        progress_frame.pack(fill=tk.X, pady=(15, 5))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient=tk.HORIZONTAL,
            style="MySpot.Horizontal.TProgressbar",
            length=100,
            mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Control buttons
        control_frame = tk.Frame(main_frame, bg=self.bg_color)
        control_frame.pack(pady=15)
        
        # Previous button
        self.prev_button = ModernUI.create_button(
            control_frame, 
            text="⏮",
            command=self.previous_track,
            size=16
        )
        self.prev_button.pack(side=tk.LEFT, padx=10)
        
        # Play/Pause button
        self.play_button = ModernUI.create_button(
            control_frame, 
            text="▶",
            command=self.toggle_play_pause,
            size=22,
            hover_color="#2D2D2D"
        )
        self.play_button.pack(side=tk.LEFT, padx=15)
        
        # Next button
        self.next_button = ModernUI.create_button(
            control_frame, 
            text="⏭",
            command=self.next_track,
            size=16
        )
        self.next_button.pack(side=tk.LEFT, padx=10)
        
        # Volume control frame at bottom
        volume_frame = tk.Frame(main_frame, bg=self.bg_color)
        volume_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 10))
        
        # Mute button
        self.mute_button = ModernUI.create_button(
            volume_frame, 
            text="🔊",
            command=self.toggle_mute,
            size=12
        )
        self.mute_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Volume slider
        self.volume_var = tk.DoubleVar(value=self.player.get_volume())
        self.volume_slider = ttk.Scale(
            volume_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.volume_var,
            command=self.set_volume,
            style="MySpot.Horizontal.TScale"
        )
        self.volume_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Volume percentage label
        self.volume_label = tk.Label(
            volume_frame,
            text=f"{int(self.volume_var.get() * 100)}%",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 9)
        )
        self.volume_label.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg="#111111", height=25)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready",
            bg="#111111",
            fg="#888888",
            font=("Segoe UI", 8),
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Keyboard shortcuts
        self.root.bind("<space>", lambda e: self.toggle_play_pause())
        self.root.bind("n", lambda e: self.next_track())
        self.root.bind("p", lambda e: self.previous_track())
        self.root.bind("m", lambda e: self.toggle_mute())
        self.root.bind("q", lambda e: self.on_close())
        self.root.bind("<plus>", lambda e: self.increase_volume())
        self.root.bind("<minus>", lambda e: self.decrease_volume())
        self.root.bind("<o>", lambda e: self.open_directory())
    
    def open_directory(self):
        """Open a directory dialog to select music folder."""
        directory = filedialog.askdirectory(
            title="Select Music Directory",
            initialdir=self.config.get('music_directory', os.path.expanduser("~/Music"))
        )
        
        if directory:
            self.status_label.config(text=f"Loading music from {directory}...")
            self.root.update()
            
            if self.playlist.scan_directory(directory):
                self.config.set('music_directory', directory)
                self._play_current_track()
                self.update_track_info()
                self.status_label.config(text=f"Loaded {self.playlist.total_tracks()} tracks")
            else:
                self.status_label.config(text="No music files found in selected directory")
    
    def _play_current_track(self):
        """Play the current track from the playlist."""
        current = self.playlist.get_current_track()
        if current:
            self.player.play(current)
            self.update_ui()
            self.status_label.config(text=f"Playing: {Path(current).name}")
    
    def toggle_play_pause(self):
        """Toggle play/pause status."""
        current = self.playlist.get_current_track()
        
        if not current:
            return
        
        status = self.player.toggle_play_pause()
        
        # Update play button text
        if status == "playing":
            self.play_button.config(text="⏸")
            self.status_label.config(text=f"Playing: {Path(current).name}")
        else:
            self.play_button.config(text="▶")
            self.status_label.config(text=f"Paused: {Path(current).name}")
    
    def next_track(self):
        """Play the next track."""
        next_track = self.playlist.next_track()
        if next_track:
            self.player.play(next_track)
            self.update_ui()
            self.status_label.config(text=f"Playing: {Path(next_track).name}")
    
    def previous_track(self):
        """Play the previous track."""
        prev_track = self.playlist.previous_track()
        if prev_track:
            self.player.play(prev_track)
            self.update_ui()
            self.status_label.config(text=f"Playing: {Path(prev_track).name}")
    
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
            self.volume_label.config(text=f"{int(volume * 100)}%")
            self.config.set('volume', volume)
        except ValueError:
            pass
    
    def increase_volume(self):
        """Increase volume by 5%."""
        new_vol = self.player.increase_volume(0.05)
        self.volume_var.set(new_vol)
        self.volume_label.config(text=f"{int(new_vol * 100)}%")
        self.config.set('volume', new_vol)
    
    def decrease_volume(self):
        """Decrease volume by 5%."""
        new_vol = self.player.decrease_volume(0.05)
        self.volume_var.set(new_vol)
        self.volume_label.config(text=f"{int(new_vol * 100)}%")
        self.config.set('volume', new_vol)
    
    def update_track_info(self):
        """Update the track information display."""
        track_info = self.playlist.get_current_track_info()
        
        if not track_info:
            self.track_var.set("No track playing")
            self.track_info_var.set("")
            self.progress_bar["value"] = 0
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
            self.play_button.config(text="⏸")
        else:
            self.play_button.config(text="▶")
        
        # Update mute button
        if self.player.is_muted():
            self.mute_button.config(text="🔇")
        else:
            self.mute_button.config(text="🔊")
        
        # Update volume slider and label
        self.volume_var.set(self.player.get_volume())
        self.volume_label.config(text=f"{int(self.player.get_volume() * 100)}%")
    
    def _poll_playback_status(self):
        """Poll for playback status changes."""
        import time
        while self.polling:
            # Check if a track is loaded but not playing and not paused
            if self.player.current_track and not self.player.is_playing() and not self.player.is_paused:
                # If track has ended, play the next one
                self.next_track()
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
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Fix for HiDPI displays
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    root = tk.Tk()
    app = GUIPlayer(root)
    app.start()

if __name__ == "__main__":
    main()
