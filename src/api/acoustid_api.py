"""
AcoustID API integration for SMF Player.
Handles audio fingerprinting and metadata lookup using AcoustID service.
"""

import urllib.request
import urllib.parse
import json
import acoustid
from acoustid import fingerprint_file
from typing import Optional, Tuple


class AcoustIDAPI:
    """Handles AcoustID API interactions for audio fingerprinting."""
    
    def __init__(self, api_key: str):
        """
        Initialize AcoustID API client.
        
        Args:
            api_key: AcoustID API key
        """
        self.api_key = api_key
    
    def get_metadata_from_file(self, file_path: str) -> Optional[Tuple[str, str]]:
        """
        Get song metadata (artist, title) from audio file using fingerprinting.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of (artist, title) or None if not found
        """
        if not self.api_key:
            print("AcoustID API key not configured")
            return None
        
        try:
            # Generate fingerprint
            fingerprint_data = fingerprint_file(file_path, force_fpcalc=True)
            if not fingerprint_data or len(fingerprint_data) < 2:
                print("Could not generate fingerprint")
                return None
            
            duration = fingerprint_data[0]
            fingerprint = str(fingerprint_data[1])
            
            # Clean fingerprint string
            if fingerprint.startswith("b'") and fingerprint.endswith("'"):
                fingerprint = fingerprint[2:-1]
            
            # Build API URL
            url = self._build_lookup_url(duration, fingerprint)
            
            # Make API request
            response = urllib.request.urlopen(url)
            data = json.loads(response.read())
            
            # Parse response
            return self._parse_lookup_response(data)
            
        except Exception as e:
            print(f"Error getting metadata from AcoustID: {e}")
            return None
    
    def _build_lookup_url(self, duration: float, fingerprint: str) -> str:
        """
        Build the AcoustID lookup URL.
        
        Args:
            duration: Audio duration in seconds
            fingerprint: Audio fingerprint
            
        Returns:
            Complete API URL
        """
        base_url = 'https://api.acoustid.org/v2/lookup'
        params = {
            'client': self.api_key,
            'meta': 'recordings+releasegroups+compress',
            'duration': str(int(duration)),
            'fingerprint': fingerprint
        }
        
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"
    
    def _parse_lookup_response(self, data: dict) -> Optional[Tuple[str, str]]:
        """
        Parse AcoustID lookup response to extract artist and title.
        
        Args:
            data: JSON response from AcoustID API
            
        Returns:
            Tuple of (artist, title) or None if not found
        """
        try:
            # Use acoustid library's parser
            results = list(acoustid.parse_lookup_result(data))
            
            for result in results:
                if result and len(result) >= 2 and None not in result[-2:]:
                    title = result[-2]
                    artist = result[-1]
                    
                    # Clean artist name (remove features, etc.)
                    if ';' in artist:
                        artist = artist.split(';')[0]
                    if ',' in artist:
                        artist = artist.split(',')[0]
                    
                    artist = artist.strip()
                    title = title.strip()
                    
                    if artist and title:
                        return (artist, title)
            
        except Exception as e:
            print(f"Error parsing AcoustID response: {e}")
        
        return None
    
    def is_configured(self) -> bool:
        """
        Check if the API is properly configured.
        
        Returns:
            True if API key is set
        """
        return bool(self.api_key and self.api_key.strip())