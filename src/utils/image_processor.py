"""
Image processing utilities for SMF Player.
Handles image manipulation and conversion between PIL and wx formats.
"""

import wx
from PIL import Image
from io import BytesIO
from typing import Optional


class ImageProcessor:
    """Handles image processing operations for the music player."""
    
    @staticmethod
    def scale_bitmap(bitmap: wx.Bitmap, width: int = 25, height: int = 30) -> wx.Bitmap:
        """
        Scale a wx.Bitmap to specified dimensions.
        
        Args:
            bitmap: The bitmap to scale
            width: Target width
            height: Target height
            
        Returns:
            Scaled bitmap
        """
        image = bitmap.ConvertToImage()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image)
    
    @staticmethod
    def pil_to_wx_image(pil_image: Image.Image) -> wx.Image:
        """
        Convert a PIL Image to wx.Image.
        
        Args:
            pil_image: PIL Image object
            
        Returns:
            wx.Image object
        """
        wx_image = wx.Image(pil_image.size[0], pil_image.size[1])
        
        # Convert to RGB and set data
        rgb_data = pil_image.convert('RGB').tobytes()
        wx_image.SetData(rgb_data)
        
        # Handle alpha channel if present
        if pil_image.mode in ('RGBA', 'LA') or 'transparency' in pil_image.info:
            if pil_image.mode != 'RGBA':
                pil_image = pil_image.convert('RGBA')
            alpha_data = pil_image.tobytes()[3::4]
            wx_image.SetAlphaData(alpha_data)
        
        return wx_image
    
    @staticmethod
    def pil_to_wx_bitmap(pil_image: Image.Image) -> wx.Bitmap:
        """
        Convert a PIL Image to wx.Bitmap.
        
        Args:
            pil_image: PIL Image object
            
        Returns:
            wx.Bitmap object
        """
        wx_image = ImageProcessor.pil_to_wx_image(pil_image)
        return wx.Bitmap(wx_image)
    
    @staticmethod
    def bytes_to_pil_image(image_bytes: bytes) -> Optional[Image.Image]:
        """
        Convert bytes data to PIL Image.
        
        Args:
            image_bytes: Image data as bytes
            
        Returns:
            PIL Image object or None if conversion fails
        """
        try:
            return Image.open(BytesIO(image_bytes))
        except Exception as e:
            print(f"Error converting bytes to PIL image: {e}")
            return None
    
    @staticmethod
    def resize_image_to_fit(image: Image.Image, max_width: int, max_height: int) -> Image.Image:
        """
        Resize an image to fit within specified dimensions while maintaining aspect ratio.
        
        Args:
            image: PIL Image to resize
            max_width: Maximum width
            max_height: Maximum height
            
        Returns:
            Resized PIL Image
        """
        # Calculate the aspect ratio
        aspect_ratio = image.width / image.height
        
        # Calculate new dimensions
        if aspect_ratio > 1:  # Wider than tall
            new_width = min(max_width, image.width)
            new_height = int(new_width / aspect_ratio)
        else:  # Taller than wide or square
            new_height = min(max_height, image.height)
            new_width = int(new_height * aspect_ratio)
        
        # Ensure we don't exceed maximum dimensions
        if new_width > max_width:
            new_width = max_width
            new_height = int(new_width / aspect_ratio)
        if new_height > max_height:
            new_height = max_height
            new_width = int(new_height * aspect_ratio)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def create_thumbnail(image: Image.Image, size: tuple = (500, 500)) -> Image.Image:
        """
        Create a thumbnail of an image.
        
        Args:
            image: PIL Image to create thumbnail from
            size: Thumbnail size as (width, height)
            
        Returns:
            Thumbnail PIL Image
        """
        thumbnail = image.copy()
        thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
        return thumbnail
    
    @staticmethod
    def display_image_on_static_bitmap(static_bitmap: wx.StaticBitmap, 
                                     pil_image: Optional[Image.Image],
                                     max_size: tuple = (500, 500)):
        """
        Display a PIL Image on a wx.StaticBitmap control.
        
        Args:
            static_bitmap: wx.StaticBitmap control to display image on
            pil_image: PIL Image to display (None for blank)
            max_size: Maximum size for the image
        """
        if pil_image is None:
            # Set blank bitmap
            blank_image = wx.Image(max_size[0], max_size[1])
            static_bitmap.SetBitmap(wx.Bitmap(blank_image))
            return
        
        try:
            # Resize image to fit
            resized_image = ImageProcessor.resize_image_to_fit(
                pil_image, max_size[0], max_size[1]
            )
            
            # Convert to wx.Bitmap and display
            wx_bitmap = ImageProcessor.pil_to_wx_bitmap(resized_image)
            static_bitmap.SetBitmap(wx_bitmap)
            
        except Exception as e:
            print(f"Error displaying image: {e}")
            # Fall back to blank image
            blank_image = wx.Image(max_size[0], max_size[1])
            static_bitmap.SetBitmap(wx.Bitmap(blank_image))
    
    @staticmethod
    def create_blank_bitmap(width: int, height: int) -> wx.Bitmap:
        """
        Create a blank bitmap of specified dimensions.
        
        Args:
            width: Bitmap width
            height: Bitmap height
            
        Returns:
            Blank wx.Bitmap
        """
        blank_image = wx.Image(width, height)
        return wx.Bitmap(blank_image)