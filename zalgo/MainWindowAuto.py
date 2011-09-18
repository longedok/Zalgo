# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created: Sun Sep 18 18:26:57 2011
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(335, 315)
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setMaximumSize(QtCore.QSize(388, 396))
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(9, 6, 321, 281))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.gridLayout = QtGui.QGridLayout(self.widget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.searchEdit = QtGui.QLineEdit(self.widget)
        self.searchEdit.setObjectName(_fromUtf8("searchEdit"))
        self.gridLayout.addWidget(self.searchEdit, 0, 0, 1, 3)
        self.searchBtn = QtGui.QPushButton(self.widget)
        self.searchBtn.setText(QtGui.QApplication.translate("MainWindow", "Search", None, QtGui.QApplication.UnicodeUTF8))
        self.searchBtn.setObjectName(_fromUtf8("searchBtn"))
        self.gridLayout.addWidget(self.searchBtn, 0, 3, 1, 1)
        self.playBtn = QtGui.QPushButton(self.widget)
        self.playBtn.setText(QtGui.QApplication.translate("MainWindow", "Play", None, QtGui.QApplication.UnicodeUTF8))
        self.playBtn.setObjectName(_fromUtf8("playBtn"))
        self.gridLayout.addWidget(self.playBtn, 3, 0, 1, 1)
        self.pauseBtn = QtGui.QPushButton(self.widget)
        self.pauseBtn.setText(QtGui.QApplication.translate("MainWindow", "Pause", None, QtGui.QApplication.UnicodeUTF8))
        self.pauseBtn.setObjectName(_fromUtf8("pauseBtn"))
        self.gridLayout.addWidget(self.pauseBtn, 3, 1, 1, 1)
        self.stopBtn = QtGui.QPushButton(self.widget)
        self.stopBtn.setText(QtGui.QApplication.translate("MainWindow", "Stop", None, QtGui.QApplication.UnicodeUTF8))
        self.stopBtn.setObjectName(_fromUtf8("stopBtn"))
        self.gridLayout.addWidget(self.stopBtn, 3, 2, 1, 1)
        self.trackList = QtGui.QListWidget(self.widget)
        self.trackList.setObjectName(_fromUtf8("trackList"))
        self.gridLayout.addWidget(self.trackList, 4, 0, 1, 4)
        self.seekSlider = phonon.Phonon.SeekSlider(self.widget)
        self.seekSlider.setObjectName(_fromUtf8("seekSlider"))
        self.gridLayout.addWidget(self.seekSlider, 2, 0, 1, 3)
        self.volumeSlider = phonon.Phonon.VolumeSlider(self.widget)
        self.volumeSlider.setObjectName(_fromUtf8("volumeSlider"))
        self.gridLayout.addWidget(self.volumeSlider, 3, 3, 1, 1)
        self.timeLbl = QtGui.QLabel(self.widget)
        self.timeLbl.setText(QtGui.QApplication.translate("MainWindow", "00:00", None, QtGui.QApplication.UnicodeUTF8))
        self.timeLbl.setAlignment(QtCore.Qt.AlignCenter)
        self.timeLbl.setObjectName(_fromUtf8("timeLbl"))
        self.gridLayout.addWidget(self.timeLbl, 2, 3, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 335, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.searchEdit, self.searchBtn)
        MainWindow.setTabOrder(self.searchBtn, self.trackList)
        MainWindow.setTabOrder(self.trackList, self.playBtn)
        MainWindow.setTabOrder(self.playBtn, self.pauseBtn)
        MainWindow.setTabOrder(self.pauseBtn, self.stopBtn)

    def retranslateUi(self, MainWindow):
        pass

from PyQt4 import phonon
