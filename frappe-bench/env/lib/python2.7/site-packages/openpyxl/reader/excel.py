from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""Read an xlsx file into Python"""

# Python stdlib imports
from zipfile import ZipFile, ZIP_DEFLATED, BadZipfile
from sys import exc_info
from io import BytesIO
import os.path
import warnings

# compatibility imports
from openpyxl.compat import unicode, file

# Allow blanket setting of KEEP_VBA for testing
try:
    from ..tests import KEEP_VBA
except ImportError:
    KEEP_VBA = False


# package imports
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.xml.constants import (
    ARC_SHARED_STRINGS,
    ARC_CORE,
    ARC_CONTENT_TYPES,
    ARC_WORKBOOK,
    ARC_THEME,
    COMMENTS_NS,
    SHARED_STRINGS,
    EXTERNAL_LINK,
    XLTM,
    XLTX,
    XLSM,
    XLSX,
)

from openpyxl.comments.comment_sheet import CommentSheet
from openpyxl.workbook import Workbook

from .strings import read_string_table
from openpyxl.styles.stylesheet import apply_stylesheet

from openpyxl.packaging.core import DocumentProperties
from openpyxl.packaging.manifest import Manifest, Override
from openpyxl.packaging.workbook import WorkbookParser
from openpyxl.packaging.relationship import get_dependents, get_rels_path

from openpyxl.worksheet.read_only import ReadOnlyWorksheet
from openpyxl.worksheet.table import Table

from openpyxl.xml.functions import fromstring

from .worksheet import WorkSheetParser

# Use exc_info for Python 2 compatibility with "except Exception[,/ as] e"


CENTRAL_DIRECTORY_SIGNATURE = b'\x50\x4b\x05\x06'
SUPPORTED_FORMATS = ('.xlsx', '.xlsm', '.xltx', '.xltm')


def repair_central_directory(zipFile, is_file_instance):
    ''' trims trailing data from the central directory
    code taken from http://stackoverflow.com/a/7457686/570216, courtesy of Uri Cohen
    '''

    f = zipFile if is_file_instance else open(zipFile, 'rb+')
    data = f.read()
    pos = data.find(CENTRAL_DIRECTORY_SIGNATURE)  # End of central directory signature
    if (pos > 0):
        sio = BytesIO(data)
        sio.seek(pos + 22)  # size of 'ZIP end of central directory record'
        sio.truncate()
        sio.seek(0)
        return sio

    f.seek(0)
    return f



def _validate_archive(filename):
    """
    Check the file is a valid zipfile
    """
    is_file_like = hasattr(filename, 'read')

    if not is_file_like and os.path.isfile(filename):
        file_format = os.path.splitext(filename)[-1].lower()
        if file_format not in SUPPORTED_FORMATS:
            if file_format == '.xls':
                msg = ('openpyxl does not support the old .xls file format, '
                       'please use xlrd to read this file, or convert it to '
                       'the more recent .xlsx file format.')
            elif file_format == '.xlsb':
                msg = ('openpyxl does not support binary format .xlsb, '
                       'please convert this file to .xlsx format if you want '
                       'to open it with openpyxl')
            else:
                msg = ('openpyxl does not support %s file format, '
                       'please check you can open '
                       'it with Excel first. '
                       'Supported formats are: %s') % (file_format,
                                                       ','.join(SUPPORTED_FORMATS))
            raise InvalidFileException(msg)


    if is_file_like:
        # fileobject must have been opened with 'rb' flag
        # it is required by zipfile
        if getattr(filename, 'encoding', None) is not None:
            raise IOError("File-object must be opened in binary mode")

    try:
        archive = ZipFile(filename, 'r', ZIP_DEFLATED)
    except BadZipfile:
        f = repair_central_directory(filename, is_file_like)
        archive = ZipFile(f, 'r', ZIP_DEFLATED)
    return archive


def _find_workbook_part(package):
    workbook_types = [XLTM, XLTX, XLSM, XLSX]
    for ct in workbook_types:
        part = package.find(ct)
        if part:
            return part

    # some applications reassign the default for application/xml
    defaults = set((p.ContentType for p in package.Default))
    workbook_type = defaults & set(workbook_types)
    if workbook_type:
        return Override("/" + ARC_WORKBOOK, workbook_type.pop())

    raise IOError("File contains no valid workbook part")


def load_workbook(filename, read_only=False, keep_vba=KEEP_VBA,
                  data_only=False, guess_types=False, keep_links=True):
    """Open the given filename and return the workbook

    :param filename: the path to open or a file-like object
    :type filename: string or a file-like object open in binary mode c.f., :class:`zipfile.ZipFile`

    :param read_only: optimised for reading, content cannot be edited
    :type read_only: bool

    :param keep_vba: preseve vba content (this does NOT mean you can use it)
    :type keep_vba: bool

    :param guess_types: guess cell content type and do not read it from the file
    :type guess_types: bool

    :param data_only: controls whether cells with formulae have either the formula (default) or the value stored the last time Excel read the sheet
    :type data_only: bool

    :param keep_links: whether links to external workbooks should be preserved. The default is True
    :type keep_links: bool

    :rtype: :class:`openpyxl.workbook.Workbook`

    .. note::

        When using lazy load, all worksheets will be :class:`openpyxl.worksheet.iter_worksheet.IterableWorksheet`
        and the returned workbook will be read-only.

    """
    archive = _validate_archive(filename)
    read_only = read_only

    src = archive.read(ARC_CONTENT_TYPES)
    root = fromstring(src)
    package = Manifest.from_tree(root)

    wb_part = _find_workbook_part(package)
    parser = WorkbookParser(archive, wb_part.PartName[1:])
    wb = parser.wb
    wb._data_only = data_only
    wb._read_only = read_only
    wb._keep_links = keep_links
    wb.guess_types = guess_types
    wb.template = wb_part.ContentType in (XLTX, XLTM)
    parser.parse()
    wb._sheets = []

    if read_only and guess_types:
        warnings.warn('Data types are not guessed when using iterator reader')

    valid_files = archive.namelist()

    # If are going to preserve the vba then attach a copy of the archive to the
    # workbook so that is available for the save.
    if keep_vba:
        wb.vba_archive = ZipFile(BytesIO(), 'a', ZIP_DEFLATED)
        for name in archive.namelist():
            wb.vba_archive.writestr(name, archive.read(name))


    if read_only:
        wb._archive = ZipFile(filename)

    # get workbook-level information
    if ARC_CORE in valid_files:
        src = fromstring(archive.read(ARC_CORE))
        wb.properties = DocumentProperties.from_tree(src)


    shared_strings = []
    ct = package.find(SHARED_STRINGS)
    if ct is not None:
        strings_path = ct.PartName[1:]
        shared_strings = read_string_table(archive.read(strings_path))


    if ARC_THEME in valid_files:
        wb.loaded_theme = archive.read(ARC_THEME)

    apply_stylesheet(archive, wb) # bind styles to workbook

    # get worksheets
    for sheet, rel in parser.find_sheets():
        sheet_name = sheet.name
        worksheet_path = rel.target
        rels_path = get_rels_path(worksheet_path)
        rels = []
        if rels_path in valid_files:
            rels = get_dependents(archive, rels_path)

        if not worksheet_path in valid_files:
            continue

        if read_only:
            ws = ReadOnlyWorksheet(wb, sheet_name, worksheet_path, None,
                                   shared_strings)

            wb._sheets.append(ws)
        else:
            fh = archive.open(worksheet_path)
            ws = wb.create_sheet(sheet_name)
            ws._rels = rels
            ws_parser = WorkSheetParser(ws, fh, shared_strings)
            ws_parser.parse()

            if rels:
                # assign any comments to cells
                for r in rels.find(COMMENTS_NS):
                    src = archive.read(r.target)
                    comment_sheet = CommentSheet.from_tree(fromstring(src))
                    for ref, comment in comment_sheet.comments:
                        ws[ref].comment = comment

                # preserve link to VML file if VBA
                if (
                    wb.vba_archive is not None
                    and ws.legacy_drawing is not None
                    ):
                    ws.legacy_drawing = rels[ws.legacy_drawing].target

                for t in ws_parser.tables:
                    src = archive.read(t)
                    xml = fromstring(src)
                    table = Table.from_tree(xml)
                    ws.add_table(table)

        ws.sheet_state = sheet.state
        ws._rels = [] # reset

    parser.assign_names()

    #wb._differential_styles.styles =  [] # tables may depened upon dxf

    archive.close()
    return wb
