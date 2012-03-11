# -*- coding: utf-8 -*-
#!/usr/bin/python -d
 
from PyQt4 import QtCore, QtGui
from testIG import Ui_ProjetGherkin
import sys

#local lib : loading db
from load_db import *

#configuration constant
import config

#time for progress bar
import time

#client lib for calling server
import xmlrpclib

def give_time(u):
    if u % 60 < 10:
        return str(u // 60) + " : " + "0" + str(u % 60)
    else:
        return str(u // 60) + " : " + str(u % 60)


class MyForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_ProjetGherkin()
        self.ui.setupUi(self)
                
        #connection with the server
        self.server = xmlrpclib.ServerProxy("http://" + config.serverName + ":" + str(config.defaultPort))
        

        self.point = -1
        self.playlist = []
        #sync with the server at the beginning
        self.sync_server()

        #saving artists and songs displayed
        #getting the lib from the xml file
        if config.serverName == "localhost":
            (self.artists, self.albums, self.songs) = get_lib()
	
        #display artists and albums at launch, if server is playing, display current infos
        self.date_display_name = -1
        if self.playlist != []:
            self.update_artists()
            if self.pointeur != -1:
                self.display_name()
                if self.server.is_playing():
                    self.runSong()
        else:
            self.display_all()

        self.update_tracks()

        #signal received, functions called
        QtCore.QObject.connect(self.ui.PlayButton, QtCore.SIGNAL("clicked()"), self.call_play_pause )
        QtCore.QObject.connect(self.ui.AudioTrack, QtCore.SIGNAL("itemActivated(QTreeWidgetItem*,int)"), self.call_change )
        QtCore.QObject.connect(self.ui.Artist, QtCore.SIGNAL("itemClicked(QTreeWidgetItem*,int)"), self.call_albums )
        QtCore.QObject.connect(self.ui.Artist, QtCore.SIGNAL("itemActivated(QTreeWidgetItem*,int)"), self.call_play_albums )
        QtCore.QObject.connect(self.ui.Album, QtCore.SIGNAL("itemClicked(QTreeWidgetItem*,int)"), self.call_tracks )
        QtCore.QObject.connect(self.ui.Album, QtCore.SIGNAL("itemActivated(QTreeWidgetItem*,int)"), self.call_play_tracks)
        QtCore.QObject.connect(self.ui.NextButton, QtCore.SIGNAL("clicked()"), self.call_next)
        QtCore.QObject.connect(self.ui.PreviousButton, QtCore.SIGNAL("clicked()"), self.call_prev)
        QtCore.QObject.connect(self.ui.RandomButton, QtCore.SIGNAL("clicked()"), self.call_random)
        QtCore.QObject.connect(self.ui.RepeatButton,QtCore.SIGNAL("clicked()"), self.call_repeat)
    	QtCore.QObject.connect(self.ui.PlaylistButton,QtCore.SIGNAL("clicked()"), self.call_playlist)
        QtCore.QObject.connect(self.ui.LookingFor, QtCore.SIGNAL("textEdited(QString)"), self.call_search)
#        QtCore.QObject.connect(self.ui.verticalSlider, QtCore.SIGNAL("valueChanged(int)"), self.call_volume )	

#-------------------------------------------------------------------
#-------------------------------------------------------------------
#Sincing with server
#-------------------------------------------------------------------
#-------------------------------------------------------------------

    def sync_server(self):
        """Sincing common variables with the server"""
        self.deselect()
        self.pointeur = self.server.get_point()
        self.playlist = self.server.get_playlist()
        if self.server.is_playing():
            self.position = self.server.get_position()
            self.duration = self.server.get_duration()
        self.date_sync = time.time()

    def apply_changes(self):
        """Called after every action that changes the song played (next, prev, change)"""
        try:
            self.song_play.terminate()
        except:
            pass
        self.server.play_pause()
        self.sync_server()
        self.select()
        self.runSong()
        self.display_name()

#-------------------------------------------------------------------
#-------------------------------------------------------------------
#Interface with signals (clicks)
#-------------------------------------------------------------------
#-------------------------------------------------------------------

    def call_play_pause(self):
        self.server.play_pause()
        self.server.sync_server()

        #do not forget to work with the other thread
     	if self.server.is_playing():
            self.runSong()
        else:
            self.song_play.terminate()

        #displaying the changes
        self.iconChange()
        self.ui.AudioTrack.topLevelItem(self.pointeur).setSelected(True)

    def call_change(self, QtWidget, val = 0):
        """When a song is doubleclicked on in the playlist"""
        #we have the id of the song clicked on
        idSong = int(QtWidget.text(4))
        self.pointeur = 0
        #looking for the selected track in the playlist
        while self.playlist[self.pointeur] != idSong:
            self.pointeur += 1
        
        self.deselect()
        self.server.change(self.pointeur)
        self.apply_changes()

    def call_next(self):
        """The function return True if it has found a new song to play, False either""" 
        self.deselect()
        self.server.next()
        self.apply_changes()
        self.select()

        #perhaps it would be better to update all tracks shown..
        if self.server.get_mode() != config.normal:
            self.ui.addTrack(self.songs[self.playlist[self.pointeur]])
        
        self.select()

    def call_prev(self):
        """When previous button clicked on, convention : go to the end if at the first"""
        self.deselect()
        self.server.prev()
        self.apply_changes()
        self.select()

    def call_play_albums(self, QtWidget):
        self.deselect()
        self.call_albums(QtWidget)
        self.server.load()
        self.apply_changes()
        self.select()

    def call_play_tracks(self, QtWidget):
        self.deselect()
        self.call_tracks(QtWidget)
        self.server.load()
        self.apply_changes()
        self.select()
   
    def call_random(self):
        self.server.random()
        self.sync_server()
        self.update_tracks()
        if self.server.get_mode() == config.random:
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap((config.randomOnIcon)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.RandomButton.setIcon(icon2)
            self.ui.RandomButton.setIconSize(QtCore.QSize(30,30))
        else:
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap((config.randomOffIcon)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.RandomButton.setIcon(icon2)
            self.ui.RandomButton.setIconSize(QtCore.QSize(30,30))
        self.update_tracks()

    def call_playlist(self):
        if self.mode == playlist:
       	    self.mode = normal
            self.markovienne.save_Markov()

	    #updating ui
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap((config.playlistOffIcon)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.PlaylistButton.setIcon(icon2)
            self.ui.PlaylistButton.setIconSize(QtCore.QSize(30,30))
    	else:
            if self.mode == random:
                self.call_random()
            
            self.mode = playlist
            #removing last elements from the playlist for it to be ready for next
            self.playlist = self.playlist[0:self.pointeur+1]
	    
            #save the data of the markovienne into the file 
    	    self.markovienne.save_Markov()

	    #updating ui
            self.update_tracks()
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap((config.playlistOnIcon)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.PlaylistButton.setIcon(icon2)
            self.ui.PlaylistButton.setIconSize(QtCore.QSize(30,30))
  
    def call_repeat(self):
        if self.repeat:
            self.repeat = False
            
            #updating ui
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap((config.repeatOffIcon)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.RepeatButton.setIcon(icon2)
            self.ui.RepeatButton.setIconSize(QtCore.QSize(30,30))
        else:
            self.repeat = True

            #updating ui
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap((config.repeatOnIcon)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.RepeatButton.setIcon(icon2)
            self.ui.RepeatButton.setIconSize(QtCore.QSize(30,30))

    def call_volume(self, int):
        self.server.set_volume(int * 10 / (self.ui.verticalSlider.maximum()-self.ui.verticalSlider.minimum()))

#-------------------------------------------------------------------
#-------------------------------------------------------------------
#UI methods
#-------------------------------------------------------------------
#-------------------------------------------------------------------

#----------------------------
#modifying constants
#----------------------------

    def set_playlist(self, playlist):
        """update playlist of ui and server"""
        self.server.set_playlist(playlist)
        self.playlist = playlist

    def set_pointeur(self, pointeur):
        """update pointeur of ui and server"""
        self.server.set_point(pointeur)
        self.pointeur = pointeur

#----------------------------
#only display methods
#----------------------------

    def deselect(self):
        """DEselect element in the tree"""
        if self.point != -1:
            self.ui.AudioTrack.topLevelItem(self.pointeur).setSelected(False)
   
    def select(self):
        """select element in the tree"""    
        if self.point != -1:
            self.ui.AudioTrack.topLevelItem(self.pointeur).setSelected(True)
 
    def display_name(self):
        """display name of song currently playing"""
        if self.date_display_name < self.date_sync:
            try:
                self.ui.LookingForNoTouch.setText(self.songs[self.playlist[self.pointeur]]["title"]+" - "+ self.songs[self.playlist[self.pointeur]]['artist'])
            except:
                self.ui.LookingForNoTouch.setText("Unknown")
            self.date_display_name = time.time()

    def display_all(self):
        """display all albums and artists and set pointeur at the beginning"""
        #cleaning the lists
        self.ui.Artist.clear()
        self.ui.Album.clear()
        self.ui.AudioTrack.clear()
        
        #sorting the artists and albums by name for it to be smarter, and display
        artists = self.artists.keys()
        artists.sort()
        self.selectedSongs = set()
        for artist in artists:
            self.ui.addArtist(artist)
            albums = list(self.artists[artist])
            albums.sort()
            for album in albums:
                self.ui.addAlbum(album)
                for idTrack in self.albums[album]:
                    self.selectedSongs.add(idTrack)
        
        #then create a playlist from this set
        self.set_playlist(make_neighbors(self.songs, self.selectedSongs))
        self.set_pointeur(0)
        
        #and update the ui then
        self.update_albums()
 
    def update_artists(self):
        """display element in the playlist"""
        #removing elements from the artist tree
        self.ui.Artist.clear()
        self.ui.Album.clear()
        self.ui.AudioTrack.clear()
        
        #add them in the ordre of the playlist => alphabetical order for artists
        self.displayedArtists = set()
        self.displayedAlbums = set()
        for idTrack in self.playlist:
            #one should be added if not yet displayed
            if self.songs[idTrack]["artist"] not in self.displayedArtists:
                self.displayedArtists.add(self.songs[idTrack]["artist"])
                self.ui.addArtist(self.songs[idTrack]["artist"])
            if self.songs[idTrack]["album"] not in self.displayedAlbums:
                self.displayedAlbums.add(self.songs[idTrack]["album"])
                self.ui.addAlbum(self.songs[idTrack]["album"])
            self.ui.addTrack(self.songs[idTrack])

    def update_albums(self):
        """display elements of the playlist"""
        self.ui.Album.clear()
        self.ui.AudioTrack.clear()
        
        #add them in the order of the playlist, that is to say, alphabetical order for albums
        self.displayedAlbums = set()
        for idTrack in self.playlist:
            #adding an album if he hasn't already been displayed
            if self.songs[idTrack]["album"] not in self.displayedAlbums:
                self.displayedAlbums.add(self.songs[idTrack]["album"])
                self.ui.addAlbum(self.songs[idTrack]["album"])
            self.ui.addTrack(self.songs[idTrack])

    def update_tracks(self):
        """display elements of the playlist"""
        #removing elements from the album tree
        self.ui.AudioTrack.clear()

        for idTrack in self.playlist:
		self.ui.addTrack(self.songs[idTrack])
   
    def call_albums(self, QtWidget):
        """When an artist is clicked on..."""
        self.selectedArtist = str(QtWidget.text(0))
        self.selectedSongs = set()
        
        #adding all the songs to the set
        for album in self.artists[self.selectedArtist]:
            for idTrack in self.albums[album]:
                self.selectedSongs.add(idTrack)
        
        #then create a playlist from this set
        self.set_playlist(make_neighbors(self.songs, self.selectedSongs))
        self.set_pointeur(0)
        
        #and update the ui then
        self.update_albums()
  
    def call_tracks(self, QtWidget):
        """When an album is doubleclicked on"""
        self.selectedAlbum = str(QtWidget.text(0))
        self.selectedSongs = self.albums[self.selectedAlbum] 
        
        #making the playlist from the set of songs
        self.set_playlist(make_neighbors(self.songs, self.selectedSongs))
        self.set_pointeur(0)
    
        self.update_tracks()
   
    def iconChange(self):
        u = self.server.is_playing()
        if u:
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap((config.pauseIcon)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.ui.PlayButton.setIcon(icon2)
            self.ui.PlayButton.setIconSize(QtCore.QSize(30, 30))
    	else:
            icon2 = QtGui.QIcon()
            icon2.addPixmap(QtGui.QPixmap((config.playIcon)), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    	    self.ui.PlayButton.setIcon(icon2)
            self.ui.PlayButton.setIconSize(QtCore.QSize(30, 30))
  
    def runSong(self):
        try:    
            self.song_play.terminate()
        except:
            pass

        self.sync_server()
        self.display_name()
        self.song_play = Song()
        self.ui.SongBar.setMaximum(self.duration)
        self.ui.SongBar.setMinimum(0)
        self.connect(self.song_play, QtCore.SIGNAL("progressUpdated"), self.updateSongProgress)
        self.song_play.start()
    
    def updateSongProgress(self):
        #we sync to server only at the end and the begining
        if self.position > self.duration - config.anticipate:
            #sync before the end or at the beginning
            self.sync_server()
            self.ui.SongBar.setMaximum(self.duration)
            self.display_name()

        try:
            self.position += config.dt 
            self.ui.SongBar.setValue(round(self.position, 0))
            self.ui.SongBar.setFormat(give_time(self.position) + " / " + give_time(self.duration))
        except:
            pass
        
        self.ui.SongBar.repaint()

    def call_search(self, QString):
        self.selectSongs = set()
        for artist in self.artists:
            for album in self.artists[artist]:
                for idTrack in self.albums[album]:
                    try:
                        b=self.songs[idTrack]['title'].__contains__(str(QString)) or  self.songs[idTrack]['album'].__contains__(str(QString)) or self.songs[idTrack]['artist'].__contains__(str(QString))
                        if b:
                            self.selectSongs.add(idTrack)
                    except:
                        pass
        #then create a playlist from this set
        self.set_playlist(make_neighbors(self.songs, self.selectSongs))
        self.set_pointeur(0)
        
        #and update the ui then
        self.update_artists()

class Song(QtCore.QThread):
    __pyqtSignals__ = ("progressUpdated")
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.min = 0
        self.max = 100000
    def run(self):
        for self.progress in range(self.min, self.max):
            self.emit(QtCore.SIGNAL("progressUpdated"))
            time.sleep(config.dt)  
     
        

app = QtGui.QApplication(sys.argv)
myapp = MyForm()
myapp.show()
sys.exit(app.exec_())
