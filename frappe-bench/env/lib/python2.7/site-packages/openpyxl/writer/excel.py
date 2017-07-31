from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""Write a .xlsx file."""

# Python stdlib imports
from io import BytesIO
import re
from zipfile import ZipFile, ZIP_DEFLATED

# package imports
from openpyxl.xml.constants import (
    ARC_SHARED_STRINGS,
    ARC_CONTENT_TYPES,
    ARC_ROOT_RELS,
    ARC_WORKBOOK_RELS,
    ARC_APP, ARC_CORE,
    ARC_THEME,
    ARC_STYLE,
    ARC_WORKBOOK,
    PACKAGE_WORKSHEETS,
    PACKAGE_CHARTSHEETS,
    PACKAGE_DRAWINGS,
    PACKAGE_CHARTS,
    PACKAGE_IMAGES,
    PACKAGE_XL
    )
from openpyxl.drawing.spreadsheet_drawing import SpreadsheetDrawing
from openpyxl.xml.functions import tostring, fromstring, Element
from openpyxl.packaging.manifest import Manifest
from openpyxl.packaging.relationship import (
    get_rels_path,
    RelationshipList,
    Relationship,
)
from openpyxl.packaging.extended import ExtendedProperties

from openpyxl.writer.strings import write_string_table
from openpyxl.writer.workbook import (
    write_root_rels,
    write_workbook_rels,
    write_workbook,
)
from openpyxl.writer.theme import write_theme
from openpyxl.writer.worksheet import write_worksheet
from openpyxl.styles.stylesheet import write_stylesheet

from openpyxl.comments.comment_sheet import CommentSheet


class ExcelWriter(object):
    """Write a workbook object to an Excel file."""

    def __init__(self, workbook, archive):
        self._archive = archive
        self.workbook = workbook
        self.manifest = Manifest()
        self.vba_modified = set()
        self._tables = []
        self._charts = []
        self._images = []
        self._drawings = []
        self._comments = []


    def write_data(self):
        """Write the various xml files into the zip archive."""
        # cleanup all worksheets
        archive = self._archive

        archive.writestr(ARC_ROOT_RELS, write_root_rels(self.workbook))
        props = ExtendedProperties()
        archive.writestr(ARC_APP, tostring(props.to_tree()))

        archive.writestr(ARC_CORE, tostring(self.workbook.properties.to_tree()))
        if self.workbook.loaded_theme:
            archive.writestr(ARC_THEME, self.workbook.loaded_theme)
        else:
            archive.writestr(ARC_THEME, write_theme())

        self._write_worksheets()
        self._write_chartsheets()
        self._write_images()
        self._write_charts()

        self._archive.writestr(ARC_SHARED_STRINGS,
                              write_string_table(self.workbook.shared_strings))
        self._write_external_links()

        stylesheet = write_stylesheet(self.workbook)
        archive.writestr(ARC_STYLE, tostring(stylesheet))

        archive.writestr(ARC_WORKBOOK, write_workbook(self.workbook))
        archive.writestr(ARC_WORKBOOK_RELS, write_workbook_rels(self.workbook))

        self._merge_vba()

        self.manifest._write(archive, self.workbook)

    def _merge_vba(self):
        """
        If workbook contains macros then extract associated files from cache
        of old file and add to archive
        """
        ARC_VBA = re.compile("|".join(
            ('xl/vba', r'xl/drawings/.*vmlDrawing\d\.vml',
             'xl/ctrlProps', 'customUI', 'xl/activeX', r'xl/media/.*\.emf')
        )
                             )

        if self.workbook.vba_archive:
            for name in set(self.workbook.vba_archive.namelist()) - self.vba_modified:
                if ARC_VBA.match(name):
                    self._archive.writestr(name, self.workbook.vba_archive.read(name))


    def _write_images(self):
        # delegate to object
        for img in self._images:
            self._archive.writestr(img.path[1:], img._data())


    def _write_charts(self):
        # delegate to object
        for chart in self._charts:
            self._archive.writestr(chart.path[1:], tostring(chart._write()))
            self.manifest.append(chart)


    def _write_drawing(self, drawing):
        """
        Write a drawing
        """
        self._drawings.append(drawing)
        drawing._id = len(self._drawings)
        for chart in drawing.charts:
            self._charts.append(chart)
            chart._id = len(self._charts)
        for img in drawing.images:
            self._images.append(img)
            img._id = len(self._images)
        rels_path = get_rels_path(drawing.path)[1:]
        self._archive.writestr(drawing.path[1:], tostring(drawing._write()))
        self._archive.writestr(rels_path, tostring(drawing._write_rels()))
        self.manifest.append(drawing)


    def _write_chartsheets(self):
        for idx, sheet in enumerate(self.workbook.chartsheets, 1):

            sheet._id = idx
            xml = tostring(sheet.to_tree())

            self._archive.writestr(sheet.path[1:], xml)
            self.manifest.append(sheet)

            if sheet._drawing:
                self._write_drawing(sheet._drawing)

                rel = Relationship(type="drawing", Target=sheet._drawing.path)
                rels = RelationshipList()
                rels.append(rel)
                tree = rels.to_tree()

                rels_path = get_rels_path(sheet.path[1:])
                self._archive.writestr(rels_path, tostring(tree))


    def _write_comment(self, ws):

        cs = CommentSheet.from_comments(ws._comments)
        self._comments.append(cs)
        cs._id = len(self._comments)
        self._archive.writestr(cs.path[1:], tostring(cs.to_tree()))
        self.manifest.append(cs)

        if ws.legacy_drawing is None:
            ws.legacy_drawing = 'xl/drawings/commentsDrawing{0}.vml'.format(cs._id)
            vml = None
        else:
            vml = fromstring(self.workbook.vba_archive.read(ws.legacy_drawing))

        vml = cs.write_shapes(vml)

        self._archive.writestr(ws.legacy_drawing, vml)
        self.vba_modified.add(ws.legacy_drawing)

        comment_rel = Relationship(Id="comments", type=cs._rel_type, Target=cs.path)
        ws._rels.append(comment_rel)


    def _write_worksheets(self):

        for idx, ws in enumerate(self.workbook.worksheets, 1):

            ws._id = idx
            xml = ws._write()
            rels_path = get_rels_path(ws.path)[1:]

            self._archive.writestr(ws.path[1:], xml)
            self.manifest.append(ws)

            if ws._drawing:
                self._write_drawing(ws._drawing)

                for r in ws._rels.Relationship:
                    if "drawing" in r.Type:
                        r.Target = ws._drawing.path

            if ws._comments:
                self._write_comment(ws)

            if ws.legacy_drawing is not None:
                shape_rel = Relationship(type="vmlDrawing", Id="anysvml",
                                         Target="/" + ws.legacy_drawing)
                ws._rels.append(shape_rel)

            for t in ws._tables:
                self._tables.append(t)
                t.id = len(self._tables)
                t._write(self._archive)
                self.manifest.append(t)
                ws._rels[t._rel_id].Target = t.path

            if ws._rels:
                tree = ws._rels.to_tree()
                self._archive.writestr(rels_path, tostring(tree))


    def _write_external_links(self):
        # delegate to object
        """Write links to external workbooks"""
        wb = self.workbook
        for idx, link in enumerate(wb._external_links, 1):
            link._id = idx
            rels_path = get_rels_path(link.path[1:])

            xml = link.to_tree()
            self._archive.writestr(link.path[1:], tostring(xml))
            rels = RelationshipList()
            rels.append(link.file_link)
            self._archive.writestr(rels_path, tostring(rels.to_tree()))
            self.manifest.append(link)


    def save(self, filename):
        """Write data into the archive."""
        self.write_data()
        self._archive.close()


def save_workbook(workbook, filename,):
    """Save the given workbook on the filesystem under the name filename.

    :param workbook: the workbook to save
    :type workbook: :class:`openpyxl.workbook.Workbook`

    :param filename: the path to which save the workbook
    :type filename: string

    :rtype: bool

    """
    archive = ZipFile(filename, 'w', ZIP_DEFLATED, allowZip64=True)
    writer = ExcelWriter(workbook, archive)
    writer.save(filename)
    return True


def save_virtual_workbook(workbook,):
    """Return an in-memory workbook, suitable for a Django response."""
    temp_buffer = BytesIO()
    archive = ZipFile(temp_buffer, 'w', ZIP_DEFLATED, allowZip64=True)

    writer = ExcelWriter(workbook, archive)

    try:
        writer.write_data()
    finally:
        archive.close()

    virtual_workbook = temp_buffer.getvalue()
    temp_buffer.close()
    return virtual_workbook
