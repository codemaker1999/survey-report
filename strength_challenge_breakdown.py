'''
This is the same as DepartmentReport but with additional
grouping structure for the questions

The categories are:
  (Strongly Agree + Agree)
    85%+      => Greatest Strength (GS)
    75% - 85% => Moderate Strength (MS)
  (Stongly Disagree + Disagree)
    40%+      => Greatest Challenge (GC)
    25% - 40% => Moderate Challenge (MC)
  Other (O)

'''
# reportlab
from reportlab.platypus import BaseDocTemplate, Frame, FrameBreak, \
     PageTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch,mm
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.colors import toColor
from reportlab.pdfgen import canvas

# project folder
from sql import SQLdb
from qnGrouping import q2g,g2qs
from utils import get_qns
from VBC import DeptVBC
from questionText import textdict

# standard lib
from itertools import cycle
from math import ceil,trunc


############################################################
class SCReport:

  def __init__(self,pdf_fp,db_fp,dept):
    # set up reportlab
    pdf_fp = pdf_fp.replace(',','__').replace('/','__')
    self.c = canvas.Canvas('pdf/'+pdf_fp,pagesize=letter)
    self.styles = getSampleStyleSheet()
    self.pstyle = self.styles['Normal']
    self.pstyle.alignment=1
    # init some variables
    self.acronyms = {'Greatest Strength'  :'GS',
                     'Moderate Strength'  :'MS',
                     'Moderate Challenge' :'MC',
                     'Greatest Challenge' :'GC',
                     'Other'              :'O'}
    self.SCitems = (('Greatest Strength', toColor('rgb(0  ,178,0)'  )),
                    ('Moderate Strength', toColor('rgb(133,175,133)')),
                    ('Moderate Challenge',toColor('rgb(165,120,120)')),
                    ('Greatest Challenge',toColor('rgb(167,  0,0)'  )),
                    ('Other',             toColor('rgb(175,175,175)')))
    # connect to db
    self.dept = dept
    self.sql = SQLdb(db_fp)
    # begin
    self.createDoc()


  def nextpage(self):
    'add page number and change page'
    self.c.setFillColor(colors.black)
    # page number
    page_num = self.c.getPageNumber()
    text = "Page #%s" % page_num
    self.c.setFont('Helvetica-Bold',14)
    self.c.drawCentredString(letter[0]/2.0, 20*mm, text)
    # yield page
    self.c.showPage()


  def createDoc(self):
    # get relevant data from db
    cmd='SELECT data FROM surveys WHERE dept="'+str(self.dept)+'";'
    data = self.sql.cur.execute(cmd)
    qndicts = []
    for s in data.fetchall():
      dic = eval(s[0])
      qndicts.append( dic )
    if qndicts == []:
      print self.dept,'failed'
      return
    #
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
    titletext = 'County X<br/>Employee Evaluation<br/>%s'%self.dept
    #
    style = self.styles['Title']
    style.fontName = 'Times-Bold'
    p = Paragraph(titletext,style)
    p.wrapOn(self.c, letter[0]/2. , 4*inch)# you must call wrap before draw!!!
    p.drawOn(self.c, letter[0]/4. , letter[1]-4*inch)
    ### technical info
    self.c.setFont('Times-Bold',16)
    self.c.drawCentredString(letter[0]/2.0, letter[1]/2.0 - 10*mm, 'Technical Information')
    # explain category breakdown and slider bar
    explanation='''
The questions in this report are grouped according to both the type of question asked and the nature of the response.
If the addition of the number of answers for "Agree" and "Strongly Agree" constitute...<br></br><br></br>
<bullet>85% or more of the total responses, this question is a "Greatest Strength".<br></br>
<bullet>between 75% and 85% of the total responses, this question is a "Moderate Strength".<br></br>
<br></br>
If the addition of the number of answers for "Disagree" and "Strongly Disagree" constitute...<br></br><br></br>
<bullet>40% or more of the total responses, this question is a "Greatest Challenge".<br></br>
<bullet>between 25% and 40% of the total responses, this question is a "Moderate Challenge".<br></br><br></br>
The green and red bar on the main page of each question group, which rates the group from "Very Positive"
to "Very Challenging", was calculated by giving...<br></br><br></br>
<bullet>"Greatest Strength" a weight of 2<br></br>
<bullet>"Moderate Strength" a weight of 1<br></br>
<bullet>"Moderate Challenge" a weight of -1<br></br>
<bullet>"Greatest Challenge" a weight of -2<br></br>
<bullet>"Other" a weight of magnitude 1 such that the results are brought closer to the middle'''
    explanation = explanation.replace('<bullet>','&nbsp; &nbsp; &nbsp; &bull; ')
    style = self.styles['BodyText']
    exp = Paragraph(explanation,style)
    exp.wrapOn(self.c, 6*inch , 6*inch)# you must call wrap before draw!!!
    exp.drawOn(self.c, 1.5*inch , 1.5*inch)
    # done
    self.nextpage()


  def addQnGroup(self,title,qndict):
    # ---------------------------------------------
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
    #
    # chart
    overall = DeptVBC(alldata,
                      (inch,inch),
                      (letter[0]-2*inch,letter[1]/3.0),
                      titletext="Overall Response")
    overall.drawOn(self.c, 0,0)
    #
    # ---------------------------------------------
    # determine categories
    # categories are
    #   Greatest Strength (GS)
    #   Moderate Strength (MS)
    #   Greatest Challenge (GC)
    #   Moderate Challenge (MC)
    #   Other (O)

    sc_dict = {'GS':[],'MS':[],'GC':[],'MC':[],'O':[]}
    for qnum,rawlst in qndict.iteritems():
      lst = filter(lambda x: 1 <= x <= 5, rawlst)
      numresponses = len(lst)
      if numresponses == 0:
        sc_dict['O'].append(qnum)
        continue
      # count results
      numSA = lst.count(1)
      numA  = lst.count(2)
      numD  = lst.count(3)
      numSD = lst.count(4)
      numO  = lst.count(5)
      num_no_response = len(rawlst) - len(lst)
      # percentage that agree/disagree
      percA = (numSA + numA)/float(numresponses)
      percD = (numSD + numD)/float(numresponses)
      if percA >= 0.85:
        sc_dict['GS'].append(qnum)
      elif 0.75 <= percA <= 0.85:
        sc_dict['MS'].append(qnum)
      elif percD >= 0.40:
        sc_dict['GC'].append(qnum)
      elif 0.25 <= percD <= 0.40:
        sc_dict['MC'].append(qnum)
      else:
        sc_dict['O'].append(qnum)

    # ---------------------------------------------
    #### slider
    # weighted offset from neutral
    lenGS = len(sc_dict['GS'])
    lenMS = len(sc_dict['MS'])
    lenMC = len(sc_dict['MC'])
    lenGC = len(sc_dict['GC'])
    lenO  = len(sc_dict['O'])
    numqns = len(qndict.keys())
    assert numqns == lenGS+lenMS+lenMC+lenGC+lenO
    weighted = ( 2*lenGS + lenMS - lenMC - 2*lenGC )
    for i in xrange(lenO):
      if weighted < 0:
        weighted += 1
      elif weighted > 0:
        weighted -= 1
    posn = weighted/float(2*numqns)
    # draw image
    im_w,im_h = 10000.0,1000.0
    w = 4*inch
    h = 3*mm
    y = letter[1]/2.0 + 10*mm
    self.c.drawImage('strengthslider.png', letter[0]/2.0 - w/2.0, y, width=w, height=h)
    # draw slider position as black slim rectangle
    self.c.setFillColor(colors.black)
    self.c.rect(letter[0]/2.0 - (w/2.0)*posn,
                y - mm,
                0.6*mm,
                h + 2*mm,
                fill=True)
    # slider descriptions
    self.c.setFont('Helvetica-Bold',10)
    self.c.drawCentredString(1.5*inch,y,'Very Positive')
    self.c.drawCentredString(letter[0]-1.5*inch,y,'Very Challenging')
    # done
    self.nextpage()
    ### Add pages for questions
    self.addQnPages(qndict,sc_dict)


  def addQnPages(self,qdict, sc_dict):
    '''
    qndict is {qnum:[1,2,2,3,4,1,...], ...}
    where the length of the list is the number of employees in
    the department
    '''

    # sort according to SC categories
    keys = []
    keys += sc_dict['GS']
    keys += sc_dict['MS']
    keys += sc_dict['MC']
    keys += sc_dict['GC']
    keys += sc_dict['O']

    # acronym for the last nonempty category
    last_cat = filter(lambda x: len(sc_dict[x])!=0, ['GS','MS','GC','MC','O'])[-1]

    # ---------------------------------------------
    # make iterator for page coords:
    # divide page into 2 columns and 5 rows, IE 10 boxes
    # each coords.next() is the bottom left coordinate tuple
    # of one of these boxes

    coords=[]

    # page margin (for one edge)
    margx = 0.5*inch
    margy = inch
    self.margx = margx
    self.margy = margy

    for j in range(5):
      for i in range(2):
        # divide page up
        x = margx + i * ( letter[0]-2*margx )/2.0
        y = margy + ( letter[1]-2*margy ) - (j+1) * ( letter[1]-2*margy )/5.0
        coords.append([x,y])

    # indefinitely repeating iterator
    coords = cycle(coords)

    # ---------------------------------------------
    # add Categories
    posn = coords.next()
    for text,colour in self.SCitems:
      ### INIT ###
      x,y = posn
      # get acronym for this category
      acr = self.acronyms[text]
      # number of questions in this category
      qlist = sc_dict[acr]
      qlist.sort()
      numqns = len( qlist )
      # skip all drawing if no questions
      if numqns == 0:
        continue

      ### Add Questions ###
      for q in qlist:
        ### INIT ###
        # q is a question number
        qindex = qlist.index(q)

        ### SC HEADER ###
        NOPAGEBREAK = False
        if qindex == 0:
          self.addCatHeader(posn,text,colour)
          NOPAGEBREAK = True

        ### ADD ONE MINI CHART ###

        # check if new page reached
        if not NOPAGEBREAK and self.istopleft([x,y]):
          self.nextpage()

        # get data in 5tuple [SA,A,D,SD,DNK]
        data = [0,0,0,0,0]
        for i in qdict[q]:
          if i >= 1:
            data[i-1]+=1

        # chart sizing stuff
        spacex = (letter[0]-2*margx)/2.0
        spacey = (letter[1]-2*margy)/5.0
        wid    = spacex - 0.5*inch
        hgt    = spacey - 0.7*inch
        px     = x + 6*mm
        py     = y + 3*mm
        qchart = DeptVBC(data,(0,0),(wid,hgt))
        qchart.drawOn(self.c,px,py)

        # question text label
        text = `q`+'. '+textdict[q]
        p = Paragraph(text,self.pstyle)
        p.wrapOn(self.c, wid,hgt)
        p.drawOn(self.c, px , py+hgt-10)

        ### OTHER DRAWING ###

        # draw sides of the box surrounding qns
        self.c.setFillColor(colour)
        # if q is in left column of qns
        if qindex % 2 == 0:
          # height of a page subdivision
          div = (letter[1]-2*margy)/5.0
          # if q in first row of questions
          if qindex == 0 or qindex == 1:
            leftheight  = div-3.05*mm
            rightheight = div-3*mm
          else:
            leftheight  = div+3*mm
            rightheight = div+3*mm
          # draw left side of box
          self.c.rect(margx+mm,
                      y+mm+0.9,
                      mm,
                      leftheight,
                      fill=1,
                      stroke=False)
          # draw right side of box
          self.c.rect(letter[0]-margx-mm,
                      y+mm+1.3,
                      mm,
                      rightheight,
                      fill=1,
                      stroke=False)
        # draw bottom of box
        # if q is the last question in qlist
        if qindex + 1 == numqns:
          self.c.rect(margx+mm+0.5,
                      y+mm,
                      letter[0]-1.1*mm-2*margx,
                      mm,
                      fill=1,
                      stroke=False)

          ### FINISH UP ###

          # go to the next blank line
          if qindex % 2 == 0:
            # if in left column
            coords.next()
            posn = coords.next()
          else:
            # if in right column
            posn = coords.next()
          # pagebreak if needed
          if acr != last_cat and self.istopleft( posn ):
            self.nextpage()
          # iterate
          x,y = posn
        else:
          # not last question
          posn = coords.next()
          # iterate
          x,y = posn

    ### MISC ###
    # page break
    self.nextpage()


  def istopleft(self, posn):
    'determine if posn is in top left division of page'
    # constants
    x,y = posn
    margx = self.margx
    margy = self.margy
    topleftx = margx
    div = (letter[1]-2*margy)/5.0
    toplefty = letter[1] - margy - div
    # calc
    if topleftx - mm < x < topleftx + mm and\
       toplefty - mm < y < toplefty + mm :
      return True
    else:
      return False


  def addCatHeader(self,posn,text,colour):
    'add header for category'
    # constants
    x,y = posn
    margx = self.margx
    margy = self.margy
    div = (letter[1]-2*margy)/5.0
    top = y + div
    # make decorative color divider
    self.c.setFillColor(colour)
    # top horizontal line left
    self.c.rect(margx+mm,   top-2.5*mm,
                2.5*inch,   mm,
                fill=1, stroke=False)
    # top horizontal line right
    self.c.rect(letter[0]-margx-2.5*inch-mm,   top-2.5*mm,
                2.5*inch,   mm,
                fill=1, stroke=False)
    # add text
    self.c.setFillColor(colors.black)
    self.c.setFont('Helvetica-Bold',13)
    txtx = letter[0]/2.0
    txty = top - 4*mm
    self.c.drawCentredString(txtx,txty,text)


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
    objs.append( SCReport('Strength_Challenge_Results_For_%s.pdf'%fn,database,d) )
