import sys
import time

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QFile, QIODevice
from PyQt4.QtGui import qApp
from PyQt4.phonon import Phonon

from MainWindowAuto import Ui_MainWindow
from Debug import debug

class MainWindow(QtGui.QMainWindow):
    def __init__(self, peer, stream_adapter, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.searchBtn.clicked.connect(self.search)
        self.ui.playBtn.clicked.connect(self.play)
        self.ui.stopBtn.clicked.connect(self.stop)
        self.ui.pauseBtn.clicked.connect(self.pause)
        
        self.__peer = peer
        self.__recv_contr = None
        self.__stream_adapter = stream_adapter
        self.__hashes = []
        self.__pid = ''
        
        self.__audio_output = Phonon.AudioOutput(Phonon.MusicCategory, self)
        self.__media_object = Phonon.MediaObject(self)
         
        self.__media_object.setTickInterval(1000)
        self.__media_object.stateChanged.connect(self.state_changed)
        self.__media_object.tick.connect(self.tick)
        
        self.ui.seekSlider.setMediaObject(self.__media_object)
        self.ui.volumeSlider.setAudioOutput(self.__audio_output)
        
        Phonon.createPath(self.__media_object, self.__audio_output)
        
    def tick(self, time):
        displayTime = QtCore.QTime(0, (time / 60000) % 60, (time / 1000) % 60)
        self.ui.timeLbl.setText(displayTime.toString('mm:ss'))
        
    def state_changed(self, newState, oldState):
        self.ui.pauseBtn.setEnabled(False)
        self.ui.playBtn.setEnabled(False)
        self.ui.stopBtn.setEnabled(False)
        
        if newState == Phonon.PlayingState:
            self.ui.pauseBtn.setEnabled(True)
            self.ui.stopBtn.setEnabled(True)
        elif newState == Phonon.StoppedState:
            self.ui.playBtn.setEnabled(True)
            self.ui.timeLbl.setText("00:00")
        elif newState == Phonon.PausedState:
            self.ui.playBtn.setEnabled(True)
            self.ui.stopBtn.setEnabled(True)

        
    def search(self):
        search_text = self.ui.searchEdit.text()
        self.ui.trackList.setCurrentIndex(self.ui.trackList.rootIndex())
        self.__peer.lookup(search_text)
        self.ui.playBtn.setEnabled(True)

    def play(self):
        self.__media_object.play()
        curr = self.ui.trackList.selectedItems()[0]
        ind = self.ui.trackList.row(curr)
        self.__peer.start_stream(self.__pid, self.__hashes[ind])
        
    def stop(self):
        self.__media_object.stop()
        
    def pause(self):
        self.__media_object.pause()

    def streamCreated(self, size):
        self.__media_object.setCurrentSource(Phonon.MediaSource(self.__stream_adapter))
        self.__media_object.play()
        debug('MainWindow.streamCreated(): strea_adapter.read(10) = %s' % self.__stream_adapter.read(10))

    def musicFound(self, pid, music_list):
        self.ui.trackList.clear()
        self.__hashes = [res['hash'] for res in music_list]
        self.__pid = str(pid)
        for result in music_list:
            self.ui.trackList.addItem('%s - %s (%s)' % (result['artist'], result['title'], result['album']))

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow(None)
    main_window.show()
    sys.exit(app.exec_())
