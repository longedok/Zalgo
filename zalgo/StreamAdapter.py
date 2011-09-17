from PyQt4.QtCore import QIODevice
import pydevd

class StreamAdapter(QIODevice):
    def __init__(self):
        super(StreamAdapter, self).__init__()
        self.__buffer = ''
        self.__offset = 0
        
    def receive_data(self, data):
        self.__buffer += str(data)
        self.readyRead.emit()
        
    # Implementation of methods derived from QIODevice
    def size(self):
        return len(self.__buffer)

    def bytesAvailable(self):
        avail = len(self.__buffer) + QIODevice.bytesAvailable(self)
        avail -= self.__offset
        return max(avail, 0)

    def readAll(self):
        return QByteArray(self.__buffer)

    def readData(self, maxlen):
        print 'test'
        number = min(maxlen, len(self.__buffer) - self.__offset)
        data = "".join(self.__buffer[self.__offset:self.__offset + number])
        self.__offset += number
        return data

    def writeData(self, data):
        self.__buffer.insert(self.__offset, data)

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