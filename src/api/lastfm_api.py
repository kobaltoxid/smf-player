"""
LastFM API integration for SMF Player.
Handles album cover art and track information retrieval from LastFM.
"""

import urllib.request
from PIL import Image
from typing import Optional, Dict, Any

from .api_base import APIBase
from ..utils.logging_utils import log_error, log_warning


class LastFMAPI(APIBase):
    """Handles LastFM API interactions for album art and track info."""
    
    def __init__(self, api_key: str):
        """
        Initialize LastFM API client.
        
        Args:
            api_key: LastFM API key
        """
        super().__init__(api_key)
        self.base_url = 'http://ws.audioscrobbler.com/2.0/'
    
    def get_track_info(self, artist: str, track: str) -> Optional[Dict[str, Any]]:
        """
        Get track information from LastFM.
        
        Args:
            artist: Artist name
            track: Track name
            
        Returns:
            Dictionary containing track information or None if not found
        """
        if not self.is_configured():
            log_warning("LastFM API key not configured", self.__class__.__name__)
            return None
        
        try:
            url = self._build_track_info_url(artist, track)
            data = self._make_get_request(url)
            
            if data is None:
                return None
            
            if 'track' in data:
                return data['track']
            else:
                log_warning(f"Track not found: {artist} - {track}", self.__class__.__name__)
                return None
                
        except Exception as e:
            log_error(f"Error getting track info from LastFM", e, self.__class__.__name__)
            return None
    
    def get_album_art_url(self, artist: str, track: str, size: str = 'large') -> Optional[str]:
        """
        Get album art URL for a track.
        
        Args:
            artist: Artist name
            track: Track name
            size: Image size ('small', 'medium', 'large', 'extralarge')
            
        Returns:
            URL of album art or None if not found
        """
        track_info = self.get_track_info(artist, track)
        if not track_info:
            return None
        
        try:
            if 'album' in track_info and 'image' in track_info['album']:
                images = track_info['album']['image']
                
                # Map size to index
                size_map = {
                    'small': 0,
                    'medium': 1,
                    'large': 2,
                    'extralarge': 3
                }
                
                size_index = size_map.get(size, 2)  # Default to large
                
                if len(images) > size_index:
                    image_url = images[size_index]['#text']
                    return image_url if image_url else None
                    
        except Exception as e:
            log_error(f"Error extracting album art URL", e, self.__class__.__name__)
        
        return None
    
    def download_album_art(self, artist: str, track: str, size: str = 'large') -> Optional[Image.Image]:
        """
        Download album art as PIL Image.
        
        Args:
            artist: Artist name
            track: Track name
            size: Image size ('small', 'medium', 'large', 'extralarge')
            
        Returns:
            PIL Image object or None if not found/downloaded
        """
        image_url = self.get_album_art_url(artist, track, size)
        if not image_url:
            return None
        
        try:
            response = urllib.request.urlopen(image_url)
            image = Image.open(response)
            return image
            
        except Exception as e:
            log_error(f"Error downloading album art from {image_url}", e, self.__class__.__name__)
            return None
    
    def get_album_name(self, artist: str, track: str) -> Optional[str]:
        """
        Get album name for a track.
        
        Args:
            artist: Artist name
            track: Track name
            
        Returns:
            Album name or None if not found
        """
        track_info = self.get_track_info(artist, track)
        if not track_info:
            return None
        
        try:
            if 'album' in track_info and 'title' in track_info['album']:
                return track_info['album']['title']
        except Exception as e:
            log_error(f"Error getting album name", e, self.__class__.__name__)
        
        return None
    
    def _build_track_info_url(self, artist: str, track: str) -> str:
        """
        Build the LastFM track.getInfo URL.
        
        Args:
            artist: Artist name
            track: Track name
            
        Returns:
            Complete API URL
        """
        params = {
            'method': 'track.getInfo',
            'format': 'json',
            'api_key': self.api_key,
            'artist': artist,
            'track': track
        }
        
        return self._build_url(self.base_url, params)
    
    def is_configured(self) -> bool:
        """
        Check if the API is properly configured.
        
        Returns:
            True if API key is set
        """
        return self._is_api_key_valid()
    
    def search_artist(self, artist_name: str, limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Search for artist information.
        
        Args:
            artist_name: Name of the artist to search for
            limit: Maximum number of results
            
        Returns:
            Dictionary containing search results or None if error
        """
        if not self.is_configured():
            return None
        
        try:
            params = {
                'method': 'artist.search',
                'format': 'json',
                'api_key': self.api_key,
                'artist': artist_name,
                'limit': str(limit)
            }
            
            url = self._build_url(self.base_url, params)
            data = self._make_get_request(url)
            
            if data is None:
                return None
            
            return data.get('results', {}).get('artistmatches', {})
            
        except Exception as e:
            log_error(f"Error searching for artist", e, self.__class__.__name__)
            return None