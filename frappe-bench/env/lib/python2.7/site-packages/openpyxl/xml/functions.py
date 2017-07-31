from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

"""
XML compatability functions
"""

# Python stdlib imports
import re
from functools import partial
# compatibility

# package imports
from openpyxl import LXML

if LXML is True:
    from lxml.etree import (
    Element,
    ElementTree,
    SubElement,
    fromstring,
    tostring,
    register_namespace,
    QName,
    xmlfile,
    XMLParser,
    )
    from xml.etree.cElementTree import iterparse
    # do not resolve entities
    safe_parser = XMLParser(resolve_entities=False)
    fromstring = partial(fromstring, parser=safe_parser)
else:
    try:
        from xml.etree.cElementTree import (
        ElementTree,
        Element,
        SubElement,
        fromstring,
        tostring,
        iterparse,
        QName
        )
    except ImportError:
        from xml.etree.ElementTree import (
        ElementTree,
        Element,
        SubElement,
        fromstring,
        tostring,
        iterparse,
        QName
        )
    from .namespace import register_namespace
    from et_xmlfile import xmlfile


from openpyxl.xml.constants import (
    CHART_NS,
    DRAWING_NS,
    SHEET_DRAWING_NS,
    CHART_DRAWING_NS,
    SHEET_MAIN_NS,
    REL_NS,
    VTYPES_NS,
    COREPROPS_NS,
    DCTERMS_NS,
    DCTERMS_PREFIX
)

# allow LXML interface
_iterparse = iterparse
def safe_iterparse(source, *args, **kw):
    return _iterparse(source)

iterparse = safe_iterparse


register_namespace(DCTERMS_PREFIX, DCTERMS_NS)
register_namespace('dcmitype', 'http://purl.org/dc/dcmitype/')
register_namespace('cp', COREPROPS_NS)
register_namespace('c', CHART_NS)
register_namespace('a', DRAWING_NS)
register_namespace('s', SHEET_MAIN_NS)
register_namespace('r', REL_NS)
register_namespace('vt', VTYPES_NS)
register_namespace('xdr', SHEET_DRAWING_NS)
register_namespace('cdr', CHART_DRAWING_NS)


tostring = partial(tostring, encoding="utf-8")


def safe_iterator(node, tag=None):
    """Return an iterator that is compatible with Python 2.6"""
    if node is None:
        return []
    if hasattr(node, "iter"):
        return node.iter(tag)
    else:
        return node.getiterator(tag)


NS_REGEX = re.compile("({(?P<namespace>.*)})?(?P<localname>.*)")

def localname(node):
    m = NS_REGEX.match(node.tag)
    return m.group('localname')
