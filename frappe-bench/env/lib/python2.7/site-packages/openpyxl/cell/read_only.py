from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

import re

from openpyxl.compat import unicode, long

from openpyxl.cell import Cell
from openpyxl.utils import get_column_letter
from openpyxl.utils.datetime import from_excel
from openpyxl.styles import is_date_format
from openpyxl.styles.numbers import BUILTIN_FORMATS


FLOAT_REGEX = re.compile(r"\.|[E-e]")


def _cast_number(value):
    "Convert numbers as string to an int or float"
    m = FLOAT_REGEX.search(value)
    if m is not None:
        return float(value)
    return long(value)


class ReadOnlyCell(object):

    __slots__ =  ('parent', 'row', 'column', '_value', 'data_type', '_style_id')

    def __init__(self, sheet, row, column, value, data_type='n', style_id=0):
        self.parent = sheet
        self._value = None
        self.row = row
        self.column = column
        self.data_type = data_type
        self.value = value
        self._style_id = style_id

    def __eq__(self, other):
        for a in self.__slots__:
            if getattr(self, a) != getattr(other, a):
                return
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def shared_strings(self):
        return self.parent.shared_strings

    @property
    def base_date(self):
        return self.parent.base_date

    @property
    def coordinate(self):
        column = get_column_letter(self.column)
        return "{1}{0}".format(self.row, column)

    @property
    def style_array(self):
        return self.parent.parent._cell_styles[self._style_id]

    @property
    def number_format(self):
        _id = self.style_array.numFmtId
        if _id < 164:
            return BUILTIN_FORMATS.get(_id, "General")
        else:
            return self.parent.parent._number_formats[_id - 164]

    @property
    def font(self):
        _id = self.style_array.fontId
        return self.parent.parent._fonts[_id]

    @property
    def fill(self):
        _id = self.style_array.fillId
        return self.parent.parent._fills[_id]

    @property
    def border(self):
        _id = self.style_array.borderId
        return self.parent.parent._borders[_id]

    @property
    def alignment(self):
        _id = self.style_array.alignmentId
        return self.parent.parent._alignments[_id]

    @property
    def protection(self):
        _id = self.style_array.protectionId
        return self.parent.parent._protections[_id]

    @property
    def is_date(self):
        return self.data_type == 'n' and is_date_format(self.number_format)

    @property
    def internal_value(self):
        return self._value

    @property
    def value(self):
        if self._value is None:
            return
        if self.data_type == 'n':
            if self.style_array:
                if is_date_format(self.number_format):
                    return from_excel(self._value, self.base_date)
            return self._value
        if self.data_type == 'b':
            return self._value == '1'
        elif self.data_type in(Cell.TYPE_INLINE, Cell.TYPE_FORMULA_CACHE_STRING):
            return unicode(self._value)
        elif self.data_type == 's':
            return unicode(self.shared_strings[int(self._value)])
        return self._value

    @value.setter
    def value(self, value):
        if self._value is not None:
            raise AttributeError("Cell is read only")
        if value is None:
            self.data_type = 'n'
        elif self.data_type == 'n':
            value = _cast_number(value)
        self._value = value


class EmptyCell(object):

    __slots__ = ()

    value = None
    is_date = False
    font = None
    border = None
    fill = None
    number_format = None
    alignment = None
    data_type = 'n'


EMPTY_CELL = EmptyCell()
