# -*- coding: iso-8859-1 -*-
"""Testcases for cssutils.stylesheets.MediaQuery"""

import xml.dom
import basetest
import cssutils.stylesheets

class MediaQueryTestCase(basetest.BaseTestCase):

    def setUp(self):
        super(MediaQueryTestCase, self).setUp()
        self.r = cssutils.stylesheets.MediaQuery()

    def test_mediaText(self):
        "MediaQuery.mediaText"
        tests = {
            u'all': None,
            u'braille': None,
            u'embossed': None,
            u'handheld': None,
            u'print': None,
            u'projection': None,
            u'screen': None,
            u'speech': None,
            u'tty': None,
            u'tv': None,
            u'ALL': None,
            u'a\\ll': None,
            u'not tv': None,
            u'n\\ot t\\v': None,
            u'only tv': None,
            u'\\only \\tv': None,
            u'PRINT': None,
            u'NOT PRINT': None,
            u'ONLY PRINT': None,
            u'tv and (color)': None,
            u'not tv and (color)': None,
            u'only tv and (color)': None,
            u'print and(color)': u'print and (color)'
            }
        self.do_equal_r(tests, att='mediaText')

        tests = {
            u'': xml.dom.SyntaxErr,
            u'two values': xml.dom.SyntaxErr,
            u'or even three': xml.dom.SyntaxErr,
            u'aural': xml.dom.SyntaxErr, # a dimension
            u'3d': xml.dom.SyntaxErr, # a dimension
            }
        self.do_raise_r(tests, att='_setMediaText')        

    def test_mediaType(self):
        "MediaQuery.mediaType"
        mq = cssutils.stylesheets.MediaQuery()

        self.assertEqual(u'', mq.mediaText)

        for mt in cssutils.stylesheets.MediaQuery.MEDIA_TYPES:
            mq.mediaType = mt
            self.assertEqual(mq.mediaType, mt)
            mq.mediaType = mt.upper()
            self.assertEqual(mq.mediaType, mt.upper())

        mt = u'3D-UNKOwn-MEDIAtype0123'
        #mq.mediaType = mt
        self.assertRaises(xml.dom.SyntaxErr, mq._setMediaType, mt)
        #self.assertRaises(xml.dom.InvalidCharacterErr, mq._setMediaType, mt)

    def test_comments(self):
        "MediaQuery.mediaText comments"
        tests = {
            u'all': None,
            u'print': None,
            u'not print': None,
            u'only print': None,
            u'print and (color)': None,
            u'print and (color) and (width)': None,
            u'print and (color: 2)': None,
            u'print and (min-width: 100px)': None,
            u'print and (min-width: 100px) and (color: red)': None,
            u'not print and (min-width: 100px)': None,
            u'only print and (min-width: 100px)': None,
            u'/*1*/ tv /*2*/': None,
            u'/*0*/ only /*1*/ tv /*2*/': None,
            u'/*0* /not /*1*/ tv /*2*/': None,
            u'/*x*/ only /*x*/ print /*x*/ and /*x*/ (/*x*/ min-width /*x*/: /*x*/ 100px /*x*/)': None,
            u'print and/*1*/(color)': u'print and /*1*/ (color)'
            }
        self.do_equal_r(tests, att='mediaText')

    def test_reprANDstr(self):
        "MediaQuery.__repr__(), .__str__()"
        mediaText='tv and (color)'
        s = cssutils.stylesheets.MediaQuery(mediaText=mediaText)
        self.assertTrue(mediaText in str(s))
        s2 = eval(repr(s))
        self.assertEqual(mediaText, s2.mediaText)
        self.assertTrue(isinstance(s2, s.__class__))


if __name__ == '__main__':
    import unittest
    unittest.main()
