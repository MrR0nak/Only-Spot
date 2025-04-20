import os
import sys
import unittest
import tempfile
import pygame
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from myspot.audio.player import AudioPlayer

class TestAudioPlayer(unittest.TestCase):
    """Test cases for the AudioPlayer class."""
    
    def setUp(self):
        """Set up test environment."""
        pygame.mixer.init = MagicMock()
        pygame.mixer.music = MagicMock()
        self.player = AudioPlayer(volume=0.7)
        
        # Create a temporary test audio file
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up after tests."""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    def test_init(self):
        """Test player initialization."""
        self.assertEqual(self.player._volume, 0.7)
        self.assertFalse(self.player._is_muted)
        pygame.mixer.init.assert_called_once()
    
    def test_play(self):
        """Test playing a file."""
        pygame.mixer.music.load = MagicMock()
        pygame.mixer.music.play = MagicMock()
        
        # Test with valid file
        result = self.player.play(self.temp_file.name)
        self.assertTrue(result)
        pygame.mixer.music.load.assert_called_with(self.temp_file.name)
        pygame.mixer.music.play.assert_called_once()
        
        # Test with invalid file
        result = self.player.play("nonexistent_file.mp3")
        self.assertFalse(result)
    
    def test_pause_unpause(self):
        """Test pause and unpause functionality."""
        pygame.mixer.music.pause = MagicMock()
        pygame.mixer.music.unpause = MagicMock()
        pygame.mixer.music.get_busy = MagicMock(return_value=True)
        
        # Test pause
        result = self.player.pause()
        self.assertTrue(result)
        pygame.mixer.music.pause.assert_called_once()
        
        # Test unpause
        result = self.player.unpause()
        self.assertTrue(result)
        pygame.mixer.music.unpause.assert_called_once()
    
    def test_toggle_play_pause(self):
        """Test toggling between play and pause."""
        self.player.pause = MagicMock(return_value=True)
        self.player.unpause = MagicMock(return_value=True)
        
        # When playing
        pygame.mixer.music.get_busy = MagicMock(return_value=True)
        result = self.player.toggle_play_pause()
        self.assertEqual(result, "paused")
        self.player.pause.assert_called_once()
        
        # When paused
        pygame.mixer.music.get_busy = MagicMock(return_value=False)
        result = self.player.toggle_play_pause()
        self.assertEqual(result, "playing")
        self.player.unpause.assert_called_once()
    
    def test_stop(self):
        """Test stopping playback."""
        pygame.mixer.music.stop = MagicMock()
        self.player.stop()
        pygame.mixer.music.stop.assert_called_once()
    
    def test_volume_control(self):
        """Test volume control functions."""
        pygame.mixer.music.set_volume = MagicMock()
        
        # Test set volume
        volume = self.player.set_volume(0.8)
        self.assertEqual(volume, 0.8)
        pygame.mixer.music.set_volume.assert_called_with(0.8)
        
        # Test increase volume
        self.player._volume = 0.5
        volume = self.player.increase_volume(0.1)
        self.assertEqual(volume, 0.6)
        
        # Test decrease volume
        volume = self.player.decrease_volume(0.2)
        self.assertEqual(volume, 0.4)
        
        # Test volume limits
        volume = self.player.set_volume(1.5)
        self.assertEqual(volume, 1.0)
        
        volume = self.player.set_volume(-0.5)
        self.assertEqual(volume, 0.0)
    
    def test_mute(self):
        """Test mute functionality."""
        pygame.mixer.music.set_volume = MagicMock()
        self.player._volume = 0.6
        
        # Test mute
        is_muted = self.player.toggle_mute()
        self.assertTrue(is_muted)
        self.assertTrue(self.player._is_muted)
        pygame.mixer.music.set_volume.assert_called_with(0)
        
        # Test unmute
        is_muted = self.player.toggle_mute()
        self.assertFalse(is_muted)
        self.assertFalse(self.player._is_muted)
        pygame.mixer.music.set_volume.assert_called_with(0.6)


if __name__ == "__main__":
    unittest.main()
    
input()