from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

from openpyxl.descriptors import (
    Float,
    Set,
    Alias,
    NoneSet,
    Sequence,
    Integer,
)
from openpyxl.descriptors.serialisable import Serialisable
from openpyxl.descriptors.sequence import ValueSequence
from openpyxl.compat import safe_string

from .colors import ColorDescriptor, Color

from openpyxl.xml.functions import Element, localname, safe_iterator
from openpyxl.xml.constants import SHEET_MAIN_NS


FILL_NONE = 'none'
FILL_SOLID = 'solid'
FILL_PATTERN_DARKDOWN = 'darkDown'
FILL_PATTERN_DARKGRAY = 'darkGray'
FILL_PATTERN_DARKGRID = 'darkGrid'
FILL_PATTERN_DARKHORIZONTAL = 'darkHorizontal'
FILL_PATTERN_DARKTRELLIS = 'darkTrellis'
FILL_PATTERN_DARKUP = 'darkUp'
FILL_PATTERN_DARKVERTICAL = 'darkVertical'
FILL_PATTERN_GRAY0625 = 'gray0625'
FILL_PATTERN_GRAY125 = 'gray125'
FILL_PATTERN_LIGHTDOWN = 'lightDown'
FILL_PATTERN_LIGHTGRAY = 'lightGray'
FILL_PATTERN_LIGHTGRID = 'lightGrid'
FILL_PATTERN_LIGHTHORIZONTAL = 'lightHorizontal'
FILL_PATTERN_LIGHTTRELLIS = 'lightTrellis'
FILL_PATTERN_LIGHTUP = 'lightUp'
FILL_PATTERN_LIGHTVERTICAL = 'lightVertical'
FILL_PATTERN_MEDIUMGRAY = 'mediumGray'

fills = (FILL_SOLID, FILL_PATTERN_DARKDOWN, FILL_PATTERN_DARKGRAY,
         FILL_PATTERN_DARKGRID, FILL_PATTERN_DARKHORIZONTAL, FILL_PATTERN_DARKTRELLIS,
         FILL_PATTERN_DARKUP, FILL_PATTERN_DARKVERTICAL, FILL_PATTERN_GRAY0625,
         FILL_PATTERN_GRAY125, FILL_PATTERN_LIGHTDOWN, FILL_PATTERN_LIGHTGRAY,
         FILL_PATTERN_LIGHTGRID, FILL_PATTERN_LIGHTHORIZONTAL,
         FILL_PATTERN_LIGHTTRELLIS, FILL_PATTERN_LIGHTUP, FILL_PATTERN_LIGHTVERTICAL,
         FILL_PATTERN_MEDIUMGRAY)


class Fill(Serialisable):

    """Base class"""

    tagname = "fill"

    @classmethod
    def from_tree(cls, el):
        children = [c for c in el]
        if not children:
            return
        child = children[0]
        if "patternFill" in child.tag:
            return PatternFill._from_tree(child)
        else:
            return GradientFill._from_tree(child)


class PatternFill(Fill):
    """Area fill patterns for use in styles.
    Caution: if you do not specify a fill_type, other attributes will have
    no effect !"""

    tagname = "patternFill"

    __elements__ = ('fgColor', 'bgColor')

    patternType = NoneSet(values=fills)
    fill_type = Alias("patternType")
    fgColor = ColorDescriptor()
    start_color = Alias("fgColor")
    bgColor = ColorDescriptor()
    end_color = Alias("bgColor")

    def __init__(self, patternType=None, fgColor=Color(), bgColor=Color(),
                 fill_type=None, start_color=None, end_color=None):
        if fill_type is not None:
            patternType = fill_type
        self.patternType = patternType
        if start_color is not None:
            fgColor = start_color
        self.fgColor = fgColor
        if end_color is not None:
            bgColor = end_color
        self.bgColor = bgColor

    @classmethod
    def _from_tree(cls, el):
        attrib = dict(el.attrib)
        for child in el:
            desc = localname(child)
            attrib[desc] = Color.from_tree(child)
        return cls(**attrib)


    def to_tree(self, tagname=None, idx=None):
        parent = Element("fill")
        el = Element(self.tagname)
        if self.patternType is not None:
            el.set('patternType', self.patternType)
        for c in self.__elements__:
            value = getattr(self, c)
            if value != Color():
                el.append(value.to_tree(c))
        parent.append(el)
        return parent


DEFAULT_EMPTY_FILL = PatternFill()
DEFAULT_GRAY_FILL = PatternFill(patternType='gray125')


def _serialise_stop(tagname, sequence, namespace=None):
    for idx, color in enumerate(sequence):
        stop = Element("stop", position=str(idx))
        stop.append(color.to_tree())
        yield stop


class GradientFill(Fill):

    tagname = "gradientFill"

    type = Set(values=('linear', 'path'))
    fill_type = Alias("type")
    degree = Float()
    left = Float()
    right = Float()
    top = Float()
    bottom = Float()
    stop = ValueSequence(expected_type=Color, to_tree=_serialise_stop)


    def __init__(self, type="linear", degree=0, left=0, right=0, top=0,
                 bottom=0, stop=(), fill_type=None):
        self.degree = degree
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.stop = stop
        if fill_type is not None:
            type = fill_type
        self.type = type


    def __iter__(self):
        for attr in self.__attrs__:
            value = getattr(self, attr)
            if value:
                yield attr, safe_string(value)


    @classmethod
    def _from_tree(cls, node):
        colors = []
        for color in safe_iterator(node, "{%s}color" % SHEET_MAIN_NS):
            colors.append(Color.from_tree(color))
        return cls(stop=colors, **node.attrib)


    def to_tree(self, tagname=None, namespace=None, idx=None):
        parent = Element("fill")
        el = super(GradientFill, self).to_tree()
        parent.append(el)
        return parent
