"""Testcases for cssutils.stylesheets.StyleSheet"""
__version__ = '$Id: test_csspagerule.py 1869 2009-10-17 19:37:40Z cthedot $'

import xml.dom
import basetest
import cssutils

class StyleSheetTestCase(basetest.BaseTestCase):

    def test_init(self):
        "StyleSheet.__init__()"
        s = cssutils.stylesheets.StyleSheet()

        self.assertEqual(s.type, 'text/css')
        self.assertEqual(s.href, None)
        self.assertEqual(s.media, None)
        self.assertEqual(s.title, u'')
        self.assertEqual(s.ownerNode, None)
        self.assertEqual(s.parentStyleSheet, None)
        self.assertEqual(s.alternate, False)
        self.assertEqual(s.disabled, False)


        s = cssutils.stylesheets.StyleSheet(type='unknown',
                                            href='test.css',
                                            media=None,
                                            title=u'title',
                                            ownerNode=None,
                                            parentStyleSheet=None,
                                            alternate=True,
                                            disabled=True)

        self.assertEqual(s.type, 'unknown')
        self.assertEqual(s.href, 'test.css')
        self.assertEqual(s.media, None)
        self.assertEqual(s.title, u'title')
        self.assertEqual(s.ownerNode, None)
        self.assertEqual(s.parentStyleSheet, None)
        self.assertEqual(s.alternate, True)
        self.assertEqual(s.disabled, True)

if __name__ == '__main__':
    import unittest
    unittest.main()
