from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, _DrawingEditorMixin, String
from reportlab.graphics.charts.textlabels import Label
from reportlab.lib.colors import toColor
from reportlab.graphics.samples.excelcolors import *
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch,mm
from math import trunc
from utils import get_qn,get_qns

# ================================================================================================
# ================================================================================================

class DeptVBC(_DrawingEditorMixin,Drawing):
  def __init__(self,nlist,posn,chartsize,
               pagesize=letter,titletext='',
               *args,**kw):
    'nlist is a 5-tuple of answers'
    #
    pw,ph=pagesize
    cw,ch=chartsize
    cx,cy=posn
    total = float(sum(nlist))
    if total == 0: total = 1

    # Add Chart
    Drawing.__init__(self,pw,ph,*args,**kw)
    self._add(self,VerticalBarChart(),name='chart',validate=None,desc="Results for a department")
    #                       cw - axis_room - padding
    self.chart.width      = cw - 25. - 5
    #                       ch - axis_room - title_room
    self.chart.height     = ch - 20. - 15
    self.chart.x          = cx + 25.
    self.chart.y          = cy + 20.

    # Colors
    green = toColor('rgb(0,200,30)')
    blue = toColor('rgb(0,128,255)')
    offwhite = toColor('rgb(200,195,230)')
    yellow = toColor('rgb(235,215,20)')
    red = toColor('rgb(255,55,55)')

    # Colour the bars
    self.chart.bars[(0,0)].fillColor = green
    self.chart.bars[(0,1)].fillColor = blue
    self.chart.bars[(0,2)].fillColor = yellow
    self.chart.bars[(0,3)].fillColor = red
    self.chart.bars[(0,4)].fillColor = offwhite

    # Configure Chart Options
    self.chart.fillColor                        = toColor('rgb(238,240,230)')
    self.chart.barSpacing                       = 1
    self.chart.barLabels.fontName               = 'Helvetica'
    self.chart.valueAxis.labels.fontName        = 'Helvetica'
    self.chart.valueAxis.labels.fontSize        = 7
    self.chart.valueAxis.forceZero              = 1
    self.chart.data                             = [nlist]
    self.chart.groupSpacing                     = 10
    self.chart.valueAxis.avoidBoundFrac         = 1
    self.chart.valueAxis.tickLeft               = 3
    self.chart.valueAxis.visibleGrid            = 1
    self.chart.categoryAxis.categoryNames       = ['%%%d Strongly\nAgree'   %trunc(round(100*nlist[0]/total)),
                                                   '%%%d Agree'             %trunc(round(100*nlist[1]/total)),
                                                   '%%%d Disagree'          %trunc(round(100*nlist[2]/total)),
                                                   '%%%d Strongly\nDisagree'%trunc(round(100*nlist[3]/total)),
                                                   '%%%d Do Not\nKnow'      %trunc(round(100*nlist[4]/total))]
    self.chart.categoryAxis.tickDown            = 3
    self.chart.categoryAxis.labels.fontName     = 'Helvetica'
    self.chart.categoryAxis.labels.textAnchor   = 'middle'
    self.chart.categoryAxis.labels.fontSize     = 6
    self.chart.categoryAxis.labels.dy           = -2

    # Title
    self._add(self,Label(),name='Title',validate=None,desc="The title at the top of the chart")
    self.Title.fontName   = 'Helvetica-Bold'
    self.Title.fontSize   = 12
    self.Title.x          = cx + cw/2.
    self.Title.y          = cy + ch - 9
    self.Title._text      = titletext
    self.Title.maxWidth  = 180
    self.Title.height    = 20
    self.Title.textAnchor ='middle'

def testDeptVBC():
  ansdic = get_qns(range(1,111))
  data = [0,0,0,0,0]
  for k,v in ansdic.iteritems():
    for i in range(5):
      data[i]+=v[i]
  #data = get_qn(87)
  halfletter = (letter[0]/2., letter[1]/2.)
  DeptVBC(data, (0,0), halfletter, halfletter).save(formats=['pdf'],outDir=None,fnRoot='VBCtest')

# ================================================================================================
# ================================================================================================

landscape = [letter[1],letter[0]]

