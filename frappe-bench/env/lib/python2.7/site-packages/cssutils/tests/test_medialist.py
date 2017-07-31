# -*- coding: iso-8859-1 -*-
"""Testcases for cssutils.stylesheets.MediaList"""

import xml.dom
import basetest
import cssutils.stylesheets

class MediaListTestCase(basetest.BaseTestCase):

    def setUp(self):
        super(MediaListTestCase, self).setUp()
        self.r = cssutils.stylesheets.MediaList()

    def test_set(self):
        "MediaList.mediaText 1"
        ml = cssutils.stylesheets.MediaList()

        self.assertEqual(0, ml.length)
        self.assertEqual(u'all', ml.mediaText)

        ml.mediaText = u' print   , screen '
        self.assertEqual(2, ml.length)
        self.assertEqual(u'print, screen', ml.mediaText)
        
        #self.assertRaisesMsg(xml.dom.InvalidModificationErr, 
        #                     basetest.msg3x('''MediaList: Ignoring new medium cssutils.stylesheets.MediaQuery(mediaText=u'tv') as already specified "all" (set ``mediaText`` instead).'''), 
        #                     ml._setMediaText, u' print , all  , tv ')
        #
        #self.assertEqual(u'all', ml.mediaText)
        #self.assertEqual(1, ml.length)

        self.assertRaises(xml.dom.SyntaxErr,
                          ml.appendMedium, u'test')

    def test_appendMedium(self):
        "MediaList.appendMedium() 1"
        ml = cssutils.stylesheets.MediaList()

        ml.appendMedium(u'print')
        self.assertEqual(1, ml.length)
        self.assertEqual(u'print', ml.mediaText)

        ml.appendMedium(u'screen')
        self.assertEqual(2, ml.length)
        self.assertEqual(u'print, screen', ml.mediaText)

        # automatic del and append!
        ml.appendMedium(u'print')
        self.assertEqual(2, ml.length)
        self.assertEqual(u'screen, print', ml.mediaText)

        # automatic del and append!
        ml.appendMedium(u'SCREEN')
        self.assertEqual(2, ml.length)
        self.assertEqual(u'print, SCREEN', ml.mediaText)

        # append invalid MediaQuery
        mq = cssutils.stylesheets.MediaQuery()
        ml.appendMedium(mq)
        self.assertEqual(2, ml.length)
        self.assertEqual(u'print, SCREEN', ml.mediaText)
        
        # append()
        mq = cssutils.stylesheets.MediaQuery('tv')
        ml.append(mq)
        self.assertEqual(3, ml.length)
        self.assertEqual(u'print, SCREEN, tv', ml.mediaText)

        # __setitem__
        self.assertRaises(IndexError, ml.__setitem__, 10, 'all')
        ml[0] = 'handheld'
        self.assertEqual(3, ml.length)
        self.assertEqual(u'handheld, SCREEN, tv', ml.mediaText)

    def test_appendAll(self):
        "MediaList.append() 2"
        ml = cssutils.stylesheets.MediaList()
        ml.appendMedium(u'print')
        ml.appendMedium(u'tv')
        self.assertEqual(2, ml.length)
        self.assertEqual(u'print, tv', ml.mediaText)

        ml.appendMedium(u'all')
        self.assertEqual(1, ml.length)
        self.assertEqual(u'all', ml.mediaText)

        self.assertRaisesMsg(xml.dom.InvalidModificationErr, 
                             basetest.msg3x('''MediaList: Ignoring new medium cssutils.stylesheets.MediaQuery(mediaText=u'tv') as already specified "all" (set ``mediaText`` instead).'''), 
                             ml.appendMedium, 'tv')
        self.assertEqual(1, ml.length)
        self.assertEqual(u'all', ml.mediaText)

        self.assertRaises(xml.dom.SyntaxErr, ml.appendMedium, u'test')

    def test_append2All(self):
        "MediaList all"
        ml = cssutils.stylesheets.MediaList()
        ml.appendMedium(u'all')
        self.assertRaisesMsg(xml.dom.InvalidModificationErr, 
                             basetest.msg3x('''MediaList: Ignoring new medium cssutils.stylesheets.MediaQuery(mediaText=u'print') as already specified "all" (set ``mediaText`` instead).'''), 
                             ml.appendMedium, 'print')
        
        sheet = cssutils.parseString('@media all, print { /**/ }')
        self.assertEqual(u'@media all {\n    /**/\n    }'.encode(), sheet.cssText)

    def test_delete(self):
        "MediaList.deleteMedium()"
        ml = cssutils.stylesheets.MediaList()

        self.assertRaises(xml.dom.NotFoundErr, ml.deleteMedium, u'all')
        self.assertRaises(xml.dom.NotFoundErr, ml.deleteMedium, u'test')

        ml.appendMedium(u'print')
        ml.deleteMedium(u'print')
        ml.appendMedium(u'tV')
        ml.deleteMedium(u'Tv')
        self.assertEqual(0, ml.length)
        self.assertEqual(u'all', ml.mediaText)

    def test_item(self):
        "MediaList.item()"
        ml = cssutils.stylesheets.MediaList()
        ml.appendMedium(u'print')
        ml.appendMedium(u'screen')

        self.assertEqual(u'print', ml.item(0))
        self.assertEqual(u'screen', ml.item(1))
        self.assertEqual(None, ml.item(2))

    # REMOVED special case!
    #def test_handheld(self):
    #    "MediaList handheld"
    #    ml = cssutils.stylesheets.MediaList()

    #    ml.mediaText = u' handheld , all  '
    #    self.assertEqual(2, ml.length)
    #    self.assertEqual(u'handheld, all', ml.mediaText)
        
    #    self.assertRaisesMsg(xml.dom.InvalidModificationErr, 
    #                         basetest.msg3x('''MediaList: Ignoring new medium cssutils.stylesheets.MediaQuery(mediaText=u'handheld') as already specified "all" (set ``mediaText`` instead).'''), 
    #                         ml._setMediaText, u' handheld , all  , tv ')
        
    def test_mediaText(self):
        "MediaList.mediaText 2"
        tests = {
            u'ALL': u'ALL',
            u'Tv': u'Tv',
            u'all': None,
            u'all, handheld': u'all',
            u'tv': None,
            u'tv, handheld, print': None,
            u'tv and (color), handheld and (width: 1px) and (color)': None,
            }
        self.do_equal_r(tests, att='mediaText')

        tests = {
            u'': xml.dom.SyntaxErr,
            u'UNKNOWN': xml.dom.SyntaxErr,
            u'a,b': xml.dom.SyntaxErr,
            u'a and (color)': xml.dom.SyntaxErr,
            u'not': xml.dom.SyntaxErr, # known but need media
            u'only': xml.dom.SyntaxErr, # known but need media
            u'not tv,': xml.dom.SyntaxErr, # known but need media
            u'all;': xml.dom.SyntaxErr,
            u'all, and(color)': xml.dom.SyntaxErr,
            u'all,': xml.dom.SyntaxErr,
            u'all, ': xml.dom.SyntaxErr,
            u'all ,': xml.dom.SyntaxErr,
            u'all, /*1*/': xml.dom.SyntaxErr,
            u'all and (color),': xml.dom.SyntaxErr,
            u'all tv, print': xml.dom.SyntaxErr,
            }
        self.do_raise_r(tests, att='_setMediaText')

    def test_comments(self):
        "MediaList.mediaText comments"
        tests = {
            u'/*1*/ tv /*2*/, /*3*/ handheld /*4*/, print': 
            u'/*1*/ tv /*2*/ /*3*/, handheld /*4*/, print',
            }
        self.do_equal_r(tests, att='mediaText')

    def test_reprANDstr(self):
        "MediaList.__repr__(), .__str__()"
        mediaText='tv, print'

        s = cssutils.stylesheets.MediaList(mediaText=mediaText)

        self.assertTrue(mediaText in str(s))

        s2 = eval(repr(s))
        self.assertTrue(isinstance(s2, s.__class__))
        self.assertTrue(mediaText == s2.mediaText)


if __name__ == '__main__':
    import unittest
    unittest.main()
