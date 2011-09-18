import time

from PyQt4.QtCore import QIODevice
from PyQt4.QtGui import qApp

from Debug import debug

import pydevd

class StreamAdapter(QIODevice):
    def __init__(self):
        super(StreamAdapter, self).__init__()
        self.__buffer = str()
        self.__offset = 0
        self.__size = 0
        
    def new_stream(self, size):
        self.__buffer = ''
        self.__offset = 0
        self.__size = size
        
    def receive_data(self, data):
        self.writeData(data)
        
    # Implementation of methods derived from QIODevice
    def size(self):
        print self.__size
        return self.__size

    def bytesAvailable(self):
        avail = len(self.__buffer) #+ QIODevice.bytesAvailable(self)
        avail -= self.__offset
        return max(avail, 0)

    def readAll(self):
        return QByteArray(self.__buffer)

    def readData(self, maxlen):
        while self.bytesAvailable() == 0:    
            qApp.processEvents()     
            time.sleep(0.1) 
        
        number = min(maxlen, len(self.__buffer) - self.__offset)    
        data = self.__buffer[self.__offset:self.__offset + number]
        self.__offset += number
        
        return data

    def writeData(self, data):
        self.__buffer += str(data)
        self.readyRead.emit()

    def seek(self, pos):
        if pos in xrange(len(self.__buffer) + 1):
            self.__offset = pos
            QIODevice.seek(self, pos)
            return True
        else:
            return False

    def isSequential(self):
        return False

    def pos(self):
        return self.__offset

if __name__ == '__main__':
    t = StreamAdapter()
    t.receive_data('Test test test test')
    t.receive_data('Cat cat cat')
    t.receive_data('Blah-blah-blah')
    print t.readData(10)
    print t.readData(10)