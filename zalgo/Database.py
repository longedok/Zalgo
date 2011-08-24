import sqlite3
import os

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
            debug('Database: init started')
            self.__fields = ['artist', 'title', 'album', 'hash', 'id', 'path']
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
            self.__first = False

    def __unzip(self, list): 
        return ([v[0] for v in list], [v[1] for v in list])

    def lookup(self, *fields, **request):
        for field in fields:
            if not field in self.__fields:
                debug('Database.store(): wrong fields in SELECT request')
                return
        valid_request = dict(filter(lambda x: x[1][1] != '', request.items())) # remove empty values
        rfields = valid_request.keys()
        compare_sings, values = self.__unzip(valid_request.values())
        sql = "SELECT " + ', '.join(fields) + " FROM music WHERE " + ' AND '.join(['(%s %s ?)' % (f, v) for (f, v) in zip(rfields, compare_sings)])
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
        cursor = self.__db_conn.cursor()
        cursor.execute(sql, tuple(values))
        self.__db_conn.commit()
        cursor.close()
