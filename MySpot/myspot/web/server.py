from flask import Flask, jsonify, request, render_template, send_from_directory
import os
import sys
import json
import threading
import logging
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ..audio.player import AudioPlayer
from ..playlist.playlist import PlaylistManager
from ..config.config import ConfigManager
# Import the voice recognizer
from ..voice.recognizer import VoiceRecognizer

logger = logging.getLogger(__name__)
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')
config = ConfigManager()
player = AudioPlayer(volume=config.get('volume', 0.5))
playlist = PlaylistManager(config.get('music_directory'))

# Initialize voice recognizer
voice_recognizer = VoiceRecognizer(player=player, playlist=playlist, config=config)
voice_enabled = config.get('voice_enabled', False)

should_poll = True
def poll_track_ended():
    import time
    global should_poll
    while should_poll:
        if player.current_track and not player.is_playing() and not player.is_paused:
            track = playlist.next_track()
            if track:
                player.play(track)
        time.sleep(0.5)

polling_thread = threading.Thread(target=poll_track_ended, daemon=True)
polling_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path), 'favicon.ico')

@app.route('/api/status', methods=['GET'])
def get_status():
    track_info = playlist.get_current_track_info()
    return jsonify({
        'playing': player.is_playing(),
        'paused': player.is_paused,
        'muted': player.is_muted(),
        'volume': player.get_volume(),
        'current_track': track_info if track_info else None,
        'total_tracks': playlist.total_tracks(),
        'voice_enabled': voice_enabled  # Add voice status
    })

@app.route('/api/tracks', methods=['GET'])
def get_tracks():
    if not playlist.tracks:
        return jsonify({'tracks': [], 'message': 'No tracks loaded'})
    tracks_info = []
    for i, track in enumerate(playlist.tracks):
        tracks_info.append({
            'index': i,
            'path': track,
            'filename': os.path.basename(track),
            'is_current': playlist.shuffled_tracks[
                              playlist.current_index] == track if playlist.shuffled_tracks else False
        })
    return jsonify({'tracks': tracks_info})

@app.route('/api/play', methods=['POST'])
def play_track():
    data = request.get_json(silent=True) or {}
    if 'index' in data:
        try:
            index = int(data['index'])
            if 0 <= index < len(playlist.tracks):
                target_track = playlist.tracks[index]
                try:
                    shuffle_index = playlist.shuffled_tracks.index(target_track)
                    playlist.current_index = shuffle_index
                except ValueError:
                    playlist.shuffle()
                    try:
                        playlist.current_index = playlist.shuffled_tracks.index(target_track)
                    except ValueError:
                        return jsonify({'success': False, 'message': 'Failed to locate track in playlist'})
                track = playlist.get_current_track()
                success = player.play(track)
                return jsonify({'success': success, 'track': os.path.basename(track) if success else None})
            else:
                return jsonify({'success': False, 'message': 'Track index out of range'})
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid track index'})
    else:
        current_track = playlist.get_current_track()
        if not current_track:
            return jsonify({'success': False, 'message': 'No track loaded'})
        if player.is_paused:
            player.unpause()
            return jsonify({'success': True, 'action': 'resumed', 'track': os.path.basename(current_track)})
        else:
            success = player.play(current_track)
            return jsonify(
                {'success': success, 'action': 'played', 'track': os.path.basename(current_track) if success else None})

@app.route('/api/pause', methods=['POST'])
def pause_track():
    if player.pause():
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Nothing playing'})

@app.route('/api/toggle', methods=['POST'])
def toggle_playback():
    status = player.toggle_play_pause()
    if status == "paused":
        return jsonify({'success': True, 'state': 'paused'})
    elif status == "playing":
        return jsonify({'success': True, 'state': 'playing'})
    else:
        return jsonify({'success': False, 'message': 'No track loaded'})

@app.route('/api/next', methods=['POST'])
def next_track():
    track = playlist.next_track()
    if track:
        success = player.play(track)
        return jsonify({'success': success, 'track': os.path.basename(track) if success else None})
    return jsonify({'success': False, 'message': 'No tracks in playlist'})

