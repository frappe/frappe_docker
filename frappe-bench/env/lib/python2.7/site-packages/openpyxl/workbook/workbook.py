from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""Workbook is the top-level container for all document information."""

from openpyxl.compat import deprecated
from openpyxl.compat import OrderedDict
from openpyxl.worksheet import Worksheet
from openpyxl.worksheet.read_only import ReadOnlyWorksheet
from openpyxl.worksheet.copier import WorksheetCopy

from openpyxl.utils import quote_sheetname
from openpyxl.utils.indexed_list import IndexedList
from openpyxl.utils.datetime  import CALENDAR_WINDOWS_1900
from openpyxl.utils.exceptions import ReadOnlyWorkbookException

from openpyxl.writer.write_only import WriteOnlyWorksheet, save_dump
from openpyxl.writer.excel import save_workbook

from openpyxl.styles.cell_style import StyleArray
from openpyxl.styles.named_styles import NamedStyle
from openpyxl.styles.differential import DifferentialStyleList
from openpyxl.styles.alignment import Alignment
from openpyxl.styles.borders import DEFAULT_BORDER
from openpyxl.styles.fills import DEFAULT_EMPTY_FILL, DEFAULT_GRAY_FILL
from openpyxl.styles.fonts import DEFAULT_FONT
from openpyxl.styles.protection import Protection
from openpyxl.styles.colors import COLOR_INDEX
from openpyxl.styles.named_styles import NamedStyleList
from openpyxl.styles.table import TableStyleList

from openpyxl.chartsheet import Chartsheet
from .defined_name import DefinedName, DefinedNameList
from openpyxl.packaging.core import DocumentProperties
from openpyxl.packaging.relationship import RelationshipList
from .protection import DocumentSecurity

from openpyxl.xml.constants import (
    XLSM,
    XLSX,
    XLTM,
    XLTX
)


class Workbook(object):
    """Workbook is the container for all other parts of the document."""

    _read_only = False
    _data_only = False
    _keep_links = True
    template = False
    path = "/xl/workbook.xml"

    def __init__(self,
                 write_only=False,
                 ):
        self._sheets = []
        self._active_sheet_index = 0
        self.defined_names = DefinedNameList()
        self._external_links = []
        self.properties = DocumentProperties()
        self.security = DocumentSecurity()
        self.__write_only = write_only
        self.shared_strings = IndexedList()

        self._setup_styles()

        self.loaded_theme = None
        self.vba_archive = None
        self.is_template = False
        self._differential_styles = DifferentialStyleList()
        self.code_name = None
        self.excel_base_date = CALENDAR_WINDOWS_1900
        self.encoding = "utf-8"

        if not self.write_only:
            self._sheets.append(Worksheet(self))

        self.rels = RelationshipList()


    def _setup_styles(self):
        """Bootstrap styles"""

        self._fonts = IndexedList()
        self._fonts.add(DEFAULT_FONT)

        self._alignments = IndexedList([Alignment()])

        self._borders = IndexedList()
        self._borders.add(DEFAULT_BORDER)

        self._fills = IndexedList()
        self._fills.add(DEFAULT_EMPTY_FILL)
        self._fills.add(DEFAULT_GRAY_FILL)

        self._number_formats = IndexedList()

        self._protections = IndexedList([Protection()])

        self._colors = COLOR_INDEX
        self._cell_styles = IndexedList([StyleArray()])
        self._named_styles = NamedStyleList()
        self.add_named_style(NamedStyle(font=DEFAULT_FONT, builtinId=0))
        self._table_styles = TableStyleList()


    @property
    def read_only(self):
        return self._read_only

    @property
    def data_only(self):
        return self._data_only

    @property
    def write_only(self):
        return self.__write_only

    @property
    def keep_links(self):
        return self._keep_links

    @deprecated("Use the .active property")
    def get_active_sheet(self):
        """Returns the current active sheet."""
        return self.active

    @property
    def active(self):
        """Get the currently active sheet or None"""
        try:
            return self._sheets[self._active_sheet_index]
        except IndexError:
            pass

    @active.setter
    def active(self, value):
        """Set the active sheet"""
        self._active_sheet_index = value

    def create_sheet(self, title=None, index=None):
        """Create a worksheet (at an optional index).

        :param title: optional title of the sheet
        :type tile: unicode
        :param index: optional position at which the sheet will be inserted
        :type index: int

        """
        if self.read_only:
            raise ReadOnlyWorkbookException('Cannot create new sheet in a read-only workbook')

        if self.write_only :
            new_ws = WriteOnlyWorksheet(parent=self, title=title)
        else:
            new_ws = Worksheet(parent=self, title=title)

        self._add_sheet(sheet=new_ws, index=index)
        return new_ws


    def _add_sheet(self, sheet, index=None):
        """Add an worksheet (at an optional index)."""

        if not isinstance(sheet, (Worksheet, WriteOnlyWorksheet, Chartsheet)):
            raise TypeError("Cannot be added to a workbook")

        if sheet.parent != self:
            raise ValueError("You cannot add worksheets from another workbook.")

        if index is None:
            self._sheets.append(sheet)
        else:
            self._sheets.insert(index, sheet)


    def remove(self, worksheet):
        """Remove a worksheet from this workbook."""
        self._sheets.remove(worksheet)


    @deprecated("Use wb.remove(worksheet) or del wb[sheetname]")
    def remove_sheet(self, worksheet):
        """Remove a worksheet from this workbook."""
        self.remove(worksheet)


    def create_chartsheet(self, title=None, index=None):
        if self.read_only:
            raise ReadOnlyWorkbookException("Cannot create new sheet in a read-only workbook")
        cs = Chartsheet(parent=self, title=title)

        self._add_sheet(cs, index)
        return cs


    @deprecated("Use wb[sheetname]")
    def get_sheet_by_name(self, name):
        """Returns a worksheet by its name.

        :param name: the name of the worksheet to look for
        :type name: string

        """
        return self[name]

    def __contains__(self, key):
        return key in set(self.sheetnames)


    def index(self, worksheet):
        """Return the index of a worksheet."""
        return self.worksheets.index(worksheet)


    @deprecated("Use wb.index(worksheet)")
    def get_index(self, worksheet):
        """Return the index of the worksheet."""
        return self.index(worksheet)

    def __getitem__(self, key):
        """Returns a worksheet by its name.

        :param name: the name of the worksheet to look for
        :type name: string

        """
        for sheet in self.worksheets:
            if sheet.title == key:
                return sheet
        raise KeyError("Worksheet {0} does not exist.".format(key))

    def __delitem__(self, key):
        sheet = self[key]
        self.remove(sheet)

    def __iter__(self):
        return iter(self.worksheets)


    @deprecated("Use wb.sheetnames")
    def get_sheet_names(self):
        return self.sheetnames

    @property
    def worksheets(self):
        return [s for s in self._sheets if isinstance(s, (Worksheet, ReadOnlyWorksheet, WriteOnlyWorksheet))]

    @property
    def chartsheets(self):
        return [s for s in self._sheets if isinstance(s, Chartsheet)]

    @property
    def sheetnames(self):
        """Returns the list of the names of worksheets in the workbook.

        Names are returned in the worksheets order.

        :rtype: list of strings

        """
        return [s.title for s in self._sheets]

    def create_named_range(self, name, worksheet=None, value=None, scope=None):
        """Create a new named_range on a worksheet"""
        defn = DefinedName(name=name, localSheetId=scope)
        if worksheet is not None:
            defn.value = "{0}!{1}".format(quote_sheetname(worksheet.title), value)
        else:
            defn.value = value

        self.defined_names.append(defn)


    def add_named_style(self, style):
        """
        Add a named style
        """
        self._named_styles.append(style)
        style.bind(self)


    @property
    def named_styles(self):
        """
        List available named styles
        """
        return self._named_styles.names


    @deprecated("Use workbook.defined_names.definedName")
    def get_named_ranges(self):
        """Return all named ranges"""
        return self.defined_names.definedName


    @deprecated("Use workbook.defined_names.append")
    def add_named_range(self, named_range):
        """Add an existing named_range to the list of named_ranges."""
        self.defined_names.append(named_range)


    @deprecated("Use workbook.defined_names[name]")
    def get_named_range(self, name):
        """Return the range specified by name."""
        return self.defined_names[name]


    @deprecated("Use del workbook.defined_names[name]")
    def remove_named_range(self, named_range):
        """Remove a named_range from this workbook."""
        del self.defined_names[named_range]


    @property
    def mime_type(self):
        """
        The mime type is determined by whether a workbook is a template or
        not and whether it contains macros or not. Excel requires the file
        extension to match but openpyxl does not enforce this.

        """
        ct = self.template and XLTX or XLSX
        if self.vba_archive:
            ct = self.template and XLTM or XLSM
        return ct


    def save(self, filename):
        """Save the current workbook under the given `filename`.
        Use this function instead of using an `ExcelWriter`.

        .. warning::
            When creating your workbook using `write_only` set to True,
            you will only be able to call this function once. Subsequents attempts to
            modify or save the file will raise an :class:`openpyxl.shared.exc.WorkbookAlreadySaved` exception.
        """
        if self.read_only:
            raise TypeError("""Workbook is read-only""")
        if self.write_only:
            save_dump(self, filename)
        else:
            save_workbook(self, filename)


    @property
    def style_names(self):
        """
        List of named styles
        """
        return [s.name for s in self._named_styles]


    def copy_worksheet(self, from_worksheet):
        """Copy an existing worksheet in the current workbook
        :warning: This function cannot copy worksheets between workbooks.
        worksheets can only be copied within the workbook that they belong

        :param from_worksheet: the worksheet to be copied from
        :return: copy of the initial worksheet
        """
        if self.__write_only or self._read_only:
            raise ValueError("Cannot copy worksheets in read-only or write-only mode")

        new_title = u"{0} Copy".format(from_worksheet.title)
        to_worksheet = self.create_sheet(title=new_title)
        cp = WorksheetCopy(source_worksheet=from_worksheet, target_worksheet=to_worksheet)
        cp.copy_worksheet()
        return to_worksheet


    def close(self):
        """
        Close workbook file if open. Only affects read-only and write-only modes.
        """
        if hasattr(self, '_archive'):
            self._archive.close()
