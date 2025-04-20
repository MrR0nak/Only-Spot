import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
import pygame
import pygetwindow as gw

from ..audio.player import AudioPlayer
from ..playlist.playlist import PlaylistManager
from ..config.config import ConfigManager

class ModernUI:
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
            command=command,
            relief="raised",
            highlightthickness=0,
            bd=0,

            highlightbackground="#3D3D3D",
            highlightcolor="#3D3D3D",
        )

        btn.bind("<Enter>", lambda e: btn.config(background=hover_color))
        btn.bind("<Leave>", lambda e: btn.config(background="#3D3D3D"))

        return btn

class GUIPlayer:
    def __init__(self, root=None):
        self.config = ConfigManager()
        self.player = AudioPlayer(volume=self.config.get('volume', 0.5))
        self.playlist = PlaylistManager(self.config.get('music_directory'))

        self.root = root or tk.Tk()
        self.root.title("MySpot Player")
        self.root.geometry("750x500")
        self.root.minsize(650, 450)

        self.bg_color = "#1E1E1E"
        self.fg_color = "#E6E6E6"
        self.accent_color = "#1DB954"
        self.button_bg = "#3D3D3D"
        self.secondary_color = "#333333"

        self.root.configure(bg=self.bg_color)

        self.style = self._setup_styles()

        self._create_ui()

        self.polling = True
        self.poll_thread = threading.Thread(target=self._poll_playback_status, daemon=True)
        self.poll_thread.start()

        if not self.playlist.tracks:
            self.open_directory()
        else:
            self.playlist.current_index = 0
            self._populate_playlist()
            self._play_current_track()

    def _setup_styles(self):
        style = ttk.Style()
        style.configure(
            "MySpot.Horizontal.TScale",
            background="#1E1E1E",
            troughcolor="#333333",
            sliderwidth=15,
            sliderlength=15
        )

        style.configure(
            "MySpot.Treeview",
            background="#2D2D2D",
            foreground="#E6E6E6",
            fieldbackground="#2D2D2D",
            rowheight=25
        )

        style.configure(
            "MySpot.Treeview.Heading",
            background="#1E1E1E",
            foreground="#AAAAAA",
            relief="flat"
        )

        style.map(
            "MySpot.Treeview",
            background=[("selected", "#1DB954")],
            foreground=[("selected", "#FFFFFF")]
        )

        return style

    def _create_ui(self):

        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

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

        folder_btn = ModernUI.create_button(
            header_frame,
            text="📁",
            command=self.open_directory,
            size=14
        )
        folder_btn.pack(side=tk.RIGHT)

        shuffle_btn = ModernUI.create_button(
            header_frame,
            text="🔀",
            command=self.shuffle_playlist,
            size=14
        )
        shuffle_btn.pack(side=tk.RIGHT, padx=5)

        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        left_pane = tk.Frame(paned_window, bg=self.bg_color)
        paned_window.add(left_pane, weight=1)

        track_frame = tk.Frame(left_pane, bg=self.secondary_color, padx=15, pady=15)
        track_frame.pack(fill=tk.X, pady=10)

        now_playing = tk.Label(
            track_frame,
            text="NOW PLAYING",
            bg=self.secondary_color,
            fg=self.accent_color,
            font=("Segoe UI", 9),
            anchor=tk.W
        )
        now_playing.pack(fill=tk.X)

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

        control_frame = tk.Frame(left_pane, bg=self.bg_color)
        control_frame.pack(pady=15)

        self.prev_button = ModernUI.create_button(
            control_frame,
            text="⏮",
            command=self.previous_track,
            size=16
        )
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.play_button = ModernUI.create_button(
            control_frame,
            text="▶",
            command=self.toggle_play_pause,
            size=22,
            hover_color="#2D2D2D"
        )
        self.play_button.pack(side=tk.LEFT, padx=15)

        self.next_button = ModernUI.create_button(
            control_frame,
            text="⏭",
            command=self.next_track,
            size=16
        )
        self.next_button.pack(side=tk.LEFT, padx=10)

        volume_frame = tk.Frame(left_pane, bg=self.bg_color)
        volume_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 10))

        self.mute_button = ModernUI.create_button(
            volume_frame,
            text="🔊",
            command=self.toggle_mute,
            size=12
        )
        self.mute_button.pack(side=tk.LEFT, padx=(0, 10))

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

        self.volume_label = tk.Label(
            volume_frame,
            text=f"{int(self.volume_var.get() * 100)}%",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 9)
        )
        self.volume_label.pack(side=tk.LEFT, padx=5)

        right_pane = tk.Frame(paned_window, bg=self.bg_color)
        paned_window.add(right_pane, weight=1)

        playlist_header = tk.Label(
            right_pane,
            text="PLAYLIST",
            bg=self.bg_color,
            fg=self.accent_color,
            font=("Segoe UI", 12, "bold"),
            anchor=tk.W
        )
        playlist_header.pack(fill=tk.X, pady=(0, 10))

        playlist_frame = tk.Frame(right_pane, bg=self.bg_color)
        playlist_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(playlist_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.playlist_tree = ttk.Treeview(
            playlist_frame,
            style="MySpot.Treeview",
            selectmode="browse",
            show="headings",
            yscrollcommand=scrollbar.set
        )
        self.playlist_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.playlist_tree.yview)

        self.playlist_tree["columns"] = ("Track",)

        self.playlist_tree.column("Track", width=280, anchor=tk.W)

        self.playlist_tree.heading("Track", text="Track", anchor=tk.W)

        self.playlist_tree.bind("<Double-1>", self.play_selected_track)

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

        self.root.bind("<space>", lambda e: self.toggle_play_pause())
        self.root.bind("n", lambda e: self.next_track())
        self.root.bind("p", lambda e: self.previous_track())
        self.root.bind("m", lambda e: self.toggle_mute())
        self.root.bind("q", lambda e: self.on_close())
        self.root.bind("<plus>", lambda e: self.increase_volume())
        self.root.bind("<minus>", lambda e: self.decrease_volume())
        self.root.bind("<o>", lambda e: self.open_directory())
        self.root.bind("s", lambda e: self.shuffle_playlist())

    def _populate_playlist(self):
        """Populate the playlist treeview with tracks."""

        for item in self.playlist_tree.get_children():
            self.playlist_tree.delete(item)

        tracks_to_display = self.playlist.shuffled_tracks if self.playlist.shuffled_tracks else self.playlist.tracks

        for i, track_path in enumerate(tracks_to_display):
            track_name = Path(track_path).name
            self.playlist_tree.insert("", "end", iid=str(i), values=(track_name,))

        if self.playlist.current_index >= 0 and self.playlist.current_index < len(tracks_to_display):
            self.playlist_tree.selection_set(str(self.playlist.current_index))
            self.playlist_tree.see(str(self.playlist.current_index))

    def play_selected_track(self, event=None):
        """Play the track selected in the playlist."""
        selected_items = self.playlist_tree.selection()
        if not selected_items:
            return

        try:
            selected_index = int(selected_items[0])

            self.playlist.current_index = selected_index

            current_track = self.playlist.get_current_track()
            if current_track:
                self.player.play(current_track)
                self.update_ui()
                self.status_label.config(text=f"Playing: {Path(current_track).name}")
        except Exception as e:
            self.status_label.config(text=f"Error playing track: {e}")

    def shuffle_playlist(self):
        """Shuffle the playlist and update the UI."""
        if self.playlist.shuffle():
            self._populate_playlist()
            self.status_label.config(text="Playlist shuffled")

    def open_directory(self):
        directory = filedialog.askdirectory(
            title="Select Music Directory",
            initialdir=self.config.get('music_directory', os.path.expanduser("~/Music"))
        )

        if directory:
            self.status_label.config(text=f"Loading music from {directory}...")
            self.root.update()

            if self.playlist.scan_directory(directory):
                self.config.set('music_directory', directory)
                self.playlist.current_index = 0
                self._populate_playlist()
                self._play_current_track()
                self.update_track_info()
                self.status_label.config(text=f"Loaded {self.playlist.total_tracks()} tracks")
            else:
                self.status_label.config(text="No music files found in selected directory")

    def _play_current_track(self):
        current = self.playlist.get_current_track()
        if current:
            self.player.play(current)

            self.update_ui()
            if self.playlist.current_index >= 0:
                self.playlist_tree.selection_set(str(self.playlist.current_index))
                self.playlist_tree.see(str(self.playlist.current_index))
            self.status_label.config(text=f"Playing: {Path(current).name}")

    def toggle_play_pause(self):
        current = self.playlist.get_current_track()

        if not current:
            return

        status = self.player.toggle_play_pause()

        if status == "playing":
            self.play_button.config(text="⏸")
            self.status_label.config(text=f"Playing: {Path(current).name}")
        else:
            self.play_button.config(text="▶")
            self.status_label.config(text=f"Paused: {Path(current).name}")

    def next_track(self):
        next_track = self.playlist.next_track()
        if next_track:
            self.player.play(next_track)

            self.update_ui()
            self.playlist_tree.selection_set(str(self.playlist.current_index))
            self.playlist_tree.see(str(self.playlist.current_index))
            self.status_label.config(text=f"Playing: {Path(next_track).name}")

    def previous_track(self):
        prev_track = self.playlist.previous_track()
        if prev_track:
            self.player.play(prev_track)

            self.update_ui()
            self.playlist_tree.selection_set(str(self.playlist.current_index))
            self.playlist_tree.see(str(self.playlist.current_index))
            self.status_label.config(text=f"Playing: {Path(prev_track).name}")

    def toggle_mute(self):
        is_muted = self.player.toggle_mute()

        if is_muted:
            self.mute_button.config(text="🔇")
        else:
            self.mute_button.config(text="🔊")

    def set_volume(self, value):
        try:
            volume = float(value)
            self.player.set_volume(volume)
            self.volume_label.config(text=f"{int(volume * 100)}%")
            self.config.set('volume', volume)
        except ValueError:
            pass

    def increase_volume(self):
        new_vol = self.player.increase_volume(0.05)
        self.volume_var.set(new_vol)
        self.volume_label.config(text=f"{int(new_vol * 100)}%")
        self.config.set('volume', new_vol)

    def decrease_volume(self):
        new_vol = self.player.decrease_volume(0.05)
        self.volume_var.set(new_vol)
        self.volume_label.config(text=f"{int(new_vol * 100)}%")
        self.config.set('volume', new_vol)

    def update_track_info(self):
        track_info = self.playlist.get_current_track_info()

        if not track_info:
            self.track_var.set("No track playing")
            self.track_info_var.set("")
            return

        self.track_var.set(track_info['filename'])
        self.track_info_var.set(f"Track {track_info['index']} of {track_info['total']}")

    def update_ui(self):
        self.update_track_info()

        if self.player.is_playing():
            self.play_button.config(text="⏸")
        else:
            self.play_button.config(text="▶")

        if self.player.is_muted():
            self.mute_button.config(text="🔇")
        else:
            self.mute_button.config(text="🔊")

        self.volume_var.set(self.player.get_volume())
        self.volume_label.config(text=f"{int(self.player.get_volume() * 100)}%")

    def _poll_playback_status(self):
        import time
        while self.polling:
            if self.player.current_track and not self.player.is_playing() and not self.player.is_paused:
                self.next_track()
            time.sleep(0.5)

    def on_close(self):
        self.config.set('volume', self.player.get_volume())
        current = self.playlist.get_current_track()
        if current:
            self.config.set('last_played', current)

        self.polling = False
        self.player.stop()
        self.root.destroy()

    def start(self):
        self.root.mainloop()

def main():
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