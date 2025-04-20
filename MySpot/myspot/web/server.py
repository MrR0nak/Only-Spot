from flask import Flask, jsonify, request, render_template, send_from_directory
import os
import sys
import json
import threading
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MySpot components
from ..audio.player import AudioPlayer
from ..playlist.playlist import PlaylistManager
from ..config.config import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')

# Global state
config = ConfigManager()
player = AudioPlayer(volume=config.get('volume', 0.5))
playlist = PlaylistManager(config.get('music_directory'))

# Flag to track polling thread status
should_poll = True

def poll_track_ended():
    """Background thread to detect when tracks end"""
    import time
    global should_poll
    
    while should_poll:
        if player.current_track and not player.is_playing() and not player.is_paused:
            track = playlist.next_track()
            if track:
                player.play(track)
                logger.info(f"Auto-playing next track: {os.path.basename(track)}")
        time.sleep(0.5)

# Start polling thread
polling_thread = threading.Thread(target=poll_track_ended, daemon=True)
polling_thread.start()

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current player and playlist status"""
    track_info = playlist.get_current_track_info()
    
    return jsonify({
        'playing': player.is_playing(),
        'paused': player.is_paused,
        'muted': player.is_muted(),
        'volume': player.get_volume(),
        'current_track': track_info if track_info else None,
        'total_tracks': playlist.total_tracks()
    })

@app.route('/api/tracks', methods=['GET'])
def get_tracks():
    """Get list of tracks in playlist"""
    if not playlist.tracks:
        return jsonify({'tracks': [], 'message': 'No tracks loaded'})
    
    # Return simplified track list with paths and filenames
    tracks_info = []
    for i, track in enumerate(playlist.tracks):
        tracks_info.append({
            'index': i,
            'path': track,
            'filename': os.path.basename(track),
            'is_current': playlist.shuffled_tracks[playlist.current_index] == track if playlist.shuffled_tracks else False
        })
    
    return jsonify({'tracks': tracks_info})

@app.route('/api/play', methods=['POST'])
def play_track():
    """Play a track"""
    data = request.get_json(silent=True) or {}
    
    if 'index' in data:
        # Play specific track by index
        try:
            index = int(data['index'])
            if 0 <= index < len(playlist.tracks):
                # Find this track in shuffled list or reset shuffle
                target_track = playlist.tracks[index]
                try:
                    # Try to find in shuffled list
                    shuffle_index = playlist.shuffled_tracks.index(target_track)
                    playlist.current_index = shuffle_index
                except ValueError:
                    # Not in shuffled list, reshuffle
                    playlist.shuffle()
                    try:
                        playlist.current_index = playlist.shuffled_tracks.index(target_track)
                    except ValueError:
                        # Something went wrong
                        return jsonify({'success': False, 'message': 'Failed to locate track in playlist'})
                
                track = playlist.get_current_track()
                success = player.play(track)
                return jsonify({'success': success, 'track': os.path.basename(track) if success else None})
            else:
                return jsonify({'success': False, 'message': 'Track index out of range'})
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid track index'})
    else:
        # Play/resume current track
        current_track = playlist.get_current_track()
        if not current_track:
            return jsonify({'success': False, 'message': 'No track loaded'})
        
        if player.is_paused:
            player.unpause()
            return jsonify({'success': True, 'action': 'resumed', 'track': os.path.basename(current_track)})
        else:
            success = player.play(current_track)
            return jsonify({'success': success, 'action': 'played', 'track': os.path.basename(current_track) if success else None})

@app.route('/api/pause', methods=['POST'])
def pause_track():
    """Pause current playback"""
    if player.pause():
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Nothing playing'})

@app.route('/api/toggle', methods=['POST'])
def toggle_playback():
    """Toggle play/pause state"""
    status = player.toggle_play_pause()
    
    if status == "paused":
        return jsonify({'success': True, 'state': 'paused'})
    elif status == "playing":
        return jsonify({'success': True, 'state': 'playing'})
    else:
        return jsonify({'success': False, 'message': 'No track loaded'})

@app.route('/api/next', methods=['POST'])
def next_track():
    """Play next track"""
    track = playlist.next_track()
    if track:
        success = player.play(track)
        return jsonify({'success': success, 'track': os.path.basename(track) if success else None})
    return jsonify({'success': False, 'message': 'No tracks in playlist'})

@app.route('/api/previous', methods=['POST'])
def previous_track():
    """Play previous track"""
    track = playlist.previous_track()
    if track:
        success = player.play(track)
        return jsonify({'success': success, 'track': os.path.basename(track) if success else None})
    return jsonify({'success': False, 'message': 'No tracks in playlist'})

@app.route('/api/volume', methods=['POST'])
def set_volume():
    """Set player volume"""
    data = request.get_json(silent=True) or {}
    
    if 'volume' in data:
        try:
            volume = float(data['volume'])
            volume = max(0.0, min(1.0, volume))  # Ensure valid range
            
            player.set_volume(volume)
            config.set('volume', volume)
            
            return jsonify({'success': True, 'volume': volume})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid volume value'})
    
    return jsonify({'success': False, 'message': 'No volume specified'})

@app.route('/api/mute', methods=['POST'])
def toggle_mute():
    """Toggle mute state"""
    is_muted = player.toggle_mute()
    return jsonify({'success': True, 'muted': is_muted})

@app.route('/api/directory', methods=['GET'])
def get_directory():
    """Get current music directory"""
    return jsonify({'directory': config.get('music_directory')})

@app.route('/api/directory', methods=['POST'])
def set_directory():
    """Set and scan a new music directory"""
    data = request.get_json(silent=True) or {}
    
    if 'directory' in data:
        directory = data['directory']
        
        if not os.path.isdir(directory):
            return jsonify({'success': False, 'message': 'Directory not found'})
        
        if playlist.scan_directory(directory):
            config.set('music_directory', directory)
            
            # Auto play first track if none playing
            if not player.is_playing() and not player.is_paused:
                playlist.current_index = 0
                track = playlist.get_current_track()
                if track:
                    player.play(track)
            
            return jsonify({
                'success': True, 
                'directory': directory, 
                'tracks': playlist.total_tracks()
            })
        else:
            return jsonify({'success': False, 'message': 'No supported audio files found'})
    
    return jsonify({'success': False, 'message': 'No directory specified'})

@app.route('/api/shuffle', methods=['POST'])
def shuffle_playlist():
    """Shuffle the playlist"""
    if playlist.shuffle():
        # Play the first track in the new shuffled list
        track = playlist.get_current_track()
        if track:
            player.play(track)
        return jsonify({'success': True, 'total_tracks': playlist.total_tracks()})
    return jsonify({'success': False, 'message': 'No tracks to shuffle'})

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found', 'status': 404}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error', 'status': 500}), 500

if __name__ == '__main__':
    # Load initial directory if needed
    if not playlist.tracks and config.get('music_directory'):
        playlist.scan_directory(config.get('music_directory'))
        
    # Restore last played track if available
    last_played = config.get('last_played')
    if last_played and os.path.exists(last_played):
        try:
            # Find in playlist and set as current
            if last_played in playlist.tracks:
                if last_played in playlist.shuffled_tracks:
                    playlist.current_index = playlist.shuffled_tracks.index(last_played)
                else:
                    playlist.shuffle()
                    try:
                        playlist.current_index = playlist.shuffled_tracks.index(last_played)
                    except ValueError:
                        playlist.current_index = 0
        except Exception as e:
            logger.error(f"Error restoring last played track: {e}")
    
    # Run the app (listening only on localhost for security)
    app.run(host="127.0.0.1", port=5000, debug=False)
