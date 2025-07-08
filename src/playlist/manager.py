"""
Playlist manager for SMF Player.
Handles playlist operations including loading, saving, filtering, and managing songs.
"""

import os
import wx
from typing import List, Dict, Optional, Tuple
from shutil import copyfile

from ..database.manager import DatabaseManager, PlaylistDatabaseManager
from ..metadata.extractor import MetadataExtractor
from ..api.acoustid_api import AcoustIDAPI
from ..api.lastfm_api import LastFMAPI
from ..api.spotify_api import SpotifyAPI
from ..utils.image_processor import ImageProcessor
from ..utils.logging_utils import get_logger, log_error, log_warning, log_info


class PlaylistManager:
    """Manages playlist operations and song data."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize playlist manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.current_playlist = []  # List of song dictionaries
        self.recommendations = []  # List of recommendation lists
        self.logger = get_logger(self.__class__.__name__)
        
        # API clients (will be set by main frame)
        self.acoustid_api = None
        self.lastfm_api = None
        self.spotify_api = None
    
    def set_api_clients(self, acoustid_api: AcoustIDAPI, lastfm_api: LastFMAPI, spotify_api: SpotifyAPI):
        """Set API client instances."""
        self.acoustid_api = acoustid_api
        self.lastfm_api = lastfm_api
        self.spotify_api = spotify_api
    
    def clear_playlist(self):
        """Clear the current playlist."""
        self.current_playlist.clear()
        self.recommendations.clear()
        self.db_manager.clear_playlist()
    
    def add_song_from_file(self, file_path: str) -> Optional[Dict[str, str]]:
        """
        Add a song to the playlist from a file path.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Song dictionary or None if failed
        """
        if not os.path.isfile(file_path):
            log_warning(f"File not found: {file_path}", self.__class__.__name__)
            return None
        
        if not MetadataExtractor.is_supported_audio_file(file_path):
            log_warning(f"Unsupported file format: {file_path}", self.__class__.__name__)
            return None
        
        # Extract metadata
        metadata = MetadataExtractor.extract_metadata(file_path)
        
        # Check if song already exists in playlist
        if self._song_exists_in_playlist(metadata['artist'], metadata['title']):
            log_info(f"Song already in playlist: {metadata['artist']} - {metadata['title']}", self.__class__.__name__)
            return None
        
        # Create song dictionary
        song = {
            'title': metadata['title'],
            'artist': metadata['artist'],
            'duration': metadata['duration'],
            'year': metadata['year'],
            'path': file_path,
            'times_played': 0,
            'rating': 0
        }
        
        # Add to database
        success = self.db_manager.insert_song(
            song['title'], song['duration'], song['artist'], 
            song['year'], song['path']
        )
        
        if success:
            # Get rating from database
            song['rating'] = self.db_manager.get_rating(song['title'], song['artist'])
            
            # Add rating entry if it doesn't exist
            self.db_manager.insert_or_update_rating(song['title'], song['artist'])
            
            # Add to current playlist
            self.current_playlist.append(song)
            return song
        
        return None
    
    def load_folder(self, folder_path: str) -> List[Dict[str, str]]:
        """
        Load all supported audio files from a folder.
        
        Args:
            folder_path: Path to the folder
            
        Returns:
            List of loaded song dictionaries
        """
        loaded_songs = []
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if MetadataExtractor.is_supported_audio_file(file):
                    file_path = os.path.join(root, file)
                    song = self.add_song_from_file(file_path)
                    if song:
                        loaded_songs.append(song)
        
        return loaded_songs
    
    def load_files(self, file_paths: List[str]) -> List[Dict[str, str]]:
        """
        Load multiple files into the playlist.
        
        Args:
            file_paths: List of file paths
            
        Returns:
            List of loaded song dictionaries
        """
        loaded_songs = []
        
        for file_path in file_paths:
            song = self.add_song_from_file(file_path)
            if song:
                loaded_songs.append(song)
        
        return loaded_songs
    
    def save_playlist(self, save_path: str) -> bool:
        """
        Save current playlist to a database file.
        
        Args:
            save_path: Path where to save the playlist
            
        Returns:
            True if saved successfully
        """
        try:
            # Ensure .db extension
            if not save_path.endswith('.db'):
                save_path += '.db'
            
            # Copy current database to save location
            copyfile(self.db_manager.db_path, save_path)
            return True
            
        except Exception as e:
            log_error(f"Error saving playlist", e, self.__class__.__name__)
            return False
    
    def load_playlist(self, playlist_path: str) -> List[Dict[str, str]]:
        """
        Load a saved playlist from a database file.
        
        Args:
            playlist_path: Path to the playlist database file
            
        Returns:
            List of loaded song dictionaries
        """
        try:
            # Create a temporary database manager for the playlist file
            playlist_db = PlaylistDatabaseManager(playlist_path)
            file_paths = playlist_db.get_all_playlist_paths()
            playlist_db.close()
            
            # Load the files
            return self.load_files(file_paths)
            
        except Exception as e:
            log_error(f"Error loading playlist", e, self.__class__.__name__)
            return []
    
    def get_song_by_index(self, index: int) -> Optional[Dict[str, str]]:
        """Get song by playlist index."""
        if 0 <= index < len(self.current_playlist):
            return self.current_playlist[index]
        return None
    
    def get_song_by_artist_title(self, artist: str, title: str) -> Optional[Tuple[Dict[str, str], int]]:
        """
        Get song and its index by artist and title.
        
        Returns:
            Tuple of (song_dict, index) or None if not found
        """
        for i, song in enumerate(self.current_playlist):
            if song['artist'] == artist and song['title'] == title:
                return song, i
        return None
    
    def update_times_played(self, song_index: int) -> int:
        """
        Update the times played counter for a song.
        
        Args:
            song_index: Index of the song in the playlist
            
        Returns:
            New times played count
        """
        if 0 <= song_index < len(self.current_playlist):
            song = self.current_playlist[song_index]
            new_count = self.db_manager.update_times_played(song['path'])
            song['times_played'] = new_count
            return new_count
        return 0
    
    def update_song_rating(self, song_index: int, rating: int):
        """
        Update the rating for a song.
        
        Args:
            song_index: Index of the song in the playlist
            rating: New rating (1-5)
        """
        if 0 <= song_index < len(self.current_playlist):
            song = self.current_playlist[song_index]
            self.db_manager.update_rating(song['title'], song['artist'], rating)
            song['rating'] = rating
    
    def filter_playlist(self, filter_type: str, filter_value: str):
        """
        Filter the current playlist by artist or title.
        
        Args:
            filter_type: 'Artist' or 'Title'
            filter_value: Value to filter by
        """
        if filter_type == 'Artist':
            self.current_playlist = [
                song for song in self.current_playlist 
                if song['artist'].lower() == filter_value.lower()
            ]
        elif filter_type == 'Title':
            self.current_playlist = [
                song for song in self.current_playlist 
                if song['title'].lower() == filter_value.lower()
            ]
        
        # Update database to match filtered playlist
        # Note: This is a destructive operation in the original code
        # You might want to implement this differently
    
    def remove_song(self, song_index: int) -> bool:
        """
        Remove a song from the playlist.
        
        Args:
            song_index: Index of the song to remove
            
        Returns:
            True if removed successfully
        """
        if 0 <= song_index < len(self.current_playlist):
            song = self.current_playlist[song_index]
            self.db_manager.delete_song_by_path(song['path'])
            del self.current_playlist[song_index]
            return True
        return False
    
    def update_song_path(self, song_index: int, new_path: str) -> bool:
        """
        Update the file path for a song (when file has been moved).
        
        Args:
            song_index: Index of the song
            new_path: New file path
            
        Returns:
            True if updated successfully
        """
        if 0 <= song_index < len(self.current_playlist):
            song = self.current_playlist[song_index]
            old_path = song['path']
            
            self.db_manager.update_song_path(old_path, new_path)
            song['path'] = new_path
            return True
        return False
    
    def find_moved_file(self, original_path: str) -> Optional[str]:
        """
        Try to find a file that has been moved within the same directory tree.
        
        Args:
            original_path: Original file path
            
        Returns:
            New path if found, None otherwise
        """
        if os.name == 'nt':
            path_parts = original_path.rsplit('\\', 1)
        else:
            path_parts = original_path.rsplit('/', 1)
        
        if len(path_parts) != 2:
            return None
        
        directory = path_parts[0]
        filename = path_parts[1]
        
        # Search in subdirectories
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return os.path.join(root, filename)
        
        return None
    
    def get_enhanced_metadata(self, song: Dict[str, str]) -> Dict[str, str]:
        """
        Get enhanced metadata using API services when basic metadata is missing.
        
        Args:
            song: Song dictionary
            
        Returns:
            Enhanced song dictionary
        """
        enhanced_song = song.copy()
        
        # If artist is empty, try AcoustID
        if not song['artist'] and self.acoustid_api and self.acoustid_api.is_configured():
            try:
                result = self.acoustid_api.get_metadata_from_file(song['path'])
                if result:
                    enhanced_song['artist'] = result[0]
                    enhanced_song['title'] = result[1]
            except Exception as e:
                log_error(f"Error getting AcoustID metadata", e, self.__class__.__name__)
        
        return enhanced_song
    
    def get_recommendations(self, artist_name: str, track_name: str) -> List[Dict[str, str]]:
        """
        Get song recommendations for an artist/track.
        
        Args:
            artist_name: Artist name
            track_name: Track name
            
        Returns:
            List of recommendation dictionaries
        """
        if not self.spotify_api or not self.spotify_api.is_configured():
            return []
        
        # Check if we already have recommendations for this artist
        for rec_list in self.recommendations:
            for rec in rec_list:
                if rec.get('seed_artist_name') == artist_name:
                    return rec_list
        
        # Try album-based recommendations first
        try:
            recommendations = self.spotify_api.get_recommendations_by_album_artist(
                track_name, artist_name
            )
            if recommendations:
                self.recommendations.append(recommendations)
                return recommendations
        except Exception as e:
            log_error(f"Error getting album-based recommendations", e, self.__class__.__name__)
        
        # Fall back to track-based recommendations
        try:
            recommendations = self.spotify_api.get_recommendations_by_track_artist(
                track_name, artist_name
            )
            if recommendations:
                self.recommendations.append(recommendations)
                return recommendations
        except Exception as e:
            log_error(f"Error getting track-based recommendations", e, self.__class__.__name__)
        
        return []
    
    def _song_exists_in_playlist(self, artist: str, title: str) -> bool:
        """Check if a song already exists in the current playlist."""
        for song in self.current_playlist:
            if song['artist'] == artist and song['title'] == title:
                return True
        return False
    
    def get_playlist_count(self) -> int:
        """Get the number of songs in the current playlist."""
        return len(self.current_playlist)
    
    def get_playlist_copy(self) -> List[Dict[str, str]]:
        """Get a copy of the current playlist."""
        return self.current_playlist.copy()