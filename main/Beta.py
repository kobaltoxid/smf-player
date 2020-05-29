#!/usr/bin/env python3

import wx
import wx.media
import os
import sys
import time
import sqlite3
import spotipy
import os
from pygame import mixer
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen import File as MutaFile
from spotipy.oauth2 import SpotifyClientCredentials


# Export or SET (for win32) the needed variables for the Spotify Web API
os.environ['SPOTIPY_CLIENT_ID'] = 'set-client-id-here'
os.environ['SPOTIPY_CLIENT_SECRET'] = 'set0client-secret-here'
os.environ['SPOTIPY_REDIRECT_URI'] = 'set-redirect-uri-here'

# Make database to store files that are currently being played.


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
        print("Unable to establish connection to database...\n")

    return conn


def insert_into_current(conn, data_field):
    sql = ''' INSERT or REPLACE INTO playlist(title, duration, artist)
              VALUES(?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (data_field[0], data_field[1], data_field[2]))


# Currently loaded songs.
currentpl = 'playing.db'


class Scope(wx.Frame):
    def __init__(self, parent, id):

        no_resize = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER |
                                                wx.MAXIMIZE_BOX)
        super().__init__(
            None, title="Scope", style=no_resize, size=(600, 800), pos=(0, 0))

        self.SetBackgroundColour("White")
        self.panel = wx.Panel(self, size=(500, 200))
        self.panel.SetBackgroundColour("Black")

        # Panel for playlist listbox and filter options.
        self.plbox = wx.Panel(self, size=(500, 600))
        self.playlist = wx.ListBox(self.plbox, size=(500,450), pos=(50,50))
        self.plbox.SetBackgroundColour("Red")

        self.createMenu()
        self.createLayout()
        self.Buttons()

        self.Center()
    
    # Menubar settings.
    def createMenu(self):
        menubar = wx.MenuBar()
        filemenu = wx.Menu()
        open = wx.MenuItem(filemenu, wx.ID_OPEN, '&Open')
        exit = wx.MenuItem(filemenu, wx.ID_CLOSE, '&Exit')
        add = wx.MenuItem(filemenu, wx.ID_OPEN, '&Add to playlist')
        filemenu.Append(open)
        filemenu.Append(add)
        filemenu.Append(exit)
        menubar.Append(filemenu, '&File')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.menuhandler)

    # Sets the layout
    def createLayout(self):
        try:
            self.Player = wx.media.MediaCtrl(self, style=wx.SIMPLE_BORDER)
        except NotImplementedError:
            self.Destroy()
            raise

        self.PlayerSlider = wx.Slider(self.panel, size=wx.DefaultSize,)
        self.PlayerSlider.Bind(wx.EVT_SLIDER, self.OnSeek)

        # Sizer for different panels.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.panel, flag=wx.EXPAND | wx.ALL)
        sizer.Add(self.plbox, flag=wx.EXPAND | wx.ALL)
        self.SetSizer(sizer)

    # Function to handle menubar options.
    def menuhandler(self, event):
        id = event.GetId()
        ev = event.GetString()
        if id == wx.ID_OPEN:
            with wx.FileDialog(self.panel, "Open Music file", wildcard="Music files (*.mp3,*.wav,*.aac,*.ogg,*.flac)|*.mp3;*.wav;*.aac;*.ogg;*.flac",
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file:

                if file.ShowModal() == wx.ID_CANCEL:
                    return

                self.pathname = file.GetPath()
                try:
                    # TODO Allow the loading of the file
                    self.loadfile(self.pathname)
                    self.getMutagenTags(self.pathname)
                   # self.playlistd(self.pathname)
                except IOError:
                    wx.LogError("Cannot open file '%s'." % self.pathname)

        if id == wx.ID_CLOSE:
            self.Close()

        """ if ev == "Add to playlist":
            # TODO add option to add pathnames to listbox.
            with wx.FileDialog(self.panel, "Open Image file", wildcard="Music files (*.mp3,*.wav,*.aac,*.ogg,*.flac)|*.mp3;*.wav;*.aac;*.ogg;*.flac",
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file:

                if file.ShowModal() == wx.ID_CANCEL:
                    return

                self.pathnameforpl = file.GetPath()
                try:
                    # TODO Allow the loading of the file
                    self.playlistd(self.pathnameforpl)

                except IOError:
                    wx.LogError("Cannot open file '%s'." % self.pathnameforpl) """

    def loadfile(self, filePath):
        # TODO implement file load
        if not self.Player.Load(filePath):
            wx.MessageBox("Unable to load; File format is not supported.", "ERROR", wx.ICON_ERROR | wx.OK)
        else:
            self.PlayerSlider.SetRange(0, self.Player.Length())

    def Buttons(self):
        picPlayBtn = wx.Bitmap("play-button.png", wx.BITMAP_TYPE_ANY)
        self.ButtonPlay = wx.BitmapToggleButton(self.panel, label=picPlayBtn, pos=(100,100))
        self.ButtonPlay.SetInitialSize()
        self.ButtonPlay.Bind(wx.EVT_TOGGLEBUTTON, self.OnPlay)

    def playlistd(self, path):
        # TODO Implement playlist adding to playing now.
        self.curr_pl = create_connection(currentpl)
        self.curr_pl.execute('''CREATE TABLE IF NOT EXISTS playlist
        (title VARCHAR(255) UNIQUE,
        duration VARCHAR(255),
        artist VARCHAR(255))''')

        self.curr_pl.commit()
        song_data = []
        song_data = self.getMutagenTags(path)
        insert_into_current(self.curr_pl, song_data)

    def getMutagenTags(self, path):
        audio = ID3(path)
        song = MutaFile(path)
        print(int(song.info.length))
        
        """ print(audio['TPE1'].text[0])
        print(audio["TIT2"].text[0]) 
        print(audio["TDRC"].text[0]) """

        self.makeCover(audio['TIT2'].text[0])
        data = []

        # Insert song data in list for inserting in database of currently playing songs.
        data.append(audio["TIT2"].text[0])
        song = MP3(path)
        d = int(song.info.length)
        minutes = d // 60
        seconds = d % 60
        duration = str(minutes) + ":" + str(seconds)
        data.append(duration)
        data.append(audio['TPE1'].text[0])

        return data

    # TODO make possible to put id3 data in database.

    def makeCover(self, track_name):

        spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials())

        # Gets album art cover by track name.
        result = spotify.search(q=track_name, limit=20)
        for track in result['tracks']['items']:
            print(track['album']['images'][0]['url'])
            break

    def OnPause(self):
        self.Player.Pause()        
    
    def OnPlay(self, event):
        if not event.GetEventObject().GetValue():
            self.OnPause()
            return

        if not self.Player.Play():
            self.ButtonPlay.SetValue(False)
            wx.MessageBox("A file must be selected.", "ERROR", wx.ICON_ERROR | wx.OK)
        
        else:
            self.PlayerSlider.SetRange(0, self.Player.Length())

    def OnSeek(self, event):
        self.Player.Seek(self.PlayerSlider.GetValue())


app = wx.App()
frame = Scope(None, -1)
frame.Show()
app.MainLoop()
