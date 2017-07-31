from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl


from openpyxl.compat import deprecated


@deprecated("""Use from openpyxl.writer.write_only import WriteOnlyCell""")
def WriteOnlyCell(ws=None, value=None):
    from .write_only import WriteOnlyCell
    return WriteOnlyCell(ws, value)
