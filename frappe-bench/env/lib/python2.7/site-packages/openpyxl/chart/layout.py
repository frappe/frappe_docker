from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

from openpyxl.descriptors.serialisable import Serialisable
from openpyxl.descriptors import (
    NoneSet,
    Float,
    Typed,
    Alias,
)

from openpyxl.descriptors.excel import ExtensionList
from openpyxl.descriptors.nested import (
    NestedNoneSet,
    NestedFloat

)

class ManualLayout(Serialisable):

    tagname = "manualLayout"

    layoutTarget = NestedNoneSet(values=(['inner', 'outer']))
    xMode = NestedNoneSet(values=(['edge', 'factor']))
    yMode = NestedNoneSet(values=(['edge', 'factor']))
    wMode = NestedNoneSet(values=(['edge', 'factor']))
    hMode = NestedNoneSet(values=(['edge', 'factor']))
    x = NestedFloat(allow_none=True)
    y = NestedFloat(allow_none=True)
    w = NestedFloat(allow_none=True)
    width = Alias('w')
    h = NestedFloat(allow_none=True)
    height = Alias('h')
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('layoutTarget', 'xMode', 'yMode', 'wMode', 'hMode', 'x',
                    'y', 'w', 'h')

    def __init__(self,
                 layoutTarget=None,
                 xMode=None,
                 yMode=None,
                 wMode=None,
                 hMode=None,
                 x=None,
                 y=None,
                 w=None,
                 h=None,
                 extLst=None,
                ):
        self.layoutTarget = layoutTarget
        self.xMode = xMode
        self.yMode = yMode
        self.wMode = wMode
        self.hMode = hMode
        self.x = x
        self.y = y
        self.w = w
        self.h = h


class Layout(Serialisable):

    tagname = "layout"

    manualLayout = Typed(expected_type=ManualLayout, allow_none=True)
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('manualLayout',)

    def __init__(self,
                 manualLayout=None,
                 extLst=None,
                ):
        self.manualLayout = manualLayout
