from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl
from openpyxl.descriptors.serialisable import Serialisable
from openpyxl.descriptors import (
    Typed,
    Alias,
    Sequence,
)


from openpyxl.drawing.text import (
    RichTextProperties,
    ListStyle,
    Paragraph,
)

from .data_source import StrRef


class RichText(Serialisable):

    """
    From the specification: 21.2.2.216

    This element specifies text formatting. The lstStyle element is not supported.
    """

    tagname = "rich"

    bodyPr = Typed(expected_type=RichTextProperties)
    properties = Alias("bodyPr")
    lstStyle = Typed(expected_type=ListStyle, allow_none=True)
    p = Sequence(expected_type=Paragraph, allow_none=True)
    paragraphs = Alias('p')

    __elements__ = ("bodyPr", "lstStyle", "p")

    def __init__(self,
                 bodyPr=None,
                 lstStyle=None,
                 p=None,
                ):
        if bodyPr is None:
            bodyPr = RichTextProperties()
        self.bodyPr = bodyPr
        self.lstStyle = lstStyle
        if p is None:
            p = [Paragraph()]
        self.p = p


class Text(Serialisable):

    strRef = Typed(expected_type=StrRef, allow_none=True)
    rich = Typed(expected_type=RichText, allow_none=True)

    __elements__ = ("strRef", "rich")

    def __init__(self,
                 strRef=None,
                 rich=None
                 ):
        self.strRef = strRef
        if rich is None:
            rich = RichText()
        self.rich = rich
