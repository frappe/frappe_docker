from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl
#
# register_namespace function under a different licence:
# The ElementTree toolkit is
#
# Copyright (c) 1999-2008 by Fredrik Lundh
#
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# and will comply with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and
# its associated documentation for any purpose and without fee is
# hereby granted, provided that the above copyright notice appears in
# all copies, and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of
# Secret Labs AB or the author not be used in advertising or publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANT-
# ABILITY AND FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR
# BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
# --------------------------------------------------------------------
# Licensed to PSF under a Contributor Agreement.
# See http://www.python.org/psf/license for licensing details.

import re

# Python 2.6 without lxml
def register_namespace(prefix, uri):
    from xml.etree.ElementTree import _namespace_map
    if re.match("ns\d+$", prefix):
        raise ValueError("Prefix format reserved for internal use")
    for k, v in _namespace_map.items():
        if k == uri or v == prefix:
            del _namespace_map[k]
    _namespace_map[uri] = prefix


try:
    from xml.etree.cElementTree import register_namespace
except ImportError:
    try:
        from xml.etree.ElementTree import register_namespace
    except ImportError:
        pass
