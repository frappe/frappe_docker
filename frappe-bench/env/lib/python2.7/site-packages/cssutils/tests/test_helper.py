# -*- coding: utf-8 -*-
"""Testcases for cssutils.helper"""
__version__ = '$Id: test_util.py 1437 2008-08-18 20:30:38Z cthedot $'

import basetest
from cssutils.helper import * 

class HelperTestCase(basetest.BaseTestCase):

    def test_normalize(self):
        "helper._normalize()"
        tests = {u'abcdefg ABCDEFG äöüß€ AÖÜ': ur'abcdefg abcdefg äöüß€ aöü',
                 ur'\ga\Ga\\\ ': ur'gaga\ ',
                 ur'0123456789': ur'0123456789',
                 ur'"\x"': ur'"x"',
                 # unicode escape seqs should have been done by
                 # the tokenizer...
                 }
        for test, exp in tests.items():
            self.assertEqual(normalize(test), exp)
            # static too
            self.assertEqual(normalize(test), exp)

#    def test_normalnumber(self):
#        "helper.normalnumber()"
#        tests = {
#                 '0': '0',
#                 '00': '0',
#                 '0.0': '0',
#                 '00.0': '0',
#                 '1': '1',
#                 '01': '1',
#                 '00.1': '0.1',
#                 '0.00001': '0.00001',
#                 '-0': '0',
#                 '-00': '0',
#                 '-0.0': '0',
#                 '-00.0': '0',
#                 '-1': '-1',
#                 '-01': '-1',
#                 '-00.1': '-0.1',
#                 '-0.00001': '-0.00001',
#                 }
#        for test, exp in tests.items():
#            self.assertEqual(exp, normalnumber(test))

    def test_string(self):
        "helper.string()"
        self.assertEqual(u'"x"', string(u'x'))
        self.assertEqual(u'"1 2ä€"', string(u'1 2ä€'))
        self.assertEqual(ur'''"'"''', string(u"'"))
        self.assertEqual(ur'"\""', string(u'"'))
        # \n = 0xa, \r = 0xd, \f = 0xc
        self.assertEqual(ur'"\a "', string('''
'''))
        self.assertEqual(ur'"\c "', string('\f'))
        self.assertEqual(ur'"\d "', string('\r'))
        self.assertEqual(ur'"\d \a "', string('\r\n'))

    def test_stringvalue(self):
        "helper.stringvalue()"
        self.assertEqual(u'x', stringvalue(u'"x"'))
        self.assertEqual(u'"', stringvalue(u'"\\""'))
        self.assertEqual(ur'x', stringvalue(ur"\x "))
        
        # escapes should have been done by tokenizer
        # so this shoule not happen at all:
        self.assertEqual(ur'a', stringvalue(ur"\a "))

    def test_uri(self):
        "helper.uri()"
        self.assertEqual(u'url(x)', uri('x'))
        self.assertEqual(u'url("(")', uri('('))
        self.assertEqual(u'url(")")', uri(')'))
        self.assertEqual(u'url(" ")', uri(' '))
        self.assertEqual(u'url(";")', uri(';'))
        self.assertEqual(u'url(",")', uri(','))
        self.assertEqual(u'url("x)x")', uri('x)x'))

    def test_urivalue(self):
        "helper.urivalue()"
        self.assertEqual(u'x', urivalue('url(x)'))
        self.assertEqual(u'x', urivalue('url("x")'))
        self.assertEqual(u')', urivalue('url(")")'))


if __name__ == '__main__':
    import unittest
    unittest.main()
