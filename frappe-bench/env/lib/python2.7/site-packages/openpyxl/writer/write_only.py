from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl


"""Write worksheets to xml representations in an optimized way"""

import atexit
from inspect import isgenerator
import os
from tempfile import NamedTemporaryFile
from zipfile import ZipFile, ZIP_DEFLATED

from openpyxl.cell import Cell, WriteOnlyCell
from openpyxl.drawing.spreadsheet_drawing import SpreadsheetDrawing
from openpyxl.worksheet import Worksheet
from openpyxl.workbook.child import _WorkbookChild
from openpyxl.worksheet.related import Related
from openpyxl.worksheet.dimensions import SheetFormatProperties

from openpyxl.utils.exceptions import WorkbookAlreadySaved

from .etree_worksheet import write_cell
from .excel import ExcelWriter
from .worksheet import write_drawing
from openpyxl.xml.constants import SHEET_MAIN_NS
from openpyxl.xml.functions import xmlfile, Element

ALL_TEMP_FILES = []


@atexit.register
def _openpyxl_shutdown():
    global ALL_TEMP_FILES
    for path in ALL_TEMP_FILES:
        if os.path.exists(path):
            os.remove(path)


def create_temporary_file(suffix=''):
    fobj = NamedTemporaryFile(mode='w+', suffix=suffix,
                              prefix='openpyxl.', delete=False)
    filename = fobj.name
    ALL_TEMP_FILES.append(filename)
    return filename


class WriteOnlyWorksheet(_WorkbookChild):
    """
    Streaming worksheet. Optimised to reduce memory by writing rows just in
    time.
    Cells can be styled and have comments Styles for rows and columns
    must be applied before writing cells
    """

    __saved = False
    writer = None
    _rel_type = Worksheet._rel_type
    _path = Worksheet._path
    mime_type = Worksheet.mime_type


    def __init__(self, parent, title):
        super(WriteOnlyWorksheet, self).__init__(parent, title)
        self._max_col = 0
        self._max_row = 0
        self._fileobj_name = create_temporary_file()

        # Methods from Worksheet
        self._add_row = Worksheet._add_row.__get__(self)
        self._add_column = Worksheet._add_column.__get__(self)
        self.add_chart = Worksheet.add_chart.__get__(self)
        self.add_image = Worksheet.add_image.__get__(self)
        self.add_table = Worksheet.add_table.__get__(self)

        setup = Worksheet._setup.__get__(self)
        setup()

        self.print_titles = Worksheet.print_titles.__get__(self)
        self.sheet_view = Worksheet.sheet_view.__get__(self)


    @property
    def freeze_panes(self):
        return Worksheet.freeze_panes.__get__(self)


    @freeze_panes.setter
    def freeze_panes(self, value):
        Worksheet.freeze_panes.__set__(self, value)


    @property
    def print_title_cols(self):
        return Worksheet.print_title_cols.__get__(self)


    @print_title_cols.setter
    def print_title_cols(self, value):
        Worksheet.print_title_cols.__set__(self, value)


    @property
    def print_title_rows(self):
        return Worksheet.print_title_rows.__get__(self)


    @print_title_rows.setter
    def print_title_rows(self, value):
        Worksheet.print_title_rows.__set__(self, value)


    @property
    def print_area(self):
        return Worksheet.print_area.__get__(self)


    @print_area.setter
    def print_area(self, value):
        Worksheet.print_area.__set__(self, value)


    @property
    def filename(self):
        return self._fileobj_name


    def _write_header(self):
        """
        Generator that creates the XML file and the sheet header
        """

        with xmlfile(self.filename) as xf:
            with xf.element("worksheet", xmlns=SHEET_MAIN_NS):

                if self.sheet_properties:
                    pr = self.sheet_properties.to_tree()

                xf.write(pr)
                xf.write(self.views.to_tree())

                cols = self.column_dimensions.to_tree()

                self.sheet_format.outlineLevelCol = self.column_dimensions.max_outline
                xf.write(self.sheet_format.to_tree())

                if cols is not None:
                    xf.write(cols)

                with xf.element("sheetData"):
                    cell = WriteOnlyCell(self)
                    try:
                        while True:
                            row = (yield)
                            row_idx = self._max_row
                            attrs = {'r': '%d' % row_idx}
                            if row_idx in self.row_dimensions:
                                dim = self.row_dimensions[row_idx]
                                attrs.update(dict(dim))

                            with xf.element("row", attrs):

                                for col_idx, value in enumerate(row, 1):
                                    if value is None:
                                        continue
                                    try:
                                        cell.value = value
                                    except ValueError:
                                        if isinstance(value, Cell):
                                            cell = value
                                        else:
                                            raise ValueError

                                    cell.col_idx = col_idx
                                    cell.row = row_idx

                                    styled = cell.has_style
                                    write_cell(xf, self, cell, styled)

                                    if styled: # styled cell or datetime
                                        cell = WriteOnlyCell(self)

                    except GeneratorExit:
                        pass

                if self.protection.sheet:
                    xf.write(self.protection.to_tree())

                if self.auto_filter.ref:
                    xf.write(self.auto_filter.to_tree())

                if self.sort_state.ref:
                    xf.write(self.sort_state.to_tree())

                if self.data_validations.count:
                    xf.write(self.data_validations.to_tree())

                drawing = write_drawing(self)
                if drawing is not None:
                    xf.write(drawing)

                if self._comments:
                    legacyDrawing = Related(id="anysvml")
                    xml = legacyDrawing.to_tree("legacyDrawing")
                    xf.write(xml)

    def close(self):
        if self.__saved:
            self._already_saved()
        if self.writer is None:
            self.writer = self._write_header()
            next(self.writer)
        self.writer.close()
        self.__saved = True

    def _cleanup(self):
        os.remove(self.filename)

    def append(self, row):
        """
        :param row: iterable containing values to append
        :type row: iterable
        """

        if (not isgenerator(row) and
            not isinstance(row, (list, tuple, range))
            ):
            self._invalid_row(row)

        self._max_row += 1

        if self.writer is None:
            self.writer = self._write_header()
            next(self.writer)

        try:
            self.writer.send(row)
        except StopIteration:
            self._already_saved()


    def _already_saved(self):
        raise WorkbookAlreadySaved('Workbook has already been saved and cannot be modified or saved anymore.')


    def _invalid_row(self, iterable):
        raise TypeError('Value must be a list, tuple, range or a generator Supplied value is {0}'.format(
            type(iterable))
                        )

    def _write(self):
        self._drawing = SpreadsheetDrawing()
        self._drawing.charts = self._charts
        self._drawing.images = self._images
        self.close()
        with open(self.filename) as src:
            out = src.read()
        self._cleanup()
        return out


def save_dump(workbook, filename):
    archive = ZipFile(filename, 'w', ZIP_DEFLATED, allowZip64=True)
    if workbook.worksheets == []:
        workbook.create_sheet()
    writer = ExcelWriter(workbook, archive)
    writer.save(filename)
    return True
