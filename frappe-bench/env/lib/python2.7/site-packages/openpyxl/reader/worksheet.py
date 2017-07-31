from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""Reader for a single worksheet."""
from io import BytesIO
from warnings import warn

# compatibility imports
from openpyxl.xml.functions import iterparse

# package imports
from openpyxl.cell import Cell
from openpyxl.worksheet.filters import AutoFilter, SortState
from openpyxl.cell.read_only import _cast_number
from openpyxl.cell.text import Text
from openpyxl.worksheet import Worksheet
from openpyxl.worksheet.dimensions import (
    ColumnDimension,
    RowDimension,
    SheetFormatProperties,
)
from openpyxl.worksheet.header_footer import HeaderFooter
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.worksheet.merge import MergeCells
from openpyxl.worksheet.page import PageMargins, PrintOptions, PrintPageSetup
from openpyxl.worksheet.protection import SheetProtection
from openpyxl.worksheet.views import SheetViewList
from openpyxl.worksheet.datavalidation import DataValidationList
from openpyxl.xml.constants import (
    SHEET_MAIN_NS,
    REL_NS,
    EXT_TYPES,
    PKG_REL_NS
)
from openpyxl.xml.functions import safe_iterator, localname
from openpyxl.styles import Color
from openpyxl.formatting import Rule
from openpyxl.formatting.formatting import ConditionalFormatting
from openpyxl.formula.translate import Translator
from openpyxl.worksheet.properties import WorksheetProperties
from openpyxl.utils import (
    coordinate_from_string,
    get_column_letter,
    column_index_from_string,
    coordinate_to_tuple,
    )
from openpyxl.descriptors.excel import ExtensionList, Extension
from openpyxl.worksheet.table import TablePartList


def _get_xml_iter(xml_source):
    """
    Possible inputs: strings, bytes, members of zipfile, temporary file
    Always return a file like object
    """
    if not hasattr(xml_source, 'read'):
        try:
            xml_source = xml_source.encode("utf-8")
        except (AttributeError, UnicodeDecodeError):
            pass
        return BytesIO(xml_source)
    else:
        try:
            xml_source.seek(0)
        except:
            # could be a zipfile
            pass
        return xml_source


class WorkSheetParser(object):

    CELL_TAG = '{%s}c' % SHEET_MAIN_NS
    VALUE_TAG = '{%s}v' % SHEET_MAIN_NS
    FORMULA_TAG = '{%s}f' % SHEET_MAIN_NS
    MERGE_TAG = '{%s}mergeCell' % SHEET_MAIN_NS
    INLINE_STRING = "{%s}is" % SHEET_MAIN_NS

    def __init__(self, ws, xml_source, shared_strings):
        self.ws = ws
        self.source = xml_source
        self.shared_strings = shared_strings
        self.guess_types = ws.parent.guess_types
        self.data_only = ws.parent.data_only
        self.styles = ws.parent._cell_styles
        self.differential_styles = ws.parent._differential_styles
        self.keep_vba = ws.parent.vba_archive is not None
        self.shared_formula_masters = {}  # {si_str: Translator()}
        self._row_count = self._col_count = 0
        self.tables = []

    def parse(self):
        dispatcher = {
            '{%s}mergeCells' % SHEET_MAIN_NS: self.parse_merge,
            '{%s}col' % SHEET_MAIN_NS: self.parse_column_dimensions,
            '{%s}row' % SHEET_MAIN_NS: self.parse_row,
            '{%s}conditionalFormatting' % SHEET_MAIN_NS: self.parser_conditional_formatting,
            '{%s}legacyDrawing' % SHEET_MAIN_NS: self.parse_legacy_drawing,
            '{%s}sheetProtection' % SHEET_MAIN_NS: self.parse_sheet_protection,
            '{%s}extLst' % SHEET_MAIN_NS: self.parse_extensions,
            '{%s}hyperlink' % SHEET_MAIN_NS: self.parse_hyperlinks,
            '{%s}tableParts' % SHEET_MAIN_NS: self.parse_tables,
                      }

        properties = {
            '{%s}printOptions' % SHEET_MAIN_NS: ('print_options', PrintOptions),
            '{%s}pageMargins' % SHEET_MAIN_NS: ('page_margins', PageMargins),
            '{%s}pageSetup' % SHEET_MAIN_NS: ('page_setup', PrintPageSetup),
            '{%s}headerFooter' % SHEET_MAIN_NS: ('HeaderFooter', HeaderFooter),
            '{%s}autoFilter' % SHEET_MAIN_NS: ('auto_filter', AutoFilter),
            '{%s}dataValidations' % SHEET_MAIN_NS: ('data_validations', DataValidationList),
            #'{%s}sheet/{%s}sortState' % (SHEET_MAIN_NS, SHEET_MAIN_NS): ('sort_state', SortState),
            '{%s}sheetPr' % SHEET_MAIN_NS: ('sheet_properties', WorksheetProperties),
            '{%s}sheetViews' % SHEET_MAIN_NS: ('views', SheetViewList),
            '{%s}sheetFormatPr' % SHEET_MAIN_NS: ('sheet_format', SheetFormatProperties)
        }

        tags = dispatcher.keys()
        stream = _get_xml_iter(self.source)
        it = iterparse(stream, tag=tags)

        for _, element in it:
            tag_name = element.tag
            if tag_name in dispatcher:
                dispatcher[tag_name](element)
                element.clear()
            elif tag_name in properties:
                prop = properties[tag_name]
                obj = prop[1].from_tree(element)
                setattr(self.ws, prop[0], obj)
                element.clear()

        self.ws._current_row = self.ws.max_row


    def parse_cell(self, element):
        value = element.find(self.VALUE_TAG)
        if value is not None:
            value = value.text
        formula = element.find(self.FORMULA_TAG)
        data_type = element.get('t', 'n')
        coordinate = element.get('r')
        self._col_count += 1
        style_id = element.get('s')

        # assign formula to cell value unless only the data is desired
        if formula is not None and not self.data_only:
            data_type = 'f'
            if formula.text:
                value = "=" + formula.text
            else:
                value = "="
            formula_type = formula.get('t')
            if formula_type:
                if formula_type != "shared":
                    self.ws.formula_attributes[coordinate] = dict(formula.attrib)

                else:
                    si = formula.get('si')  # Shared group index for shared formulas

                    # The spec (18.3.1.40) defines shared formulae in
                    # terms of the following:
                    #
                    # `master`: "The first formula in a group of shared
                    #            formulas"
                    # `ref`: "Range of cells which the formula applies
                    #        to." It's a required attribute on the master
                    #        cell, forbidden otherwise.
                    # `shared cell`: "A cell is shared only when si is
                    #                 used and t is `shared`."
                    #
                    # Whether to use the cell's given formula or the
                    # master's depends on whether the cell is shared,
                    # whether it's in the ref, and whether it defines its
                    # own formula, as follows:
                    #
                    #  Shared?   Has formula? | In ref    Not in ref
                    # ========= ==============|======== ===============
                    #   Yes          Yes      | master   impl. defined
                    #    No          Yes      |  own         own
                    #   Yes           No      | master   impl. defined
                    #    No           No      |  ??          N/A
                    #
                    # The ?? is because the spec is silent on this issue,
                    # though my inference is that the cell does not
                    # receive a formula at all.
                    #
                    # For this implementation, we are using the master
                    # formula in the two "impl. defined" cases and no
                    # formula in the "??" case. This choice of
                    # implementation allows us to disregard the `ref`
                    # parameter altogether, and does not require
                    # computing expressions like `C5 in A1:D6`.
                    # Presumably, Excel does not generate spreadsheets
                    # with such contradictions.
                    if si in self.shared_formula_masters:
                        trans = self.shared_formula_masters[si]
                        value = trans.translate_formula(coordinate)
                    else:
                        self.shared_formula_masters[si] = Translator(value, coordinate)


        style_array = None
        if style_id is not None:
            style_id = int(style_id)
            style_array = self.styles[style_id]

        if coordinate:
            row, column = coordinate_to_tuple(coordinate)
        else:
            row, column = self._row_count, self._col_count

        cell = Cell(self.ws, row=row, col_idx=column, style_array=style_array)
        self.ws._cells[(row, column)] = cell

        if value is not None:
            if data_type == 'n':
                value = _cast_number(value)
            elif data_type == 'b':
                value = bool(int(value))
            elif data_type == 's':
                value = self.shared_strings[int(value)]
            elif data_type == 'str':
                data_type = 's'

        else:
            if data_type == 'inlineStr':
                child = element.find(self.INLINE_STRING)
                if child is not None:
                    data_type = 's'
                    richtext = Text.from_tree(child)
                    value = richtext.content

        if self.guess_types or value is None:
            cell.value = value
        else:
            cell._value=value
            cell.data_type=data_type


    def parse_merge(self, element):
        merged = MergeCells.from_tree(element)
        for c in merged.mergeCell:
            self.ws.merge_cells(c.ref)


    def parse_column_dimensions(self, col):
        attrs = dict(col.attrib)
        column = get_column_letter(int(attrs['min']))
        attrs['index'] = column
        if 'style' in attrs:
            attrs['style'] = self.styles[int(attrs['style'])]
        dim = ColumnDimension(self.ws, **attrs)
        self.ws.column_dimensions[column] = dim


    def parse_row(self, row):
        attrs = dict(row.attrib)

        if "r" in attrs:
            self._row_count = int(attrs['r'])
        else:
            self._row_count += 1
        self._col_count = 0
        keys = set(attrs)
        for key in keys:
            if key == "s":
                attrs['s'] = self.styles[int(attrs['s'])]
            elif key.startswith('{'):
                del attrs[key]


        keys = set(attrs)
        if keys != set(['r', 'spans']) and keys != set(['r']):
            # don't create dimension objects unless they have relevant information
            dim = RowDimension(self.ws, **attrs)
            self.ws.row_dimensions[dim.index] = dim

        for cell in safe_iterator(row, self.CELL_TAG):
            self.parse_cell(cell)


    def parser_conditional_formatting(self, element):
        cf = ConditionalFormatting.from_tree(element)
        for rule in cf.rules:
            if rule.dxfId is not None:
                rule.dxf = self.differential_styles[rule.dxfId]
            self.ws.conditional_formatting.add(cf.sqref, rule)


    def parse_sheet_protection(self, element):
        self.ws.protection = SheetProtection.from_tree(element)
        password = element.get("password")
        if password is not None:
            self.ws.protection.set_password(password, True)


    def parse_legacy_drawing(self, element):
        if self.keep_vba:
            # For now just save the legacy drawing id.
            # We will later look up the file name
            self.ws.legacy_drawing = element.get('{%s}id' % REL_NS)


    def parse_extensions(self, element):
        extLst = ExtensionList.from_tree(element)
        for e in extLst.ext:
            ext_type = EXT_TYPES.get(e.uri.upper(), "Unknown")
            msg = "{0} extension is not supported and will be removed".format(ext_type)
            warn(msg)


    def parse_hyperlinks(self, element):
        link = Hyperlink.from_tree(element)
        if link.id:
            rel = self.ws._rels[link.id]
            link.target = rel.Target
        if ":" in link.ref:
            # range of cells
            for row in self.ws[link.ref]:
                for cell in row:
                    cell.hyperlink = link
        else:
            self.ws[link.ref].hyperlink = link


    def parse_tables(self, element):
        for t in TablePartList.from_tree(element).tablePart:
            rel = self.ws._rels[t.id]
            self.tables.append(rel.Target)
