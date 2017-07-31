from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

from itertools import chain

from openpyxl.compat import unicode
from openpyxl.descriptors.serialisable import Serialisable
from openpyxl.descriptors import (
    MinMax,
    Typed,
    String,
    Strict,
)
from openpyxl.worksheet import Worksheet
from openpyxl.utils import (
    get_column_letter,
    range_to_tuple,
    quote_sheetname
)


class DummyWorksheet:


    def __init__(self, title):
        self.title = title


class Reference(Strict):

    """
    Normalise cell range references
    """

    min_row = MinMax(min=1, max=1000000, expected_type=int)
    max_row = MinMax(min=1, max=1000000, expected_type=int)
    min_col = MinMax(min=1, max=16384, expected_type=int)
    max_col = MinMax(min=1, max=16384, expected_type=int)
    range_string = String(allow_none=True)

    def __init__(self,
                 worksheet=None,
                 min_col=None,
                 min_row=None,
                 max_col=None,
                 max_row=None,
                 range_string=None
                 ):
        if range_string is not None:
            sheetname, boundaries = range_to_tuple(range_string)
            min_col, min_row, max_col, max_row = boundaries
            worksheet = DummyWorksheet(sheetname)

        self.worksheet = worksheet
        self.min_col = min_col
        self.min_row = min_row
        if max_col is None:
            max_col = min_col
        self.max_col = max_col
        if max_row is None:
            max_row = min_row
        self.max_row = max_row


    def __repr__(self):
        return unicode(self)


    def __str__(self):
        fmt = u"{0}!${1}${2}:${3}${4}"
        if (self.min_col == self.max_col
            and self.min_row == self.max_row):
            fmt = u"{0}!${1}${2}"
        return fmt.format(self.sheetname,
                          get_column_letter(self.min_col), self.min_row,
                          get_column_letter(self.max_col), self.max_row
                          )


    __unicode__ = __str__



    def __len__(self):
        if self.min_row == self.max_row:
            return 1 + self.max_col - self.min_col
        return 1 + self.max_row - self.min_row


    @property
    def rows(self):
        """
        Return all cells in range by column
        """
        for row in range(self.min_row, self.max_row+1):
            yield tuple('%s%d' % (get_column_letter(col), row)
                    for col in range(self.min_col, self.max_col+1))


    @property
    def cols(self):
        """
        Return all cells in range by row
        """
        for col in range(self.min_col, self.max_col+1):
            yield tuple('%s%d' % (get_column_letter(col), row)
                        for row in range(self.min_row, self.max_row+1))


    @property
    def cells(self):
        """
        Return a flattened list of all cells (by column)
        """
        return chain.from_iterable(self.cols)


    def pop(self):
        """
        Return and remove the first cell
        """
        cell = next(self.cells)
        if self.min_row == self.max_row:
            self.min_col += 1
        else:
            self.min_row += 1
        return cell


    @property
    def sheetname(self):
        return quote_sheetname(self.worksheet.title)
