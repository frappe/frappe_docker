"""Tests for parsing which does not raise Exceptions normally"""
__version__ = '$Id: test_parse.py 1281 2008-06-04 21:12:29Z cthedot $'

import logging
import StringIO
import sys
import xml.dom
import basetest
import cssutils

class ErrorHandlerTestCase(basetest.BaseTestCase):

    def setUp(self):
        "replace default log and ignore its output"
        self._oldlog = cssutils.log._log
        self._saved = cssutils.log.raiseExceptions

        cssutils.log.raiseExceptions = False
        cssutils.log.setLog(logging.getLogger('IGNORED-CSSUTILS-TEST'))

    def tearDown(self):
        "reset default log"
        cssutils.log.setLog(self._oldlog)
        # for tests only
        cssutils.log.setLevel(logging.FATAL)
        cssutils.log.raiseExceptions = self._saved

    def _setHandler(self):
        "sets new handler and returns StringIO instance to getvalue"
        s = StringIO.StringIO()
        h = logging.StreamHandler(s)
        h.setFormatter(logging.Formatter('%(levelname)s    %(message)s'))
        # remove if present already
        cssutils.log.removeHandler(h)
        cssutils.log.addHandler(h)
        return s

    def test_calls(self):
        "cssutils.log.*"
        s = self._setHandler()
        cssutils.log.setLevel(logging.DEBUG)
        cssutils.log.debug('msg', neverraise=True)
        self.assertEqual(s.getvalue(), u'DEBUG    msg\n')

        s = self._setHandler()
        cssutils.log.setLevel(logging.INFO)
        cssutils.log.info('msg', neverraise=True)
        self.assertEqual(s.getvalue(), u'INFO    msg\n')

        s = self._setHandler()
        cssutils.log.setLevel(logging.WARNING)
        cssutils.log.warn('msg', neverraise=True)
        self.assertEqual(s.getvalue(), u'WARNING    msg\n')

        s = self._setHandler()
        cssutils.log.setLevel(logging.ERROR)
        cssutils.log.error('msg', neverraise=True)
        self.assertEqual(s.getvalue(), u'ERROR    msg\n')

        s = self._setHandler()
        cssutils.log.setLevel(logging.FATAL)
        cssutils.log.fatal('msg', neverraise=True)
        self.assertEqual(s.getvalue(), u'CRITICAL    msg\n')

        s = self._setHandler()
        cssutils.log.setLevel(logging.CRITICAL)
        cssutils.log.critical('msg', neverraise=True)
        self.assertEqual(s.getvalue(), u'CRITICAL    msg\n')

        s = self._setHandler()
        cssutils.log.setLevel(logging.CRITICAL)
        cssutils.log.error('msg', neverraise=True)
        self.assertEqual(s.getvalue(), u'')

    def test_linecol(self):
        "cssutils.log line col"
        o = cssutils.log.raiseExceptions
        cssutils.log.raiseExceptions = True
        
        s = cssutils.css.CSSStyleSheet()
        try:
            s.cssText = '@import x;'
        except xml.dom.DOMException, e:                
            self.assertEqual(str(e), 'CSSImportRule: Unexpected ident. [1:9: x]')
            self.assertEqual(e.line, 1)
            self.assertEqual(e.col, 9)
            if sys.platform.startswith('java'):
                self.assertEqual(e.msg, u'CSSImportRule: Unexpected ident. [1:9: x]')
            else:
                self.assertEqual(e.args, (u'CSSImportRule: Unexpected ident. [1:9: x]',))
        
        cssutils.log.raiseExceptions = o

    def test_handlers(self):
        "cssutils.log"
        s = self._setHandler()

        cssutils.log.setLevel(logging.FATAL)
        self.assertEqual(cssutils.log.getEffectiveLevel(), logging.FATAL)

        cssutils.parseString('a { color: 1 }')
        self.assertEqual(s.getvalue(), u'')

        cssutils.log.setLevel(logging.DEBUG)
        cssutils.parseString('a { color: 1 }')
        # TODO: Fix?
#        self.assertEqual(s.getvalue(),
#                         u'ERROR    Property: Invalid value for "CSS Color Module Level 3/CSS Level 2.1" property: 1 [1:5: color]\n')
        self.assertEqual(s.getvalue(),
                         u'ERROR    Property: Invalid value for "CSS Level 2.1" property: 1 [1:5: color]\n')

        s = self._setHandler()

        cssutils.log.setLevel(logging.ERROR)
        cssutils.parseUrl('http://example.com')
        self.assertEqual(s.getvalue()[:38],
                         u'ERROR    Expected "text/css" mime type')

    def test_parsevalidation(self):
        style = 'color: 1'
        t = 'a { %s }' % style
                
        cssutils.log.setLevel(logging.DEBUG)
        
        # sheet
        s = self._setHandler()
        cssutils.parseString(t)
        self.assertNotEqual(len(s.getvalue()), 0)
        
        s = self._setHandler()
        cssutils.parseString(t, validate=False)
        self.assertEqual(s.getvalue(), '')

        # style
        s = self._setHandler()
        cssutils.parseStyle(style)
        self.assertNotEqual(len(s.getvalue()), 0)

        s = self._setHandler()
        cssutils.parseStyle(style, validate=True)
        self.assertNotEqual(len(s.getvalue()), 0)

        s = self._setHandler()
        cssutils.parseStyle(style, validate=False)
        self.assertEqual(s.getvalue(), '')
               

if __name__ == '__main__':
    import unittest
    unittest.main()
