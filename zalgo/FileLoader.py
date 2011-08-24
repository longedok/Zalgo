import id3reader
import sha

from Debug import debug
from Database import Database

class FileLoader(object):
    def __init__(self, pathes = []):
        debug('FileLoader: init started')
        self.__pathes = pathes[:]
        self.__allowed_extensions = ['.mp3']
        self.__db = Database()
        debug('FileLoader: init complete')

    def index_files(self, pathes):
        for path in pathes:
            if not path in self.__pathes:
                self.__pathes.append(path)
        for dirname in self.__pathes:
            for root, _, files in os.walk(dirname):
                valid_files = [f for f in files if os.path.splitext(f)[1] in self.__allowed_extensions]
                for valid_file in valid_files:
                    full_path = os.path.join(root, valid_file)
                    sha_obj = sha.new()
                    fdata = self.load_file(full_path)
                    if fdata:
                        id3r = id3reader.Reader(full_path)
                        sha_obj.update(fdata)
                        hash = sha_obj.hexdigest()
                        id3r = id3reader.Reader(full_path)
                        title, album, artist = id3r.getValue('title'), id3r.getValue('album'), id3r.getValue('performer')
                        self.__db.store(['title', 'artist', 'album', 'path', 'hash'], 
                                [title, artist, album, full_path, hash])
                        del sha_obj
        self.__db_conn.commit()
        cursor.close()

    def load_file(self, name):
        try:
            fobject = open(name, 'rb')
            fraw_data = fobject.read()
        except IOError:
            return None
        return fraw_data

if __name__ == '__main__':
    t1 = FileLoader()
