import sys

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QVariant, Qt
from PyQt4.phonon import Phonon

from MainWindowAuto import Ui_MainWindow

class Track(object):
    def __init__(self,  titile=u'', artist=u'', album=u'', _hash=''):
        self.__hash = _hash
        self.__artist = artist
        self.__title = titile
        self.__album = album

    def get_hash(self):
        return self.__hash

    def get_artist(self):
        return self.__artist

    def get_title(self):
        return self.__title

    def get_album(self):
        return self.__album

    def set_hash(self, value):
        self.__hash = value

    def set_artist(self, value):
        self.__artist = value

    def set_title(self, value):
        self.__title = value

    def set_album(self, value):
        self.__album = value
        
    hash_ = property(get_hash, set_hash, None, None)
    artist = property(get_artist, set_artist, None, None)
    title = property(get_title, set_title, None, None)
    album = property(get_album, set_album, None, None)

class TrackModel(QtCore.QAbstractListModel):
    __track_list = list()
    
    def init(self, parent=None):
        super(TrackModel, self).__init__() 
        
    def setTrackList(self, tracks):
        self.__track_list = list(tracks)
        
    def rowCount(self, index):
        return len(self.__track_list)
    
    def data(self, index, role=Qt.DisplayRole):
        tr = self.__track_list[index.row()]
        if role == Qt.DisplayRole:   
            return QVariant("%s - %s (%s)" % (tr.artist, tr.title, tr.album))
        elif role == Qt.UserRole:
            return tr
            
class MainWindow(QtGui.QMainWindow):
    def __init__(self, peer, stream_adapter, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.__track_list = TrackModel()
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.trackListView.setModel(self.__track_list)
        self.ui.trackListView.doubleClicked.connect(self.list_double_clicked)
        self.ui.trackListView.clicked.connect(self.list_clicked)
        self.ui.searchBtn.clicked.connect(self.search)
        self.ui.playBtn.clicked.connect(self.play)
        self.ui.stopBtn.clicked.connect(self.stop)
        self.ui.pauseBtn.clicked.connect(self.pause)
        self.setWindowTitle('Zalgo')
          
        self.__peer = peer
        self.__recv_contr = None
        self.__stream_adapter = stream_adapter
        self.__hashes = []
        self.__pid = ''    
        self.__playing_now = None
        
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
        self.__peer.lookup(search_text)
        self.ui.playBtn.setEnabled(True)

    def play(self):
        if self.__media_object.state() != Phonon.PausedState:
            self.__playing_now = self.ui.trackListView.currentIndex()
            track = self.__track_list.data(self.__playing_now, Qt.UserRole)
            self.__peer.start_stream(self.__pid, track.hash_)
        self.__media_object.play()
        
    def stop(self):
        self.__media_object.stop()
        
    def pause(self):
        self.__media_object.pause()

    def streamCreated(self, size):
        self.__media_object.setCurrentSource(Phonon.MediaSource(self.__stream_adapter))
        self.__media_object.play()

    def musicFound(self, pid, music_list):
        self.__track_list.reset()
        self.__pid = str(pid)
        self.__track_list.setTrackList([Track(t['title'], t['artist'], t['album'], t['hash']) for t in music_list])
    
    def list_double_clicked(self, item):
        if self.__playing_now != self.ui.trackListView.currentIndex():
            self.__media_object.stop()
        self.play()
        
    def list_clicked(self, item):
        self.ui.playBtn.setEnabled(True)

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    main_window = MainWindow(None)
    main_window.show()
    sys.exit(app.exec_())
