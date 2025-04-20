import sys
import os
import tkinter as tk
from tkinter import ttk
from myspot.ui.gui import main as gui_main
from myspot.ui.cli import main as cli_main
from myspot.web.server import app as web_app
import threading

class MySpotLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MySpot Launcher")
        self.root.geometry("400x300")
        self.root.minsize(400, 300)
        
        # Set dark theme
        self.bg_color = "#1E1E1E"
        self.fg_color = "#E6E6E6"
        self.accent_color = "#1DB954"  # Spotify green
        self.button_bg = "#3D3D3D"
        
        self.root.configure(bg=self.bg_color)
        
        self._create_ui()
    
    def _create_ui(self):
        # Main frame with padding
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=25)
        
        # Header
        title_label = tk.Label(
            main_frame,
            text="MySpot Player",
            bg=self.bg_color,
            fg=self.accent_color,
            font=("Segoe UI", 24, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Select mode text
        select_label = tk.Label(
            main_frame,
            text="Select a mode to start:",
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 12)
        )
        select_label.pack(pady=(0, 15))
        
        # Buttons container
        buttons_frame = tk.Frame(main_frame, bg=self.bg_color)
        buttons_frame.pack(fill=tk.X, pady=5)
        
        # Server button
        server_btn = self.create_button(
            buttons_frame, 
            "🌐  1. Web Server", 
            self.start_server,
            14
        )
        server_btn.pack(fill=tk.X, pady=5)
        
        # GUI button
        gui_btn = self.create_button(
            buttons_frame, 
            "🖥️  2. Local GUI", 
            self.start_gui,
            14
        )
        gui_btn.pack(fill=tk.X, pady=5)
        
        # CLI button
        cli_btn = self.create_button(
            buttons_frame, 
            "📟  3. Local CLI", 
            self.start_cli,
            14
        )
        cli_btn.pack(fill=tk.X, pady=5)
        
        # Exit button
        exit_btn = self.create_button(
            main_frame, 
            "Exit", 
            self.root.destroy,
            12,
            hover_color="#A83232"
        )
        exit_btn.pack(pady=(20, 0))
        
        # Keyboard shortcuts
        self.root.bind('1', lambda e: self.start_server())
        self.root.bind('2', lambda e: self.start_gui())
        self.root.bind('3', lambda e: self.start_cli())
        self.root.bind('<Escape>', lambda e: self.root.destroy())
    
    def create_button(self, parent, text, command, size=12, hover_color="#333333"):
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", size),
            bg=self.button_bg,
            fg="#FFFFFF",
            activebackground="#444444",
            activeforeground="#FFFFFF",
            borderwidth=0,
            padx=10,
            pady=8,
            cursor="hand2",
            command=command
        )
        
        btn.bind("<Enter>", lambda e: btn.config(background=hover_color))
        btn.bind("<Leave>", lambda e: btn.config(background=self.button_bg))
        
        return btn
    
    def start_server(self):
        self.root.destroy()
        print("Starting MySpot Web Server...")
        web_app.run(host="127.0.0.1", port=5000, debug=False)
    
    def start_gui(self):
        self.root.destroy()
        print("Starting MySpot GUI...")
        gui_main()
    
    def start_cli(self):
        self.root.destroy()
        print("Starting MySpot CLI...")
        cli_main()
    
    def run(self):
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        self.root.mainloop()

if __name__ == "__main__":
    launcher = MySpotLauncher()
    launcher.run()
