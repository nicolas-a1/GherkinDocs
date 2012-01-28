#!/usr/bin/python -d
 
from PyQt4 import QtCore, QtGui
from testIG import Ui_ProjetGherkin
import sys
#local lib : loading db
from load_db import *

#configuration constant
import config

#config file
import time
import random

#client lib for calling server
import xmlrpclib


class MyForm(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_ProjetGherkin()
        self.ui.setupUi(self)
        self.pointeur = 0
        self.random =False
        self.repeat = False 
    #getting in touch with server
        self.server = xmlrpclib.ServerProxy("http://localhost:" + str(config.defaultPort))

    #just to show what commands are available

    #print self.server.system.listMethods()

        self.songs = get_lib()

        for u in self.songs:
            self.ui.addTrack(u)
	    self.ui.addAlbum(u)
	    self.ui.addArtist(u)
# l'except est present pour les fichiers n'ayant pas de titre.

    #loading song into the server
        self.server.load(self.songs[self.pointeur]['location'])
        
    
        QtCore.QObject.connect(self.ui.PlayButton, QtCore.SIGNAL("clicked()"), self.call_play_pause )
        QtCore.QObject.connect(self.ui.AudioTrack, QtCore.SIGNAL("itemDoubleClicked(QTreeWidgetItem*,int)"), self.call_load )
        QtCore.QObject.connect(self.ui.NextButton, QtCore.SIGNAL("clicked()"), self.call_next)
        QtCore.QObject.connect(self.ui.PreviousButton, QtCore.SIGNAL("clicked()"), self.call_prev)
        QtCore.QObject.connect(self.ui.RandomButton, QtCore.SIGNAL("clicked()"), self.call_random)
        QtCore.QObject.connect(self.ui.RepeatButton,QtCore.SIGNAL("clicked()"), self.call_repeat)
#       QtCore.QObject.connect(self.server, QtCore.SIGNAL("Fin_de_lecture"), self.call_next)
	

    def add_entry(self):
        self.ui.lineEdit.selectAll()
        self.ui.lineEdit.cut()
        self.ui.textEdit.append("")
        self.ui.textEdit.paste()

    def call_play_pause(self):
        self.server.play_pause()
     	self.runSong()
        self.iconChange()

    def call_load(self, QtWidget, val = 0):
        self.server.stop()
        s = str(QtWidget.text(3))
        self.pointeur = int(QtWidget.text(4))
        self.server.load(s)
        self.server.play_pause()
    	self.iconChange()
        self.runSong()

    def call_next(self):
        self.server.stop()

        if self.random == False:
            self.pointeur+=1
            self.server.load(self.songs[self.pointeur]['location'])
            print self.songs[self.pointeur]['title']
        else:
# On est en mode random, donc on fait n'importe quoi.
            self.pointeur = random.randint(0, self.songs[-1]['id'])
            self.server.load(self.songs[self.pointeur]['location'])
            print self.songs[self.pointeur]['title']

        self.server.play_pause()
        self.iconChange()
        self.runSong()  


    def call_prev(self):
        self.server.stop()

        if not self.random:
            self.pointeur-=1
            self.server.load(self.songs[self.pointeur]['location'])
        else:
            self.pointeur = random.randint(0,self.songs[-1]['id'])
            self.server.load(self.songs[self.pointeur]['location'])

        self.server.play_pause()
        self.iconChange()
        self.runSong()

    def call_random(self):
        if self.random:
            self.random = False
        else:
            self.random = True
    
    def call_repeat(self):
        if self.repeat:
            self.repeat = False
        else:
            self.repeat = True

   

    def iconChange(self):
        u = self.server.is_playing()
#        print u
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
        self.song_play = Song()
        self.connect(self.song_play, QtCore.SIGNAL("progressUpdated"),
        self.updateSongProgress2)
        self.song_play.start()

    def updateSongProgress(self, min, max, progress):
        self.ui.SongBar.setMinimum(min)
        self.ui.SongBar.setMaximum(max)
        self.ui.SongBar.setValue(progress)
        self.ui.SongBar.repaint()

    def updateSongProgress2(self):
        self.setWindowTitle("Projet Gherkin : "+ self.songs[self.pointeur]['title'] )
        self.ui.SongBar.setMinimum(0)
        try:
            self.ui.SongBar.setMaximum(self.server.get_duration())
            self.ui.SongBar.setValue(self.server.get_position())
        except:
            pass
        self.ui.SongBar.repaint()
        try:
            if (self.server.get_position() == self.server.get_duration() and self.server.get_position() > 0):
                self.call_next()
                if self.repeat:
                    self.call_prev()
                if not self.server.is_playing():
                    self.server.play_pause()
                    self.iconChange()
                else:
                    self.iconChange()
            else:
                pass
        except:
            pass



class Song(QtCore.QThread):
    __pyqtSignals__ = ("progressUpdated")
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.min = 0
        self.max = 100000
        self.progress = 0
    def run(self):
	for self.progress in range(self.min, self.max):
            self.emit(QtCore.SIGNAL("progressUpdated"))
            time.sleep(0.2)  
     
        

app = QtGui.QApplication(sys.argv)
myapp = MyForm()
myapp.show()
sys.exit(app.exec_())