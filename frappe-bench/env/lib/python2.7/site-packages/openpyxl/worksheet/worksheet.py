from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""Worksheet is the 2nd-level container in Excel."""


# Python stdlib imports
from itertools import islice, product
import re
from inspect import isgenerator
from warnings import warn

# compatibility imports
from openpyxl.compat import (
    unicode,
    range,
    basestring,
    deprecated,
    safe_string
)

# package imports
from openpyxl.utils import (
    coordinate_from_string,
    column_index_from_string,
    get_column_letter,
    range_boundaries,
    rows_from_range,
    coordinate_to_tuple,
    absolute_coordinate,
)
from openpyxl.utils.cell import COORD_RE

from openpyxl.cell import Cell
from openpyxl.utils.exceptions import (
    SheetTitleException,
    InsufficientCoordinatesException,
    NamedRangeException
)
from openpyxl.utils.units import (
    points_to_pixels,
    DEFAULT_COLUMN_WIDTH,
    DEFAULT_ROW_HEIGHT,
)
from openpyxl.formatting.formatting import ConditionalFormattingList
from openpyxl.packaging.relationship import RelationshipList
from openpyxl.workbook.child import _WorkbookChild
from openpyxl.workbook.defined_name import COL_RANGE_RE, ROW_RANGE_RE
from openpyxl.utils.bound_dictionary import BoundDictionary

from .datavalidation import DataValidationList
from .page import (
    PrintPageSetup,
    PageMargins,
    PrintOptions,
)
from .dimensions import (
    ColumnDimension,
    RowDimension,
    DimensionHolder,
    SheetFormatProperties,
)
from .protection import SheetProtection
from .filters import AutoFilter, SortState
from .views import (
    SheetView,
    Pane,
    Selection,
    SheetViewList,
)
from .properties import WorksheetProperties
from .pagebreak import PageBreak


@deprecated("Use the worksheet.values property")
def flatten(results):
    """Return cell values row-by-row"""

    for row in results:
        yield(c.value for c in row)


class Worksheet(_WorkbookChild):
    """Represents a worksheet.

    Do not create worksheets yourself,
    use :func:`openpyxl.workbook.Workbook.create_sheet` instead

    """

    _rel_type = "worksheet"
    _path = "/xl/worksheets/sheet{0}.xml"
    mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"

    BREAK_NONE = 0
    BREAK_ROW = 1
    BREAK_COLUMN = 2

    SHEETSTATE_VISIBLE = 'visible'
    SHEETSTATE_HIDDEN = 'hidden'
    SHEETSTATE_VERYHIDDEN = 'veryHidden'

    # Paper size
    PAPERSIZE_LETTER = '1'
    PAPERSIZE_LETTER_SMALL = '2'
    PAPERSIZE_TABLOID = '3'
    PAPERSIZE_LEDGER = '4'
    PAPERSIZE_LEGAL = '5'
    PAPERSIZE_STATEMENT = '6'
    PAPERSIZE_EXECUTIVE = '7'
    PAPERSIZE_A3 = '8'
    PAPERSIZE_A4 = '9'
    PAPERSIZE_A4_SMALL = '10'
    PAPERSIZE_A5 = '11'

    # Page orientation
    ORIENTATION_PORTRAIT = 'portrait'
    ORIENTATION_LANDSCAPE = 'landscape'

    def __init__(self, parent, title=None):
        _WorkbookChild.__init__(self, parent, title)
        self._setup()

    def _setup(self):
        self.row_dimensions = BoundDictionary("index", self._add_row)
        self.column_dimensions = DimensionHolder(worksheet=self,
                                                 default_factory=self._add_column)
        self.page_breaks = PageBreak()
        self._cells = {}
        self._charts = []
        self._images = []
        self._rels = RelationshipList()
        self._drawing = None
        self._comments = []
        self._merged_cells = []
        self._tables = []
        self.data_validations = DataValidationList()
        self._hyperlinks = []
        self.sheet_state = 'visible'
        self.page_setup = PrintPageSetup(worksheet=self)
        self.print_options = PrintOptions()
        self._print_rows = None
        self._print_cols = None
        self._print_area = None
        self.page_margins = PageMargins()
        self.views = SheetViewList()
        self.protection = SheetProtection()

        self._current_row = 0
        self.auto_filter = AutoFilter()
        self.sort_state = SortState()
        self.paper_size = None
        self.formula_attributes = {}
        self.orientation = None
        self.conditional_formatting = ConditionalFormattingList()
        self.legacy_drawing = None
        self.sheet_properties = WorksheetProperties()
        self.sheet_format = SheetFormatProperties()


    @property
    def sheet_view(self):
        return self.views.sheetView[0]


    @property
    def selected_cell(self):
        return self.sheet_view.selection.sqref


    @property
    def active_cell(self):
        return self.sheet_view.selection.activeCell

    @property
    def show_gridlines(self):
        return self.sheet_view.showGridLines


    """ To keep compatibility with previous versions"""
    @property
    def show_summary_below(self):
        return self.sheet_properties.outlinePr.summaryBelow

    @property
    def show_summary_right(self):
        return self.sheet_properties.outlinePr.summaryRight

    @property
    def vba_code(self):
        for attr in ("codeName", "enableFormatConditionsCalculation",
                     "filterMode", "published", "syncHorizontal", "syncRef",
                     "syncVertical", "transitionEvaluation", "transitionEntry"):
            value = getattr(self.sheet_properties, attr)
            if value is not None:
                yield attr, safe_string(value)

    @vba_code.setter
    def vba_code(self, value):
        for k, v in value.items():
            if k in ("codeName", "enableFormatConditionsCalculation",
                     "filterMode", "published", "syncHorizontal", "syncRef",
                     "syncVertical", "transitionEvaluation", "transitionEntry"):
                setattr(self.sheet_properties, k, v)

    """ End To keep compatibility with previous versions"""


    @deprecated("Use the ws.values property")
    def get_cell_collection(self):
        """Return an unordered list of the cells in this worksheet."""
        return self._cells.values()


    @property
    def freeze_panes(self):
        if self.sheet_view.pane is not None:
            return self.sheet_view.pane.topLeftCell

    @freeze_panes.setter
    def freeze_panes(self, topLeftCell=None):
        if isinstance(topLeftCell, Cell):
            topLeftCell = topLeftCell.coordinate
        if topLeftCell == 'A1':
            topLeftCell = None

        if not topLeftCell:
            self.sheet_view.pane = None
            return

        row, column = coordinate_to_tuple(topLeftCell)

        view = self.sheet_view
        view.pane = Pane(topLeftCell=topLeftCell,
                        activePane="topRight",
                        state="frozen")
        view.selection[0].pane = "topRight"

        if column > 1:
            view.pane.xSplit = column - 1
        if row > 1:
            view.pane.ySplit = row - 1
            view.pane.activePane = 'bottomLeft'
            view.selection[0].pane = "bottomLeft"
            if column > 1:
                view.selection[0].pane = "bottomRight"
                view.pane.activePane = 'bottomRight'

        if row > 1 and column > 1:
            sel = list(view.selection)
            sel.insert(0, Selection(pane="topRight", activeCell=None, sqref=None))
            sel.insert(1, Selection(pane="bottomLeft", activeCell=None, sqref=None))
            view.selection = sel


    @deprecated("Set print titles rows or columns directly")
    def add_print_title(self, n, rows_or_cols='rows'):
        """ Print Titles are rows or columns that are repeated on each printed sheet.
        This adds n rows or columns at the top or left of the sheet
        """

        scope = self.parent.get_index(self)

        if rows_or_cols == 'cols':
            self.print_title_cols = 'A:%s' % get_column_letter(n)

        else:
            self.print_title_rows = '1:%d' % n


    def cell(self, coordinate=None, row=None, column=None, value=None):
        """Returns a cell object based on the given coordinates.

        Usage: cell(row=15, column=1, value=5)

        Calling `cell` creates cells in memory when they
        are first accessed.

        :param row: row index of the cell (e.g. 4)
        :type row: int

        :param column: column index of the cell (e.g. 3)
        :type column: int

        :param coordinate: coordinates of the cell (e.g. 'B12')
        :type coordinate: string

        :param value: value of the cell (e.g. 5)
        :type value: numeric or time or string or bool or none

        :raise: InsufficientCoordinatesException when neither row nor column are not given

        :rtype: openpyxl.cell.Cell

        """

        if (row is None or column is None) and coordinate is None:
            msg = "You have to provide a value either for " \
                   "'coordinate' or for 'row' *and* 'column'"
            raise InsufficientCoordinatesException(msg)

        if coordinate is not None:
            warn("Using a coordinate with ws.cell is deprecated. Use ws[coordinate] instead")
            row, column = coordinate_to_tuple(coordinate)

        if row < 1 or column < 1:
            raise ValueError("Row or column values must be at least 1")

        cell = self._get_cell(row, column)
        if value is not None:
            cell.value = value

        return cell


    def _get_cell(self, row, column):
        """
        Internal method for getting a cell from a worksheet.
        Will create a new cell if one doesn't already exist.
        """
        coordinate = (row, column)
        if not coordinate in self._cells:
            cell = Cell(self, row=row, col_idx=column)
            self._add_cell(cell)
        return self._cells[coordinate]


    def _add_cell(self, cell):
        """
        Internal method for adding cell objects.
        """
        column = cell.col_idx
        row = cell.row
        self._current_row = max(row, self._current_row)
        self._cells[(row, column)] = cell


    def __getitem__(self, key):
        """Convenience access by Excel style coordinates

        The key can be a single cell coordinate 'A1', a range of cells 'A1:D25',
        individual rows or columns 'A', 4 or ranges of rows or columns 'A:D',
        4:10.

        Single cells will always be created if they do not exist.

        Returns either a single cell or a tuple of rows or columns.
        """
        if isinstance(key, slice):
            if not all([key.start, key.stop]):
                raise IndexError("{0} is not a valid coordinate or range".format(key))
            key = "{0}:{1}".format(key.start, key.stop)

        if isinstance(key, int):
            key = str(key
                      )
        min_col, min_row, max_col, max_row = range_boundaries(key)

        if not any([min_col, min_row, max_col, max_row]):
            raise IndexError("{0} is not a valid coordinate or range".format(key))

        if not min_row:
            cols = tuple(self.iter_cols(min_col, max_col))
            if min_col == max_col:
                cols = cols[0]
            return cols
        if not min_col:
            rows = tuple(self.iter_rows(min_col=min_col, min_row=min_row,
                                        max_col=self.max_column, max_row=max_row))
            if min_row == max_row:
                rows = rows[0]
            return rows
        if ":" not in key:
            return self._get_cell(min_row, min_col)
        return tuple(self.iter_rows(min_row=min_row, min_col=min_col,
                                    max_row=max_row, max_col=max_col))


    def __setitem__(self, key, value):
        self[key].value = value


    def __iter__(self):
        return self.iter_rows()


    @property
    def min_row(self):
        min_row = 1
        if self._cells:
            rows = set(c[0] for c in self._cells)
            min_row = min(rows)
        return min_row


    @property
    def max_row(self):
        """Returns the maximum row index containing data

        :rtype: int
        """
        max_row = 1
        if self._cells:
            rows = set(c[0] for c in self._cells)
            max_row = max(rows)
        return max_row


    @property
    def min_column(self):
        min_col = 1
        if self._cells:
            cols = set(c[1] for c in self._cells)
            min_col = min(cols)
        return min_col


    @property
    def max_column(self):
        """Get the largest value for column currently stored.

        :rtype: int
        """
        max_col = 1
        if self._cells:
            cols = set(c[1] for c in self._cells)
            max_col = max(cols)
        return max_col


    def calculate_dimension(self):
        """Return the minimum bounding range for all cells containing data."""
        if self._cells:
            rows = set()
            cols = set()
            for row, col in self._cells:
                rows.add(row)
                cols.add(col)
            max_row = max(rows)
            max_col = max(cols)
            min_col = min(cols)
            min_row = min(rows)
        else:
            return "A1:A1"

        return '%s%d:%s%d' % (
            get_column_letter(min_col), min_row,
            get_column_letter(max_col), max_row
        )


    @property
    def dimensions(self):
        return self.calculate_dimension()


    def iter_rows(self, range_string=None, min_row=None, max_row=None, min_col=None, max_col=None,
                  row_offset=0, column_offset=0):
        """
        Return cells from the worksheet as rows. Boundaries for the cells can
        be passed in either as indices of rows and columns.

        If no boundaries are passed in the cells will start at A1.

        If no cells are in the worksheet an empty tuple will be returned.


        Additional rows and columns can be created using offsets.

        :param range_string: range string (e.g. 'A1:B2') *deprecated*
        :type range_string: string

        :param min_col: smallest column index (1-based index)
        :type min_col: int

        :param min_row: smallest row index (1-based index)
        :type min_row: int

        :param max_col: largest column index (1-based index)
        :type max_col: int

        :param max_row: smallest row index (1-based index)
        :type max_row: int

        :param row_offset: additional rows (e.g. 4)
        :type row_offset: int

        :param column_offset: additional columns (e.g. 3)
        :type column_offset: int

        :rtype: generator
        """

        if range_string is not None:
            warn("Using a range string is deprecated. Use ws[range_string]")
            min_col, min_row, max_col, max_row = range_boundaries(range_string.upper())

        if self._current_row == 0 and not any([min_col, min_row, max_col, max_row ]):
            return ()

        min_col = min_col or 1
        min_row = min_row or 1
        max_col = max_col or self.max_column
        max_row = max_row or self.max_row

        if max_col is not None:
            max_col += column_offset
        if max_row is not None:
            max_row += row_offset
        return self._cells_by_row(min_col + column_offset,
                                  min_row + row_offset,
                                  max_col,
                                  max_row)


    def _cells_by_row(self, min_col, min_row, max_col, max_row):
        for row in range(min_row, max_row + 1):
            yield tuple(self.cell(row=row, column=column)
                    for column in range(min_col, max_col + 1))


    @property
    def rows(self):
        """Iterate over all rows in the worksheet"""
        return self.iter_rows()


    @property
    def values(self):
        """
        Return the values of all the cells, row by row
        """
        for row in self.iter_rows():
            yield tuple(c.value for c in row)


    def iter_cols(self, min_col=None, max_col=None, min_row=None, max_row=None):
        """
        Returns all cells in the worksheet from the first row as columns.

        If no boundaries are passed in the cells will start at A1.

        If no cells are in the worksheet an empty tuple will be returned.

        :param min_col: smallest column index (1-based index)
        :type min_col: int

        :param min_row: smallest row index (1-based index)
        :type min_row: int

        :param max_col: largest column index (1-based index)
        :type max_col: int

        :param max_row: smallest row index (1-based index)
        :type max_row: int

        :rtype: generator
        """

        if self._current_row == 0 and not any([min_col, min_row, max_col, max_row ]):
            return ()

        min_col = min_col or 1
        min_row = min_row or 1
        max_col = max_col or self.max_column
        max_row = max_row or self.max_row

        return self._cells_by_col(
            min_col, min_row, max_col, max_row
        )


    def _cells_by_col(self, min_col, min_row, max_col, max_row):
        """
        Get cells by column
        """
        for column in range(min_col, max_col+1):
            yield tuple(self.cell(row=row, column=column)
                        for row in range(min_row, max_row+1))


    @property
    def columns(self):
        """Iterate over all columns in the worksheet"""
        return self.iter_cols()


    @deprecated("""
    Use ws.iter_rows() or ws.iter_cols() depending whether you
    want rows or columns returned.
    """)
    def get_squared_range(self, min_col, min_row, max_col, max_row):
        """Returns a 2D array of cells. Will create any cells within the
        boundaries that do not already exist

        :param min_col: smallest column index (1-based index)
        :type min_col: int

        :param min_row: smallest row index (1-based index)
        :type min_row: int

        :param max_col: largest column index (1-based index)
        :type max_col: int

        :param max_row: smallest row index (1-based index)
        :type max_row: int

        :rtype: generator
        """

        return self._cells_by_row(min_col, min_row, max_col, max_row)


    @deprecated("""Ranges are workbook objects. Use wb.defined_names[range_name]""")
    def get_named_range(self, range_name):
        """
        Returns a 2D array of cells, with optional row and column offsets.

        :param range_name: `named range` name
        :type range_name: string

        :rtype: tuple[tuple[openpyxl.cell.Cell]]
        """
        defn = self.parent.defined_names[range_name]
        if defn.localSheetId and defn.localSheetId != self.parent.get_index(self):
            msg = "{0} not available in this worksheet".format(range_name)
            raise KeyError(msg)

        if defn.type != "RANGE":
            msg = '{0} refers to a value, not a range'.format(range_name)
            raise NameError(msg)

        result = []
        for title, cells_range in defn.destinations:
            ws = self.parent[title]
            if ws != self:
                raise NamedRangeException("Range includes cells from another worksheet")

            rows = ws[cells_range]
            if isinstance(rows, Cell):
                rows = [(rows, )]

            for row in rows:
                result.extend(row)

        return tuple(result)


    def set_printer_settings(self, paper_size, orientation):
        """Set printer settings """

        self.page_setup.paperSize = paper_size
        if orientation not in (self.ORIENTATION_PORTRAIT, self.ORIENTATION_LANDSCAPE):
            raise ValueError("Values should be %s or %s" % (self.ORIENTATION_PORTRAIT, self.ORIENTATION_LANDSCAPE))
        self.page_setup.orientation = orientation


    def add_data_validation(self, data_validation):
        """ Add a data-validation object to the sheet.  The data-validation
            object defines the type of data-validation to be applied and the
            cell or range of cells it should apply to.
        """
        self.data_validations.append(data_validation)

    def add_chart(self, chart, anchor=None):
        """
        Add a chart to the sheet
        Optionally provide a cell for the top-left anchor
        """
        if anchor is not None:
            chart.anchor = anchor
        self._charts.append(chart)

    def add_image(self, img, anchor=None):
        """
        Add an image to the sheet.
        Optionally provide a cell for the top-left anchor
        """
        if anchor is not None:
            cell = self[anchor]
            img.anchor(cell, anchortype="oneCell")
        self._images.append(img)


    def add_table(self, table):
        self._tables.append(table)


    def merge_cells(self, range_string=None, start_row=None, start_column=None, end_row=None, end_column=None):
        """ Set merge on a cell range.  Range is a cell range (e.g. A1:E1) """
        if not range_string and not all((start_row, start_column, end_row, end_column)):
            msg = "You have to provide a value either for 'coordinate' or for\
            'start_row', 'start_column', 'end_row' *and* 'end_column'"
            raise ValueError(msg)
        elif not range_string:
            range_string = '%s%s:%s%s' % (get_column_letter(start_column),
                                          start_row,
                                          get_column_letter(end_column),
                                          end_row)
        elif ":" not in range_string:
            if COORD_RE.match(range_string):
                return  # Single cell, do nothing
            raise ValueError("Range must be a cell range (e.g. A1:E1)")
        else:
            range_string = range_string.replace('$', '')

        if range_string not in self._merged_cells:
            self._merged_cells.append(range_string)

        min_col, min_row, max_col, max_row = range_boundaries(range_string)
        rows = range(min_row, max_row+1)
        cols = range(min_col, max_col+1)
        cells = product(rows, cols)
        # all but the top-left cell are removed
        for c in islice(cells, 1, None):
            if c in self._cells:
                del self._cells[c]


    @property
    def merged_cells(self):
        """Utility for checking whether a cell has been merged or not"""
        cells = set()
        for _range in self._merged_cells:
            for row in rows_from_range(_range):
                cells = cells.union(set(row))
        return cells


    @property
    def merged_cell_ranges(self):
        """Return a copy of cell ranges"""
        return self._merged_cells[:]


    def unmerge_cells(self, range_string=None, start_row=None, start_column=None, end_row=None, end_column=None):
        """ Remove merge on a cell range.  Range is a cell range (e.g. A1:E1) """
        if not range_string:
            if start_row is None or start_column is None or end_row is None or end_column is None:
                msg = "You have to provide a value either for "\
                    "'coordinate' or for 'start_row', 'start_column', 'end_row' *and* 'end_column'"
                raise InsufficientCoordinatesException(msg)
            else:
                range_string = '%s%s:%s%s' % (get_column_letter(start_column), start_row, get_column_letter(end_column), end_row)
        elif len(range_string.split(':')) != 2:
            msg = "Range must be a cell range (e.g. A1:E1)"
            raise InsufficientCoordinatesException(msg)
        else:
            range_string = range_string.replace('$', '')

        if range_string in self._merged_cells:
            self._merged_cells.remove(range_string)

        else:
            msg = 'Cell range %s not known as merged.' % range_string
            raise InsufficientCoordinatesException(msg)

    def append(self, iterable):
        """Appends a group of values at the bottom of the current sheet.

        * If it's a list: all values are added in order, starting from the first column
        * If it's a dict: values are assigned to the columns indicated by the keys (numbers or letters)

        :param iterable: list, range or generator, or dict containing values to append
        :type iterable: list|tuple|range|generator or dict

        Usage:

        * append(['This is A1', 'This is B1', 'This is C1'])
        * **or** append({'A' : 'This is A1', 'C' : 'This is C1'})
        * **or** append({1 : 'This is A1', 3 : 'This is C1'})

        :raise: TypeError when iterable is neither a list/tuple nor a dict

        """
        row_idx = self._current_row + 1

        if (isinstance(iterable, (list, tuple, range))
            or isgenerator(iterable)):
            for col_idx, content in enumerate(iterable, 1):
                if isinstance(content, Cell):
                    # compatible with write-only mode
                    cell = content
                    if cell.parent and cell.parent != self:
                        raise ValueError("Cells cannot be copied from other worksheets")
                    cell.parent = self
                    cell.col_idx = col_idx
                    cell.row = row_idx
                else:
                    cell = Cell(self, row=row_idx, col_idx=col_idx, value=content)
                self._cells[(row_idx, col_idx)] = cell

        elif isinstance(iterable, dict):
            for col_idx, content in iterable.items():
                if isinstance(col_idx, basestring):
                    col_idx = column_index_from_string(col_idx)
                cell = Cell(self, row=row_idx, col_idx=col_idx, value=content)
                self._cells[(row_idx, col_idx)] = cell

        else:
            self._invalid_row(iterable)

        self._current_row = row_idx


    def _invalid_row(self, iterable):
        raise TypeError('Value must be a list, tuple, range or generator, or a dict. Supplied value is {0}'.format(
            type(iterable))
                        )


    @deprecated("Charts and images should be positioned using anchor objects")
    def point_pos(self, left=0, top=0):
        """ tells which cell is under the given coordinates (in pixels)
        counting from the top-left corner of the sheet.
        Can be used to locate images and charts on the worksheet """

        if left < 0 or top < 0:
            raise ValueError("Coordinates must be positive")

        current_col = 1
        current_row = 1
        column_dimensions = self.column_dimensions
        row_dimensions = self.row_dimensions
        default_width = points_to_pixels(DEFAULT_COLUMN_WIDTH)
        default_height = points_to_pixels(DEFAULT_ROW_HEIGHT)
        left_pos = 0
        top_pos = 0

        while left_pos <= left:
            letter = get_column_letter(current_col)
            current_col += 1
            if letter in column_dimensions:
                cdw = column_dimensions[letter].width
                if cdw is not None:
                    left_pos += points_to_pixels(cdw)
                    continue
            left_pos += default_width

        while top_pos <= top:
            row = current_row
            current_row += 1
            if row in row_dimensions:
                rdh = row_dimensions[row].height
                if rdh is not None:
                    top_pos += points_to_pixels(rdh)
                    continue
            top_pos += default_height

        return (letter, row)


    def _add_column(self):
        """Dimension factory for column information"""

        return ColumnDimension(self)

    def _add_row(self):
        """Dimension factory for row information"""

        return RowDimension(self)


    def _write(self):
        from openpyxl.drawing.spreadsheet_drawing import SpreadsheetDrawing
        from openpyxl.writer.worksheet import write_worksheet
        self._drawing = SpreadsheetDrawing()
        self._drawing.charts = self._charts
        self._drawing.images = self._images
        return write_worksheet(self)


    @property
    def print_title_rows(self):
        if self._print_rows:
            return self._print_rows


    @print_title_rows.setter
    def print_title_rows(self, rows):
        """
        Set rows to be printed on the top of every page
        format `1:3`
        """
        if rows is not None:
            if not ROW_RANGE_RE.match(rows):
                raise ValueError("Print title rows must be the form 1:3")
        self._print_rows = rows


    @property
    def print_title_cols(self):
        if self._print_cols:
            return self._print_cols


    @print_title_cols.setter
    def print_title_cols(self, cols):
        """
        Set cols to be printed on the left of every page
        format ``A:C`
        """
        if cols is not None:
            if not COL_RANGE_RE.match(cols):
                raise ValueError("Print title cols must be the form C:D")
        self._print_cols = cols


    @property
    def print_titles(self):
        if self.print_title_cols and self.print_title_rows:
            return ",".join([self.print_title_rows, self.print_title_cols])
        else:
            return self.print_title_rows or self.print_title_cols


    @property
    def print_area(self):
        """
        Return the print area for the worksheet, if set
        """
        return self._print_area


    @print_area.setter
    def print_area(self, value):
        """
        Range of cells in the form A1:D4 or list of ranges
        """
        if isinstance(value, basestring):
            value = [value]

        self._print_area = [absolute_coordinate(v) for v in value]
