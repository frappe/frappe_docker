# -*- coding: utf-8 -*-
"""Testcases for new cssutils.tokenize.Tokenizer

TODO: old tests as new ones are **not complete**!
"""

import sys
import xml.dom
import basetest
import cssutils.tokenize2 as tokenize2
from cssutils.tokenize2 import *

class TokenizerTestCase(basetest.BaseTestCase):

    testsall = {
        # IDENT
        u'äöüß€': [('IDENT', u'äöüß€', 1, 1)],
        u' a ': [('S', u' ', 1, 1),
                 ('IDENT', u'a', 1, 2),
                 ('S', u' ', 1, 3)],
        u'_a': [('IDENT', u'_a', 1, 1)],
        u'-a': [('IDENT', u'-a', 1, 1)],
        u'aA-_\200\377': [('IDENT', u'aA-_\200\377', 1, 1)],
        u'a1': [('IDENT', u'a1', 1, 1)],
        # escapes must end with S or max 6 digits:
        u'\\44 b': [('IDENT', u'Db', 1, 1)],
        u'\\44  b': [('IDENT', u'D', 1, 1),
                     ('S', u' ', 1, 5),
                     ('IDENT', u'b', 1, 6)],
        u'\\44\nb': [('IDENT', u'Db', 1, 1)],
        u'\\44\rb': [('IDENT', u'Db', 1, 1)],
        u'\\44\fb': [('IDENT', u'Db', 1, 1)],
        u'\\44\n*': [('IDENT', u'D', 1, 1),
                    ('CHAR', u'*', 2, 1)],
        u'\\44  a': [('IDENT', u'D', 1, 1),
                    ('S', u' ', 1, 5),
                    ('IDENT', u'a', 1, 6)],
        # TODO:
        # Note that this means that a "real" space after the escape sequence
        # must itself either be escaped or doubled:
        u'\\44\ x': [('IDENT', u'D\\ x', 1, 1)],
        u'\\44  ': [('IDENT', u'D', 1, 1),
                     ('S', u' ', 1, 5)],

        ur'\44': [('IDENT', u'D', 1, 1)],
        ur'\\': [('IDENT', ur'\\', 1, 1)],
        ur'\{': [('IDENT', ur'\{', 1, 1)],
        ur'\"': [('IDENT', ur'\"', 1, 1)],
        ur'\(': [('IDENT', ur'\(', 1, 1)],
        ur'\1 \22 \333 \4444 \55555 \666666 \777777 7 \7777777':
            [(
                ('IDENT', u'\x01"\u0333\u4444\U00055555\\666666 \\777777 7', 1, 1)
                if sys.maxunicode > 0x10000 else
                ('IDENT', u'\x01"\u0333\u4444\\55555 \\666666 \\777777 7', 1, 1)
            ),
            ('S', ' ', 1, 43),
            ('IDENT', '\\7777777', 1, 44)
        ],
        # Not a function, important for media queries
        u'and(': [('IDENT', u'and', 1, 1), ('CHAR', u'(', 1, 4)],


        u'\\1 b': [('IDENT', u'\x01b', 1, 1)],
        u'\\44 b': [('IDENT', u'Db', 1, 1)],
        u'\\123 b': [('IDENT', u'\u0123b', 1, 1)],
        u'\\1234 b': [('IDENT', u'\u1234b', 1, 1)],
        u'\\12345 b':
            [(
                ('IDENT', u'\U00012345b', 1, 1)
                if sys.maxunicode > 0x10000 else
                ('IDENT', u'\\12345 b', 1, 1)
            )],
        u'\\123456 b': [('IDENT', u'\\123456 b', 1, 1)],
        u'\\1234567 b': [('IDENT', u'\\1234567', 1, 1),
                         ('S', u' ', 1, 9),
                         ('IDENT', u'b', 1, 10)],
        u'\\{\\}\\(\\)\\[\\]\\#\\@\\.\\,':
            [('IDENT', u'\\{\\}\\(\\)\\[\\]\\#\\@\\.\\,', 1, 1)],

        # STRING
        u' "" ': [('S', u' ', 1, 1),
                 ('STRING', u'""', 1, 2),
                 ('S', u' ', 1, 4)],
        u' "\'" ': [('S', u' ', 1, 1),
                 ('STRING', u'"\'"', 1, 2),
                 ('S', u' ', 1, 5)],
        u" '' ": [('S', u' ', 1, 1),
                 ('STRING', u"''", 1, 2),
                 ('S', u' ', 1, 4)],
        u" '' ": [('S', u' ', 1, 1),
                 ('STRING', u"''", 1, 2),
                 ('S', u' ', 1, 4)],
        # until 0.9.5.x
        #u"'\\\n'": [('STRING', u"'\\\n'", 1, 1)],
        #u"'\\\n\\\n\\\n'": [('STRING', u"'\\\n\\\n\\\n'", 1, 1)],
        #u"'\\\f'": [('STRING', u"'\\\f'", 1, 1)],
        #u"'\\\r'": [('STRING', u"'\\\r'", 1, 1)],
        #u"'\\\r\n'": [('STRING', u"'\\\r\n'", 1, 1)],
        #u"'1\\\n2'": [('STRING', u"'1\\\n2'", 1, 1)],
        # from 0.9.6a0 escaped nl is removed from string
        u"'\\\n'": [('STRING', u"''", 1, 1)],
        u"'\\\n\\\n\\\n'": [('STRING', u"''", 1, 1)],
        u"'\\\f'": [('STRING', u"''", 1, 1)],
        u"'\\\r'": [('STRING', u"''", 1, 1)],
        u"'1\\\n2'": [('STRING', u"'12'", 1, 1)],
        u"'1\\\r\n2'": [('STRING', u"'12'", 1, 1)],
        #ur'"\0020|\0020"': [('STRING', u'"\\0020|\\0020"', 1, 1)],
        ur'"\61|\0061"': [('STRING', u'"a|a"', 1, 1)],

        # HASH
        u' #a ': [('S', u' ', 1, 1),
                 ('HASH', u'#a', 1, 2),
                 ('S', u' ', 1, 4)],

        u'#ccc': [('HASH', u'#ccc', 1, 1)],
        u'#111': [('HASH', u'#111', 1, 1)],
        u'#a1a1a1': [('HASH', u'#a1a1a1', 1, 1)],
        u'#1a1a1a': [('HASH', u'#1a1a1a', 1, 1)],

        # NUMBER, for plus see CSS3
        u' 0 ': [('S', u' ', 1, 1),
                 ('NUMBER', u'0', 1, 2),
                 ('S', u' ', 1, 3)],
        u' 0.1 ': [('S', u' ', 1, 1),
                 ('NUMBER', u'0.1', 1, 2),
                 ('S', u' ', 1, 5)],
        u' .0 ': [('S', u' ', 1, 1),
                 ('NUMBER', u'.0', 1, 2),
                 ('S', u' ', 1, 4)],

        u' -0 ': [('S', u' ', 1, 1),
                 #('CHAR', u'-', 1, 2),
                 #('NUMBER', u'0', 1, 3),
                 ('NUMBER', u'-0', 1, 2),
                 ('S', u' ', 1, 4)],

        # PERCENTAGE
        u' 0% ': [('S', u' ', 1, 1),
                 ('PERCENTAGE', u'0%', 1, 2),
                 ('S', u' ', 1, 4)],
        u' .5% ': [('S', u' ', 1, 1),
                 ('PERCENTAGE', u'.5%', 1, 2),
                 ('S', u' ', 1, 5)],

        # URI
        u' url() ': [('S', u' ', 1, 1),
                 ('URI', u'url()', 1, 2),
                 ('S', u' ', 1, 7)],
        u' url(a) ': [('S', u' ', 1, 1),
                 ('URI', u'url(a)', 1, 2),
                 ('S', u' ', 1, 8)],
        u' url("a") ': [('S', u' ', 1, 1),
                 ('URI', u'url("a")', 1, 2),
                 ('S', u' ', 1, 10)],
        u' url( a ) ': [('S', u' ', 1, 1),
                 ('URI', u'url( a )', 1, 2),
                 ('S', u' ', 1, 10)],

        # UNICODE-RANGE

        # CDO
        u' <!-- ': [('S', u' ', 1, 1),
                   ('CDO', u'<!--', 1, 2),
                   ('S', u' ', 1, 6)],
        u'"<!--""-->"': [('STRING', u'"<!--"', 1, 1),
                    ('STRING', u'"-->"', 1, 7)],

        # CDC
        u' --> ': [('S', u' ', 1, 1),
                  ('CDC', u'-->', 1, 2),
                  ('S', u' ', 1, 5)],

        # S
        u' ': [('S', u' ', 1, 1)],
        u'  ': [('S', u'  ', 1, 1)],
        u'\r': [('S', u'\r', 1, 1)],
        u'\n': [('S', u'\n', 1, 1)],
        u'\r\n': [('S', u'\r\n', 1, 1)],
        u'\f': [('S', u'\f', 1, 1)],
        u'\r': [('S', u'\r', 1, 1)],
        u'\t': [('S', u'\t', 1, 1)],
        u'\r\n\r\n\f\t ': [('S', u'\r\n\r\n\f\t ', 1, 1)],

        # COMMENT, for incomplete see later
        u'/*x*/ ': [('COMMENT', u'/*x*/', 1, 1),
                    ('S', u' ', 1, 6)],

        # FUNCTION
        u' x( ': [('S', u' ', 1, 1),
                  ('FUNCTION', u'x(', 1, 2),
                  ('S', u' ', 1, 4)],

        # INCLUDES
        u' ~= ': [('S', u' ', 1, 1),
                  ('INCLUDES', u'~=', 1, 2),
                  ('S', u' ', 1, 4)],
        u'~==': [('INCLUDES', u'~=', 1, 1), ('CHAR', u'=', 1, 3)],

        # DASHMATCH
        u' |= ': [('S', u' ', 1, 1),
                  ('DASHMATCH', u'|=', 1, 2),
                  ('S', u' ', 1, 4)],
        u'|==': [('DASHMATCH', u'|=', 1, 1), ('CHAR', u'=', 1, 3)],

        # CHAR
        u' @ ': [('S', u' ', 1, 1),
                  ('CHAR', u'@', 1, 2),
                  ('S', u' ', 1, 3)],

        # --- overwritten for CSS 2.1 ---
        # LBRACE
        u' { ': [('S', u' ', 1, 1),
                 ('CHAR', u'{', 1, 2),
                 ('S', u' ', 1, 3)],
        # PLUS
        u' + ': [('S', u' ', 1, 1),
                 ('CHAR', u'+', 1, 2),
                 ('S', u' ', 1, 3)],
        # GREATER
        u' > ': [('S', u' ', 1, 1),
                 ('CHAR', u'>', 1, 2),
                 ('S', u' ', 1, 3)],
        # COMMA
        u' , ': [('S', u' ', 1, 1),
                 ('CHAR', u',', 1, 2),
                 ('S', u' ', 1, 3)],
        # class
        u' . ': [('S', u' ', 1, 1),
                  ('CHAR', u'.', 1, 2),
                  ('S', u' ', 1, 3)],
        }

    tests3 = {
        # UNICODE-RANGE
        u' u+0 ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+0', 1, 2),
                  ('S', u' ', 1, 5)],
        u' u+01 ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+01', 1, 2),
                  ('S', u' ', 1, 6)],
        u' u+012 ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+012', 1, 2),
                  ('S', u' ', 1, 7)],
        u' u+0123 ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+0123', 1, 2),
                  ('S', u' ', 1, 8)],
        u' u+01234 ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+01234', 1, 2),
                  ('S', u' ', 1, 9)],
        u' u+012345 ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+012345', 1, 2),
                  ('S', u' ', 1, 10)],
        u' u+0123456 ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+012345', 1, 2),
                  ('NUMBER', u'6', 1, 10),
                  ('S', u' ', 1, 11)],
        u' U+123456 ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'U+123456', 1, 2),
                  ('S', u' ', 1, 10)],
        u' \\55+abcdef ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'U+abcdef', 1, 2),
                  ('S', u' ', 1, 12)],
        u' \\75+abcdef ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+abcdef', 1, 2),
                  ('S', u' ', 1, 12)],
        u' u+0-1 ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+0-1', 1, 2),
                  ('S', u' ', 1, 7)],
        u' u+0-1, u+123456-abcdef ': [('S', u' ', 1, 1),
                  ('UNICODE-RANGE', u'u+0-1', 1, 2),
                  ('CHAR', u',', 1, 7),
                  ('S', u' ', 1, 8),
                  ('UNICODE-RANGE', u'u+123456-abcdef', 1, 9),
                  ('S', u' ', 1, 24)],

        # specials
        u'c\\olor': [('IDENT', u'c\\olor', 1, 1)],
        #u'-1': [('CHAR', u'-', 1, 1), ('NUMBER', u'1', 1, 2)],
        #u'-1px': [('CHAR', u'-', 1, 1), ('DIMENSION', u'1px', 1, 2)],
        u'-1': [('NUMBER', u'-1', 1, 1)],
        u'-1px': [('DIMENSION', u'-1px', 1, 1)],

        # ATKEYWORD
        u' @x ': [('S', u' ', 1, 1),
                  ('ATKEYWORD', u'@x', 1, 2),
                  ('S', u' ', 1, 4)],
        u'@X': [('ATKEYWORD', u'@X', 1, 1)],
        u'@\\x': [('ATKEYWORD', u'@\\x', 1, 1)],
        # -
        u'@1x': [('CHAR', u'@', 1, 1),
                  ('DIMENSION', u'1x', 1, 2)],

        # DIMENSION
        u' 0px ': [('S', u' ', 1, 1),
                 ('DIMENSION', u'0px', 1, 2),
                 ('S', u' ', 1, 5)],
        u' 1s ': [('S', u' ', 1, 1),
                 ('DIMENSION', u'1s', 1, 2),
                 ('S', u' ', 1, 4)],
        u'0.2EM': [('DIMENSION', u'0.2EM', 1, 1)],
        u'1p\\x': [('DIMENSION', u'1p\\x', 1, 1)],
        u'1PX': [('DIMENSION', u'1PX', 1, 1)],

        # NUMBER
        u' - 0 ': [('S', u' ', 1, 1),
                 ('CHAR', u'-', 1, 2),
                 ('S', u' ', 1, 3),
                 ('NUMBER', u'0', 1, 4),
                 ('S', u' ', 1, 5)],
        u' + 0 ': [('S', u' ', 1, 1),
                 ('CHAR', u'+', 1, 2),
                 ('S', u' ', 1, 3),
                 ('NUMBER', u'0', 1, 4),
                 ('S', u' ', 1, 5)],

        # PREFIXMATCH
        u' ^= ': [('S', u' ', 1, 1),
                  ('PREFIXMATCH', u'^=', 1, 2),
                  ('S', u' ', 1, 4)],
        u'^==': [('PREFIXMATCH', u'^=', 1, 1), ('CHAR', u'=', 1, 3)],

        # SUFFIXMATCH
        u' $= ': [('S', u' ', 1, 1),
                  ('SUFFIXMATCH', u'$=', 1, 2),
                  ('S', u' ', 1, 4)],
        u'$==': [('SUFFIXMATCH', u'$=', 1, 1), ('CHAR', u'=', 1, 3)],

        # SUBSTRINGMATCH
        u' *= ': [('S', u' ', 1, 1),
                  ('SUBSTRINGMATCH', u'*=', 1, 2),
                  ('S', u' ', 1, 4)],
        u'*==': [('SUBSTRINGMATCH', u'*=', 1, 1), ('CHAR', u'=', 1, 3)],

        # BOM only at start
