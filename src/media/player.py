"""
Media player module for SMF Player.
Encapsulates wx.media.MediaCtrl and provides a clean interface for media playback.
"""

import wx
import wx.media
from typing import Optional, Callable

from ..utils.logging_utils import get_logger, log_error, log_warning


class MediaPlayer:
    """Wrapper around wx.media.MediaCtrl with additional functionality."""
    
    def __init__(self, parent: wx.Window):
        """
        Initialize the media player.
        
        Args:
            parent: Parent wx.Window for the MediaCtrl
        """
        self.parent = parent
        self.media_ctrl = None
        self.current_file = None
        self.volume = 1.0
        self.is_playing = False
        self.is_paused = False
        self.logger = get_logger(self.__class__.__name__)
        
        # Callbacks
        self.on_media_finished = None
        
        self._create_media_ctrl()
    
    def _create_media_ctrl(self):
        """Create the wx.media.MediaCtrl."""
        try:
            self.media_ctrl = wx.media.MediaCtrl(self.parent, style=wx.SIMPLE_BORDER)
            self.media_ctrl.SetVolume(self.volume)
        except NotImplementedError:
            log_error("Media control not supported on this platform", None, self.__class__.__name__)
            raise RuntimeError("Media control not supported on this platform")
    
    def load_file(self, file_path: str) -> bool:
        """
        Load a media file.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            True if file loaded successfully
        """
        if not self.media_ctrl:
            return False
        
        try:
            success = self.media_ctrl.Load(file_path)
            if success:
                self.current_file = file_path
                self.is_playing = False
                self.is_paused = False
            return success
        except Exception as e:
            log_error(f"Error loading file {file_path}", e, self.__class__.__name__)
            return False
    
    def load_uri(self, uri: str) -> bool:
        """
        Load a media URI (for streaming).
        
        Args:
            uri: URI to load
            
        Returns:
            True if URI loaded successfully
        """
        if not self.media_ctrl:
            return False
        
        try:
            success = self.media_ctrl.LoadURI(uri)
            if success:
                self.current_file = uri
                self.is_playing = False
                self.is_paused = False
            return success
        except Exception as e:
            log_error(f"Error loading URI {uri}", e, self.__class__.__name__)
            return False
    
    def play(self) -> bool:
        """
        Start or resume playback.
        
        Returns:
            True if playback started successfully
        """
        if not self.media_ctrl or not self.current_file:
            return False
        
        try:
            success = self.media_ctrl.Play()
            if success:
                self.is_playing = True
                self.is_paused = False
            return success
        except Exception as e:
            log_error(f"Error starting playback", e, self.__class__.__name__)
            return False
    
    def pause(self):
        """Pause playback."""
        if self.media_ctrl and self.is_playing:
            try:
                self.media_ctrl.Pause()
                self.is_paused = True
                self.is_playing = False
            except Exception as e:
                log_error(f"Error pausing playback", e, self.__class__.__name__)
    
    def stop(self):
        """Stop playback."""
        if self.media_ctrl:
            try:
                self.media_ctrl.Stop()
                self.is_playing = False
                self.is_paused = False
            except Exception as e:
                log_error(f"Error stopping playback", e, self.__class__.__name__)
    
    def seek(self, position: int):
        """
        Seek to a specific position.
        
        Args:
            position: Position in milliseconds
        """
        if self.media_ctrl:
            try:
                self.media_ctrl.Seek(position)
            except Exception as e:
                log_error(f"Error seeking to position {position}", e, self.__class__.__name__)
    
    def get_position(self) -> int:
        """
        Get current playback position.
        
        Returns:
            Current position in milliseconds
        """
        if self.media_ctrl:
            try:
                return self.media_ctrl.Tell()
            except Exception as e:
                log_error(f"Error getting position", e, self.__class__.__name__)
        return 0
    
    def get_length(self) -> int:
        """
        Get total length of current media.
        
        Returns:
            Total length in milliseconds
        """
        if self.media_ctrl:
            try:
                return self.media_ctrl.Length()
            except Exception as e:
                log_error(f"Error getting length", e, self.__class__.__name__)
        return 0
    
    def set_volume(self, volume: float):
        """
        Set playback volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        if self.media_ctrl:
            try:
                self.media_ctrl.SetVolume(self.volume)
            except Exception as e:
                log_error(f"Error setting volume", e, self.__class__.__name__)
    
    def get_volume(self) -> float:
        """
        Get current volume level.
        
        Returns:
            Current volume (0.0 to 1.0)
        """
        return self.volume
    
    def get_state(self) -> str:
        """
        Get current playback state.
        
        Returns:
            State string: 'playing', 'paused', 'stopped'
        """
        if self.is_playing:
            return 'playing'
        elif self.is_paused:
            return 'paused'
        else:
            return 'stopped'
    
    def is_at_end(self) -> bool:
        """
        Check if playback has reached the end.
        
        Returns:
            True if at end of media
        """
        if not self.media_ctrl:
            return False
        
        try:
            position = self.get_position()
            length = self.get_length()
            return position >= length and length > 0
        except Exception as e:
            log_error(f"Error checking if at end", e, self.__class__.__name__)
            return False
    
    def set_media_finished_callback(self, callback: Callable):
        """
        Set callback for when media finishes playing.
        
        Args:
            callback: Function to call when media finishes
        """
        self.on_media_finished = callback
    
    def cleanup(self):
        """Clean up resources."""
        self.stop()
        if self.media_ctrl:
            self.media_ctrl.Destroy()
            self.media_ctrl = None