from reportlab.platypus import BaseDocTemplate, Frame, FrameBreak, \
     PageTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch,mm
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
#
from sql import SQLdb
from qnGrouping import q2g,g2qs
from math import ceil,trunc
from utils import get_qns
from VBC import DeptVBC
from questionText import textdict
#
class DeptReport:
  def __init__(self,pdf_fp,db_fp,dept):
    # set up reportlab
    self.styles = getSampleStyleSheet()
    self.pstyle = self.styles['Normal']
    self.pstyle.alignment=1
    pdf_fp = pdf_fp.replace(',','__').replace('/','__')
    self.c = canvas.Canvas('pdf/'+pdf_fp,pagesize=letter)
    # connect to db
    self.dept = dept
    self.sql = SQLdb(db_fp)
    # begin
    self.createDoc()

  def nextpage(self):
    'add page number and change page'
    # page number
    page_num = self.c.getPageNumber()
    text = "Page #%s" % page_num
    self.c.setFont('Helvetica-Bold',14)
    self.c.drawCentredString(letter[0]/2.0, 20*mm, text)
    # draw line
    self.c.setStrokeColor(colors.black)
    self.c.line(inch,25*mm,letter[0]-inch,25*mm)
    # yield page
    self.c.showPage()

  def createDoc(self):
    # get relevant data from db
    cmd='SELECT data FROM surveys WHERE dept="' + str(self.dept) + '";'
    data = self.sql.cur.execute(cmd)
    qndicts = []
    for s in data.fetchall():
      dic = eval(s[0])
      qndicts.append( dic )
    if qndicts == []:
      print self.dept,'failed'
      return

    # add title page
    self.addTitlePage()
    # add each question group
    for g,qns in g2qs.iteritems():
      qanswers = {}
      for q in qns:
        anslist=[]
        for qd in qndicts:
          anslist.append( qd[q] )
        qanswers[q] = anslist
      # example: qnaswers == {23:[2,2,1,3,2,2,...,2], ...}
      self.addQnGroup(g,qanswers)
    self.sql.close()
    # create and save
    self.save()

  def addTitlePage(self):
    # logo
    im_w,im_h = 600,425
    w,h  =  im_w/4.0, im_h/4.0
    self.c.drawImage('generic-countylogo.png', letter[0]/2.0 - w/2.0, 8.5*inch, width=w, height=h)
    # text
    if self.dept.startswith('Property'):
      tempdept = 'Property Services'
    else: tempdept = self.dept
    titletext = 'County X<br/>Employee Evaluation<br/>%s Results'%tempdept
    #
    style = self.styles['Title']
    style.fontName = 'Times-Bold'
    p = Paragraph(titletext,style)
    p.wrapOn(self.c, letter[0]/2. , 4*inch)# you must call wrap before draw!!!
    p.drawOn(self.c, letter[0]/4. , letter[1]-4*inch)
    self.nextpage()

  def addQnGroup(self,title,qndict):
    ### Add main page
    # label
    self.c.setFont('Times-Bold',16)
    self.c.drawCentredString(letter[0]/2.0, letter[1]-2*inch, title)
    # data
    alldata=[0,0,0,0,0]
    for k,v in qndict.iteritems():
      for i in v: #v is list of answer indeces [2,2,2,3,1,1,...]
        if i >= 1:
          alldata[i-1] += 1
    # chart
    overall = DeptVBC(alldata,
                      (inch,inch),
                      (letter[0]-2*inch,2*letter[1]/3.0),
                      titletext="Overall Response")
    overall.drawOn(self.c, 0,0)
    self.nextpage()
    ### Add pages for questions
    keys = qndict.keys()
    keys.sort()
    numpages = trunc(ceil(len(qndict)/8.))
    for i in xrange(numpages):
      onepage = {}
      for j in xrange(8):
        if len(keys):
          key = keys.pop(0)
          onepage[key]=qndict[key]
      self.addQnPage(onepage)

  def addQnPage(self,qdict):
    # init
    keys = qdict.keys()
    keys.sort()
    # iterate
    for k,i in zip(keys,range(len(keys))):
      # topleft coords
      x = int(i>3)
      y = i%4
      # generate chart
      data = [0,0,0,0,0]
      for i in qdict[k]:
        if i >= 1:
          data[i-1]+=1
      # sizing
      spacex = (letter[0]-inch)/2.
      spacey = (letter[1]-2*inch)/4.
      wid= spacex - 0.5*inch
      hgt= spacey - 0.5*inch
      px = 0.5*inch + x*spacex
      py = 1.4*inch + (3-y)*spacey
      qchart = DeptVBC(data,(0,0),(wid,hgt))
      qchart.drawOn(self.c,px,py)
      # label
      text = `k`+'. '+textdict[k]
      p = Paragraph(text,self.pstyle)
      p.wrapOn(self.c, wid,hgt)
      p.drawOn(self.c, px , py+hgt-10)
    # page break
    self.nextpage()
  def save(self):
    self.c.save()
    print 'Done',self.dept

if __name__ == '__main__':
  depts = [ \
    "Operations",
    "Finance",
    "Library",
    "Museum",
    "Recreation",
    "Fire Department",
  ]
  database = 'generic-surveys.db'
  objs = []
  for d in depts:
    fn = ''.join(d.split(' '))
    objs.append( DeptReport('Deptartment_Report_For_%s.pdf'%fn,database,d) )
