from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

""" Read worksheets on-demand
"""

# compatibility
from openpyxl.compat import (
    range,
    deprecated
)

# package
from openpyxl.cell.text import Text

from openpyxl.xml.functions import iterparse, safe_iterator
from openpyxl.xml.constants import SHEET_MAIN_NS

from openpyxl.worksheet import Worksheet
from openpyxl.utils import (
    column_index_from_string,
    get_column_letter,
    coordinate_to_tuple,
)
from openpyxl.worksheet.dimensions import SheetDimension
from openpyxl.cell.read_only import ReadOnlyCell, EMPTY_CELL


def read_dimension(source):
    if hasattr(source, "encode"):
        return

    min_row = min_col =  max_row = max_col = None
    DIMENSION_TAG = '{%s}dimension' % SHEET_MAIN_NS
    DATA_TAG = '{%s}sheetData' % SHEET_MAIN_NS
    it = iterparse(source, tag=[DIMENSION_TAG, DATA_TAG])

    for _event, element in it:
        if element.tag == DIMENSION_TAG:
            dim = SheetDimension.from_tree(element)
            return dim.boundaries

        elif element.tag == DATA_TAG:
            # Dimensions missing
            break
        element.clear()


ROW_TAG = '{%s}row' % SHEET_MAIN_NS
CELL_TAG = '{%s}c' % SHEET_MAIN_NS
VALUE_TAG = '{%s}v' % SHEET_MAIN_NS
FORMULA_TAG = '{%s}f' % SHEET_MAIN_NS
INLINE_TAG = '{%s}is' % SHEET_MAIN_NS
DIMENSION_TAG = '{%s}dimension' % SHEET_MAIN_NS


class ReadOnlyWorksheet(object):

    _xml = None
    _min_column = 1
    _min_row = 1
    _max_column = _max_row = None

    def __init__(self, parent_workbook, title, worksheet_path,
                 xml_source, shared_strings):
        self.parent = parent_workbook
        self.title = title
        self._current_row = None
        self.worksheet_path = worksheet_path
        self.shared_strings = shared_strings
        self.base_date = parent_workbook.excel_base_date
        self.xml_source = xml_source
        dimensions = read_dimension(self.xml_source)
        if dimensions is not None:
            self.min_column, self.min_row, self.max_column, self.max_row = dimensions

        # Methods from Worksheet
        self.cell = Worksheet.cell.__get__(self)
        self.iter_rows = Worksheet.iter_rows.__get__(self)


    def __getitem__(self, key):
        # use protected method from Worksheet
        meth = Worksheet.__getitem__.__get__(self)
        return meth(key)


    @property
    def xml_source(self):
        """Parse xml source on demand, default to Excel archive"""
        if self._xml is None:
            return self.parent._archive.open(self.worksheet_path)
        return self._xml


    @xml_source.setter
    def xml_source(self, value):
        self._xml = value


    @deprecated("Use ws.iter_rows()")
    def get_squared_range(self, min_col, min_row, max_col, max_row):
        return self._cells_by_row(min_col, min_row, max_col, max_row)


    def _cells_by_row(self, min_col, min_row, max_col, max_row):
        """
        The source worksheet file may have columns or rows missing.
        Missing cells will be created.
        """
        if max_col is not None:
            empty_row = tuple(EMPTY_CELL for column in range(min_col, max_col + 1))
        else:
            empty_row = []
        row_counter = min_row

        p = iterparse(self.xml_source, tag=[ROW_TAG], remove_blank_text=True)
        for _event, element in p:
            if element.tag == ROW_TAG:
                row_id = int(element.get("r", row_counter))

                # got all the rows we need
                if max_row is not None and row_id > max_row:
                    break

                # some rows are missing
                for row_counter in range(row_counter, row_id):
                    row_counter += 1
                    yield empty_row

                # return cells from a row
                if min_row <= row_id:
                    yield tuple(self._get_row(element, min_col, max_col, row_counter=row_counter))
                    row_counter += 1

                element.clear()


    def _get_row(self, element, min_col=1, max_col=None, row_counter=None):
        """Return cells from a particular row"""
        col_counter = min_col
        data_only = getattr(self.parent, 'data_only', False)

        for cell in safe_iterator(element, CELL_TAG):
            coordinate = cell.get('r')
            if coordinate:
                row, column = coordinate_to_tuple(coordinate)
            else:
                row, column = row_counter, col_counter

            if max_col is not None and column > max_col:
                break

            if min_col <= column:
                if col_counter < column:
                    for col_counter in range(max(col_counter, min_col), column):
                        # pad row with missing cells
                        yield EMPTY_CELL

                data_type = cell.get('t', 'n')
                style_id = int(cell.get('s', 0))
                value = None

                formula = cell.findtext(FORMULA_TAG)
                if formula is not None and not data_only:
                    data_type = 'f'
                    value = "=%s" % formula

                elif data_type == 'inlineStr':
                    child = cell.find(INLINE_TAG)
                    if child is not None:
                        richtext = Text.from_tree(child)
                        value = richtext.content

                else:
                    value = cell.findtext(VALUE_TAG) or None

                yield ReadOnlyCell(self, row, column,
                                   value, data_type, style_id)
            col_counter = column + 1

        if max_col is not None:
            for _ in range(col_counter, max_col+1):
                yield EMPTY_CELL


    def _get_cell(self, row, column):
        """Cells are returned by a generator which can be empty"""
        for row in self.get_squared_range(column, row, column, row):
            if row:
                return row[0]
        return EMPTY_CELL


    @property
    def rows(self):
        return self.iter_rows()


    def __iter__(self):
        return self.iter_rows()


    def calculate_dimension(self, force=False):
        if not all([self.max_column, self.max_row]):
            if force:
                self._calculate_dimension()
            else:
                raise ValueError("Worksheet is unsized, use calculate_dimension(force=True)")
        return '%s%d:%s%d' % (
           get_column_letter(self.min_column), self.min_row,
           get_column_letter(self.max_column), self.max_row
       )


    def _calculate_dimension(self):
        """
        Loop through all the cells to get the size of a worksheet.
        Do this only if it is explicitly requested.
        """

        max_col = 0
        for r in self.rows:
            if not r:
                continue
            cell = r[-1]
            max_col = max(max_col, cell.column)

        self.max_row = cell.row
        self.max_column = max_col


    @property
    def min_row(self):
        return self._min_row

    @min_row.setter
    def min_row(self, value):
        self._min_row = value


    @property
    def max_row(self):
        return self._max_row

    @max_row.setter
    def max_row(self, value):
        self._max_row = value


    @property
    def min_column(self):
        return self._min_column

    @min_column.setter
    def min_column(self, value):
        self._min_column = value


    @property
    def max_column(self):
        return self._max_column


    @max_column.setter
    def max_column(self, value):
        self._max_column = value
