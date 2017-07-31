"""
Collection of utility primitives for charts.
"""

from openpyxl.compat import unicode
from openpyxl.descriptors.serialisable import Serialisable
from openpyxl.descriptors import (
    Bool,
    Typed,
    Alias,
    String,
    Integer,
    Sequence,
)
from openpyxl.descriptors.excel import ExtensionList
from openpyxl.descriptors.nested import (
    NestedString,
    NestedText,
    NestedInteger,
)


class NumFmt(Serialisable):

    formatCode = String()
    sourceLinked = Bool()

    def __init__(self,
                 formatCode=None,
                 sourceLinked=False
                ):
        self.formatCode = formatCode
        self.sourceLinked = sourceLinked


class NumVal(Serialisable):

    idx = Integer()
    formatCode = NestedText(allow_none=True, expected_type=unicode)
    v = NestedText(allow_none=True, expected_type=float)

    def __init__(self,
                 idx=None,
                 formatCode=None,
                 v=None,
                ):
        self.idx = idx
        self.formatCode = formatCode
        self.v = v


class NumData(Serialisable):

    formatCode = NestedText(expected_type=str, allow_none=True)
    ptCount = NestedInteger(allow_none=True)
    pt = Sequence(expected_type=NumVal)
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('formatCode', 'ptCount', 'pt')

    def __init__(self,
                 formatCode=None,
                 ptCount=None,
                 pt=(),
                 extLst=None,
                ):
        self.formatCode = formatCode
        self.ptCount = ptCount
        self.pt = pt


class NumRef(Serialisable):

    f = NestedText(expected_type=unicode)
    ref = Alias('f')
    numCache = Typed(expected_type=NumData, allow_none=True)
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('f', 'numCache')

    def __init__(self,
                 f=None,
                 numCache=None,
                 extLst=None,
                ):
        self.f = f
        self.numCache = numCache


class StrVal(Serialisable):

    tagname = "strVal"

    idx = Integer()
    v = NestedText(expected_type=unicode)

    def __init__(self,
                 idx=0,
                 v=None,
                ):
        self.idx = idx
        self.v = v


class StrData(Serialisable):

    tagname = "strData"

    ptCount = NestedInteger(allow_none=True)
    pt = Typed(expected_type=StrVal, allow_none=True)
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('ptCount', 'pt')

    def __init__(self,
                 ptCount=None,
                 pt=None,
                 extLst=None,
                ):
        self.ptCount = ptCount
        self.pt = pt


class StrRef(Serialisable):

    tagname = "strRef"

    f = NestedText(expected_type=unicode, allow_none=True)
    strCache = Typed(expected_type=StrData, allow_none=True)
    extLst = Typed(expected_type=ExtensionList, allow_none=True)

    __elements__ = ('f', 'strCache')

    def __init__(self,
                 f=None,
                 strCache=None,
                 extLst=None,
                ):
        self.f = f
        self.strCache = strCache


class NumDataSource(Serialisable):

    numRef = Typed(expected_type=NumRef, allow_none=True)
    numLit = Typed(expected_type=NumData, allow_none=True)


    def __init__(self,
                 numRef=None,
                 numLit=None,
                 ):
        self.numRef = numRef
        self.numLit = numLit


class AxDataSource(Serialisable):

    numRef = Typed(expected_type=NumRef, allow_none=True)
    numLit = Typed(expected_type=NumData, allow_none=True)
    strRef = Typed(expected_type=StrRef, allow_none=True)
    strLit = Typed(expected_type=StrData, allow_none=True)

    def __init__(self,
                 numRef=None,
                 numLit=None,
                 strRef=None,
                 strLit=None,
                 ):
        self.numRef = numRef
        self.numLit = numLit
        self.strRef = strRef
        self.strLit = strLit
