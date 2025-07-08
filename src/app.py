"""
Main application entry point for SMF Player.
"""

import wx
import sys
import os

# Add the src directory to the Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_frame import MainFrame


class SMFPlayerApp(wx.App):
    """Main application class for SMF Player."""
    
    def OnInit(self):
        """Initialize the application."""
        try:
            # Create and show the main frame
            frame = MainFrame(None, -1)
            frame.Show()
            
            # Set as the top window
            self.SetTopWindow(frame)
            
            return True
            
        except Exception as e:
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