# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created: Sun Sep 04 21:59:38 2011
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
        MainWindow.resize(311, 309)
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 301, 261))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.searchEdit = QtGui.QLineEdit(self.verticalLayoutWidget)
        self.searchEdit.setObjectName(_fromUtf8("searchEdit"))
        self.horizontalLayout.addWidget(self.searchEdit)
        self.searchBtn = QtGui.QPushButton(self.verticalLayoutWidget)
        self.searchBtn.setText(QtGui.QApplication.translate("MainWindow", "Поиск", None, QtGui.QApplication.UnicodeUTF8))
        self.searchBtn.setObjectName(_fromUtf8("searchBtn"))
        self.horizontalLayout.addWidget(self.searchBtn)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.trackList = QtGui.QListWidget(self.verticalLayoutWidget)
        self.trackList.setObjectName(_fromUtf8("trackList"))
        self.verticalLayout_2.addWidget(self.trackList)
        self.playBtn = QtGui.QPushButton(self.verticalLayoutWidget)
        self.playBtn.setText(QtGui.QApplication.translate("MainWindow", "Проиграть", None, QtGui.QApplication.UnicodeUTF8))
        self.playBtn.setObjectName(_fromUtf8("playBtn"))
        self.verticalLayout_2.addWidget(self.playBtn)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 311, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.searchEdit, self.searchBtn)
        MainWindow.setTabOrder(self.searchBtn, self.playBtn)

    def retranslateUi(self, MainWindow):
        pass

