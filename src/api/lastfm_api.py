"""
LastFM API integration for SMF Player.
Handles album cover art and track information retrieval from LastFM.
"""

import urllib.request
import urllib.parse
import json
from PIL import Image
from typing import Optional, Dict, Any


class LastFMAPI:
    """Handles LastFM API interactions for album art and track info."""
    
    def __init__(self, api_key: str):
        """
        Initialize LastFM API client.
        
        Args:
            api_key: LastFM API key
        """
        self.api_key = api_key
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
            print("LastFM API key not configured")
            return None
        
        try:
            url = self._build_track_info_url(artist, track)
            response = urllib.request.urlopen(url)
            data = json.load(response)
            
            if 'track' in data:
                return data['track']
            else:
                print(f"Track not found: {artist} - {track}")
                return None
                
        except Exception as e:
            print(f"Error getting track info from LastFM: {e}")
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
            print(f"Error extracting album art URL: {e}")
        
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
            print(f"Error downloading album art: {e}")
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
            print(f"Error getting album name: {e}")
        
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
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}?{query_string}"
    
    def is_configured(self) -> bool:
        """
        Check if the API is properly configured.
        
        Returns:
            True if API key is set
        """
        return bool(self.api_key and self.api_key.strip())
    
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
            
            query_string = urllib.parse.urlencode(params)
            url = f"{self.base_url}?{query_string}"
            
            response = urllib.request.urlopen(url)
            data = json.load(response)
            
            return data.get('results', {}).get('artistmatches', {})
            
        except Exception as e:
            print(f"Error searching for artist: {e}")
            return None