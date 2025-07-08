"""
Base class for API clients in SMF Player.
Provides common functionality for HTTP requests and JSON parsing.
"""

import urllib.request
import urllib.parse
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from ..utils.logging_utils import get_logger, log_error


class APIBase(ABC):
    """Base class for API clients with common HTTP request functionality."""
    
    def __init__(self, api_key: str):
        """
        Initialize the API client.
        
        Args:
            api_key: API key for authentication
        """
        self.api_key = api_key
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the API is properly configured.
        
        Returns:
            True if API is configured and ready to use
        """
        pass
    
    def _make_get_request(self, url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Make a GET request and parse JSON response.
        
        Args:
            url: URL to request
            timeout: Request timeout in seconds
            
        Returns:
            Parsed JSON response or None if request failed
        """
        try:
            self.logger.debug(f"Making GET request to: {url}")
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'SMF Player/1.0')
            
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = json.load(response)
                self.logger.debug(f"Request successful, received {len(str(data))} bytes")
                return data
                
        except urllib.error.HTTPError as e:
            log_error(f"HTTP error {e.code} when requesting {url}", e, self.__class__.__name__)
            return None
        except urllib.error.URLError as e:
            log_error(f"URL error when requesting {url}", e, self.__class__.__name__)
            return None
        except json.JSONDecodeError as e:
            log_error(f"JSON decode error for response from {url}", e, self.__class__.__name__)
            return None
        except Exception as e:
            log_error(f"Unexpected error when requesting {url}", e, self.__class__.__name__)
            return None
    
    def _build_url(self, base_url: str, params: Dict[str, str]) -> str:
        """
        Build a URL with query parameters.
        
        Args:
            base_url: Base URL
            params: Dictionary of query parameters
            
        Returns:
            Complete URL with encoded parameters
        """
        query_string = urllib.parse.urlencode(params)
        return f"{base_url}?{query_string}"
    
    def _is_api_key_valid(self) -> bool:
        """
        Check if the API key is valid (not empty or placeholder).
        
        Returns:
            True if API key appears valid
        """
        if not self.api_key or not self.api_key.strip():
            return False
        
        # Check for common placeholder values
        placeholder_values = [
            'your-api-key-here',
            'set-api-key-here',
            'api-key',
            'key',
            'placeholder'
        ]
        
        return self.api_key.lower() not in placeholder_values