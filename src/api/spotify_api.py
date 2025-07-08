"""
Spotify API integration for SMF Player.
Handles song recommendations and artist/track search using Spotify Web API.
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict, Optional, Tuple

from ..utils.logging_utils import get_logger, log_error, log_warning


class SpotifyAPI:
    """Handles Spotify API interactions for recommendations and search."""
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Spotify API client.
        
        Args:
            client_id: Spotify client ID
            client_secret: Spotify client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.spotify = None
        self.logger = get_logger(self.__class__.__name__)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Spotify client with credentials."""
        if not self.is_configured():
            log_warning("Spotify API credentials not configured", self.__class__.__name__)
            return
        
        try:
            client_credentials_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            self.spotify = spotipy.Spotify(
                client_credentials_manager=client_credentials_manager
            )
        except Exception as e:
            log_error(f"Error initializing Spotify client", e, self.__class__.__name__)
            self.spotify = None
    
    def search_artist_by_album(self, artist_name: str, album_name: str) -> Optional[str]:
        """
        Search for an artist ID by album and artist name.
        
        Args:
            artist_name: Name of the artist
            album_name: Name of the album
            
        Returns:
            Spotify artist ID or None if not found
        """
        if not self.spotify:
            return None
        
        try:
            offset = 0
            while offset < 100:  # Limit search to prevent infinite loops
                results = self.spotify.search(
                    q=f'album:{album_name} artist:{artist_name}',
                    type='album',
                    limit=50,
                    offset=offset
                )
                
                for album in results['albums']['items']:
                    if artist_name.lower() == album['artists'][0]['name'].lower():
                        return album['artists'][0]['id']
                
                offset += 50
                
                # Break if no more results
                if len(results['albums']['items']) < 50:
                    break
                    
        except Exception as e:
            log_error(f"Error searching for artist by album", e, self.__class__.__name__)
        
        return None
    
    def search_artist_by_track(self, artist_name: str, track_name: str) -> Optional[str]:
        """
        Search for an artist ID by track and artist name.
        
        Args:
            artist_name: Name of the artist
            track_name: Name of the track
            
        Returns:
            Spotify artist ID or None if not found
        """
        if not self.spotify:
            return None
        
        try:
            offset = 0
            while offset < 150:  # Limit search to prevent infinite loops
                results = self.spotify.search(
                    q=f'track:{track_name} artist:{artist_name}',
                    type='track',
                    limit=50,
                    offset=offset
                )
                
                for track in results['tracks']['items']:
                    return track['artists'][0]['id']  # Return first match
                
                offset += 50
                
                # Break if no more results
                if len(results['tracks']['items']) < 50:
                    break
                    
        except Exception as e:
            log_error(f"Error searching for artist by track", e, self.__class__.__name__)
        
        return None
    
    def get_recommendations_by_artist(self, artist_id: str, limit: int = 20) -> List[Dict[str, str]]:
        """
        Get song recommendations based on an artist.
        
        Args:
            artist_id: Spotify artist ID
            limit: Maximum number of recommendations
            
        Returns:
            List of recommendation dictionaries with artist, title, preview_url, and seed_artist
        """
        if not self.spotify or not artist_id:
            return []
        
        try:
            recommendations = self.spotify.recommendations(
                seed_artists=[artist_id],
                limit=limit
            )
            
            results = []
            for track in recommendations['tracks']:
                if track['preview_url']:  # Only include tracks with preview URLs
                    results.append({
                        'artist': track['artists'][0]['name'],
                        'title': track['name'],
                        'preview_url': track['preview_url'],
                        'seed_artist': artist_id
                    })
            
            return results
            
        except Exception as e:
            log_error(f"Error getting recommendations", e, self.__class__.__name__)
            return []
    
    def get_recommendations_by_album_artist(self, track_name: str, artist_name: str) -> List[Dict[str, str]]:
        """
        Get recommendations by first finding the artist through album search.
        
        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            
        Returns:
            List of recommendation dictionaries
        """
        # First try to get album name from LastFM or use track name as fallback
        album_name = track_name  # Simplified - in real implementation, get from LastFM
        
        artist_id = self.search_artist_by_album(artist_name, album_name)
        if not artist_id:
            return []
        
        recommendations = self.get_recommendations_by_artist(artist_id)
        
        # Add the seed artist name to each recommendation for reference
        for rec in recommendations:
            rec['seed_artist_name'] = artist_name
        
        return recommendations
    
    def get_recommendations_by_track_artist(self, track_name: str, artist_name: str) -> List[Dict[str, str]]:
        """
        Get recommendations by finding the artist through track search.
        
        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            
        Returns:
            List of recommendation dictionaries
        """
        artist_id = self.search_artist_by_track(artist_name, track_name)
        if not artist_id:
            return []
        
        recommendations = self.get_recommendations_by_artist(artist_id)
        
        # Add the seed artist name to each recommendation for reference
        for rec in recommendations:
            rec['seed_artist_name'] = artist_name
        
        return recommendations
    
    def search_track(self, track_name: str, artist_name: str = None) -> Optional[Dict]:
        """
        Search for a specific track.
        
        Args:
            track_name: Name of the track
            artist_name: Optional artist name to narrow search
            
        Returns:
            Track information dictionary or None if not found
        """
        if not self.spotify:
            return None
        
        try:
            query = f'track:{track_name}'
            if artist_name:
                query += f' artist:{artist_name}'
            
            results = self.spotify.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                return results['tracks']['items'][0]
                
        except Exception as e:
            log_error(f"Error searching for track", e, self.__class__.__name__)
        
        return None
    
    def is_configured(self) -> bool:
        """
        Check if the API is properly configured.
        
        Returns:
            True if client credentials are set
        """
        return bool(
            self.client_id and self.client_id.strip() and 
            self.client_secret and self.client_secret.strip() and
            self.client_id != 'set-client-id-here' and
            self.client_secret != 'set-client-secret-here'
        )