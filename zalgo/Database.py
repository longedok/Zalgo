import os
import sqlite3
import time

from PyQt4.QtCore import QThread
from PyQt4.QtGui import qApp

from Debug import debug

class Database(QThread):
    __instance = None
    __first = True
    __request_queue = []

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(Database, cls).__new__(cls, *args, **kwargs)
        else:
            cls.__first = False
        return cls.__instance
        
    def __init__(self):
        if self.__first:
            super(Database, self).__init__()
            self.start()
            self.__first = False
            self.__fields = ['artist', 'title', 'album', 'hash', 'id', 'path']

    def __create_db(self):
        debug('Database: init started')
        self.__db_file = 'media_db'
        self.__db_conn = None
        if not os.path.exists(self.__db_file):
            self.__db_conn = sqlite3.connect(self.__db_file)
            cursor = self.__db_conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS music 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 title TEXT, 
                 artist TEXT, 
                 album TEXT, 
                 path TEXT, 
                 hash TEXT)''')
            self.__db_conn.commit()
            debug('Database.__init__(): table "music" has been created')
            cursor.close()
        else:
            self.__db_conn = sqlite3.connect(self.__db_file)
        debug('Database: init complete')
        
    def run(self):
        self.__create_db()
        while 1:
            queue_len = len(self.__request_queue)
            for _ in xrange(queue_len):
                (sql, values, callback) = self.__request_queue.pop()
                cursor = self.__db_conn.cursor()
                cursor.execute(sql, tuple(values))
                if callback:
                    callback(list(cursor))
                self.__db_conn.commit()
                cursor.close()
            time.sleep(0.1)

    def __unzip(self, list): 
        return ([v[0] for v in list], [v[1] for v in list])

    def lookup(self, callback, *fields, **values):
        '''callback  callback with logic for db answer processing.
           fields    list of fields that should be passed into callback as result.
           values    dict. key - name of table field, value - tuple
                     of comparasion sign and value of corresponding field.
           
           Forms sql requst, creates tuple of (sql_request, values, callback) and put 
           it into request processing queue.
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
        debug('Database.lookup(): sql %s' % sql)
        self.__request_queue.append((sql, values, callback))

    def store(self, fields, values):
        if len(fields) != len(values):
            debug('Database.store(): len(fields) != len(values) so request cannot be made')
            return
        for field in fields:
            if not field in self.__fields:
                debug('Database.store(): wrong fields in INSERT request')
                return
        sql = "INSERT INTO music (" + ', '.join(fields) + ") VALUES (" + ', '.join(['?'] * len(values)) + ')'
        self.__request_queue.append((sql, values, None))

if __name__ == '__main__':
    def test(x):
        pass
    db = Database()
    db.lookup(test, 'title', 'hash', album=('LIKE', 'Starlight'), artist=('=', 'Muse'))
