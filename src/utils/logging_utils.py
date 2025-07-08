"""
Centralized logging utilities for SMF Player.
Provides consistent logging across the application with configurable output.
"""

import logging
import sys
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logging(
    level: int = logging.INFO,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_to_file: bool = False,
    log_file_path: str = "smf_player.log"
) -> None:
    """
    Set up centralized logging for the application.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        format_string: Format string for log messages
        log_to_file: Whether to log to a file in addition to console
        log_file_path: Path to the log file if log_to_file is True
    """
    global _logger
    
    # Create logger
    _logger = logging.getLogger("SMFPlayer")
    _logger.setLevel(level)
    
    # Clear any existing handlers
    _logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        try:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            _logger.addHandler(file_handler)
        except Exception as e:
            _logger.error(f"Failed to create file handler for {log_file_path}: {e}")


def get_logger(name: str = "SMFPlayer") -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Name for the logger (will be appended to main logger name)
        
    Returns:
        Logger instance
    """
    global _logger
    
    if _logger is None:
        setup_logging()
    
    if name == "SMFPlayer":
        return _logger
    else:
        return _logger.getChild(name)


def log_error(message: str, exception: Optional[Exception] = None, logger_name: str = "SMFPlayer") -> None:
    """
    Convenience function to log errors.
    
    Args:
        message: Error message
        exception: Optional exception object
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    if exception:
        logger.error(f"{message}: {exception}")
    else:
        logger.error(message)


def log_warning(message: str, logger_name: str = "SMFPlayer") -> None:
    """
    Convenience function to log warnings.
    
    Args:
        message: Warning message
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    logger.warning(message)


def log_info(message: str, logger_name: str = "SMFPlayer") -> None:
    """
    Convenience function to log info messages.
    
    Args:
        message: Info message
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    logger.info(message)


def log_debug(message: str, logger_name: str = "SMFPlayer") -> None:
    """
    Convenience function to log debug messages.
    
    Args:
        message: Debug message
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    logger.debug(message)


def wx_error_handler(message: str, exception: Optional[Exception] = None) -> None:
    """
    Error handler that works with wx applications.
    Logs the error and optionally shows a wx.MessageBox if wx is available.
    
    Args:
        message: Error message
        exception: Optional exception object
    """
    log_error(message, exception, "UI")
    
    # Try to show wx error dialog if wx is available
    try:
        import wx
        if wx.GetApp() is not None:
            error_msg = f"{message}"
            if exception:
                error_msg += f": {exception}"
            wx.LogError(error_msg)
    except ImportError:
        # wx not available, just log
        pass