@app.route('/api/previous', methods=['POST'])
def previous_track():
    track = playlist.previous_track()
    if track:
        success = player.play(track)
        return jsonify({'success': success, 'track': os.path.basename(track) if success else None})
    return jsonify({'success': False, 'message': 'No tracks in playlist'})

@app.route('/api/volume', methods=['POST'])
def set_volume():
    data = request.get_json(silent=True) or {}
    if 'volume' in data:
        try:
            volume = float(data['volume'])
            volume = max(0.0, min(1.0, volume))
            player.set_volume(volume)
            config.set('volume', volume)
            return jsonify({'success': True, 'volume': volume})
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid volume value'})
    return jsonify({'success': False, 'message': 'No volume specified'})

@app.route('/api/mute', methods=['POST'])
def toggle_mute():
    is_muted = player.toggle_mute()
    return jsonify({'success': True, 'muted': is_muted})

@app.route('/api/directory', methods=['GET'])
def get_directory():
    return jsonify({'directory': config.get('music_directory')})

@app.route('/api/directory', methods=['POST'])
def set_directory():
    data = request.get_json(silent=True) or {}
    if 'directory' in data:
        directory = data['directory']
        if not os.path.isdir(directory):
            return jsonify({'success': False, 'message': 'Directory not found'})
        if playlist.scan_directory(directory):
            config.set('music_directory', directory)
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
    if playlist.shuffle():
        track = playlist.get_current_track()
        if track:
            player.play(track)
        return jsonify({'success': True, 'total_tracks': playlist.total_tracks()})
    return jsonify({'success': False, 'message': 'No tracks to shuffle'})

# Voice recognition endpoints
@app.route('/api/voice/on', methods=['POST'])
def enable_voice():
    global voice_enabled
    if voice_enabled:
        return jsonify({'success': True, 'status': 'Voice recognition already enabled'})
    
    success = voice_recognizer.start()
    if success:
        voice_enabled = True
        config.set('voice_enabled', True)
        return jsonify({'success': True, 'status': 'Voice recognition enabled'})
    else:
        return jsonify({'success': False, 'message': 'Failed to enable voice recognition'})

@app.route('/api/voice/off', methods=['POST'])
def disable_voice():
    global voice_enabled
    if not voice_enabled:
        return jsonify({'success': True, 'status': 'Voice recognition already disabled'})
    
    success = voice_recognizer.stop()
    if success:
        voice_enabled = False
        config.set('voice_enabled', False)
        return jsonify({'success': True, 'status': 'Voice recognition disabled'})
    else:
        return jsonify({'success': False, 'message': 'Failed to disable voice recognition'})

@app.route('/api/voice/status', methods=['GET'])
def voice_status():
    return jsonify({
        'enabled': voice_enabled,
        'initialized': voice_recognizer.model is not None
    })

@app.errorhandler(404)
def not_found(e):
    logger.error(f"404 error: {request.path}")
    return jsonify({'error': 'Not found', 'status': 404}), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"500 error: {str(e)}")
    return jsonify({'error': 'Server error', 'status': 500}), 500

def main():
    parser = argparse.ArgumentParser(description='MySpot Web Player')
    parser.add_argument('--host', default='127.0.0.1', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--voice', action='store_true', help='Enable voice recognition on startup')
    args = parser.parse_args()

    # Check if we should enable voice recognition at startup
    global voice_enabled
    voice_start = args.voice or config.get('voice_enabled', False)
    
    if voice_start:
        logger.info("Initializing voice recognition...")
        if voice_recognizer.initialize() and voice_recognizer.start():
            voice_enabled = True
            logger.info("Voice recognition enabled")
        else:
            logger.warning("Failed to initialize voice recognition")
    
    if not playlist.tracks and config.get('music_directory'):
        playlist.scan_directory(config.get('music_directory'))
    
    last_played = config.get('last_played')
    if last_played and os.path.exists(last_played):
        if last_played in playlist.tracks:
            if last_played in playlist.shuffled_tracks:
                playlist.current_index = playlist.shuffled_tracks.index(last_played)
            else:
                playlist.shuffle()
                try:
                    playlist.current_index = playlist.shuffled_tracks.index(last_played)
                except ValueError:
                    playlist.current_index = 0
                    
    # Save the current config before starting
    config.save_config()
    
    # Run the app
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()
