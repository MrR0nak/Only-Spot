import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from myspot.playlist.playlist import PlaylistManager
from myspot.playlist import utils

class TestPlaylistManager(unittest.TestCase):
    """Test cases for the PlaylistManager class."""
    
    def setUp(self):
        """Set up test environment with mock audio files."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create some mock audio files
        self.audio_files = []
        for i in range(5):
            ext = '.mp3' if i % 2 == 0 else '.flac'
            file_path = os.path.join(self.test_dir, f"test{i}{ext}")
            with open(file_path, 'w') as f:
                f.write("mock audio data")
            self.audio_files.append(file_path)
        
        # Create a non-audio file too
        self.non_audio = os.path.join(self.test_dir, "test.txt")
        with open(self.non_audio, 'w') as f:
            f.write("this is not audio")
        
        # Set up playlist manager
        self.playlist = PlaylistManager()
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.test_dir)
    
    def test_scan_directory(self):
        """Test scanning a directory for audio files."""
        # Test with valid directory
        result = self.playlist.scan_directory(self.test_dir)
        self.assertTrue(result)
        self.assertEqual(len(self.playlist.tracks), 5)
        
        # Test with invalid directory
        result = self.playlist.scan_directory("/nonexistent/directory")
        self.assertFalse(result)
    
    def test_shuffle(self):
        """Test shuffling the playlist."""
        # Can't shuffle empty playlist
        self.assertFalse(self.playlist.shuffle())
        
        # Shuffle with tracks
        self.playlist.tracks = self.audio_files
        self.assertTrue(self.playlist.shuffle())
        
        # Check if shuffled list contains all tracks
        self.assertEqual(sorted(self.playlist.tracks), sorted(self.playlist.shuffled_tracks))
        
        # Check that current index is set
        self.assertEqual(self.playlist.current_index, 0)
    
    def test_get_current_track(self):
        """Test getting the current track."""
        # No tracks
        self.assertIsNone(self.playlist.get_current_track())
        
        # With tracks
        self.playlist.tracks = self.audio_files
        self.playlist.shuffle()
        
        current = self.playlist.get_current_track()
        self.assertIn(current, self.audio_files)
    
    def test_next_track(self):
        """Test moving to the next track."""
        # No tracks
        self.assertIsNone(self.playlist.next_track())
        
        # With tracks
        self.playlist.tracks = self.audio_files
        self.playlist.shuffle()
        
        # Save initial position
        initial_index = self.playlist.current_index
        initial_track = self.playlist.get_current_track()
        
        # Move to next track
        next_track = self.playlist.next_track()
        self.assertNotEqual(initial_track, next_track)
        self.assertEqual(self.playlist.current_index, initial_index + 1)
    
    def test_previous_track(self):
        """Test moving to the previous track."""
        # No tracks
        self.assertIsNone(self.playlist.previous_track())
        
        # With tracks
        self.playlist.tracks = self.audio_files
        self.playlist.shuffle()
        
        # Move to a middle position
        self.playlist.current_index = 2
        current = self.playlist.get_current_track()
        
        # Get previous track
        prev = self.playlist.previous_track()
        self.assertNotEqual(current, prev)
        self.assertEqual(self.playlist.current_index, 1)
    
    def test_wraparound(self):
        """Test that next/previous track wraps around."""
        self.playlist.tracks = self.audio_files
        self.playlist.shuffle()
        
        # Test wraparound for next
        self.playlist.current_index = len(self.playlist.shuffled_tracks) - 1
        next_track = self.playlist.next_track()
        self.assertEqual(self.playlist.current_index, 0)
        
        # Test wraparound for previous
        prev_track = self.playlist.previous_track()
        self.assertEqual(self.playlist.current_index, len(self.playlist.shuffled_tracks) - 1)


class TestPlaylistUtils(unittest.TestCase):
    """Test cases for playlist utility functions."""
    
    def setUp(self):
        """Set up test environment with mock audio files."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create some mock audio files
        self.audio_files = []
        for i in range(3):
            for ext in ['.mp3', '.wav', '.flac']:
                file_path = os.path.join(self.test_dir, f"test{i}{ext}")
                with open(file_path, 'w') as f:
                    f.write("mock audio data")
                self.audio_files.append(file_path)
        
        # Create a subdirectory with more files
        self.sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.sub_dir)
        for i in range(2):
            file_path = os.path.join(self.sub_dir, f"subtest{i}.mp3")
            with open(file_path, 'w') as f:
                f.write("mock audio data")
            self.audio_files.append(file_path)
        
        # Create non-audio files
        self.non_audio = []
        for ext in ['.txt', '.jpg', '.png']:
            file_path = os.path.join(self.test_dir, f"test{ext}")
            with open(file_path, 'w') as f:
                f.write("non-audio data")
            self.non_audio.append(file_path)
    
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.test_dir)
    
    def test_scan_audio_files(self):
        """Test scanning for audio files."""
        supported = ['.mp3', '.wav', '.flac']
        found = utils.scan_audio_files(self.test_dir, supported)
        
        # Should find all audio files including in subdirectory
        self.assertEqual(len(found), 11)  # 9 in main dir + 2 in subdir
        
        # All files should be audio files
        for file in found:
            self.assertTrue(os.path.splitext(file)[1].lower() in supported)
        
        # Non-audio files should not be included
        for file in self.non_audio:
            self.assertNotIn(file, found)
    
    def test_get_file_metadata(self):
        """Test getting file metadata."""
        test_file = self.audio_files[0]
        metadata = utils.get_file_metadata(test_file)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['filename'], os.path.basename(test_file))
        self.assertTrue('size' in metadata)
        self.assertTrue('modified' in metadata)
        self.assertEqual(metadata['extension'], os.path.splitext(test_file)[1].lower())
        
        # Test with nonexistent file
        metadata = utils.get_file_metadata("/nonexistent/file.mp3")
        self.assertIsNone(metadata)


if __name__ == "__main__":
    unittest.main()