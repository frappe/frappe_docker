from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""
Enclosing chart object. The various chart types are actually child objects.
Will probably need to call this indirectly
"""

from openpyxl.compat import unicode

from openpyxl.descriptors.serialisable import Serialisable
from openpyxl.descriptors import (
    Bool,
    Float,
    Typed,
    MinMax,
    Integer,
    NoneSet,
    String,
    Alias,
    Sequence,
)
from openpyxl.descriptors.excel import (
    Percentage,
    ExtensionList,
    Relation
)

from openpyxl.descriptors.nested import (
    NestedBool,
    NestedNoneSet,
    NestedInteger,
    NestedString,
    NestedMinMax,
    NestedText,
)

from openpyxl.drawing.colors import ColorMapping
from .text import Text, RichText
from .layout import Layout
from .shapes import GraphicalProperties
from .legend import Legend
from .marker import PictureOptions, Marker
from .label import DataLabel
from ._3d import _3DBase, View3D

from .area_chart import AreaChart, AreaChart3D
from .bar_chart import BarChart, BarChart3D
from .bubble_chart import BubbleChart
from .line_chart import LineChart, LineChart3D
from .pie_chart import PieChart, PieChart3D, ProjectedPieChart, DoughnutChart
from .radar_chart import RadarChart
from .scatter_chart import ScatterChart
from .stock_chart import StockChart
from .surface_chart import SurfaceChart, SurfaceChart3D

from .axis import NumericAxis, TextAxis, SeriesAxis, DateAxis
from .title import Title
from .print_settings import PrintSettings

from openpyxl.xml.functions import Element


class PivotFormat(Serialisable):

    tagname = "pivotFmt"

    idx = NestedInteger(nested=True)
    spPr = Typed(expected_type=GraphicalProperties, allow_none=True)
    graphicalProperties = Alias("spPr")
    txPr = Typed(expected_type=RichText, allow_none=True)
    TextBody = Alias("txPr")
    marker = Typed(expected_type=Marker, allow_none=True)
    dLbl = Typed(expected_type=DataLabel, allow_none=True)
    DataLabel = Alias("dLbl")
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('idx', 'spPr', 'txPr', 'marker', 'dLbl')

    def __init__(self,
                 idx=0,
                 spPr=None,
                 txPr=None,
                 marker=None,
                 dLbl=None,
                 extLst=None,
                ):
        self.idx = idx
        self.spPr = spPr
        self.txPr = txPr
        self.marker = marker
        self.dLbl = dLbl


class PivotFormatList(Serialisable):

    tagname = "pivotFmts"

    pivotFmt = Sequence(expected_type=PivotFormat, allow_none=True)

    __elements__ = ('pivotFmt',)

    def __init__(self,
                 pivotFmt=(),
                ):
        self.pivotFmt = pivotFmt


class DataTable(Serialisable):

    tagname = "dTable"

    showHorzBorder = NestedBool(allow_none=True)
    showVertBorder = NestedBool(allow_none=True)
    showOutline = NestedBool(allow_none=True)
    showKeys = NestedBool(allow_none=True)
    spPr = Typed(expected_type=GraphicalProperties, allow_none=True)
    graphicalProperties = Alias('spPr')
    txPr = Typed(expected_type=RichText, allow_none=True)
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('showHorzBorder', 'showVertBorder', 'showOutline',
                    'showKeys', 'spPr', 'txPr')

    def __init__(self,
                 showHorzBorder=None,
                 showVertBorder=None,
                 showOutline=None,
                 showKeys=None,
                 spPr=None,
                 txPr=None,
                 extLst=None,
                ):
        self.showHorzBorder = showHorzBorder
        self.showVertBorder = showVertBorder
        self.showOutline = showOutline
        self.showKeys = showKeys
        self.spPr = spPr
        self.txPr = txPr


class PlotArea(Serialisable):

    tagname = "plotArea"

    layout = Typed(expected_type=Layout, allow_none=True)
    dTable = Typed(expected_type=DataTable, allow_none=True)
    spPr = Typed(expected_type=GraphicalProperties, allow_none=True)
    graphicalProperties = Alias("spPr")
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    # at least one chart
    areaChart = Typed(expected_type=AreaChart, allow_none=True)
    area3DChart = Typed(expected_type=AreaChart3D, allow_none=True)
    lineChart = Typed(expected_type=LineChart, allow_none=True)
    line3DChart = Typed(expected_type=LineChart3D, allow_none=True)
    stockChart = Typed(expected_type=StockChart, allow_none=True)
    radarChart = Typed(expected_type=RadarChart, allow_none=True)
    scatterChart = Typed(expected_type=ScatterChart, allow_none=True)
    pieChart = Typed(expected_type=PieChart, allow_none=True)
    pie3DChart = Typed(expected_type=PieChart3D, allow_none=True)
    doughnutChart = Typed(expected_type=DoughnutChart, allow_none=True)
    barChart = Typed(expected_type=BarChart, allow_none=True)
    bar3DChart = Typed(expected_type=BarChart3D, allow_none=True)
    ofPieChart = Typed(expected_type=ProjectedPieChart, allow_none=True)
    surfaceChart = Typed(expected_type=SurfaceChart, allow_none=True)
    surface3DChart = Typed(expected_type=SurfaceChart3D, allow_none=True)
    bubbleChart = Typed(expected_type=BubbleChart, allow_none=True)

    # maybe axes
    valAx = Sequence(expected_type=NumericAxis, allow_none=True)
    catAx = Sequence(expected_type=TextAxis, allow_none=True)
    dateAx = Sequence(expected_type=DateAxis, allow_none=True)
    serAx = Sequence(expected_type=SeriesAxis, allow_none=True)

    __elements__ = ('layout', 'areaChart', 'area3DChart', 'lineChart',
                    'line3DChart', 'stockChart', 'radarChart', 'scatterChart', 'pieChart',
                    'pie3DChart', 'doughnutChart', 'barChart', 'bar3DChart', 'ofPieChart',
                    'surfaceChart', 'surface3DChart', 'bubbleChart', 'valAx', 'catAx', 'dateAx', 'serAx',
                    'dTable', 'spPr')

    def __init__(self,
                 layout=None,
                 dTable=None,
                 spPr=None,
                 areaChart=None,
                 area3DChart=None,
                 lineChart=None,
                 line3DChart=None,
                 stockChart=None,
                 radarChart=None,
                 scatterChart=None,
                 pieChart=None,
                 pie3DChart=None,
                 doughnutChart=None,
                 barChart=None,
                 bar3DChart=None,
                 ofPieChart=None,
                 surfaceChart=None,
                 surface3DChart=None,
                 bubbleChart=None,
                 valAx=(),
                 catAx=(),
                 serAx=(),
                 dateAx=(),
                 extLst=None,
                ):
        self.layout = layout
        self.dTable = dTable
        self.spPr = spPr
        self.areaChart = areaChart
        self.area3DChart = area3DChart
        self.lineChart = lineChart
        self.line3DChart = line3DChart
        self.stockChart = stockChart
        self.radarChart = radarChart
        self.scatterChart = scatterChart
        self.pieChart = pieChart
        self.pie3DChart = pie3DChart
        self.doughnutChart = doughnutChart
        self.barChart = barChart
        self.bar3DChart = bar3DChart
        self.ofPieChart = ofPieChart
        self.surfaceChart = surfaceChart
        self.surface3DChart = surface3DChart
        self.bubbleChart = bubbleChart
        self.valAx = valAx
        self.catAx = catAx
        self.dateAx = dateAx
        self.serAx = serAx
        self._charts = []


    def to_tree(self, tagname=None, idx=None):
        if tagname is None:
            tagname = self.tagname
        el = Element(tagname)
        if self.layout is not None:
            el.append(self.layout.to_tree())
        for chart in self._charts:
            el.append(chart.to_tree())
        for ax in ['valAx', 'catAx', 'dateAx', 'serAx',]:
            seq = getattr(self, ax)
            if seq:
                for obj in seq:
                    el.append(obj.to_tree())
        for attr in ['dTable', 'spPr']:
            obj = getattr(self, attr)
            if obj is not None:
                el.append(obj.to_tree())
        return el


class ChartContainer(Serialisable):

    tagname = "chart"

    title = Typed(expected_type=Title, allow_none=True)
    autoTitleDeleted = NestedBool(allow_none=True)
    pivotFmts = Typed(expected_type=PivotFormatList, allow_none=True)
    view3D = _3DBase.view3D
    floor = _3DBase.floor
    sideWall = _3DBase.sideWall
    backWall = _3DBase.backWall
    plotArea = Typed(expected_type=PlotArea, )
    legend = Typed(expected_type=Legend, allow_none=True)
    plotVisOnly = NestedBool(allow_none=True)
    dispBlanksAs = NestedNoneSet(values=(['span', 'gap', 'zero']))
    showDLblsOverMax = NestedBool(allow_none=True)
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('title', 'autoTitleDeleted', 'pivotFmts', 'view3D',
                    'floor', 'sideWall', 'backWall', 'plotArea', 'legend', 'plotVisOnly',
                    'dispBlanksAs', 'showDLblsOverMax')

    def __init__(self,
                 title=None,
                 autoTitleDeleted=None,
                 pivotFmts=None,
                 view3D=None,
                 floor=None,
                 sideWall=None,
                 backWall=None,
                 plotArea=None,
                 legend=None,
                 plotVisOnly=None,
                 dispBlanksAs="gap",
                 showDLblsOverMax=None,
                 extLst=None,
                ):
        self.title = title
        self.autoTitleDeleted = autoTitleDeleted
        self.pivotFmts = pivotFmts
        self.view3D = view3D
        self.floor = floor
        self.sideWall = sideWall
        self.backWall = backWall
        if plotArea is None:
            plotArea = PlotArea()
        self.plotArea = plotArea
        self.legend = legend
        self.plotVisOnly = plotVisOnly
        self.dispBlanksAs = dispBlanksAs
        self.showDLblsOverMax = showDLblsOverMax


class Protection(Serialisable):

    tagname = "protection"

    chartObject = NestedBool(allow_none=True)
    data = NestedBool(allow_none=True)
    formatting = NestedBool(allow_none=True)
    selection = NestedBool(allow_none=True)
    userInterface = NestedBool(allow_none=True)

    __elements__ = ("chartObject", "data", "formatting", "selection", "userInterface")

    def __init__(self,
                 chartObject=None,
                 data=None,
                 formatting=None,
                 selection=None,
                 userInterface=None,
                ):
        self.chartObject = chartObject
        self.data = data
        self.formatting = formatting
        self.selection = selection
        self.userInterface = userInterface


class PivotSource(Serialisable):

    tagname = "pivotSource"

    name = NestedText(expected_type=unicode)
    fmtId = NestedText(expected_type=int)
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('name', 'fmtId')

    def __init__(self,
                 name=None,
                 fmtId=None,
                 extLst=None,
                ):
        self.name = name
        self.fmtId = fmtId


class ExternalData(Serialisable):

    tagname = "externalData"

    autoUpdate = NestedBool(allow_none=True)
    id = String() # Needs namespace

    def __init__(self,
                 autoUpdate=None,
                 id=None
                ):
        self.autoUpdate = autoUpdate
        self.id = id


class ChartSpace(Serialisable):

    tagname = "chartSpace"

    date1904 = NestedBool(allow_none=True)
    lang = NestedString(allow_none=True)
    roundedCorners = NestedBool(allow_none=True)
    style = NestedMinMax(allow_none=True, min=1, max=48)
    clrMapOvr = Typed(expected_type=ColorMapping, allow_none=True)
    pivotSource = Typed(expected_type=PivotSource, allow_none=True)
    protection = Typed(expected_type=Protection, allow_none=True)
    chart = Typed(expected_type=ChartContainer)
    spPr = Typed(expected_type=GraphicalProperties, allow_none=True)
    graphicalProperties = Alias("spPr")
    txPr = Typed(expected_type=RichText, allow_none=True)
    textProperties = Alias("txPr")
    externalData = Typed(expected_type=ExternalData, allow_none=True)
    printSettings = Typed(expected_type=PrintSettings, allow_none=True)
    userShapes = Relation()
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('date1904', 'lang', 'roundedCorners', 'style',
                    'clrMapOvr', 'pivotSource', 'protection', 'chart', 'spPr', 'txPr',
                    'externalData', 'printSettings', 'userShapes')

    def __init__(self,
                 date1904=None,
                 lang=None,
                 roundedCorners=None,
                 style=None,
                 clrMapOvr=None,
                 pivotSource=None,
                 protection=None,
                 chart=None,
                 spPr=None,
                 txPr=None,
                 externalData=None,
                 printSettings=None,
                 userShapes=None,
                 extLst=None,
                ):
        self.date1904 = date1904
        self.lang = lang
        self.roundedCorners = roundedCorners
        self.style = style
        self.clrMapOvr = clrMapOvr
        self.pivotSource = pivotSource
        self.protection = protection
        self.chart = chart
        self.spPr = spPr
        self.txPr = txPr
        self.externalData = externalData
        self.printSettings = printSettings
        self.userShapes = userShapes
        self.extLst = extLst
