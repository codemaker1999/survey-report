import sys
from reportlab.platypus import BaseDocTemplate, Frame, FrameBreak, \
  PageTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch,mm
from reportlab.lib.colors import toColor
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
#
from sql import SQLdb
from qnGrouping import q2g,g2qs
from math import ceil,trunc
from utils import get_qns
from VBC import DeptVBC, ClusterVBC
from questionText import textdict


db = None
depts = [ \
  "Operations",
  "Finance",
  "Library",
  "Museum",
  "Recreation",
  "Fire Department",
]
landscape = [letter[1],letter[0]]


class AdminReport:

  def __init__(self,pdf_fp,db_fp):
    # set up reportlab
    self.c = canvas.Canvas('pdf/'+pdf_fp,pagesize=landscape)
    self.styles = getSampleStyleSheet()
    self.pstyle = self.styles['Normal']
    self.pstyle.alignment=1
    # connect to db
    self.sql = SQLdb(db_fp)
    # begin
    self.createDoc()


  def nextpage(self,colour=colors.black):
    'add page number and change page'
    # page number
    page_num = self.c.getPageNumber()
    text = "Page #%s" % page_num
    self.c.setFont('Helvetica-Bold',14)
    r,g,b = colour.rgb()
    self.c.setFillColorRGB(r,g,b)
    self.c.drawCentredString(landscape[0]/2.0, 20*mm, text)
    # reset font color
    self.c.setFillColorRGB(0,0,0)
    # yield page
    self.c.showPage()


  def createDoc(self):
    # add title page
    self.addTitlePage()

    # qndata is a dict of
    #   {qn:{dept:5tuple,...},...}
    # initialise empty dict for convenience
    qndata = {}
    for i in xrange(1,111):
      qndata[i] = {}
      for d in depts:
        qndata[i][d] = [0.0, 0.0, 0.0, 0.0, 0.0]
    # connect to db and get all data
    data = self.sql.cur.execute('SELECT * FROM surveys')
    datafetchall = data.fetchall()
    for row in datafetchall:
      # unpack
      dic  = eval(row[1])
      try:
        dept = eval(row[0])
      except:
        dept = row[0]

      if dept in depts:
        # collect data
        #sqlDeptDict={}
        for qnum,index in dic.iteritems():
          if 1 <= qnum <= 110 and index >= 1:
            qndata[qnum][dept][index-1] += 1.0

    # Catch empty db or read error
    if len(qndata)==0:
      print 'failed'
      return

    # make dict of qngroup data
    groupdata = {}
    g2qs_iter = list(g2qs.iteritems())
    for g,qns in g2qs_iter:
      # g is group name
      # qns is list of question nums in group
      groupdata[g]={}
      for d in depts:
        groupdata[g][d] = [0.0, 0.0, 0.0, 0.0, 0.0]
        for q in qns:
          for i in range(5):
            groupdata[g][d][i] += qndata[q][d][i]

    # colors for the departments (page number is coloured)
    grpcolours = []
    nGrps = len(g2qs_iter)
    assert nGrps == 19 # REMOVE
    for i in range(nGrps):
      # Generate new color for each department
      c = toColor('hsl({},100%,40%)'.format(360*(i+1)/float(nGrps)))
      grpcolours.append(c)

    # add data to pdf
    for tup, colour in zip(g2qs_iter,grpcolours):
      g,qns = tup
      # note:
      # addData(title,qndict,colour=colors.black)
      title = 'Results for '+g
      # combine and normalize data
      normdata = self.normDeptData(groupdata[g])
      self.addData( title, normdata, colour )
      qns=list(qns)
      qns.sort()
      for q in qns:
        text = `q`+'. '+textdict[q]
        normdata2 = self.normDeptData( qndata[q] )
        self.addData( text, normdata2, colour )

    # close db connection
    self.sql.close()
    # save to PDF
    self.save()


  def normDeptData(self, deptdict):
    'Normalize Results'
    newdeptdict = {}
    for d,ans in deptdict.iteritems():
      newdeptdict[d] = ans
      total = sum(ans)
      if total != 0.0:
        for i in xrange(5):
          newdeptdict[d][i] *= 100.0/float(total)
    return newdeptdict


  def addTitlePage(self):
    # logo
    im_w,im_h = 600,425
    w,h  =  im_w/4.0, im_h/4.0
    self.c.drawImage('generic-countylogo.png', landscape[0]/2.0 - w/2.0,
                     landscape[1] - 4*inch, width=w, height=h)
    # text
    titletext = 'County X<br/>'+\
                'Employee Evaluation<br/>'+\
                'Results By Department'
    style = self.styles['Title']
    style.fontName = 'Times-Bold'
    p = Paragraph(titletext,style)
    # you must call wrap before draw!!!
    p.wrapOn(self.c, landscape[0]/2. , 4*inch)
    p.drawOn(self.c, landscape[0]/4. , letter[1]-4*inch)
    self.nextpage()


  def addData(self,title,qndict,colour=colors.black):
    'Add group OR question data as full-page graph'
    ### add title
    p = Paragraph(title,self.styles['Heading1'])
    # you must call wrap before draw!!!
    p.wrapOn(self.c, landscape[0]-inch , inch)
    p.drawOn(self.c, 0.7*inch, landscape[1]-1.2*inch)
    ### overall chart
    overalldata = [0.0, 0.0, 0.0, 0.0, 0.0]
    for d,ans in qndict.iteritems():
      for i in xrange(5):
        overalldata[i] += ans[i]
    # re-norm
    total = float(sum(overalldata))
    # print total
    if total == 0.0: total = 1.0
    for i in xrange(5):
      overalldata[i] *= 100/total
    # add chart
    overall = DeptVBC(overalldata,(0.5*inch,landscape[1]/2.0 + 0.7*inch),
                      (landscape[0]/3.5,landscape[1]/4.0),pagesize=landscape,
                      titletext='Overall')
    overall.drawOn(self.c, 0,0)
    ### per-department chart
    deptchart = ClusterVBC(qndict)
    deptchart.drawOn(self.c, 0,0)
    ### add note box
    self.c.setFont('Helvetica-Bold',10)
    self.c.drawCentredString(landscape[0]/2.0, landscape[1]-1.4*inch, 'Notes')
    self.c.rect(3.8*inch, 5.15*inch, 3.4*inch, 1.9*inch,stroke=1,fill=0)
    ### add page markers
    r,g,b = colour.rgb()
    self.c.setFillColorRGB(r,g,b)
    self.c.circle(10.3*inch, 0.86*inch, 0.05*inch, fill=1)
    self.c.circle(0.7*inch, 0.86*inch, 0.05*inch, fill=1)
    ### done
    self.nextpage()


  def save(self):
    self.c.save()


if __name__ == '__main__':
  database = 'generic-surveys.db'
  r = AdminReport('Overall_Department_Comparison.pdf',database)
