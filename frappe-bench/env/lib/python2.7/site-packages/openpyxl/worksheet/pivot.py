from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

from openpyxl.descriptors import (
    Bool,
    Integer,
    String,
    Set,
    NoneSet,
)
from openpyxl.descriptors.serialisable import Serialisable


class PivotSelection(Serialisable):

    pane = Set(values=("bottomRight", "topRight", "bottomLeft", "topLeft"))
    showHeader = Bool()
    label = Bool()
    data = Bool()
    extendable = Bool()
    count = Integer()
    axis = String(allow_none=True)
    dimension = Integer()
    start = Integer()
    min = Integer()
    max = Integer()
    activeRow = Integer()
    activeCol = Integer()
    previousRow = Integer()
    previousCol = Integer()
    click = Integer()

    def __init__(self,
                 pane=None,
                 showHeader=None,
                 label=None,
                 data=None,
                 extendable=None,
                 count=None,
                 axis=None,
                 dimension=None,
                 start=None,
                 min=None,
                 max=None,
                 activeRow=None,
                 activeCol=None,
                 previousRow=None,
                 previousCol=None,
                 click=None):
        self.pane = pane
        self.showHeader = showHeader
        self.label = label
        self.data = data
        self.extendable = extendable
        self.count = count
        self.axis = axis
        self.dimension = dimension
        self.start = start
        self.min = min
        self.max = max
        self.activeRow = activeRow
        self.activeCol = activeCol
        self.previousRow = previousRow
        self.previousCol = previousCol
        self.click = click


class PivotArea(Serialisable):

    field = Integer(allow_none=True)
    type = NoneSet(values=("normal", "data", "all", "origin", "button", "topEnd"))
    dataOnly = Bool()
    labelOnly = Bool()
    grandRow = Bool()
    grandCol = Bool()
    cacheIndex = Bool()
    outline = Bool()
    offset = String()
    collapsedLevelsAreSubtotals = Bool()
    axis = String(allow_none=True)
    fieldPosition = Integer(allow_none=True)

    def __init__(self,
                 field=None,
                 type=None,
                 dataOnly=None,
                 labelOnly=None,
                 grandRow=None,
                 grandCol=None,
                 cacheIndex=None,
                 outline=None,
                 offset=None,
                 collapsedLevelsAreSubtotals=None,
                 axis=None,
                 fieldPosition=None):
        self.field = field
        self.type = type
        self.dataOnly = dataOnly
        self.labelOnly = labelOnly
        self.grandRow = grandRow
        self.grandCol = grandCol
        self.cacheIndex = cacheIndex
        self.outline = outline
        self.offset = offset
        self.collapsedLevelsAreSubtotals = collapsedLevelsAreSubtotals
        self.axis = axis
        self.fieldPosition = fieldPosition


class PivotAreaReferences(Serialisable):

    count = Integer()

    def __init__(self, count=None):
        count = count


class PivotAreaReference(Serialisable):

    field = Integer(allow_none=True)
    count = Integer()
    selected = Bool()
    byPosition = Bool()
    relative = Bool()
    defaultSubtotal = Bool()
    sumSubtotal = Bool()
    countASubtotal = Bool()
    avgSubtotal = Bool()
    maxSubtotal = Bool()
    minSubtotal = Bool()
    productSubtotal = Bool()
    countSubtotal = Bool()
    stdDevSubtotal = Bool()
    stdDevPSubtotal = Bool()
    varSubtotal = Bool()
    varPSubtotal = Bool()

    def __init__(self,
                 field=None,
                 count=None,
                 selected=None,
                 byPosition=None,
                 relative=None,
                 defaultSubtotal=None,
                 sumSubtotal=None,
                 countASubtotal=None,
                 avgSubtotal=None,
                 maxSubtotal=None,
                 minSubtotal=None,
                 productSubtotal=None,
                 countSubtotal=None,
                 stdDevSubtotal=None,
                 stdDevPSubtotal=None,
                 varSubtotal=None,
                 varPSubtotal=None):
        self.field = field
        self.count = count
        self.selected = selected
        self.byPosition = byPosition
        self.relative = relative
        self.defaultSubtotal = defaultSubtotal
        self.sumSubtotal = sumSubtotal
        self.countASubtotal = countASubtotal
        self.avgSubtotal = avgSubtotal
        self.maxSubtotal = maxSubtotal
        self.minSubtotal = minSubtotal
        self.productSubtotal = productSubtotal
        self.countSubtotal = countSubtotal
        self.stdDevSubtotal = stdDevSubtotal
        self.stdDevPSubtotal = stdDevPSubtotal
        self.varSubtotal = varSubtotal
        self.varPSubtotal = varPSubtotal


class Index(Serialisable):
    v = Integer()

    def __init__(self, v=None):
        self.v = v
