import id3reader
import sha
import os

from PyQt4.QtCore import QThread

from Debug import debug
from Database import Database

class partial(object):
    def __init__(*args, **kw):
        self = args[0]
        self.fn, self.args, self.kw = (args[1], args[2:], kw)

    def __call__(self, *args, **kw):
        if kw and self.kw:
            d = self.kw.copy()
            d.update(kw)
        else:
            d = kw or self.kw
        return self.fn(*(self.args + args), **d)

class FileLoader(QThread):
    def __init__(self, pathes = []):
        super(FileLoader, self).__init__()
        debug('FileLoader: init started')
        self.__pathes = pathes[:]
        self.__allowed_extensions = ['.mp3']
        self.__db = Database()
        self.start()
        debug('FileLoader: init complete')
        
    def run(self):
        debug('FileLoader.run(): indexing started')
        import pydevd   
        os.stat_float_times(int(0))
        for dirname in self.__pathes:
            for root, _, files in os.walk(dirname):
                valid_files = [f for f in files if os.path.splitext(f)[1] in self.__allowed_extensions]
                for valid_file in valid_files:
                    full_path = os.path.join(root, valid_file)
                    file_stat = os.stat(full_path) 
                     
                    result_list = self.__db.lookup('last_modified', path=('=', full_path))
                    last_modified = int(result_list[0][0]) if len(result_list) > 0 else None
                    if file_stat.st_mtime != last_modified:
                        last_modified = file_stat.st_mtime
                        sha_obj = sha.new()
                        try:
                            file = open(full_path, 'rb')
                            data = file.read(8192)
                            file.close()
                        except IOError, e:
                            debug("FileLoader.run(): Can't read file '%s'. %s" % (full_path, str(e)))
                        else:
                            id3r = id3reader.Reader(full_path)
                            sha_obj.update(data)
                            hash = sha_obj.hexdigest()
                            title, album, artist = id3r.getValue('title'), id3r.getValue('album'), id3r.getValue('performer')
                            self.__db.store(['title', 'artist', 'album', 'path', 'hash', 'last_modified'], 
                                            [title, artist, album, full_path, hash, last_modified])
                    
        debug('FileLoader.run(): indexing finished')

    def load_file(self, name):
        try:
            fobject = open(name, 'rb')
            fraw_data = fobject.read()
        except IOError:
            return None
        return fraw_data

if __name__ == '__main__':
    t1 = FileLoader()
