"""
Configuration module for SMF Player.
Centralizes API keys, database paths, and other settings.
"""

import os

# API Keys - These should be set by the user
SPOTIPY_CLIENT_ID = 'set-client-id-here'
SPOTIPY_CLIENT_SECRET = 'set-client-secret-here'
SPOTIPY_REDIRECT_URI = 'set-client-uri-here'

# LastFM API key
LASTFM_API_KEY = ''

# AcoustID API key
ACOUSTID_API_KEY = ''

# Database configuration
DEFAULT_PLAYLIST_DB = 'playing.db'

# Supported audio file extensions
SUPPORTED_AUDIO_EXTENSIONS = ('.mp3', '.flac', '.wav', '.aac', '.ogg')

# UI Configuration
WINDOW_SIZE = (1300, 800)
WINDOW_POSITION = (0, 0)
ALBUM_ART_SIZE = (500, 500)
BUTTON_SIZE = (25, 30)

def setup_spotify_environment():
    """Set up Spotify environment variables."""
    os.environ['SPOTIPY_CLIENT_ID'] = SPOTIPY_CLIENT_ID
    os.environ['SPOTIPY_CLIENT_SECRET'] = SPOTIPY_CLIENT_SECRET
    os.environ['SPOTIPY_REDIRECT_URI'] = SPOTIPY_REDIRECT_URI