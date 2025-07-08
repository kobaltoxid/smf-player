"""
AcoustID API integration for SMF Player.
Handles audio fingerprinting and metadata lookup using AcoustID service.
"""

import acoustid
from acoustid import fingerprint_file
from typing import Optional, Tuple

from .api_base import APIBase
from ..utils.logging_utils import log_error, log_warning


class AcoustIDAPI(APIBase):
    """Handles AcoustID API interactions for audio fingerprinting."""
    
    def __init__(self, api_key: str):
        """
        Initialize AcoustID API client.
        
        Args:
            api_key: AcoustID API key
        """
        super().__init__(api_key)
    
    def get_metadata_from_file(self, file_path: str) -> Optional[Tuple[str, str]]:
        """
        Get song metadata (artist, title) from audio file using fingerprinting.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of (artist, title) or None if not found
        """
        if not self.is_configured():
            log_warning("AcoustID API key not configured", self.__class__.__name__)
            return None
        
        try:
            # Generate fingerprint
            fingerprint_data = fingerprint_file(file_path, force_fpcalc=True)
            if not fingerprint_data or len(fingerprint_data) < 2:
                log_warning(f"Could not generate fingerprint for {file_path}", self.__class__.__name__)
                return None
            
            duration = fingerprint_data[0]
            fingerprint = str(fingerprint_data[1])
            
            # Clean fingerprint string
            if fingerprint.startswith("b'") and fingerprint.endswith("'"):
                fingerprint = fingerprint[2:-1]
            
            # Build API URL
            url = self._build_lookup_url(duration, fingerprint)
            
            # Make API request
            data = self._make_get_request(url)
            if data is None:
                return None
            
            # Parse response
            return self._parse_lookup_response(data)
            
        except Exception as e:
            log_error(f"Error getting metadata from AcoustID", e, self.__class__.__name__)
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
        
        return self._build_url(base_url, params)
    
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
            log_error(f"Error parsing AcoustID response", e, self.__class__.__name__)
        
        return None
    
    def is_configured(self) -> bool:
        """
        Check if the API is properly configured.
        
        Returns:
            True if API key is set
        """
        return self._is_api_key_valid()