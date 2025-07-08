"""
Database manager for SMF Player.
Handles all SQLite database operations for playlists and ratings.
"""

import sqlite3
import os
from typing import List, Tuple, Optional

from ..utils.logging_utils import get_logger, log_error


class DatabaseManager:
    """Manages SQLite database operations for the music player."""
    
    def __init__(self, db_path: str = 'playing.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.logger = get_logger(self.__class__.__name__)
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish connection to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            log_error(f"Database connection error", e, self.__class__.__name__)
            raise
    
    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        # Create playlist table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist (
                title VARCHAR(255),
                duration VARCHAR(255),
                artist VARCHAR(255),
                year VARCHAR(255),
                path VARCHAR(255) UNIQUE,
                timesplayed INTEGER DEFAULT 0
            )
        ''')
        
        # Create rating table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate (
                title VARCHAR(255),
                artist VARCHAR(255),
                rating INTEGER,
                UNIQUE(title, artist)
            )
        ''')
        
        self.conn.commit()
    
    def clear_playlist(self):
        """Clear all songs from the current playlist."""
        self.cursor.execute('DELETE FROM playlist')
        self.conn.commit()
    
    def insert_song(self, title: str, duration: str, artist: str, year: str, path: str) -> bool:
        """Insert a new song into the playlist."""
        try:
            self.cursor.execute('''
                REPLACE INTO playlist (title, duration, artist, year, path, timesplayed)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (title, duration, artist, year, path))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            log_error(f"Error inserting song", e, self.__class__.__name__)
            return False
    
    def update_times_played(self, path: str) -> int:
        """Increment and return the times played counter for a song."""
        try:
            # Get current count
            self.cursor.execute('SELECT timesplayed FROM playlist WHERE path = ?', (path,))
            result = self.cursor.fetchone()
            if result:
                new_count = result[0] + 1
                self.cursor.execute(
                    'UPDATE playlist SET timesplayed = ? WHERE path = ?',
                    (new_count, path)
                )
                self.conn.commit()
                return new_count
            return 0
        except sqlite3.Error as e:
            log_error(f"Error updating times played", e, self.__class__.__name__)
            return 0
    
    def get_song_by_artist_title(self, artist: str, title: str) -> Optional[Tuple]:
        """Get song information by artist and title."""
        try:
            self.cursor.execute(
                'SELECT path FROM playlist WHERE artist = ? AND title = ?',
                (artist, title)
            )
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            log_error(f"Error getting song", e, self.__class__.__name__)
            return None
    
    def get_times_played(self, path: str) -> int:
        """Get the times played count for a song."""
        try:
            self.cursor.execute('SELECT timesplayed FROM playlist WHERE path = ?', (path,))
            result = self.cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            log_error(f"Error getting times played", e, self.__class__.__name__)
            return 0
    
    def delete_song_by_path(self, path: str):
        """Delete a song from the playlist by path."""
        try:
            self.cursor.execute('DELETE FROM playlist WHERE path = ?', (path,))
            self.conn.commit()
        except sqlite3.Error as e:
            log_error(f"Error deleting song", e, self.__class__.__name__)
    
    def delete_song_by_artist_title(self, artist: str, title: str):
        """Delete a song from the playlist by artist and title."""
        try:
            self.cursor.execute(
                'DELETE FROM playlist WHERE artist = ? AND title = ?',
                (artist, title)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            log_error(f"Error deleting song", e, self.__class__.__name__)
    
    def update_song_path(self, old_path: str, new_path: str):
        """Update the path of a song in the database."""
        try:
            self.cursor.execute(
                'UPDATE playlist SET path = ? WHERE path = ?',
                (new_path, old_path)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            log_error(f"Error updating song path", e, self.__class__.__name__)
    
    def insert_or_update_rating(self, title: str, artist: str, rating: int = None):
        """Insert or update a song rating."""
        try:
            if rating is not None:
                self.cursor.execute('''
                    REPLACE INTO rate (title, artist, rating)
                    VALUES (?, ?, ?)
                ''', (title, artist, rating))
            else:
                # Insert with existing rating if available
                self.cursor.execute('''
                    REPLACE INTO rate (title, artist, rating)
                    VALUES (?, ?, (SELECT rating FROM rate WHERE title = ? AND artist = ?))
                ''', (title, artist, title, artist))
            self.conn.commit()
        except sqlite3.Error as e:
            log_error(f"Error inserting/updating rating", e, self.__class__.__name__)
    
    def get_rating(self, title: str, artist: str) -> Optional[int]:
        """Get the rating for a song."""
        try:
            self.cursor.execute(
                'SELECT rating FROM rate WHERE title = ? AND artist = ?',
                (title, artist)
            )
            result = self.cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except sqlite3.Error as e:
            log_error(f"Error getting rating", e, self.__class__.__name__)
            return 0
    
    def update_rating(self, title: str, artist: str, rating: int):
        """Update the rating for a song."""
        try:
            self.cursor.execute(
                'UPDATE rate SET rating = ? WHERE title = ? AND artist = ?',
                (rating, title, artist)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            log_error(f"Error updating rating", e, self.__class__.__name__)
    
    def get_all_playlist_paths(self) -> List[str]:
        """Get all file paths from the current playlist."""
        try:
            self.cursor.execute('SELECT path FROM playlist')
            return [row[0] for row in self.cursor.fetchall()]
        except sqlite3.Error as e:
            log_error(f"Error getting playlist paths", e, self.__class__.__name__)
            return []
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()


class PlaylistDatabaseManager(DatabaseManager):
    """Specialized database manager for saved playlist files."""
    
    def __init__(self, playlist_path: str):
        # Don't call parent __init__ as we want different behavior
        self.db_path = playlist_path
        self.conn = None
        self.cursor = None
        self._connect()
        # Note: We don't create tables here as we're reading existing playlists