#        u'\xFEFF ': [('BOM', u'\xfeFF', 1, 1),
#                  ('S', u' ', 1, 1)],
#        u' \xFEFF ': [('S', u' ', 1, 1),
#                  ('IDENT', u'\xfeFF', 1, 2),
#                  ('S', u' ', 1, 5)],
        u'\xfe\xff ': [('BOM', u'\xfe\xff', 1, 1),
                  ('S', u' ', 1, 1)],
        u' \xfe\xff ': [('S', u' ', 1, 1),
                  ('IDENT', u'\xfe\xff', 1, 2),
                  ('S', u' ', 1, 4)],
        u'\xef\xbb\xbf ': [('BOM', u'\xef\xbb\xbf', 1, 1),
                  ('S', u' ', 1, 1)],
        u' \xef\xbb\xbf ': [('S', u' ', 1, 1),
                  ('IDENT', u'\xef\xbb\xbf', 1, 2),
                  ('S', u' ', 1, 5)],        }

    tests2 = {
        # escapes work not for a-f!
        # IMPORT_SYM
        u' @import ': [('S', u' ', 1, 1),
                 ('IMPORT_SYM', u'@import', 1, 2),
                 ('S', u' ', 1, 9)],
        u'@IMPORT': [('IMPORT_SYM', u'@IMPORT', 1, 1)],
        u'@\\49\r\nMPORT': [('IMPORT_SYM', u'@\\49\r\nMPORT', 1, 1)],
        ur'@\i\m\p\o\r\t': [('IMPORT_SYM', ur'@\i\m\p\o\r\t', 1, 1)],
        ur'@\I\M\P\O\R\T': [('IMPORT_SYM', ur'@\I\M\P\O\R\T', 1, 1)],
        ur'@\49 \04d\0050\0004f\000052\54': [('IMPORT_SYM',
                                        ur'@\49 \04d\0050\0004f\000052\54',
                                        1, 1)],
        ur'@\69 \06d\0070\0006f\000072\74': [('IMPORT_SYM',
                                        ur'@\69 \06d\0070\0006f\000072\74',
                                        1, 1)],

        # PAGE_SYM
        u' @page ': [('S', u' ', 1, 1),
                 ('PAGE_SYM', u'@page', 1, 2),
                 ('S', u' ', 1, 7)],
        u'@PAGE': [('PAGE_SYM', u'@PAGE', 1, 1)],
        ur'@\pa\ge': [('PAGE_SYM', ur'@\pa\ge', 1, 1)],
        ur'@\PA\GE': [('PAGE_SYM', ur'@\PA\GE', 1, 1)],
        ur'@\50\41\47\45': [('PAGE_SYM', ur'@\50\41\47\45', 1, 1)],
        ur'@\70\61\67\65': [('PAGE_SYM', ur'@\70\61\67\65', 1, 1)],

        # MEDIA_SYM
        u' @media ': [('S', u' ', 1, 1),
                 ('MEDIA_SYM', u'@media', 1, 2),
                 ('S', u' ', 1, 8)],
        u'@MEDIA': [('MEDIA_SYM', u'@MEDIA', 1, 1)],
        ur'@\med\ia': [('MEDIA_SYM', ur'@\med\ia', 1, 1)],
        ur'@\MED\IA': [('MEDIA_SYM', ur'@\MED\IA', 1, 1)],
        u'@\\4d\n\\45\r\\44\t\\49\r\nA': [('MEDIA_SYM', u'@\\4d\n\\45\r\\44\t\\49\r\nA', 1, 1)],
        u'@\\4d\n\\45\r\\44\t\\49\r\\41\f': [('MEDIA_SYM',
                                        u'@\\4d\n\\45\r\\44\t\\49\r\\41\f',
                                        1, 1)],
        u'@\\6d\n\\65\r\\64\t\\69\r\\61\f': [('MEDIA_SYM',
                                        u'@\\6d\n\\65\r\\64\t\\69\r\\61\f',
                                        1, 1)],

        # FONT_FACE_SYM
        u' @font-face ': [('S', u' ', 1, 1),
                 ('FONT_FACE_SYM', u'@font-face', 1, 2),
                 ('S', u' ', 1, 12)],
        u'@FONT-FACE': [('FONT_FACE_SYM', u'@FONT-FACE', 1, 1)],
        ur'@f\o\n\t\-face': [('FONT_FACE_SYM', ur'@f\o\n\t\-face', 1, 1)],
        ur'@F\O\N\T\-FACE': [('FONT_FACE_SYM', ur'@F\O\N\T\-FACE', 1, 1)],
        # TODO: "-" as hex!
        ur'@\46\4f\4e\54\-\46\41\43\45': [('FONT_FACE_SYM',
            ur'@\46\4f\4e\54\-\46\41\43\45', 1, 1)],
        ur'@\66\6f\6e\74\-\66\61\63\65': [('FONT_FACE_SYM',
            ur'@\66\6f\6e\74\-\66\61\63\65', 1, 1)],

        # CHARSET_SYM only if "@charset "!
        u'@charset  ': [('CHARSET_SYM', u'@charset ', 1, 1),
                        ('S', u' ', 1, 10)],
        u' @charset  ': [('S', u' ', 1, 1),
                 ('CHARSET_SYM', u'@charset ', 1, 2), # not at start
                 ('S', u' ', 1, 11)],
        u'@charset': [('ATKEYWORD', u'@charset', 1, 1)], # no ending S
        u'@CHARSET ': [('ATKEYWORD', u'@CHARSET', 1, 1),# uppercase
                       ('S', u' ', 1, 9)],
        u'@cha\\rset ': [('ATKEYWORD', u'@cha\\rset', 1, 1), # not literal
                         ('S', u' ', 1, 10)],

        # NAMESPACE_SYM
        u' @namespace ': [('S', u' ', 1, 1),
                 ('NAMESPACE_SYM', u'@namespace', 1, 2),
                 ('S', u' ', 1, 12)],
        ur'@NAMESPACE': [('NAMESPACE_SYM', ur'@NAMESPACE', 1, 1)],
        ur'@\na\me\s\pace': [('NAMESPACE_SYM', ur'@\na\me\s\pace', 1, 1)],
        ur'@\NA\ME\S\PACE': [('NAMESPACE_SYM', ur'@\NA\ME\S\PACE', 1, 1)],
        ur'@\4e\41\4d\45\53\50\41\43\45': [('NAMESPACE_SYM',
            ur'@\4e\41\4d\45\53\50\41\43\45', 1, 1)],
        ur'@\6e\61\6d\65\73\70\61\63\65': [('NAMESPACE_SYM',
            ur'@\6e\61\6d\65\73\70\61\63\65', 1, 1)],

        # ATKEYWORD
        u' @unknown ': [('S', u' ', 1, 1),
                 ('ATKEYWORD', u'@unknown', 1, 2),
                 ('S', u' ', 1, 10)],

        # STRING
        # strings with linebreak in it
        u' "\\na"\na': [('S', u' ', 1, 1),
                   ('STRING', u'"\\na"', 1, 2),
                   ('S', u'\n', 1, 7),
                   ('IDENT', u'a', 2, 1)],
        u" '\\na'\na": [('S', u' ', 1, 1),
                   ('STRING', u"'\\na'", 1, 2),
                   ('S', u'\n', 1, 7),
                   ('IDENT', u'a', 2, 1)],
        u' "\\r\\n\\t\\n\\ra"a': [('S', u' ', 1, 1),
                   ('STRING', u'"\\r\\n\\t\\n\\ra"', 1, 2),
                   ('IDENT', u'a', 1, 15)],

        # IMPORTANT_SYM is not IDENT!!!
        u' !important ': [('S', u' ', 1, 1),
                ('CHAR', u'!', 1, 2),
                 ('IDENT', u'important', 1, 3),
                 ('S', u' ', 1, 12)],
        u'! /*1*/ important ': [
                ('CHAR', u'!', 1, 1),
                ('S', u' ', 1, 2),
                ('COMMENT', u'/*1*/', 1, 3),
                ('S', u' ', 1, 8),
                 ('IDENT', u'important', 1, 9),
                 ('S', u' ', 1, 18)],
        u'! important': [('CHAR', u'!', 1, 1),
                         ('S', u' ', 1, 2),
                         ('IDENT', u'important', 1, 3)],
        u'!\n\timportant': [('CHAR', u'!', 1, 1),
                            ('S', u'\n\t', 1, 2),
                            ('IDENT', u'important', 2, 2)],
        u'!IMPORTANT': [('CHAR', u'!', 1, 1),
                        ('IDENT', u'IMPORTANT', 1, 2)],
        ur'!\i\m\p\o\r\ta\n\t': [('CHAR', u'!', 1, 1),
                                 ('IDENT',
                                  ur'\i\m\p\o\r\ta\n\t', 1, 2)],
        ur'!\I\M\P\O\R\Ta\N\T': [('CHAR', u'!', 1, 1),
                                 ('IDENT',
                                  ur'\I\M\P\O\R\Ta\N\T', 1, 2)],
        ur'!\49\4d\50\4f\52\54\41\4e\54': [('CHAR', u'!', 1, 1),
                                           ('IDENT',
                                            ur'IMPORTANT',
                                            1, 2)],
        ur'!\69\6d\70\6f\72\74\61\6e\74': [('CHAR', u'!', 1, 1),
                                           ('IDENT',
                                            ur'important',
                                            1, 2)],
        }

    # overwriting tests in testsall
    tests2only = {
        # LBRACE
        u' { ': [('S', u' ', 1, 1),
                 ('LBRACE', u'{', 1, 2),
                 ('S', u' ', 1, 3)],
        # PLUS
        u' + ': [('S', u' ', 1, 1),
                 ('PLUS', u'+', 1, 2),
                 ('S', u' ', 1, 3)],
        # GREATER
        u' > ': [('S', u' ', 1, 1),
                 ('GREATER', u'>', 1, 2),
                 ('S', u' ', 1, 3)],
        # COMMA
        u' , ': [('S', u' ', 1, 1),
                 ('COMMA', u',', 1, 2),
                 ('S', u' ', 1, 3)],
        # class
        u' . ': [('S', u' ', 1, 1),
                 ('CLASS', u'.', 1, 2),
                 ('S', u' ', 1, 3)],
        }

    testsfullsheet = {
        # escape ends with explicit space but \r\n as single space
        u'\\65\r\nb': [('IDENT', u'eb', 1, 1)],

        # STRING
        ur'"\""': [('STRING', ur'"\""', 1, 1)],
        ur'"\" "': [('STRING', ur'"\" "', 1, 1)],
        u"""'\\''""": [('STRING', u"""'\\''""", 1, 1)],
        u'''"\\""''': [('STRING', u'''"\\""''', 1, 1)],
        u' "\na': [('S', u' ', 1, 1),
                   ('INVALID', u'"', 1, 2),
                   ('S', u'\n', 1, 3),
                   ('IDENT', u'a', 2, 1)],

        # strings with linebreak in it
        u' "\\na\na': [('S', u' ', 1, 1),
                   ('INVALID', u'"\\na', 1, 2),
                   ('S', u'\n', 1, 6),
                   ('IDENT', u'a', 2, 1)],
        u' "\\r\\n\\t\\n\\ra\na': [('S', u' ', 1, 1),
                   ('INVALID', u'"\\r\\n\\t\\n\\ra', 1, 2),
                   ('S', u'\n', 1, 14),
                   ('IDENT', u'a', 2, 1)],
        # URI
        u'ur\\l(a)': [('URI', u'ur\\l(a)', 1, 1)],
        u'url(a)': [('URI', u'url(a)', 1, 1)],
        u'\\55r\\4c(a)': [('URI', u'UrL(a)', 1, 1)],
        u'\\75r\\6c(a)': [('URI', u'url(a)', 1, 1)],
        u' url())': [('S', u' ', 1, 1),
                 ('URI', u'url()', 1, 2),
                 ('CHAR', u')', 1, 7)],
        u'url("x"))': [('URI', u'url("x")', 1, 1),
                       ('CHAR', u')', 1, 9)],
        u"url('x'))": [('URI', u"url('x')", 1, 1),
                       ('CHAR', u')', 1, 9)],
        }

    # tests if fullsheet=False is set on tokenizer
    testsfullsheetfalse = {
        # COMMENT incomplete
        u'/*': [('CHAR', u'/', 1, 1),
                ('CHAR', u'*', 1, 2)],

        # INVALID incomplete
        u' " ': [('S', u' ', 1, 1),
                 ('INVALID', u'" ', 1, 2)],
        u" 'abc\"with quote\" in it": [('S', u' ', 1, 1),
                 ('INVALID', u"'abc\"with quote\" in it", 1, 2)],

        # URI incomplete
        u'url(a': [('FUNCTION', u'url(', 1, 1),
                   ('IDENT', u'a', 1, 5)],
        u'url("a': [('FUNCTION', u'url(', 1, 1),
                   ('INVALID', u'"a', 1, 5)],
        u"url('a": [('FUNCTION', u'url(', 1, 1),
                   ('INVALID', u"'a", 1, 5)],
        u"UR\\l('a": [('FUNCTION', u'UR\\l(', 1, 1),
                   ('INVALID', u"'a", 1, 6)],
        }

    # tests if fullsheet=True is set on tokenizer
    testsfullsheettrue = {
        # COMMENT incomplete
        u'/*': [('COMMENT', u'/**/', 1, 1)],

#        # INVALID incomplete => STRING
        u' " ': [('S', u' ', 1, 1),
                 ('STRING', u'" "', 1, 2)],
        u" 'abc\"with quote\" in it": [('S', u' ', 1, 1),
                 ('STRING', u"'abc\"with quote\" in it'", 1, 2)],

        # URI incomplete FUNC => URI
        u'url(a': [('URI', u'url(a)', 1, 1)],
        u'url( a': [('URI', u'url( a)', 1, 1)],
        u'url("a': [('URI', u'url("a")', 1, 1)],
        u'url( "a ': [('URI', u'url( "a ")', 1, 1)],
        u"url('a": [('URI', u"url('a')", 1, 1)],
        u'url("a"': [('URI', u'url("a")', 1, 1)],
        u"url('a'": [('URI', u"url('a')", 1, 1)],
        }

    def setUp(self):
        #log = cssutils.errorhandler.ErrorHandler()
        self.tokenizer = Tokenizer()

