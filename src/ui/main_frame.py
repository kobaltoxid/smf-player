"""
Main frame for SMF Player.
Refactored UI class that delegates business logic to specialized modules.
"""

import wx
import wx.media
import os
from functools import partial
from typing import Optional

from ..config import (
    WINDOW_SIZE, WINDOW_POSITION, ALBUM_ART_SIZE, BUTTON_SIZE,
    setup_spotify_environment, LASTFM_API_KEY, ACOUSTID_API_KEY,
    SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, DEFAULT_PLAYLIST_DB
)
from ..database.manager import DatabaseManager
from ..media.player import MediaPlayer
from ..playlist.manager import PlaylistManager
from ..api.acoustid_api import AcoustIDAPI
from ..api.lastfm_api import LastFMAPI
from ..api.spotify_api import SpotifyAPI
from ..utils.image_processor import ImageProcessor
from ..metadata.extractor import MetadataExtractor
from ..utils.logging_utils import log_info, log_error, log_warning
from .dialog_helpers import DialogHelpers


class MainFrame(wx.Frame):
    """Main application frame with modular architecture."""
    
    def __init__(self, parent, id):
        """Initialize the main frame."""
        # Window setup
        no_resize = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        super().__init__(
            None, title="SMF Player", style=no_resize, 
            size=WINDOW_SIZE, pos=WINDOW_POSITION
        )
        
        # Initialize core components
        self._initialize_components()
        
        # Set up UI
        self.SetBackgroundColour("Black")
        self._create_panels()
        self._create_layout()
        self._create_menu()
        self._create_buttons()
        self._setup_timer()
        
        # Bind events
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Center()
    
    def _initialize_components(self):
        """Initialize all core components and managers."""
        # Set up Spotify environment
        setup_spotify_environment()
        
        # Initialize database manager
        self.db_manager = DatabaseManager(DEFAULT_PLAYLIST_DB)
        
        # Initialize media player
        self.media_player = MediaPlayer(self)
        
        # Initialize playlist manager
        self.playlist_manager = PlaylistManager(self.db_manager)
        
        # Initialize API clients
        self.acoustid_api = AcoustIDAPI(ACOUSTID_API_KEY)
        self.lastfm_api = LastFMAPI(LASTFM_API_KEY)
        self.spotify_api = SpotifyAPI(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
        
        # Set API clients in playlist manager
        self.playlist_manager.set_api_clients(
            self.acoustid_api, self.lastfm_api, self.spotify_api
        )
        
        # UI state variables
        self.current_volume = 100
        self.count_add_to_playlist = 0
        self.current_song_index = -1
        self.repeat_mode = False
    
    def _create_panels(self):
        """Create all UI panels."""
        # Playback control panel
        self.playback_panel = wx.Panel(self, size=(700, 200))
        self.playback_panel.SetBackgroundColour("Black")
        
        # Album cover display panel
        self.display_panel = wx.Panel(self, size=(700, 600))
        self.display_panel.SetBackgroundColour("Black")
        self.album_art_display = wx.StaticBitmap(
            self.display_panel, size=ALBUM_ART_SIZE, pos=(100, 50)
        )
        
        # Playlist panel
        self.playlist_panel = wx.Panel(self, size=(600, 500))
        self.playlist_panel.SetBackgroundColour("SALMON")
        
        # Create playlist list control
        self.playlist_listctrl = wx.ListCtrl(
            self.playlist_panel, size=(550, 425), pos=(25, 10), 
            style=wx.LC_REPORT
        )
        self.playlist_listctrl.AppendColumn("Artist", width=170)
        self.playlist_listctrl.AppendColumn("Title", width=170)
        self.playlist_listctrl.AppendColumn("Duration", width=70)
        self.playlist_listctrl.AppendColumn("Counter", width=70)
        self.playlist_listctrl.AppendColumn("Rating", width=70)
        self.playlist_listctrl.SetBackgroundColour("Black")
        self.playlist_listctrl.SetTextColour("White")
        self.playlist_listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_playlist_item_selected)
        
        # Recommendations panel
        self.recommendations_panel = wx.Panel(self, size=(600, 300))
        self.recommendations_panel.SetBackgroundColour("SALMON")
        
        # Create recommendations list control
        self.recommendations_listctrl = wx.ListCtrl(
            self.recommendations_panel, size=(550, 220), pos=(25, 0),
            style=wx.LC_REPORT
        )
        self.recommendations_listctrl.AppendColumn("Artist", width=200)
        self.recommendations_listctrl.AppendColumn("Title", width=200)
        self.recommendations_listctrl.AppendColumn("Duration", width=150)
        self.recommendations_listctrl.SetBackgroundColour("Black")
        self.recommendations_listctrl.SetTextColour("White")
        self.recommendations_listctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self._on_recommendation_selected)
    
    def _create_layout(self):
        """Create the main layout using sizers."""
        # Create playback slider
        self.playback_slider = wx.Slider(
            self.playback_panel, style=wx.SL_HORIZONTAL, 
            size=(400, -1), pos=(150, 10)
        )
        self.playback_slider.Bind(wx.EVT_SLIDER, self._on_seek)
        
        # Create volume slider
        self.volume_slider = wx.Slider(
            self.playback_panel, style=wx.SL_HORIZONTAL,
            size=(100, -1), pos=(450, 40)
        )
        self.volume_slider.SetRange(0, 100)
        self.volume_slider.SetValue(100)
        self.volume_slider.Bind(wx.EVT_SLIDER, self._on_volume_change)
        
        # Create filter controls
        filter_choices = ['Artist', 'Title']
        self.filter_combo = wx.ComboBox(
            self.playlist_panel, choices=filter_choices, pos=(355, 450)
        )
        self.filter_text = wx.TextCtrl(
            self.playlist_panel, size=(100, 34), pos=(245, 450)
        )
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        right_sizer = wx.BoxSizer(wx.VERTICAL)
        
        left_sizer.Add(self.display_panel, flag=wx.EXPAND | wx.ALL)
        left_sizer.Add(self.playback_panel, flag=wx.EXPAND | wx.ALL)
        right_sizer.Add(self.playlist_panel, flag=wx.EXPAND | wx.ALL)
        right_sizer.Add(self.recommendations_panel, flag=wx.EXPAND | wx.ALL)
        
        main_sizer.Add(left_sizer)
        main_sizer.Add(right_sizer)
        self.SetSizer(main_sizer)
    
    def _create_menu(self):
        """Create the menu bar."""
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        help_menu = wx.Menu()
        
        # File menu items
        open_file = file_menu.Append(-1, '&Open')
        open_folder = file_menu.Append(-1, '&Open folder')
        add_to_playlist = file_menu.Append(-1, '&Add to playlist')
        open_playlist = file_menu.Append(-1, '&Open Playlist')
        save_playlist = file_menu.Append(-1, '&Save Playlist')
        exit_app = file_menu.Append(-1, '&Exit')
        
        # Help menu items
        about = help_menu.Append(-1, "&About")
        
        menubar.Append(file_menu, '&File')
        menubar.Append(help_menu, "&Help")
        self.SetMenuBar(menubar)
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, partial(self._on_menu_handler, 'open_folder'), open_folder)
        self.Bind(wx.EVT_MENU, partial(self._on_menu_handler, 'open_file'), open_file)
        self.Bind(wx.EVT_MENU, partial(self._on_menu_handler, 'add_to_playlist'), add_to_playlist)
        self.Bind(wx.EVT_MENU, partial(self._on_menu_handler, 'exit'), exit_app)
        self.Bind(wx.EVT_MENU, partial(self._on_menu_handler, 'save_playlist'), save_playlist)
        self.Bind(wx.EVT_MENU, partial(self._on_menu_handler, 'open_playlist'), open_playlist)
        self.Bind(wx.EVT_MENU, partial(self._on_menu_handler, 'about'), about)
    
    def _create_buttons(self):
        """Create playback and control buttons."""
        # Load button images
        try:
            play_btn_img = wx.Bitmap("src/resources/play-button.png", wx.BITMAP_TYPE_ANY)
            play_btn_img = ImageProcessor.scale_bitmap(play_btn_img, *BUTTON_SIZE)
            
            prev_btn_img = wx.Bitmap("src/resources/previous-song-button.png", wx.BITMAP_TYPE_ANY)
            prev_btn_img = ImageProcessor.scale_bitmap(prev_btn_img, *BUTTON_SIZE)
            
            next_btn_img = wx.Bitmap("src/resources/next-song-button.png", wx.BITMAP_TYPE_ANY)
            next_btn_img = ImageProcessor.scale_bitmap(next_btn_img, *BUTTON_SIZE)
            
            repeat_btn_img = wx.Bitmap("src/resources/repeat-button.png", wx.BITMAP_TYPE_ANY)
            repeat_btn_img = ImageProcessor.scale_bitmap(repeat_btn_img, *BUTTON_SIZE)
        except Exception as e:
            log_error("Failed to load button images", e, "MainFrame")
            # Create default buttons without images
            play_btn_img = None
            prev_btn_img = None
            next_btn_img = None
            repeat_btn_img = None
        
        # Create buttons
        if play_btn_img:
            self.play_button = wx.BitmapToggleButton(
                self.playback_panel, label=play_btn_img, pos=(325, 40)
            )
        else:
            self.play_button = wx.ToggleButton(
                self.playback_panel, label="Play", pos=(325, 40)
            )
        
        if prev_btn_img:
            self.prev_button = wx.BitmapButton(
                self.playback_panel, bitmap=prev_btn_img, pos=(260, 40)
            )
        else:
            self.prev_button = wx.Button(
                self.playback_panel, label="Prev", pos=(260, 40)
            )
        
        if next_btn_img:
            self.next_button = wx.BitmapButton(
                self.playback_panel, bitmap=next_btn_img, pos=(390, 40)
            )
        else:
            self.next_button = wx.Button(
                self.playback_panel, label="Next", pos=(390, 40)
            )
        
        if repeat_btn_img:
            self.repeat_button = wx.BitmapToggleButton(
                self.playback_panel, label=repeat_btn_img, pos=(195, 40)
            )
        else:
            self.repeat_button = wx.ToggleButton(
                self.playback_panel, label="Repeat", pos=(195, 40)
            )
        
        # Create filter button
        self.filter_button = wx.Button(
            self.playlist_panel, label="Filter", size=(100, 30), pos=(475, 453)
        )
        
        # Create rating radio box
        rating_choices = ['1', '2', '3', '4', '5']
        self.rating_radiobox = wx.RadioBox(
            self.playlist_panel, -1, "Rating", pos=(25, 440),
            size=(180, 45), choices=rating_choices, style=wx.RA_HORIZONTAL
        )
        self.rating_radiobox.SetForegroundColour((40, 40, 40))
        
        # Bind button events
        self.play_button.Bind(wx.EVT_TOGGLEBUTTON, self._on_play)
        self.prev_button.Bind(wx.EVT_BUTTON, self._on_previous)
        self.next_button.Bind(wx.EVT_BUTTON, self._on_next)
        self.repeat_button.Bind(wx.EVT_TOGGLEBUTTON, self._on_repeat)
        self.filter_button.Bind(wx.EVT_BUTTON, self._on_filter)
        self.rating_radiobox.Bind(wx.EVT_RADIOBOX, self._on_rating_change)
    
    def _setup_timer(self):
        """Set up the playback timer."""
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._on_timer)
        self.timer.Start(50)  # Update every 50ms
    
    # Event handlers
    def _on_close(self, event):
        """Handle window close event."""
        self.timer.Stop()
        self.db_manager.close()
        self.media_player.set_volume(1.0)
        self.media_player.cleanup()
        self.Destroy()
    
    def _on_menu_handler(self, action: str, event):
        """Handle menu item selections."""
        if action == 'open_folder':
            self._open_folder()
        elif action == 'open_file':
            self._open_file()
        elif action == 'add_to_playlist':
            self._add_to_playlist()
        elif action == 'save_playlist':
            self._save_playlist()
        elif action == 'open_playlist':
            self._open_playlist()
        elif action == 'exit':
            self.Close()
        elif action == 'about':
            self._show_about()
    
    def _open_folder(self):
        """Open a folder and load all music files."""
        folder_path = DialogHelpers.show_directory_dialog(
            self, "Open Music Dir"
        )
        if not folder_path:
            return
        
        log_info(f"Opening folder: {folder_path}", "MainFrame")
        
        # Clear current playlist
        self.playlist_manager.clear_playlist()
        self._clear_ui()
        
        # Load folder
        try:
            loaded_songs = self.playlist_manager.load_folder(folder_path)
            self._refresh_playlist_display()
            
            if loaded_songs:
                self._select_first_song()
                log_info(f"Loaded {len(loaded_songs)} songs from folder", "MainFrame")
                
        except Exception as e:
            log_error("Failed to load folder", e, "MainFrame")
            DialogHelpers.show_error_message(self, f"Error loading folder: {e}")
    
    def _open_file(self):
        """Open a single music file."""
        file_path = DialogHelpers.show_single_file_dialog(
            self, "Open Music file",
            "Music files (*.mp3,*.wav,*.aac,*.ogg,*.flac)|*.mp3;*.wav;*.aac;*.ogg;*.flac"
        )
        if not file_path:
            return
        
        log_info(f"Opening file: {file_path}", "MainFrame")
        
        # Clear current playlist
        self.playlist_manager.clear_playlist()
        self._clear_ui()
        
        # Load file
        try:
            song = self.playlist_manager.add_song_from_file(file_path)
            if song:
                self._refresh_playlist_display()
                self._select_first_song()
                self._load_song_at_index(0)
                log_info("File loaded successfully", "MainFrame")
                
        except Exception as e:
            log_error("Failed to open file", e, "MainFrame")
            DialogHelpers.show_error_message(self, f"Cannot open file '{file_path}': {e}")
    
    def _add_to_playlist(self):
        """Add files to the current playlist."""
        file_paths = DialogHelpers.show_multiple_file_dialog(
            self, "Add music file to playlist",
            "Music files (*.mp3,*.wav,*.aac,*.ogg,*.flac)|*.mp3;*.wav;*.aac;*.ogg;*.flac"
        )
        if not file_paths:
            return
        
        log_info(f"Adding {len(file_paths)} files to playlist", "MainFrame")
        
        try:
            loaded_songs = self.playlist_manager.load_files(file_paths)
            self._refresh_playlist_display()
            
            # If this is the first song(s) added, select the first one
            if self.playlist_manager.get_playlist_count() == len(loaded_songs):
                self._select_first_song()
                if self.count_add_to_playlist < 1:
                    self._load_song_at_index(0)
                    self.count_add_to_playlist += 1
            
            log_info(f"Added {len(loaded_songs)} songs to playlist", "MainFrame")
                    
        except Exception as e:
            log_error("Failed to add files to playlist", e, "MainFrame")
            DialogHelpers.show_error_message(self, f"Error adding files to playlist: {e}")
    
    def _save_playlist(self):
        """Save the current playlist."""
        if self.playlist_manager.get_playlist_count() < 1:
            DialogHelpers.show_warning_message(self, "No songs in playlist to save.")
            return
        
        save_path = DialogHelpers.show_save_dialog(
            self, "Save playlist", "Playlist file (*.db)|*.db"
        )
        if not save_path:
            return
        
        log_info(f"Saving playlist to: {save_path}", "MainFrame")
        
        try:
            success = self.playlist_manager.save_playlist(save_path)
            if success:
                log_info("Playlist saved successfully", "MainFrame")
                DialogHelpers.show_info_message(self, "Playlist saved successfully!")
            else:
                log_error("Failed to save playlist", None, "MainFrame")
                DialogHelpers.show_error_message(self, "Error saving playlist")
        except Exception as e:
            log_error("Failed to save playlist", e, "MainFrame")
            DialogHelpers.show_error_message(self, f"Error saving playlist: {e}")
    
    def _open_playlist(self):
        """Open a saved playlist."""
        playlist_path = DialogHelpers.show_single_file_dialog(
            self, "Open playlist file", "Playlist files (*.db)|*.db"
        )
        if not playlist_path:
            return
        
        log_info(f"Opening playlist: {playlist_path}", "MainFrame")
        
        # Clear current playlist
        self.playlist_manager.clear_playlist()
        self._clear_ui()
        self.count_add_to_playlist = 0
        
        try:
            loaded_songs = self.playlist_manager.load_playlist(playlist_path)
            self._refresh_playlist_display()
            
            if loaded_songs:
                self._select_first_song()
                self._load_song_at_index(0)
                self.count_add_to_playlist += 1
                log_info(f"Loaded {len(loaded_songs)} songs from playlist", "MainFrame")
            else:
                log_warning("No songs found in playlist file", "MainFrame")
                
        except Exception as e:
            log_error("Failed to open playlist", e, "MainFrame")
            DialogHelpers.show_error_message(self, f"Error opening playlist: {e}")
    
    def _show_about(self):
        """Show about dialog."""
        DialogHelpers.show_info_message(
            self,
            "SMF Player is free for use and covered by the GNU v3.0 license.",
            "SMF Player ver 0.2.0"
        )
    
    def _on_playlist_item_selected(self, event):
        """Handle playlist item selection."""
        row = event.GetEventObject().GetFocusedItem()
        self._load_song_at_index(row)
    
    def _on_recommendation_selected(self, event):
        """Handle recommendation item selection."""
        row = event.GetEventObject().GetFocusedItem()
        
        # Get recommendation data
        cols = self.recommendations_listctrl.GetColumnCount()
        data = []
        for col in range(cols - 1):
            item = self.recommendations_listctrl.GetItem(itemIdx=row, col=col)
            data.append(item.GetText())
        
        artist_name = data[0]
        song_title = data[1]
        
        # Find the recommendation in our stored data
        recommendations = self.playlist_manager.recommendations
        for rec_list in recommendations:
            for rec in rec_list:
                if rec['artist'] == artist_name and rec['title'] == song_title:
                    # Load and play the preview
                    if self.media_player.load_uri(rec['preview_url']):
                        self.media_player.play()
                        self.playback_slider.SetValue(0)
                        self.playback_slider.SetRange(0, 30000)  # 30 second preview
                        self.play_button.SetValue(True)
                    return
    
    def _on_play(self, event):
        """Handle play/pause button."""
        if not event.GetEventObject().GetValue():
            self.media_player.pause()
            return
        
        if not self.media_player.play():
            self.play_button.SetValue(False)
            DialogHelpers.show_error_message(self, "A file must be selected.")
        else:
            length = self.media_player.get_length()
            self.playback_slider.SetRange(0, length)
    
    def _on_previous(self, event):
        """Handle previous button."""
        if self.current_song_index > 0:
            new_index = self.current_song_index - 1
            self._select_song_at_index(new_index)
            self._load_song_at_index(new_index)
    
    def _on_next(self, event):
        """Handle next button."""
        playlist_count = self.playlist_manager.get_playlist_count()
        if self.current_song_index < playlist_count - 1:
            new_index = self.current_song_index + 1
            self._select_song_at_index(new_index)
            self._load_song_at_index(new_index)
    
    def _on_repeat(self, event):
        """Handle repeat button toggle."""
        self.repeat_mode = event.GetEventObject().GetValue()
    
    def _on_seek(self, event):
        """Handle playback slider seek."""
        position = self.playback_slider.GetValue()
        self.media_player.seek(position)
    
    def _on_volume_change(self, event):
        """Handle volume slider change."""
        self.current_volume = self.volume_slider.GetValue()
        self.media_player.set_volume(self.current_volume / 100.0)
    
    def _on_filter(self, event):
        """Handle filter button click."""
        filter_text = self.filter_text.GetValue()
        filter_selection = self.filter_combo.GetCurrentSelection()
        
        if filter_selection == -1:
            return
        
        filter_type = self.filter_combo.GetString(filter_selection)
        
        if filter_text:
            self.playlist_manager.filter_playlist(filter_type, filter_text)
            self._refresh_playlist_display()
            self._clear_playback()
    
    def _on_rating_change(self, event):
        """Handle rating change."""
        if self.current_song_index >= 0:
            rating = int(event.GetString())
            self.playlist_manager.update_song_rating(self.current_song_index, rating)
            
            # Update the display
            self.playlist_listctrl.SetItem(self.current_song_index, 4, str(rating))
    
    def _on_timer(self, event):
        """Handle timer events for playback progress."""
        if self.media_player.get_state() == 'playing':
            position = self.media_player.get_position()
            self.playback_slider.SetValue(position)
            
            # Check if song finished
            if self.media_player.is_at_end():
                if self.repeat_mode:
                    # Repeat current song
                    self._load_song_at_index(self.current_song_index)
                else:
                    # Move to next song
                    self._on_next(None)
    
    # UI Helper Methods
    def _clear_ui(self):
        """Clear all UI displays."""
        self._clear_playback()
        self._clear_playlist_display()
        self._clear_recommendations_display()
        self._clear_album_art()
    
    def _clear_playback(self):
        """Clear playback controls."""
        self.media_player.stop()
        self.playback_slider.SetValue(0)
        self.play_button.SetValue(False)
    
    def _clear_playlist_display(self):
        """Clear the playlist display."""
        self.playlist_listctrl.DeleteAllItems()
        self.current_song_index = -1
    
    def _clear_recommendations_display(self):
        """Clear the recommendations display."""
        self.recommendations_listctrl.DeleteAllItems()
    
    def _clear_album_art(self):
        """Clear the album art display."""
        ImageProcessor.display_image_on_static_bitmap(
            self.album_art_display, None, ALBUM_ART_SIZE
        )
    
    def _refresh_playlist_display(self):
        """Refresh the playlist display with current data."""
        self._clear_playlist_display()
        
        playlist = self.playlist_manager.get_playlist_copy()
        for i, song in enumerate(playlist):
            self.playlist_listctrl.InsertItem(i, song['artist'])
            self.playlist_listctrl.SetItem(i, 1, song['title'])
            self.playlist_listctrl.SetItem(i, 2, song['duration'])
            self.playlist_listctrl.SetItem(i, 3, str(song['times_played']))
            self.playlist_listctrl.SetItem(i, 4, str(song['rating']))
    
    def _select_first_song(self):
        """Select the first song in the playlist."""
        if self.playlist_manager.get_playlist_count() > 0:
            self._select_song_at_index(0)
    
    def _select_song_at_index(self, index: int):
        """Select a song at the given index."""
        if 0 <= index < self.playlist_manager.get_playlist_count():
            self.playlist_listctrl.SetItemState(
                index, wx.LIST_STATE_FOCUSED, wx.LIST_STATE_FOCUSED
            )
            self.playlist_listctrl.Select(index, on=1)
            self.current_song_index = index
    
    def _load_song_at_index(self, index: int):
        """Load and prepare a song at the given index."""
        song = self.playlist_manager.get_song_by_index(index)
        if not song:
            return
        
        self._clear_recommendations_display()
        
        # Check if file exists
        if not os.path.isfile(song['path']):
            # Try to find moved file
            new_path = self.playlist_manager.find_moved_file(song['path'])
            if new_path:
                self.playlist_manager.update_song_path(index, new_path)
                song['path'] = new_path
            else:
                log_warning(f"File missing: {song['path']}", "MainFrame")
                DialogHelpers.show_error_message(self, "The file is missing.")
                self.playlist_manager.remove_song(index)
                self._refresh_playlist_display()
                self._clear_playback()
                # Try to play next song
                self._on_next(None)
                return
        
        # Load the file
        if self.media_player.load_file(song['path']):
            self.playback_slider.SetRange(0, self.media_player.get_length())
            self.playback_slider.SetValue(0)
            self.media_player.play()
            self.play_button.SetValue(True)
            
            # Update times played
            new_count = self.playlist_manager.update_times_played(index)
            self.playlist_listctrl.SetItem(index, 3, str(new_count))
            
            # Get enhanced metadata if needed
            enhanced_song = self.playlist_manager.get_enhanced_metadata(song)
            
            # Load album art and recommendations
            self._load_album_art(enhanced_song)
            self._load_recommendations(enhanced_song, index)
    
    def _load_album_art(self, song: dict):
        """Load album art for a song."""
        # First try embedded album art
        embedded_art = MetadataExtractor.get_embedded_album_art(song['path'])
        if embedded_art:
            pil_image = ImageProcessor.bytes_to_pil_image(embedded_art)
            if pil_image:
                ImageProcessor.display_image_on_static_bitmap(
                    self.album_art_display, pil_image, ALBUM_ART_SIZE
                )
                return
        
        # Try LastFM if we have artist and title
        if song['artist'] and song['title'] and self.lastfm_api.is_configured():
            try:
                pil_image = self.lastfm_api.download_album_art(
                    song['artist'], song['title'], 'extralarge'
                )
                if pil_image:
                    ImageProcessor.display_image_on_static_bitmap(
                        self.album_art_display, pil_image, ALBUM_ART_SIZE
                    )
                    return
            except Exception as e:
                log_error("Failed to load album art from LastFM", e, "MainFrame")
        
        # Fall back to blank image
        self._clear_album_art()
    
    def _load_recommendations(self, song: dict, song_index: int):
        """Load recommendations for a song."""
        if not song['artist'] or not song['title']:
            return
        
        # Only get recommendations if song hasn't been played much
        times_played = self.playlist_manager.db_manager.get_times_played(song['path'])
        if times_played > 1:
            return
        
        try:
            recommendations = self.playlist_manager.get_recommendations(
                song['artist'], song['title']
            )
            self._display_recommendations(recommendations, song['artist'])
        except Exception as e:
            log_error("Failed to load recommendations", e, "MainFrame")
    
    def _display_recommendations(self, recommendations: list, artist_name: str):
        """Display recommendations in the recommendations list."""
        self._clear_recommendations_display()
        
        for i, rec in enumerate(recommendations):
            if rec.get('seed_artist_name') == artist_name:
                self.recommendations_listctrl.InsertItem(i, rec['artist'])
                self.recommendations_listctrl.SetItem(i, 1, rec['title'])
                self.recommendations_listctrl.SetItem(i, 2, '0:30')  # Preview duration