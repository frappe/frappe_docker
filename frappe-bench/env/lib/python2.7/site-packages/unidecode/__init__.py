# -*- coding: utf-8 -*-
# vi:tabstop=4:expandtab:sw=4
"""Transliterate Unicode text into plain 7-bit ASCII.

Example usage:
>>> from unidecode import unidecode:
>>> unidecode(u"\u5317\u4EB0")
"Bei Jing "

The transliteration uses a straightforward map, and doesn't have alternatives
for the same character based on language, position, or anything else.

In Python 3, a standard string object will be returned. If you need bytes, use:
>>> unidecode("Κνωσός").encode("ascii")
b'Knosos'
"""
import warnings
from sys import version_info

Cache = {}


def _warn_if_not_unicode(string):
    if version_info[0] < 3 and not isinstance(string, unicode):
        warnings.warn(  "Argument %r is not an unicode object. "
                        "Passing an encoded string will likely have "
                        "unexpected results." % (type(string),),
                        RuntimeWarning, 2)


def unidecode_expect_ascii(string):
    """Transliterate an Unicode object into an ASCII string

    >>> unidecode(u"\u5317\u4EB0")
    "Bei Jing "

    This function first tries to convert the string using ASCII codec.
    If it fails (because of non-ASCII characters), it falls back to
    transliteration using the character tables.

    This is approx. five times faster if the string only contains ASCII
    characters, but slightly slower than using unidecode directly if non-ASCII
    chars are present.
    """

    _warn_if_not_unicode(string)
    try:
        bytestring = string.encode('ASCII')
    except UnicodeEncodeError:
        return _unidecode(string)
    if version_info[0] >= 3:
        return string
    else:
        return bytestring

def unidecode_expect_nonascii(string):
    """Transliterate an Unicode object into an ASCII string

    >>> unidecode(u"\u5317\u4EB0")
    "Bei Jing "
    """

    _warn_if_not_unicode(string)
    return _unidecode(string)

unidecode = unidecode_expect_ascii

def _unidecode(string):
    retval = []

    for char in string:
        codepoint = ord(char)

        if codepoint < 0x80: # Basic ASCII
            retval.append(str(char))
            continue
        
        if codepoint > 0xeffff:
            continue # Characters in Private Use Area and above are ignored

        if 0xd800 <= codepoint <= 0xdfff:
            warnings.warn(  "Surrogate character %r will be ignored. "
                            "You might be using a narrow Python build." % (char,),
                            RuntimeWarning, 2)

        section = codepoint >> 8   # Chop off the last two hex digits
        position = codepoint % 256 # Last two hex digits

        try:
            table = Cache[section]
        except KeyError:
            try:
                mod = __import__('unidecode.x%03x'%(section), globals(), locals(), ['data'])
            except ImportError:
                Cache[section] = None
                continue   # No match: ignore this character and carry on.

            Cache[section] = table = mod.data

        if table and len(table) > position:
            retval.append( table[position] )

    return ''.join(retval)