#    NOT USED
#    def test_push(self):
#        "Tokenizer.push()"
#        r = []
#        def do():
#            T = Tokenizer()
#            x = False
#            for t in T.tokenize('1 x 2 3'):
#                if not x and t[1] == 'x':
#                    T.push(t)
#                    x = True
#                r.append(t[1])
#            return ''.join(r)
#
#        # push reinserts token into token stream, so x is doubled
#        self.assertEqual('1 xx 2 3', do())

#    def test_linenumbers(self):
#        "Tokenizer line + col"
#        pass

    def test_tokenize(self):
        "cssutils Tokenizer().tokenize()"
        import cssutils.cssproductions
        tokenizer = Tokenizer(cssutils.cssproductions.MACROS,
                              cssutils.cssproductions.PRODUCTIONS)
        tests = {}
        tests.update(self.testsall)
        tests.update(self.tests2)
        tests.update(self.tests3)
        tests.update(self.testsfullsheet)
        tests.update(self.testsfullsheetfalse)
        for css in tests:
            # check token format
            tokens = tokenizer.tokenize(css)
            for i, actual in enumerate(tokens):
                expected = tests[css][i]
                self.assertEqual(expected, actual)

            # check if all same number of tokens
            tokens = list(tokenizer.tokenize(css))
            self.assertEqual(len(tokens), len(tests[css]))

    def test_tokenizefullsheet(self):
        "cssutils Tokenizer().tokenize(fullsheet=True)"
        import cssutils.cssproductions
        tokenizer = Tokenizer(cssutils.cssproductions.MACROS,
                              cssutils.cssproductions.PRODUCTIONS)
        tests = {}
        tests.update(self.testsall)
        tests.update(self.tests2)
        tests.update(self.tests3)
        tests.update(self.testsfullsheet)
        tests.update(self.testsfullsheettrue)
        for css in tests:
            # check token format
            tokens = tokenizer.tokenize(css, fullsheet=True)
            for i, actual in enumerate(tokens):
                try:
                    expected = tests[css][i]
                except IndexError:
                    # EOF is added
                    self.assertEqual(actual[0], 'EOF')
                else:
                    self.assertEqual(expected, actual)

            # check if all same number of tokens
            tokens = list(tokenizer.tokenize(css, fullsheet=True))
            # EOF is added so -1
            self.assertEqual(len(tokens) - 1, len(tests[css]))


    # --------------

    def __old(self):

        testsOLD = {
            u'x x1 -x .-x #_x -': [(1, 1, tt.IDENT, u'x'),
               (1, 2, 'S', u' '),
               (1, 3, tt.IDENT, u'x1'),
               (1, 5, 'S', u' '),
               (1, 6, tt.IDENT, u'-x'),
               (1, 8, 'S', u' '),
               (1, 9, tt.CLASS, u'.'),
               (1, 10, tt.IDENT, u'-x'),
               (1, 12, 'S', u' '),
               (1, 13, tt.HASH, u'#_x'),
               (1, 16, 'S', u' '),
               (1, 17, 'DELIM', u'-')],

            # num
            u'1 1.1 -1 -1.1 .1 -.1 1.': [(1, 1, tt.NUMBER, u'1'),
               (1, 2, 'S', u' '), (1, 3, tt.NUMBER, u'1.1'),
               (1, 6, 'S', u' '), (1, 7, tt.NUMBER, u'-1'),
               (1, 9, 'S', u' '), (1, 10, tt.NUMBER, u'-1.1'),
               (1, 14, 'S', u' '), (1, 15, tt.NUMBER, u'0.1'),
               (1, 17, 'S', u' '), (1, 18, tt.NUMBER, u'-0.1'),
               (1, 21, 'S', u' '),
               (1, 22, tt.NUMBER, u'1'), (1, 23, tt.CLASS, u'.')
                                         ],
            # CSS3 pseudo
            u'::': [(1, 1, tt.PSEUDO_ELEMENT, u'::')],

            # SPECIALS
            u'*+>~{},': [(1, 1, tt.UNIVERSAL, u'*'),
               (1, 2, tt.PLUS, u'+'),
               (1, 3, tt.GREATER, u'>'),
               (1, 4, tt.TILDE, u'~'),
               (1, 5, tt.LBRACE, u'{'),
               (1, 6, tt.RBRACE, u'}'),
               (1, 7, tt.COMMA, u',')],

            # DELIM
            u'!%:&$|': [(1, 1, 'DELIM', u'!'),
               (1, 2, 'DELIM', u'%'),
               (1, 3, 'DELIM', u':'),
               (1, 4, 'DELIM', u'&'),
               (1, 5, 'DELIM', u'$'),
               (1, 6, 'DELIM', u'|')],


            # DIMENSION
            u'5em': [(1, 1, tt.DIMENSION, u'5em')],
            u' 5em': [(1, 1, 'S', u' '), (1, 2, tt.DIMENSION, u'5em')],
            u'5em ': [(1, 1, tt.DIMENSION, u'5em'), (1, 4, 'S', u' ')],

            u'-5em': [(1, 1, tt.DIMENSION, u'-5em')],
            u' -5em': [(1, 1, 'S', u' '), (1, 2, tt.DIMENSION, u'-5em')],
            u'-5em ': [(1, 1, tt.DIMENSION, u'-5em'), (1, 5, 'S', u' ')],

            u'.5em': [(1, 1, tt.DIMENSION, u'0.5em')],
            u' .5em': [(1, 1, 'S', u' '), (1, 2, tt.DIMENSION, u'0.5em')],
            u'.5em ': [(1, 1, tt.DIMENSION, u'0.5em'), (1, 5, 'S', u' ')],

            u'-.5em': [(1, 1, tt.DIMENSION, u'-0.5em')],
            u' -.5em': [(1, 1, 'S', u' '), (1, 2, tt.DIMENSION, u'-0.5em')],
            u'-.5em ': [(1, 1, tt.DIMENSION, u'-0.5em'), (1, 6, 'S', u' ')],

            u'5em5_-': [(1, 1, tt.DIMENSION, u'5em5_-')],

            u'a a5 a5a 5 5a 5a5': [(1, 1, tt.IDENT, u'a'),
               (1, 2, 'S', u' '),
               (1, 3, tt.IDENT, u'a5'),
               (1, 5, 'S', u' '),
               (1, 6, tt.IDENT, u'a5a'),
               (1, 9, 'S', u' '),
               (1, 10, tt.NUMBER, u'5'),
               (1, 11, 'S', u' '),
               (1, 12, tt.DIMENSION, u'5a'),
               (1, 14, 'S', u' '),
               (1, 15, tt.DIMENSION, u'5a5')],

            # URI
            u'url()': [(1, 1, tt.URI, u'url()')],
            u'url();': [(1, 1, tt.URI, u'url()'), (1, 6, tt.SEMICOLON, ';')],
            u'url("x")': [(1, 1, tt.URI, u'url("x")')],
            u'url( "x")': [(1, 1, tt.URI, u'url("x")')],
            u'url("x" )': [(1, 1, tt.URI, u'url("x")')],
            u'url( "x" )': [(1, 1, tt.URI, u'url("x")')],
            u' url("x")': [
                (1, 1, 'S', u' '),
                (1, 2, tt.URI, u'url("x")')],
            u'url("x") ': [
                (1, 1, tt.URI, u'url("x")'),
                (1, 9, 'S', u' '),
                ],
            u'url(ab)': [(1, 1, tt.URI, u'url(ab)')],
            u'url($#/ab)': [(1, 1, tt.URI, u'url($#/ab)')],
            u'url(\1233/a/b)': [(1, 1, tt.URI, u'url(\1233/a/b)')],
            # not URI
            u'url("1""2")': [
                (1, 1, tt.FUNCTION, u'url('),
                (1, 5, tt.STRING, u'"1"'),
                (1, 8, tt.STRING, u'"2"'),
                (1, 11, tt.RPARANTHESIS, u')'),
                ],
            u'url(a"2")': [
                (1, 1, tt.FUNCTION, u'url('),
                (1, 5, tt.IDENT, u'a'),
                (1, 6, tt.STRING, u'"2"'),
                (1, 9, tt.RPARANTHESIS, u')'),
                ],
            u'url(a b)': [
                (1, 1, tt.FUNCTION, u'url('),
                (1, 5, tt.IDENT, u'a'),
                (1, 6, 'S', u' '),
                (1, 7, tt.IDENT, u'b'),
                (1, 8, tt.RPARANTHESIS, u')'),
                ],

            # FUNCTION
            u' counter("x")': [
               (1,1, 'S', u' '),
               (1, 2, tt.FUNCTION, u'counter('),
               (1, 10, tt.STRING, u'"x"'),
               (1, 13, tt.RPARANTHESIS, u')')],
            # HASH
            u'# #a #_a #-a #1': [
                (1, 1, 'DELIM', u'#'),
                (1, 2, 'S', u' '),
                (1, 3, tt.HASH, u'#a'),
                (1, 5, 'S', u' '),
                (1, 6, tt.HASH, u'#_a'),
                (1, 9, 'S', u' '),
                (1, 10, tt.HASH, u'#-a'),
                (1, 13, 'S', u' '),
                (1, 14, tt.HASH, u'#1')
                ],
            u'#1a1 ': [
                (1, 1, tt.HASH, u'#1a1'),
                (1, 5, 'S', u' '),
                ],
            u'#1a1\n': [
                (1, 1, tt.HASH, u'#1a1'),
                (1, 5, 'S', u'\n'),
                ],
            u'#1a1{': [
                (1, 1, tt.HASH, u'#1a1'),
                (1, 5, tt.LBRACE, u'{'),
                ],
            u'#1a1 {': [
                (1, 1, tt.HASH, u'#1a1'),
                (1, 5, 'S', u' '),
                (1, 6, tt.LBRACE, u'{'),
                ],
            u'#1a1\n{': [
                (1, 1, tt.HASH, u'#1a1'),
                (1, 5, 'S', u'\n'),
                (2, 1, tt.LBRACE, u'{'),
                ],
            u'#1a1\n {': [
                (1, 1, tt.HASH, u'#1a1'),
                (1, 5, 'S', u'\n '),
                (2, 2, tt.LBRACE, u'{'),
                ],
            u'#1a1 \n{': [
                (1, 1, tt.HASH, u'#1a1'),
                (1, 5, 'S', u' \n'),
                (2, 1, tt.LBRACE, u'{'),
                ],
            # STRINGS with NL
            u'"x\n': [(1,1, tt.INVALID, u'"x\n')],
            u'"x\r': [(1,1, tt.INVALID, u'"x\r')],
            u'"x\f': [(1,1, tt.INVALID, u'"x\f')],
            u'"x\n ': [
               (1,1, tt.INVALID, u'"x\n'),
               (2,1, 'S', u' ')
               ]

            }

        tests = {
            u'/*a': xml.dom.SyntaxErr,
            u'"a': xml.dom.SyntaxErr,
            u"'a": xml.dom.SyntaxErr,
            u"\\0 a": xml.dom.SyntaxErr,
            u"\\00": xml.dom.SyntaxErr,
            u"\\000": xml.dom.SyntaxErr,
            u"\\0000": xml.dom.SyntaxErr,
            u"\\00000": xml.dom.SyntaxErr,
            u"\\000000": xml.dom.SyntaxErr,
            u"\\0000001": xml.dom.SyntaxErr
            }
#        self.tokenizer.log.raiseExceptions = True #!!
#        for css, exception in tests.items():
#            self.assertRaises(exception, self.tokenizer.tokenize, css)


class TokenizerUtilsTestCase(basetest.BaseTestCase):
    """Tests for the util functions of tokenize"""
    __metaclass__ = basetest.GenerateTests

    def gen_test_has_at(self, string, pos, text, expected):
        self.assertEqual(tokenize2.has_at(string, pos, text), expected)
    gen_test_has_at.cases = [
        ('foo', 0, 'foo', True),
        ('foo', 0, 'f', True),
        ('foo', 1, 'o', True),
        ('foo', 1, 'oo', True),
        ('foo', 4, 'foo', False),
        ('foo', 0, 'bar', False),
        ('foo', 0, 'foobar', False),
    ]

    def gen_test_suffix_eq(self, string, pos, suffix, expected):
        self.assertEqual(tokenize2.suffix_eq(string, pos, suffix), expected)
    gen_test_suffix_eq.cases = [
        ('foobar', 0, 'foobar', True),
        ('foobar', 3, 'bar', True),
        ('foobar', 3, 'foo', False),
        ('foobar', 10, 'bar', False),
    ]


if __name__ == '__main__':
    import unittest
    unittest.main()
