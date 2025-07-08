"""
Main application entry point for SMF Player.
"""

import wx
import sys
import os
import logging

# Add the src directory to the Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_frame import MainFrame
from src.utils.logging_utils import setup_logging, log_error, log_info


class SMFPlayerApp(wx.App):
    """Main application class for SMF Player."""
    
    def OnInit(self):
        """Initialize the application."""
        try:
            # Initialize logging system
            setup_logging(
                level=logging.INFO,
                log_to_file=True,
                log_file_path="smf_player.log"
            )
            
            log_info("Starting SMF Player application", "App")
            
            # Create and show the main frame
            frame = MainFrame(None, -1)
            frame.Show()
            
            # Set as the top window
            self.SetTopWindow(frame)
            
            log_info("SMF Player application initialized successfully", "App")
            return True
            
        except Exception as e:
            log_error("Failed to initialize SMF Player", e, "App")
            wx.MessageBox(
                f"Error starting SMF Player: {e}",
                "Startup Error",
                wx.OK | wx.ICON_ERROR
            )
            return False


def main():
    """Main entry point function."""
    # Create and run the application
    app = SMFPlayerApp()
    app.MainLoop()


if __name__ == '__main__':
    main()