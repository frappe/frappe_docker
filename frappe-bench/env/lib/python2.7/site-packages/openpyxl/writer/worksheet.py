from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""Write worksheets to xml representations."""

# Python stdlib imports
from io import BytesIO
from warnings import warn

# package imports
from openpyxl.xml.functions import xmlfile
from openpyxl.xml.constants import SHEET_MAIN_NS

from openpyxl.styles.differential import DifferentialStyle
from openpyxl.packaging.relationship import Relationship, RelationshipList
from openpyxl.worksheet.merge import MergeCells, MergeCell
from openpyxl.worksheet.properties import WorksheetProperties
from openpyxl.worksheet.hyperlink import (
    Hyperlink,
    HyperlinkList,
)
from openpyxl.worksheet.related import Related
from openpyxl.worksheet.table import TablePartList
from openpyxl.worksheet.header_footer import HeaderFooter
from openpyxl.worksheet.dimensions import (
    SheetFormatProperties,
    SheetDimension,
)

from .etree_worksheet import write_rows


def write_mergecells(worksheet):
    """Write merged cells to xml."""

    merged = [MergeCell(ref) for ref in worksheet._merged_cells]

    if merged:
        return MergeCells(mergeCell=merged).to_tree()


def write_conditional_formatting(worksheet):
    """Write conditional formatting to xml."""
    df = DifferentialStyle()
    wb = worksheet.parent
    for cf in worksheet.conditional_formatting:
        for rule in cf.rules:
            if rule.dxf and rule.dxf != df:
                rule.dxfId = wb._differential_styles.add(rule.dxf)
        yield cf.to_tree()


def write_hyperlinks(worksheet):
    """Write worksheet hyperlinks to xml."""
    links = HyperlinkList()

    for link in worksheet._hyperlinks:
        if link.target:
            rel = Relationship(type="hyperlink", TargetMode="External", Target=link.target)
            worksheet._rels.append(rel)
            link.id = rel.id
        links.hyperlink.append(link)

    return links


def write_drawing(worksheet):
    """
    Add link to drawing if required
    """
    if worksheet._charts or worksheet._images:
        rel = Relationship(type="drawing", Target="")
        worksheet._rels.append(rel)
        drawing = Related()
        drawing.id = rel.id
        return drawing.to_tree("drawing")


def write_worksheet(worksheet):
    """Write a worksheet to an xml file."""

    ws = worksheet
    ws._rels = RelationshipList()
    ws._hyperlinks = []

    out = BytesIO()

    with xmlfile(out) as xf:
        with xf.element('worksheet', xmlns=SHEET_MAIN_NS):

            props = ws.sheet_properties.to_tree()
            xf.write(props)

            dim = SheetDimension(ref=ws.calculate_dimension())
            xf.write(dim.to_tree())

            xf.write(ws.views.to_tree())

            cols = ws.column_dimensions.to_tree()
            ws.sheet_format.outlineLevelCol = ws.column_dimensions.max_outline
            xf.write(ws.sheet_format.to_tree())

            if cols is not None:
                xf.write(cols)

            # write data
            write_rows(xf, ws)

            if ws.protection.sheet:
                xf.write(ws.protection.to_tree())

            if ws.auto_filter:
                xf.write(ws.auto_filter.to_tree())

            if ws.sort_state:
                xf.write(ws.sort_state.to_tree())

            merge = write_mergecells(ws)
            if merge is not None:
                xf.write(merge)

            cfs = write_conditional_formatting(ws)
            for cf in cfs:
                xf.write(cf)

            if ws.data_validations:
                xf.write(ws.data_validations.to_tree())

            hyper = write_hyperlinks(ws)
            if hyper:
                xf.write(hyper.to_tree())

            options = ws.print_options
            if dict(options):
                new_element = options.to_tree()
                xf.write(new_element)

            margins = ws.page_margins.to_tree()
            xf.write(margins)

            setup = ws.page_setup
            if dict(setup):
                new_element = setup.to_tree()
                xf.write(new_element)

            if bool(ws.HeaderFooter):
                xf.write(ws.HeaderFooter.to_tree())

            if ws.page_breaks:
                xf.write(ws.page_breaks.to_tree())

            drawing = write_drawing(ws)
            if drawing is not None:
                xf.write(drawing)

            # if there is an existing vml file associated with this sheet or if there
            # are any comments we need to add a legacyDrawing relation to the vml file.
            if (ws.legacy_drawing is not None or ws._comments):
                legacyDrawing = Related(id="anysvml")
                xml = legacyDrawing.to_tree("legacyDrawing")
                xf.write(xml)

            tables = _add_table_headers(ws)
            if tables:
                xf.write(tables.to_tree())

    xml = out.getvalue()
    out.close()
    return xml


def _add_table_headers(ws):
    """
    Check if tables have tableColumns and create them and autoFilter if necessary.
    Column headers will be taken from the first row of the table.
    """

    tables = TablePartList()

    for table in ws._tables:
        if not table.tableColumns:
            table._initialise_columns()
            if table.headerRowCount:
                row = ws[table.ref][0]
                for cell, col in zip(row, table.tableColumns):
                    if cell.data_type != "s":
                        warn("File may not be readable: column headings must be strings.")
                    col.name = str(cell.value)
        rel = Relationship(type=table._rel_type, Target="")
        ws._rels.append(rel)
        table._rel_id = rel.Id
        tables.append(Related(id=rel.Id))

    return tables
