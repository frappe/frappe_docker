from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

from openpyxl.xml.functions import NS_REGEX, Element
from openpyxl.xml.constants import CHART_NS, REL_NS, DRAWING_NS

from openpyxl.descriptors.serialisable import Serialisable
from openpyxl.descriptors import (
    Typed,
    Bool,
    NoneSet,
    Integer,
    Set,
    String,
    Alias,
)
from openpyxl.descriptors.excel import Relation
from openpyxl.descriptors.excel import ExtensionList as OfficeArtExtensionList

from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.chart.text import RichText

from .effect import *
from .fill import RelativeRect, BlipFillProperties
from .text import Hyperlink, EmbeddedWAVAudioFile
from .shapes import (
    Transform2D,
    Point2D,
    PositiveSize2D,
    Scene3D,
    ShapeStyle,
)

class GroupTransform2D(Serialisable):

    rot = Integer()
    flipH = Bool(allow_none=True)
    flipV = Bool(allow_none=True)
    off = Typed(expected_type=Point2D, allow_none=True)
    ext = Typed(expected_type=PositiveSize2D, allow_none=True)
    chOff = Typed(expected_type=Point2D, allow_none=True)
    chExt = Typed(expected_type=PositiveSize2D, allow_none=True)

    def __init__(self,
                 rot=None,
                 flipH=None,
                 flipV=None,
                 off=None,
                 ext=None,
                 chOff=None,
                 chExt=None,
                ):
        self.rot = rot
        self.flipH = flipH
        self.flipV = flipV
        self.off = off
        self.ext = ext
        self.chOff = chOff
        self.chExt = chExt


