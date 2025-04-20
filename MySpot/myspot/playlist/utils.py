import os
import logging
from pathlib import Path
logger = logging.getLogger(__name__)
def scan_audio_files(directory, supported_formats):
    audio_files = []
    try:
        abs_directory = os.path.abspath(directory)
        for root, _, files in os.walk(abs_directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.splitext(file_path)[1].lower() in supported_formats:
                    audio_files.append(file_path)
        logger.info(f"Found {len(audio_files)} audio files in {directory}")
        return audio_files
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {e}")
        return []
def get_file_metadata(file_path):
    try:
        path = Path(file_path)
        return {
            'filename': path.name,
            'size': path.stat().st_size,
            'modified': path.stat().st_mtime,
            'extension': path.suffix.lower()
        }
    except Exception as e:
        logger.error(f"Error getting metadata for {file_path}: {e}")
        return None