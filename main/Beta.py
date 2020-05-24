#!/usr/bin/env python3

import wx
import os
import sys
import time
import sqlite3
import spotipy
import os
from pygame import mixer
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from spotipy.oauth2 import SpotifyClientCredentials


#Export or SET (for win32) the needed variables for the Spotify Web API
os.environ['SPOTIPY_CLIENT_ID'] = 'set-client-id-here'
os.environ['SPOTIPY_CLIENT_SECRET'] = 'set0client-secret-here'
os.environ['SPOTIPY_REDIRECT_URI'] = 'set-redirect-uri-here'


class Scope(wx.Frame):
    def __init__(self, parent, id):

        no_resize = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER |
                                                wx.MAXIMIZE_BOX)

        super().__init__(
            None, title="Scope", style=no_resize, size=(1024, 1024), pos=(0, 0))
        self.SetBackgroundColour("White")
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour("Gray")

        

        menubar = wx.MenuBar()
        filemenu = wx.Menu()
        open = wx.MenuItem(filemenu, wx.ID_OPEN, '&Open')
        exit = wx.MenuItem(filemenu, wx.ID_CLOSE, '&Exit')
        filemenu.Append(open)
        filemenu.Append(exit)
        menubar.Append(filemenu, '&File')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.menuhandler)

        self.items = wx.BoxSizer(wx.HORIZONTAL)

    def menuhandler(self, event):
        id = event.GetId()
        if id == wx.ID_OPEN:
            with wx.FileDialog(self.panel, "Open Image file", wildcard="Music files (*.mp3,*.wav,*.aac,*.ogg,*.flac)|*.mp3;*.wav;*.aac;*.ogg;*.flac",
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as file:

                if file.ShowModal() == wx.ID_CANCEL:
                    return

                self.pathname = file.GetPath()
                try:
                    # TODO Allow the loading of the file

                    loadfile(self.pathname)

                except IOError:
                    wx.LogError("Cannot open file '%s'." % newfile)

        if id == wx.ID_CLOSE:
            self.Close()

    def loadfile(self, path):
        # TODO implement file load
        s = 4

    def playlistd(self, path):
        # TODO Implement playlist adding to playing now.
        s = 3

    def getMutagenTags(self, path):

        audio = ID3(path)

        print("Artist: %s" % audio['TPE1'].text[0])
        print("Track: %s" % audio["TIT2"].text[0])
        print("Release Year: %s" % audio["TDRC"].text[0])

        # TODO make possible to put id3 data in database.


app = wx.App()
frame = Scope(None, -1)
frame.Show()
app.MainLoop()
