#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

#standards libraries
#audio
import gst

#os
import os

#Qt
from PyQt4 import QtCore, QtGui

#http server
from SimpleXMLRPCServer import SimpleXMLRPCServer

#config file
import config

class audio_server:
    def __init__(self):
        self.playing = False
        self.player = gst.element_factory_make("playbin2", "player")
        fakesink = gst.element_factory_make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
    
    def load(self, path):
        print path
        if os.path.isfile(path):
            self.player.set_property("uri", "file://" + path)
        else:
            print "bad file path"

    def load_bis(self, u, integer):
        print u.child(0).text(0)
        self.load(u.child(0).text(0))

    def play_pause(self, Qt = 0, integer =0):
        if not self.playing:
            self.player.set_state(gst.STATE_PLAYING)
            self.playing = True
        else:
            self.player.set_state(gst.STATE_PAUSED)
            self.playing = False
    
    def stop(self, Qt = 0, integer =0):
        self.player.set_state(gst.STATE_NULL)

    def get_duration(self):
        return self.player.QUERY_DURATION

    def get_position(self):
        return self.player.QUERY_POSITION
    
    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
        elif t == gst.MESSAGE_ERROR:
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug

# Create server
server = SimpleXMLRPCServer(("localhost", config.defaultPort), allow_none=True)
server.register_introspection_functions()
server.register_instance(audio_server())

# Run the server's main loop
server.serve_forever()