class ClusterVBC(_DrawingEditorMixin,Drawing):
  def __init__(self,deptdict,pagesize=landscape,
               titletext='Breakdown by Department',*args,**kw):
    '''
    container object for cluster vbc
    posn is 2-tuple of co-ordinates
    chartsize is 2-tuple of (width,hight)
    deptdict is {<dept>:(<num of SA>,...),...}
    deptdict example {"dept1":[23,43,12,1,34],
                      "dept2":[12,23,54,34,12],
                      ...}
    '''
    #
    pw,ph=pagesize
    cw,ch= (pw-inch,ph/2.)
    cx,cy=(0.5*inch,inch)
    # Init a drawing
    Drawing.__init__(self,pw,ph,*args,**kw)
    # Add a chart, set properties
    self._add(self,VerticalBarChart(),name='chart',validate=None,desc="A chart")
    #                       cw - axis_room - padding
    self.chart.width      = cw - 15
    #                       ch - axis_room - title_room
    self.chart.height     = ch - 40. - 10
    self.chart.x          = cx + 15
    self.chart.y          = cy + 15
    #
    nDepts = len(deptdict)
    # chartdata needs to be a 5-tuple (SA,A,..) of answers by dept (34,54,23,..)
    chartdata=[]
    # legendpairs needs to be list of 2-tuples (color,deptname)
    legendpairs=[]
    for (k,v),i in zip(deptdict.items(),range(nDepts)):
      # k is the dept name
      # v is an answer tuple for that dept
      # Generate new color for each department
      color = toColor('hsl({},100%,50%)'.format(360*(i+1)/float(nDepts)))
      # Set chart bars to this color
      self.chart.bars[i].fillColor = color
      # Add 5-tuple of data to chart
      chartdata.append(v)
      legendpairs.append((color, k))
    # Axes
    self.chart.fillColor                        = toColor('rgb(238,240,230)')
    self.chart.barLabels.fontName               = 'Helvetica'
    self.chart.valueAxis.labels.fontName        = 'Helvetica'
    self.chart.valueAxis.labels.fontSize        = 8
    self.chart.valueAxis.forceZero              = 1
    self.chart.data                             = chartdata
    self.chart.groupSpacing                     = 10
    self.chart.valueAxis.avoidBoundFrac         = 1
    self.chart.valueAxis.tickLeft               = 3
    self.chart.valueAxis.visibleGrid            = 1
    self.chart.categoryAxis.categoryNames       = ['Strongly Agree',
                                                   'Agree',
                                                   'Disagree',
                                                   'Strongly Disagree',
                                                   'Do Not Know']
    self.chart.categoryAxis.tickDown            = 3
    self.chart.categoryAxis.labels.fontName     = 'Helvetica'
    self.chart.categoryAxis.labels.textAnchor   = 'middle'
    self.chart.categoryAxis.labels.fontSize     = 8
    self.chart.categoryAxis.visibleGrid         = 1
    # Title
    self._add(self,Label(),name='Title',validate=None,desc="The title at the top of the chart")
    self.Title.fontName   = 'Helvetica-Bold'
    self.Title.fontSize   = 15
    self.Title.x          = pw/2.0
    self.Title.y          = ch + cy - 25
    self.Title._text      = titletext
    #self.Title.height     = 20
    self.Title.textAnchor ='middle'
    # Legends
    for i in xrange(len(legendpairs)): #xrange(7)
      self._add(self,Legend(),name='Legend',validate=None,desc="The legend or key for the chart")
      self.Legend.colorNamePairs  = [legendpairs[i]]
      self.Legend.fontName        = 'Helvetica'
      self.Legend.fontSize        = 6
      self.Legend.x               = cx + cw - 220
      self.Legend.y               = 2*ch - 110 - int(130*(i/float(len(legendpairs))))
      self.Legend.alignment       ='right'
    # for j,i in zip(range(nDepts-7),range(7,nDepts)):
    #   self._add(self,Legend(),name='Legend',validate=None,desc="The legend or key for the chart")
    #   self.Legend.colorNamePairs  = [legendpairs[i]]
    #   self.Legend.fontName        = 'Helvetica'
    #   self.Legend.fontSize        = 9
    #   self.Legend.x               = cx + cw - 90
    #   self.Legend.y               = 2*ch - 110 - j*20
    #   self.Legend.alignment       ='right'

def testclusterVBC():
  depts = [ \
    "Operations",
    "Finance",
    "Library",
    "Museum",
    "Recreation",
    "Fire Department",
  ]
  deptdict={}
  for d in depts:
    ansdic = get_qns(range(1,111),d)
    data = [0,0,0,0,0]
    for k,v in ansdic.iteritems():
      # k is question number
      # v is 5-tuple of answers
      for i in range(5):
        data[i]+=v[i]
    deptdict[d]=data

  # normalize
  for d,ans in deptdict.iteritems():
    total = sum(ans)
    if total == 0: continue
    total = float(total)
    for i in xrange(5):
      ans[i] = 100*ans[i]/total
    deptdict[d] = ans

  pagesize = landscape
  ClusterVBC(deptdict).save(formats=['pdf'],outDir=None,
                                      fnRoot='_clusterVBCtest')

# ================================================================================================
# ================================================================================================

if __name__ == '__main__':
    pass
    testclusterVBC()
