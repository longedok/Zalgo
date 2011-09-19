from random import randint

from PyQt4.QtCore import QObject, QFile, pyqtSignal, QIODevice

from Debug import debug

class ReceiveController(QObject):
    streamCreated = pyqtSignal(int)
    contentReceived = pyqtSignal('QByteArray')
    nextPacketRequests = pyqtSignal('QString', list, list)
    
    def __init__(self):
        super(ReceiveController, self).__init__()
        self.__file = None
        self.__pid2ready = dict()
        self.__current_sid = str()
        
    def recreate(self, stream_id, peer_id, size):
        peer_id = str(peer_id)
        stream_id = str(stream_id)
        
        if self.__current_sid == stream_id:
            self.add_peer(peer_id)
            return
        else:
            self.__current_sid = stream_id
        
        self.__last_packet = 0
        self.__last_peer = 0
        
        self.__inbox = list()
        
        if self.__file is not None:
            if self.__file.isOpen():
                self.__file.close()
                self.__file.remove()
        filename = 'files/%s.mp3' % ''.join([chr(randint(ord('a'), ord('z'))) for _ in xrange(10)])
        self.__file = QFile(filename)
        self.__file.open(QIODevice.ReadWrite)
        
        self.__pid2ready = {peer_id: True}
        
        self.__fisrt = True
        self.__data_consistent_to = 0
        self.__was_null = False
        self.__offset = 0
        
        pids, packet_nums = self.get_packet_requests()
        self.nextPacketRequests.emit(self.__current_sid, pids, packet_nums)
        self.streamCreated.emit(size)
    
    def get_peers(self):
        return self.__pid2ready.keys()
        
    def get_packet_requests(self):
        if len(self.__pid2ready.keys()) > 0:
            ready_pids = filter(lambda key: self.__pid2ready[key], self.__pid2ready.keys())
            for pid in ready_pids:
                self.__pid2ready[pid] = False  
                          
            last_pack = self.__last_packet
            self.__last_packet += 1
            
            return (ready_pids, range(last_pack, last_pack + len(ready_pids)))
        else:
            return None

    def add_peer(self, peer_id):
        self.__peers[str(peer_id)] = True

    def remove_peer(self, peer_id):
        if peer_id in self.__pid2ready.keys():
            del self.__pid2ready[peer_id]

    def __consistent_to(self):
        if not self.__was_null:
            return 0
        
        for i, _ in enumerate(self.__inbox[self.__data_consistent_to:-1]):
            if self.__inbox[i + 1][0] - self.__inbox[i][0] != 1:
                self.__data_consistent_to = i
                return i
            
        if len(self.__inbox) > 0:
            self.__data_consistent_to = self.__inbox[len(self.__inbox) - 1][0]
            
        return self.__data_consistent_to


    def receive_packet(self, _from, peer_id, data):
        peer_id, data = str(peer_id), str(data)
        debug('ReceiveController().receive_packet(): Binary from %s has been received' % peer_id)
        
        if _from == 0:
            self.__was_null = True
        self.__pid2ready[peer_id] = True
        
        i = 0
        while i < len(self.__inbox) and self.__inbox[i][0] < _from:
            i += 1
        self.__inbox.insert(i, (_from, data))
        
        if len(self.__inbox) > 0:
            self.__last_packet = self.__inbox[len(self.__inbox) - 1][0] + 1
            
        cons_to = self.__consistent_to()    
        if cons_to > -1:
            inbox = map(lambda x: x[1], self.__inbox)
            final_data = "".join(inbox[:cons_to])
            
            self.contentReceived.emit(final_data)
            
            pids, nums = self.get_packet_requests()
            self.nextPacketRequests.emit(self.__current_sid, pids, nums)
            
            self.__file.writeData(final_data)
            self.__file.flush()
            
            self.__inbox = self.__inbox[cons_to:]      