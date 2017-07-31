from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""Manage individual cells in a spreadsheet.

The Cell class is required to know its value and type, display options,
and any other features of an Excel cell.  Utilities for referencing
cells using Excel's 'A1' column/row nomenclature are also provided.

"""

__docformat__ = "restructuredtext en"

# Python stdlib imports
from copy import copy
import datetime
import re

from openpyxl.compat import (
    unicode,
    basestring,
    bytes,
    NUMERIC_TYPES,
    range,
    deprecated,
)
from openpyxl.utils.units import (
    DEFAULT_ROW_HEIGHT,
    DEFAULT_COLUMN_WIDTH
)
from openpyxl.utils.datetime  import (
    to_excel,
    time_to_days,
    timedelta_to_days,
    from_excel
    )
from openpyxl.utils.exceptions import (
    IllegalCharacterError
)
from openpyxl.utils.units import points_to_pixels
from openpyxl.utils import (
    get_column_letter,
    column_index_from_string,
)
from openpyxl.styles import numbers, is_date_format
from openpyxl.styles.styleable import StyleableObject
from openpyxl.worksheet.hyperlink import Hyperlink

# constants


TIME_TYPES = (datetime.datetime, datetime.date, datetime.time, datetime.timedelta)
STRING_TYPES = (basestring, unicode, bytes)
KNOWN_TYPES = NUMERIC_TYPES + TIME_TYPES + STRING_TYPES + (bool, type(None))

PERCENT_REGEX = re.compile(r'^(?P<number>\-?[0-9]*\.?[0-9]*\s?)\%$')
TIME_REGEX = re.compile(r"""
^(?: # HH:MM and HH:MM:SS
(?P<hour>[0-1]{0,1}[0-9]{2}):
(?P<minute>[0-5][0-9]):?
(?P<second>[0-5][0-9])?$)
|
^(?: # MM:SS.
([0-5][0-9]):
([0-5][0-9])?\.
(?P<microsecond>\d{1,6}))
""", re.VERBOSE)
NUMBER_REGEX = re.compile(r'^-?([\d]|[\d]+\.[\d]*|\.[\d]+|[1-9][\d]+\.?[\d]*)((E|e)[-+]?[\d]+)?$')
ILLEGAL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')

ERROR_CODES = ('#NULL!', '#DIV/0!', '#VALUE!', '#REF!', '#NAME?', '#NUM!',
               '#N/A')


class Cell(StyleableObject):
    """Describes cell associated properties.

    Properties of interest include style, type, value, and address.

    """
    __slots__ = (
        'row',
        'col_idx',
        '_value',
        'data_type',
        'parent',
        '_hyperlink',
        '_comment',
                 )

    ERROR_CODES = ERROR_CODES

    TYPE_STRING = 's'
    TYPE_FORMULA = 'f'
    TYPE_NUMERIC = 'n'
    TYPE_BOOL = 'b'
    TYPE_NULL = 'n'
    TYPE_INLINE = 'inlineStr'
    TYPE_ERROR = 'e'
    TYPE_FORMULA_CACHE_STRING = 'str'

    VALID_TYPES = (TYPE_STRING, TYPE_FORMULA, TYPE_NUMERIC, TYPE_BOOL,
                   TYPE_NULL, TYPE_INLINE, TYPE_ERROR, TYPE_FORMULA_CACHE_STRING)


    def __init__(self, worksheet, column=None, row=None, value=None, col_idx=None, style_array=None):
        super(Cell, self).__init__(worksheet, style_array)
        self.row = row
        # _value is the stored value, while value is the displayed value
        self._value = None
        self._hyperlink = None
        self.data_type = 'n'
        if value is not None:
            self.value = value
        self._comment = None
        if column is not None:
            col_idx = column_index_from_string(column)
        self.col_idx = col_idx


    @property
    def coordinate(self):
        return '%s%d' % (self.column, self.row)

    @property
    def column(self):
        return get_column_letter(self.col_idx)

    @property
    def encoding(self):
        return self.parent.encoding

    @property
    def base_date(self):
        return self.parent.parent.excel_base_date

    @property
    def guess_types(self):
        return getattr(self.parent.parent, 'guess_types', False)

    def __repr__(self):
        return "<Cell {0!r}.{1}>".format(self.parent.title, self.coordinate)

    def check_string(self, value):
        """Check string coding, length, and line break character"""
        if value is None:
            return
        # convert to unicode string
        if not isinstance(value, unicode):
            value = unicode(value, self.encoding)
        value = unicode(value)
        # string must never be longer than 32,767 characters
        # truncate if necessary
        value = value[:32767]
        if next(ILLEGAL_CHARACTERS_RE.finditer(value), None):
            raise IllegalCharacterError
        return value

    def check_error(self, value):
        """Tries to convert Error" else N/A"""
        try:
            return unicode(value)
        except UnicodeDecodeError:
            return u'#N/A'

    def set_explicit_value(self, value=None, data_type=TYPE_STRING):
        """Coerce values according to their explicit type"""
        if data_type not in self.VALID_TYPES:
            raise ValueError('Invalid data type: %s' % data_type)
        if isinstance(value, STRING_TYPES):
            value = self.check_string(value)
        self._value = value
        self.data_type = data_type


    def _bind_value(self, value):
        """Given a value, infer the correct data type"""

        self.data_type = "n"

        if value is True or value is False:
            self.data_type = self.TYPE_BOOL

        elif isinstance(value, NUMERIC_TYPES):
            pass

        elif isinstance(value, TIME_TYPES):
            value = self._cast_datetime(value)

        elif isinstance(value, STRING_TYPES):
            value = self.check_string(value)
            self.data_type = self.TYPE_STRING
            if len(value) > 1 and value.startswith("="):
                self.data_type = self.TYPE_FORMULA
            elif value in self.ERROR_CODES:
                self.data_type = self.TYPE_ERROR
            elif self.guess_types:
                value = self._infer_value(value)

        elif value is not None:
            raise ValueError("Cannot convert {0!r} to Excel".format(value))

        self._value = value


    def _infer_value(self, value):
        """Given a string, infer type and formatting options."""
        if not isinstance(value, unicode):
            value = str(value)

        # number detection
        v = self._cast_numeric(value)
        if v is None:
            # percentage detection
            v = self._cast_percentage(value)
        if v is None:
            # time detection
            v = self._cast_time(value)
        if v is not None:
            self.data_type = self.TYPE_NUMERIC
            return v

        return value


    def _cast_numeric(self, value):
        """Explicity convert a string to a numeric value"""
        if NUMBER_REGEX.match(value):
            try:
                return int(value)
            except ValueError:
                return float(value)

    def _cast_percentage(self, value):
        """Explicitly convert a string to numeric value and format as a
        percentage"""
        match = PERCENT_REGEX.match(value)
        if match:
            self.number_format = numbers.FORMAT_PERCENTAGE
            return float(match.group('number')) / 100


    def _cast_time(self, value):
        """Explicitly convert a string to a number and format as datetime or
        time"""
        match = TIME_REGEX.match(value)
        if match:
            if match.group("microsecond") is not None:
                value = value[:12]
                pattern = "%M:%S.%f"
                fmt = numbers.FORMAT_DATE_TIME5
            elif match.group('second') is None:
                fmt = numbers.FORMAT_DATE_TIME3
                pattern = "%H:%M"
            else:
                pattern = "%H:%M:%S"
                fmt = numbers.FORMAT_DATE_TIME6
            value = datetime.datetime.strptime(value, pattern)
            self.number_format = fmt
            return time_to_days(value)


    def _cast_datetime(self, value):
        """Convert Python datetime to Excel and set formatting"""
        if isinstance(value, datetime.datetime):
            value = to_excel(value, self.base_date)
            self.number_format = numbers.FORMAT_DATE_DATETIME
        elif isinstance(value, datetime.date):
            value = to_excel(value, self.base_date)
            self.number_format = numbers.FORMAT_DATE_YYYYMMDD2
        elif isinstance(value, datetime.time):
            value = time_to_days(value)
            self.number_format = numbers.FORMAT_DATE_TIME6
        elif isinstance(value, datetime.timedelta):
            value = timedelta_to_days(value)
            self.number_format = numbers.FORMAT_DATE_TIMEDELTA
        return value

    @property
    def value(self):
        """Get or set the value held in the cell.

        :rtype: depends on the value (string, float, int or
            :class:`datetime.datetime`)
        """
        value = self._value
        if value is not None and self.is_date:
            value = from_excel(value, self.base_date)
        return value

    @value.setter
    def value(self, value):
        """Set the value and infer type and display options."""
        self._bind_value(value)

    @property
    def internal_value(self):
        """Always returns the value for excel."""
        return self._value

    @property
    def hyperlink(self):
        """Return the hyperlink target or an empty string"""
        return self._hyperlink


    @hyperlink.setter
    def hyperlink(self, val):
        """Set value and display for hyperlinks in a cell.
        Automatically sets the `value` of the cell with link text,
        but you can modify it afterwards by setting the `value`
        property, and the hyperlink will remain.
        Hyperlink is removed if set to ``None``."""
        if val is None:
            self._hyperlink = None
        else:
            if not isinstance(val, Hyperlink):
                val = Hyperlink(ref="", target=val)
            val.ref = self.coordinate
            self._hyperlink = val
            if self._value is None:
                self.value = val.target or val.location


    @property
    def is_date(self):
        """Whether the value is formatted as a date

        :rtype: bool
        """
        if self.data_type == "n" and self.number_format != "General":
            return is_date_format(self.number_format)
        return False

    def offset(self, row=0, column=0):
        """Returns a cell location relative to this cell.

        :param row: number of rows to offset
        :type row: int

        :param column: number of columns to offset
        :type column: int

        :rtype: :class:`openpyxl.cell.Cell`
        """
        offset_column = self.col_idx + column
        offset_row = self.row + row
        return self.parent.cell(column=offset_column, row=offset_row)

    @property
    @deprecated("Use anchor objects for positioning")
    def anchor(self):
        """ returns the expected position of a cell in pixels from the top-left
            of the sheet. For example, A1 anchor should be (0,0).

            :rtype: tuple(int, int)
        """
        left_columns = (column_index_from_string(self.column) - 1)
        column_dimensions = self.parent.column_dimensions
        left_anchor = 0
        default_width = points_to_pixels(DEFAULT_COLUMN_WIDTH)

        for col_idx in range(left_columns):
            letter = get_column_letter(col_idx + 1)
            if letter in column_dimensions:
                cdw = column_dimensions.get(letter).width or default_width
                if cdw > 0:
                    left_anchor += points_to_pixels(cdw)
                    continue
            left_anchor += default_width

        row_dimensions = self.parent.row_dimensions
        top_anchor = 0
        top_rows = (self.row - 1)
        default_height = points_to_pixels(DEFAULT_ROW_HEIGHT)
        for row_idx in range(1, top_rows + 1):
            if row_idx in row_dimensions:
                rdh = row_dimensions[row_idx].height or default_height
                if rdh > 0:
                    top_anchor += points_to_pixels(rdh)
                    continue
            top_anchor += default_height

        return (left_anchor, top_anchor)

    @property
    def comment(self):
        """ Returns the comment associated with this cell

            :rtype: :class:`openpyxl.comments.Comment`
        """
        return self._comment


    @comment.setter
    def comment(self, value):
        """
        Assign a comment to a cell
        """

        if value is not None:
            if value.parent:
                value = copy(value)
            value.bind(self)
        elif value is None and self._comment:
            self._comment.unbind()
        self._comment = value


def WriteOnlyCell(ws=None, value=None):
    return Cell(worksheet=ws, column='A', row=1, value=value)
