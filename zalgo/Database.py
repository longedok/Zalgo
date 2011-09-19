import os
import sqlite3
import time
from threading import Lock

from Debug import debug

class Database(object):
    __instance = None
    __first = True

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(Database, cls).__new__(cls, *args, **kwargs)
        else:
            cls.__first = False
        return cls.__instance
        
    def __init__(self):
        if self.__first:
            self.__mutex = Lock()
            self.__first = False
            self.__fields = ['artist', 'title', 'album', 'hash', 'id', 'path', 'last_modified']
            self.__create_db()

    def __create_db(self):
        debug('Database: init started')
        self.__db_file = 'media_db'
        if not os.path.exists(self.__db_file):
            self.__db_conn = sqlite3.connect(self.__db_file, check_same_thread=False)
            cursor = self.__db_conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS music 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 title TEXT, 
                 artist TEXT, 
                 album TEXT, 
                 path TEXT, 
                 hash TEXT,
                 last_modified INT)''')
            self.__db_conn.commit()
            debug('Database.__init__(): table "music" has been created')
            cursor.close()
        else:
            self.__db_conn = sqlite3.connect(self.__db_file, check_same_thread=False)
        debug('Database: init complete')

    def __unzip(self, list): 
        return ([v[0] for v in list], [v[1] for v in list])

    def lookup(self, *fields, **values):
        '''fields    list of fields that should be passed into callback as result.
           values    dict. key - name of table field, value - tuple
                     of comparasion sign and value of corresponding field.
           
           Forms sql requst from parameters and performs it.
        '''
        for field in fields:
            if not field in self.__fields: # checks if field is exists in table
                debug('Database.lookup(): wrong field in SELECT request: %s' % field)
                return
        not_empty = dict(filter(lambda x: x[1][1] != '', values.items())) # remove empty values
        parameters = not_empty.keys()
        signs, values = self.__unzip(not_empty.values())
        sql = ("SELECT " + ', '.join(fields) + " FROM music WHERE " + 
                    ' AND '.join(["(%s %s ?)" % (f, v) for (f, v) in zip(parameters, signs)]))
        with self.__mutex:
            cursor = self.__db_conn.cursor()
            cursor.execute(sql, tuple(values))
            result = list(cursor)
            cursor.close()
        return result

    def store(self, fields, values):
        if len(fields) != len(values):
            debug('Database.store(): len(fields) != len(values) so request cannot be made')
            return
        for field in fields:
            if not field in self.__fields:
                debug('Database.store(): wrong fields in INSERT request')
                return
        sql = "INSERT INTO music (" + ', '.join(fields) + ") VALUES (" + ', '.join(['?'] * len(values)) + ')'
        with self.__mutex:
            cursor = self.__db_conn.cursor()
            cursor.execute(sql, tuple(values))
            self.__db_conn.commit()
            cursor.close()
        
if __name__ == '__main__':
    def test(x):
        pass
    db = Database()
    db.lookup(test, 'title', 'hash', album=('LIKE', 'Starlight'), artist=('=', 'Muse'))
