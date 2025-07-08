"""
Dialog helper utilities for SMF Player UI.
Provides common dialog functionality to reduce code duplication.
"""

import wx
from typing import Optional, List, Tuple

from ..utils.logging_utils import get_logger, log_error


class DialogHelpers:
    """Helper class for common UI dialogs."""
    
    @staticmethod
    def show_file_dialog(
        parent: wx.Window,
        title: str,
        wildcard: str,
        style: int = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        multiple: bool = False
    ) -> Optional[List[str]]:
        """
        Show a file dialog and return selected file paths.
        
        Args:
            parent: Parent window
            title: Dialog title
            wildcard: File type filter
            style: Dialog style flags
            multiple: Whether to allow multiple file selection
            
        Returns:
            List of selected file paths, or None if cancelled
        """
        logger = get_logger("DialogHelpers")
        
        try:
            if multiple:
                style |= wx.FD_MULTIPLE
            
            with wx.FileDialog(parent, title, wildcard=wildcard, style=style) as dialog:
                if dialog.ShowModal() == wx.ID_CANCEL:
                    return None
                
                if multiple:
                    return dialog.GetPaths()
                else:
                    return [dialog.GetPath()]
                    
        except Exception as e:
            log_error(f"Error showing file dialog", e, "DialogHelpers")
            return None
    
    @staticmethod
    def show_single_file_dialog(
        parent: wx.Window,
        title: str,
        wildcard: str,
        style: int = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    ) -> Optional[str]:
        """
        Show a file dialog for single file selection and return the file path.
        
        Args:
            parent: Parent window
            title: Dialog title
            wildcard: File type filter
            style: Dialog style flags
            
        Returns:
            Selected file path, or None if cancelled
        """
        result = DialogHelpers.show_file_dialog(parent, title, wildcard, style, multiple=False)
        return result[0] if result else None
    
    @staticmethod
    def show_multiple_file_dialog(
        parent: wx.Window,
        title: str,
        wildcard: str,
        style: int = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    ) -> Optional[List[str]]:
        """
        Show a file dialog for multiple file selection and return the file paths.
        
        Args:
            parent: Parent window
            title: Dialog title
            wildcard: File type filter
            style: Dialog style flags
            
        Returns:
            List of selected file paths, or None if cancelled
        """
        return DialogHelpers.show_file_dialog(parent, title, wildcard, style, multiple=True)
    
    @staticmethod
    def show_directory_dialog(
        parent: wx.Window,
        title: str,
        style: int = wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
    ) -> Optional[str]:
        """
        Show a directory dialog and return selected directory path.
        
        Args:
            parent: Parent window
            title: Dialog title
            style: Dialog style flags
            
        Returns:
            Selected directory path, or None if cancelled
        """
        return DialogHelpers.show_dir_dialog(parent, title, style)
    
    @staticmethod
    def show_dir_dialog(
        parent: wx.Window,
        title: str,
        style: int = wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST
    ) -> Optional[str]:
        """
        Show a directory dialog and return selected directory path.
        
        Args:
            parent: Parent window
            title: Dialog title
            style: Dialog style flags
            
        Returns:
            Selected directory path, or None if cancelled
        """
        logger = get_logger("DialogHelpers")
        
        try:
            with wx.DirDialog(parent, title, style=style) as dialog:
                if dialog.ShowModal() == wx.ID_CANCEL:
                    return None
                
                return dialog.GetPath()
                
        except Exception as e:
            log_error(f"Error showing directory dialog", e, "DialogHelpers")
            return None
    
    @staticmethod
    def show_save_dialog(
        parent: wx.Window,
        title: str,
        wildcard: str,
        default_filename: str = ""
    ) -> Optional[str]:
        """
        Show a save file dialog and return selected file path.
        
        Args:
            parent: Parent window
            title: Dialog title
            wildcard: File type filter
            default_filename: Default filename
            
        Returns:
            Selected file path, or None if cancelled
        """
        logger = get_logger("DialogHelpers")
        
        try:
            with wx.FileDialog(
                parent, 
                title, 
                wildcard=wildcard,
                defaultFile=default_filename,
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
            ) as dialog:
                if dialog.ShowModal() == wx.ID_CANCEL:
                    return None
                
                return dialog.GetPath()
                
        except Exception as e:
            log_error(f"Error showing save dialog", e, "DialogHelpers")
            return None
    
    @staticmethod
    def show_message_box(
        parent: wx.Window,
        message: str,
        title: str = "Information",
        style: int = wx.OK | wx.ICON_INFORMATION
    ) -> int:
        """
        Show a message box dialog.
        
        Args:
            parent: Parent window
            message: Message to display
            title: Dialog title
            style: Dialog style flags
            
        Returns:
            Dialog result (wx.ID_OK, wx.ID_CANCEL, etc.)
        """
        try:
            with wx.MessageDialog(parent, message, title, style) as dialog:
                return dialog.ShowModal()
                
        except Exception as e:
            log_error(f"Error showing message box", e, "DialogHelpers")
            return wx.ID_CANCEL
    
    @staticmethod
    def show_error_message(parent: wx.Window, message: str, title: str = "Error") -> None:
        """
        Show an error message dialog.
        
        Args:
            parent: Parent window
            message: Error message to display
            title: Dialog title
        """
        DialogHelpers.show_message_box(
            parent, message, title, wx.OK | wx.ICON_ERROR
        )
    
    @staticmethod
    def show_warning_message(parent: wx.Window, message: str, title: str = "Warning") -> None:
        """
        Show a warning message dialog.
        
        Args:
            parent: Parent window
            message: Warning message to display
            title: Dialog title
        """
        DialogHelpers.show_message_box(
            parent, message, title, wx.OK | wx.ICON_WARNING
        )
    
    @staticmethod
    def show_info_message(parent: wx.Window, message: str, title: str = "Information") -> None:
        """
        Show an information message dialog.
        
        Args:
            parent: Parent window
            message: Information message to display
            title: Dialog title
        """
        DialogHelpers.show_message_box(
            parent, message, title, wx.OK | wx.ICON_INFORMATION
        )