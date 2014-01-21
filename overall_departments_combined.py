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


db = None # DEBUG
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
    self.c = canvas.Canvas('pdf/'+pdf_fp,pagesize=letter)
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
    self.c.drawCentredString(letter[0]/2.0, 20*mm, text)
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
      dic  = eval(row[1])
      try:
        dept = eval(row[0])
      except:
        dept = row[0]

      if dept in depts:
        # collect data
        #sqlDeptDict={}
        for qnum,index in dic.iteritems():
          # if 1 <= qnum <= 110 and index >= 1:
          if 1 <= qnum <= 110 and (not qnum in g2qs['County Council']) and index >= 1:
            assert (not qnum in  (6, 29, 57, 87, 108))
            qndata[qnum][dept][index-1] += 1.0

    # Catch empty db or read error
    if len(qndata)==0:
      print 'failed'
      return

    # make dict of qngroup data
    groupdata = {}
    tmp_g2qs = g2qs.pop('County Council')
    g2qs_iter = list(g2qs.iteritems())
    for g,qns in g2qs_iter:
      # g is group name
      # qns is list of question nums in group
      groupdata[g]={}
      for d in depts:
        groupdata[g][d] = [0.0, 0.0, 0.0, 0.0, 0.0]
        for q in qns:
          assert (not q in  (6, 29, 57, 87, 108))
          for i in range(5):
            groupdata[g][d][i] += qndata[q][d][i]

    # colors for the departments (page number is coloured)
    grpcolours = []
    nGrps = len(g2qs_iter)
    for i in range(nGrps):
      # Generate new color for each department
      c = toColor('hsl({},100%,40%)'.format(360*(i+1)/float(nGrps)))
      grpcolours.append(c)

    # add data to pdf
    # for (g,qns), colour in zip(g2qs.iteritems(),grpcolours):
    for tup, colour in zip(g2qs_iter,grpcolours):
      g,qns = tup
      # note:
      # addData(title,qndict,colour=colors.black)
      title = 'Results for '+g
      # combine and normalize data
      normdata = self.normDeptData(groupdata[g])
      # add group data
      self.addGroupData( title, normdata, colour )
      # init question data
      qns=list(qns)
      qns.sort()
      # handle first 1 to 6 qns
      qs = []
      while len(qs)<6:
        try:
          qs.append(qns.pop(0))
        except IndexError:
          break
      qdic = {}
      for q in qs:
        text = `q`+'. '+textdict[q]
        normdata = self.normDeptData( qndata[q] )
        qdic[q] = [text,normdata,colour]
      self.addQnData( qdic,startat=2 )
      # find num of pages needed (8 qns per page)
      numqns   = len(qns)
      numpages = int(ceil(numqns/8.))
      for i in xrange(numpages):
        index = 8*i + 8
        if index>numqns:
          qs = qns[i*8:]
        else:
          qs = qns[i*8:index]
        # add these quenstions to page
        qdic = {}
        for q in qs:
          text = `q`+'. '+textdict[q]
          normdata = self.normDeptData( qndata[q] )
          qdic[q] = [text,normdata,colour]
        self.addQnData( qdic )
    # close db connection
    self.sql.close()
    # save to PDF
    self.save()


  def addGroupData(self,title,qndict,colour=colors.black):
    'Add group data as full-page graph'
    ### add title
    s = self.styles['Title']
    s.fontName = 'Helvetica'
    p = Paragraph(title,s)
    # you must call wrap before draw!!!
    p.wrapOn(self.c, letter[0] , inch)
    p.drawOn(self.c, 0, letter[1]-1.1*inch)
    ### overall chart
    overalldata = [0,0,0,0,0]
    for d,ans in qndict.iteritems():
      for i in xrange(5):
        overalldata[i] += ans[i]
    # re-norm
    total = float(sum(overalldata))
    if total == 0: total = 1
    for i in xrange(5):
      overalldata[i] *= 100/total
    # add chart
    overall = DeptVBC(overalldata,(0.5*inch,letter[1]*3/4.0-3*mm),
                      (letter[0]-inch,letter[1]/4.-inch),pagesize=letter,
                      titletext='')
    overall.drawOn(self.c, 0,0)
##    ### add page markers
##    r,g,b = colour.rgb()
##    self.c.setFillColorRGB(r,g,b)
##    self.c.circle(10.3*inch, 0.86*inch, 0.05*inch, fill=1)
##    self.c.circle(0.7*inch, 0.86*inch, 0.05*inch, fill=1)
    ### done


  def addQnData(self,qdic,startat=0):
    'Add question data as 8 small graphs'
    'startat determines an offset for graphs'
    'for example, startat=4 makes means there is room for 4 graphs on the'
    'lower half of the page'
    keys = qdic.keys()
    keys.sort()
    xs=[0,1]*4
    ys=[0,0,1,1,2,2,3,3]
    for k,j in zip(keys,range(len(keys))):
      i = j+startat
      # topleft coords
      x = xs[i]
      y = ys[i]
      # generate chart
      qinfo = qdic[k]
      # qinfo is [str,5tuple,color]=[title,answers,colour]
      datadict = qinfo[1]
      data = [0,0,0,0,0]
      for d,ans in datadict.iteritems():
        for i in xrange(5):
          data[i] += ans[i]
      # re-norm
      total = float(sum(data))
      if total == 0: total = 1
      for i in xrange(5):
        data[i] *= 100/total
      #
      assert len(data)==5
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
      text = qinfo[0]
      p = Paragraph(text,self.pstyle)
      p.wrapOn(self.c, wid,hgt)
      p.drawOn(self.c, px , py+hgt-10)
##    ### add page markers
##    r,g,b = colour.rgb()
##    self.c.setFillColorRGB(r,g,b)
##    self.c.circle(10.3*inch, 0.86*inch, 0.05*inch, fill=1)
##    self.c.circle(0.7*inch, 0.86*inch, 0.05*inch, fill=1)
    ### done
    self.nextpage()


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
    self.c.drawImage('generic-countylogo.png', letter[0]/2.0 - w/2.0,
                     letter[1] - 4*inch, width=w, height=h)
    # text
    titletext = 'County X<br/>'+\
                'Employee Evaluation<br/>'+\
                'Combined Department Results'
    style = self.styles['Title']
    style.fontName = 'Times-Bold'
    p = Paragraph(titletext,style)
    # you must call wrap before draw!!!
    p.wrapOn(self.c, letter[0]/2. , 4*inch)
    p.drawOn(self.c, letter[0]/4. , letter[1]-5.5*inch)
    self.nextpage()


  def save(self):
    self.c.save()


if __name__ == '__main__':
  database = 'generic-surveys.db'
  r = AdminReport('Overall_Departments_Combined.pdf',database)
