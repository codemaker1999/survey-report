from sql import SQLdb

dbpath = 'generic-surveys.db'

def get_qn(n):
  'Return 5 item list of all answers to question n'
  sql = SQLdb(dbpath)
  data = sql.cur.execute('SELECT data FROM surveys')
  ans = [0,0,0,0,0]
  for row in data:
    qdict = eval( row[0] )
    qans = qdict[n]
    ans[qans-1] += 1
  sql.close()
  return ans

def get_qns(nlist,dept=None):
  'Return dict of { <qn num> : [<num of SA>, <num of A>, ...] }'
  sql = SQLdb(dbpath)
  if dept:
    cmd='SELECT data FROM surveys WHERE dept="'+str(dept)+'";'
  else:
    cmd = 'SELECT data FROM surveys'
  data = sql.cur.execute(cmd)
  # initialise
  d = {}
  for n in nlist:
    d[n] = [0,0,0,0,0]
  for row in data:
    qdict = eval( row[0] )
    for n in nlist:
      qans = qdict[n]
      d[n][qans-1] += 1
  sql.close()
  return d

if __name__ == '__main__':
  pass
  #a = get_qn(9)
  #d = get_qns([3,54,88])
