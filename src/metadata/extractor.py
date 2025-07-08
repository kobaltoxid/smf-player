"""
Metadata extractor for SMF Player.
Handles extraction of metadata from audio files using mutagen and ID3.
"""

import os
import re
import wave
import contextlib
from typing import Dict, Optional
from mutagen.id3 import ID3
from mutagen import File as MutaFile


class MetadataExtractor:
    """Extracts metadata from audio files."""
    
    @staticmethod
    def extract_metadata(file_path: str) -> Dict[str, str]:
        """
        Extract metadata from an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing metadata: title, artist, duration, year
        """
        metadata = {
            'title': 'n/a',
            'artist': '',
            'duration': '0:00',
            'year': ''
        }
        
        # Get backup name from filename
        backup_name = os.path.splitext(os.path.basename(file_path))[0]
        metadata['title'] = backup_name
        
        # Get duration
        duration_seconds = MetadataExtractor._get_duration(file_path)
        metadata['duration'] = MetadataExtractor._format_duration(duration_seconds)
        
        # Try to extract ID3 tags
        try:
            audio = ID3(file_path)
            
            # Extract artist
            if 'TPE1' in audio:
                artist = audio['TPE1'].text[0]
                # Clean artist name (remove features, parentheses, etc.)
                artist = re.split(r'[,\(\)\?]', artist)[0].strip()
                metadata['artist'] = artist
            
            # Extract title
            if 'TIT2' in audio:
                title = audio['TIT2'].text[0]
                # Clean title
                title = re.split(r'[,\(\)\?]', title)[0].strip()
                metadata['title'] = title
            
            # Extract year
            if 'TDRC' in audio:
                metadata['year'] = str(audio['TDRC'].text[0])
                
        except Exception as e:
            print(f"Could not extract ID3 tags from {file_path}: {e}")
            # Keep the backup values
        
        return metadata
    
    @staticmethod
    def _get_duration(file_path: str) -> float:
        """
        Get the duration of an audio file in seconds.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Duration in seconds
        """
        try:
            # Try using mutagen first
            song = MutaFile(file_path)
            if song and hasattr(song, 'info') and hasattr(song.info, 'length'):
                return float(song.info.length)
        except Exception:
            pass
        
        # Fallback for WAV files
        if file_path.lower().endswith('.wav'):
            try:
                with contextlib.closing(wave.open(file_path, 'r')) as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    return frames / float(rate)
            except Exception as e:
                print(f"Could not get WAV duration for {file_path}: {e}")
        
        return 0.0
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """
        Format duration from seconds to MM:SS format.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted duration string
        """
        if seconds <= 0:
            return "0:00"
        
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    @staticmethod
    def get_embedded_album_art(file_path: str) -> Optional[bytes]:
        """
        Extract embedded album art from an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Album art data as bytes, or None if not found
        """
        try:
            tags = ID3(file_path)
            if "APIC:" in tags:
                return tags.get("APIC:").data
        except Exception as e:
            print(f"Could not extract album art from {file_path}: {e}")
        
        return None
    
    @staticmethod
    def is_supported_audio_file(file_path: str) -> bool:
        """
        Check if a file is a supported audio format.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file is a supported audio format
        """
        from ..config import SUPPORTED_AUDIO_EXTENSIONS
        return file_path.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS)