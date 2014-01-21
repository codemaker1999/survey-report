from time import time
import sqlite3
defaultpath = 'survey.db'

class SQLdb:
    'Helper class for SQL'
    def __init__(self, fn=defaultpath):
        'Open a survey db'
        # Connect to SQLITE3 db
        self.fn  = fn
        self.con = sqlite3.connect(fn)
        self.cur = self.con.cursor()

    def add_table(self,name,cols):
        'Add a table to the DB'
        # Unsavoury use of SQL!
        self.cur.execute('CREATE TABLE IF NOT EXISTS %s'%' '.join([name,cols]))

    def reconnect(self):
        'Close the connection and open it again'
        'Note: reconnect may be required when dropping tables'
        self.cur.close()
        self.con.close()
        self.con = sqlite3.connect(self.fn)
        self.cur = self.con.cursor()

    def close(self):
        'Close the db'
        self.cur.close()
        self.con.close()

def test():
    sql = SQLdb()
    # make table
    sql.cur.execute('CREATE TABLE IF NOT EXISTS survs (id,dept,data)')
    from string import ascii_uppercase
    from random import choice, randint
    idchars = [x for x in ascii_uppercase]+[`i` for i in xrange(10)]
    for i in xrange(20):
        _id  = ''.join([choice(idchars) for j in xrange(8)])
        dept = 'department '+`i`
        data = `{n:randint(0,4) for n in xrange(112)}`
        sql.cur.execute('INSERT INTO survs VALUES (?,?,?)',(_id,dept,data))
    sql.con.commit()
    sql.close()

if __name__ == '__main__':
    #test()
    pass