class GroupShapeProperties(Serialisable):

    bwMode = Set(values=(['clr', 'auto', 'gray', 'ltGray', 'invGray',
                          'grayWhite', 'blackGray', 'blackWhite', 'black', 'white', 'hidden']))
    xfrm = Typed(expected_type=GroupTransform2D, allow_none=True)
    scene3d = Typed(expected_type=Scene3D, allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    def __init__(self,
                 bwMode=None,
                 xfrm=None,
                 scene3d=None,
                 extLst=None,
                ):
        self.bwMode = bwMode
        self.xfrm = xfrm
        self.scene3d = scene3d
        self.extLst = extLst


class GroupLocking(Serialisable):

    noGrp = Bool(allow_none=True)
    noUngrp = Bool(allow_none=True)
    noSelect = Bool(allow_none=True)
    noRot = Bool(allow_none=True)
    noChangeAspect = Bool(allow_none=True)
    noChangeArrowheads = Bool(allow_none=True)
    noMove = Bool(allow_none=True)
    noResize = Bool(allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    def __init__(self,
                 noGrp=None,
                 noUngrp=None,
                 noSelect=None,
                 noRot=None,
                 noChangeAspect=None,
                 noChangeArrowheads=None,
                 noMove=None,
                 noResize=None,
                 extLst=None,
                ):
        self.noGrp = noGrp
        self.noUngrp = noUngrp
        self.noSelect = noSelect
        self.noRot = noRot
        self.noChangeAspect = noChangeAspect
        self.noChangeArrowheads = noChangeArrowheads
        self.noMove = noMove
        self.noResize = noResize
        self.extLst = extLst


class NonVisualGroupDrawingShapeProps(Serialisable):

    grpSpLocks = Typed(expected_type=GroupLocking, allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    def __init__(self,
                 grpSpLocks=None,
                 extLst=None,
                ):
        self.grpSpLocks = grpSpLocks
        self.extLst = extLst


class NonVisualDrawingShapeProps(Serialisable):

    tagname = "cNvSpPr"

    spLocks = Typed(expected_type=GroupLocking, allow_none=True)
    txBax = Bool(allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    def __init__(self,
                 spLocks=None,
                 txBox=None,
                 extLst=None,
                ):
        self.spLocks = spLocks
        self.txBox = txBox
        self.extLst = extLst


class NonVisualDrawingProps(Serialisable):

    tagname = "cNvPr"

    id = Integer()
    name = String()
    descr = String(allow_none=True)
    hidden = Bool(allow_none=True)
    title = String(allow_none=True)
    hlinkClick = Typed(expected_type=Hyperlink, allow_none=True)
    hlinkHover = Typed(expected_type=Hyperlink, allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    def __init__(self,
                 id=None,
                 name=None,
                 descr=None,
                 hidden=None,
                 title=None,
                 hlinkClick=None,
                 hlinkHover=None,
                 extLst=None,
                ):
        self.id = id
        self.name = name
        self.descr = descr
        self.hidden = hidden
        self.title = title
        self.hlinkClick = hlinkClick
        self.hlinkHover = hlinkHover
        self.extLst = extLst


class NonVisualGroupShape(Serialisable):

    cNvPr = Typed(expected_type=NonVisualDrawingProps, )
    cNvGrpSpPr = Typed(expected_type=NonVisualGroupDrawingShapeProps, )

    def __init__(self,
                 cNvPr=None,
                 cNvGrpSpPr=None,
                ):
        self.cNvPr = cNvPr
        self.cNvGrpSpPr = cNvGrpSpPr


class GroupShape(Serialisable):

    nvGrpSpPr = Typed(expected_type=NonVisualGroupShape, )
    grpSpPr = Typed(expected_type=GroupShapeProperties, )

    def __init__(self,
                 nvGrpSpPr=None,
                 grpSpPr=None,
                ):
        self.nvGrpSpPr = nvGrpSpPr
        self.grpSpPr = grpSpPr


class GraphicFrameLocking(Serialisable):

    noGrp = Bool(allow_none=True)
    noDrilldown = Bool(allow_none=True)
    noSelect = Bool(allow_none=True)
    noChangeAspect = Bool(allow_none=True)
    noMove = Bool(allow_none=True)
    noResize = Bool(allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    def __init__(self,
                 noGrp=None,
                 noDrilldown=None,
                 noSelect=None,
                 noChangeAspect=None,
                 noMove=None,
                 noResize=None,
                 extLst=None,
                ):
        self.noGrp = noGrp
        self.noDrilldown = noDrilldown
        self.noSelect = noSelect
        self.noChangeAspect = noChangeAspect
        self.noMove = noMove
        self.noResize = noResize
        self.extLst = extLst


class NonVisualGraphicFrameProperties(Serialisable):

    tagname = "cNvGraphicFramePr"

    graphicFrameLocks = Typed(expected_type=GraphicFrameLocking, allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    def __init__(self,
                 graphicFrameLocks=None,
                 extLst=None,
                ):
        self.graphicFrameLocks = graphicFrameLocks
        self.extLst = extLst


class NonVisualGraphicFrame(Serialisable):

    tagname = "nvGraphicFramePr"

    cNvPr = Typed(expected_type=NonVisualDrawingProps)
    cNvGraphicFramePr = Typed(expected_type=NonVisualGraphicFrameProperties)

    __elements__ = ('cNvPr', 'cNvGraphicFramePr')

    def __init__(self,
                 cNvPr=None,
                 cNvGraphicFramePr=None,
                ):
        if cNvPr is None:
            cNvPr = NonVisualDrawingProps(id=0, name="Chart 0")
        self.cNvPr = cNvPr
        if cNvGraphicFramePr is None:
            cNvGraphicFramePr = NonVisualGraphicFrameProperties()
        self.cNvGraphicFramePr = cNvGraphicFramePr


class ChartRelation(Serialisable):

    tagname = "chart"
    namespace = CHART_NS

    id = Relation()

    def __init__(self, id):
        self.id = id


class GraphicData(Serialisable):

    tagname = "graphicData"
    namespace = DRAWING_NS

    uri = String()
    chart = Typed(expected_type=ChartRelation, allow_none=True)


    def __init__(self,
                 uri=CHART_NS,
                 chart=None,
                ):
        self.uri = uri
        self.chart = None


class GraphicObject(Serialisable):

    tagname = "graphic"
    namespace = DRAWING_NS

    graphicData = Typed(expected_type=GraphicData)

    def __init__(self,
                 graphicData=None,
                ):
        if graphicData is None:
            graphicData = GraphicData()
        self.graphicData = graphicData


class GraphicFrame(Serialisable):

    tagname = "graphicFrame"

    nvGraphicFramePr = Typed(expected_type=NonVisualGraphicFrame)
    xfrm = Typed(expected_type=Transform2D)
    graphic = Typed(expected_type=GraphicObject)
    macro = String(allow_none=True)
    fPublished = Bool(allow_none=True)

    __elements__ = ('nvGraphicFramePr', 'xfrm', 'graphic', 'macro', 'fPublished')

    def __init__(self,
                 nvGraphicFramePr=None,
                 xfrm=None,
                 graphic=None,
                 macro=None,
                 fPublished=None,
                 ):
        if nvGraphicFramePr is None:
            nvGraphicFramePr = NonVisualGraphicFrame()
        self.nvGraphicFramePr = nvGraphicFramePr
        if xfrm is None:
            xfrm = Transform2D()
        self.xfrm = xfrm
        if graphic is None:
            graphic = GraphicObject()
        self.graphic = graphic
        self.macro = macro
        self.fPublished = fPublished


class Connection(Serialisable):

    id = Integer()
    idx = Integer()

    def __init__(self,
                 id=None,
                 idx=None,
                ):
        self.id = id
        self.idx = idx


class ConnectorLocking(Serialisable):

    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    def __init__(self,
                 extLst=None,
                ):
        self.extLst = extLst


class NonVisualConnectorProperties(Serialisable):

    cxnSpLocks = Typed(expected_type=ConnectorLocking, allow_none=True)
    stCxn = Typed(expected_type=Connection, allow_none=True)
    endCxn = Typed(expected_type=Connection, allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    def __init__(self,
                 cxnSpLocks=None,
                 stCxn=None,
                 endCxn=None,
                 extLst=None,
                ):
        self.cxnSpLocks = cxnSpLocks
        self.stCxn = stCxn
        self.endCxn = endCxn
        self.extLst = extLst


class ConnectorNonVisual(Serialisable):

    cNvPr = Typed(expected_type=NonVisualDrawingProps, )
    cNvCxnSpPr = Typed(expected_type=NonVisualConnectorProperties, )

    def __init__(self,
                 cNvPr=None,
                 cNvCxnSpPr=None,
                ):
        self.cNvPr = cNvPr
        self.cNvCxnSpPr = cNvCxnSpPr


class ShapeMeta(Serialisable):

    tagname = "nvSpPr"

    cNvPr = Typed(expected_type=NonVisualDrawingProps)
    cNvSpPr = Typed(expected_type=NonVisualDrawingShapeProps)

    def __init__(self, cNvPr=None, cNvSpPr=None):
        self.cNvPr = cNvPr
        self.cNvSpPr = cNvSpPr


class Shape(Serialisable):

    macro = String(allow_none=True)
    textlink = String(allow_none=True)
    fPublished = Bool(allow_none=True)
    nvSpPr = Typed(expected_type=ShapeMeta)
    meta = Alias("nvSpPr")
    spPr = Typed(expected_type=GraphicalProperties)
    graphicalProperties = Alias("spPr")
    style = Typed(expected_type=ShapeStyle, allow_none=True)
    txBody = Typed(expected_type=RichText, allow_none=True)

    def __init__(self,
                 macro=None,
                 textlink=None,
                 fPublished=None,
                 nvSpPr=None,
                 spPr=None,
                 style=None,
                 txBody=None,
                ):
        self.macro = macro
        self.textlink = textlink
        self.fPublished = fPublished
        self.nvSpPr =nvSpPr
        self.spPr = spPr
        self.style = style
        self.txBody = txBody


class PictureLocking(Serialisable):

    tagname = "picLocks"
    namespace = DRAWING_NS

    #Using attribute group AG_Locking
    noCrop = Bool(allow_none=True)
    noGrp = Bool(allow_none=True)
    noSelect = Bool(allow_none=True)
    noRot = Bool(allow_none=True)
    noChangeAspect = Bool(allow_none=True)
    noMove = Bool(allow_none=True)
    noResize = Bool(allow_none=True)
    noEditPoints = Bool(allow_none=True)
    noAdjustHandles = Bool(allow_none=True)
    noChangeArrowheads = Bool(allow_none=True)
    noChangeShapeType = Bool(allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    __elements__ = ()

    def __init__(self,
                 noCrop=None,
                 noGrp=None,
                 noSelect=None,
                 noRot=None,
                 noChangeAspect=None,
                 noMove=None,
                 noResize=None,
                 noEditPoints=None,
                 noAdjustHandles=None,
                 noChangeArrowheads=None,
                 noChangeShapeType=None,
                 extLst=None,
                ):
        self.noCrop = noCrop
        self.noGrp = noGrp
        self.noSelect = noSelect
        self.noRot = noRot
        self.noChangeAspect = noChangeAspect
        self.noMove = noMove
        self.noResize = noResize
        self.noEditPoints = noEditPoints
        self.noAdjustHandles = noAdjustHandles
        self.noChangeArrowheads = noChangeArrowheads
        self.noChangeShapeType = noChangeShapeType


class NonVisualPictureProperties(Serialisable):

    tagname = "cNvPicPr"

    preferRelativeResize = Bool(allow_none=True)
    picLocks = Typed(expected_type=PictureLocking, allow_none=True)
    extLst = Typed(expected_type=OfficeArtExtensionList, allow_none=True)

    __elements__ = ("picLocks",)

    def __init__(self,
                 preferRelativeResize=None,
                 picLocks=None,
                 extLst=None,
                ):
        self.preferRelativeResize = preferRelativeResize
        self.picLocks = picLocks


class PictureNonVisual(Serialisable):

    tagname = "nvPicPr"

    cNvPr = Typed(expected_type=NonVisualDrawingProps, )
    cNvPicPr = Typed(expected_type=NonVisualPictureProperties, )

    __elements__ = ("cNvPr", "cNvPicPr")

    def __init__(self,
                 cNvPr=None,
                 cNvPicPr=None,
                ):
        if cNvPr is None:
            cNvPr = NonVisualDrawingProps(id=0, name="Image 1", descr="Name of file")
        self.cNvPr = cNvPr
        if cNvPicPr is None:
            cNvPicPr = NonVisualPictureProperties()
        self.cNvPicPr = cNvPicPr


class PictureFrame(Serialisable):

    tagname = "pic"

    macro = String(allow_none=True)
    fPublished = Bool(allow_none=True)
    nvPicPr = Typed(expected_type=PictureNonVisual, )
    blipFill = Typed(expected_type=BlipFillProperties, )
    spPr = Typed(expected_type=GraphicalProperties, )
    graphicalProperties = Alias('spPr')
    style = Typed(expected_type=ShapeStyle, allow_none=True)

    __elements__ = ("nvPicPr", "blipFill", "spPr", "style")

    def __init__(self,
                 macro=None,
                 fPublished=None,
                 nvPicPr=None,
                 blipFill=None,
                 spPr=None,
                 style=None,
                ):
        self.macro = macro
        self.fPublished = fPublished
        if nvPicPr is None:
            nvPicPr = PictureNonVisual()
        self.nvPicPr = nvPicPr
        if blipFill is None:
            blipFill = BlipFillProperties()
        self.blipFill = blipFill
        if spPr is None:
            spPr = GraphicalProperties()
        self.spPr = spPr
        self.style = style
