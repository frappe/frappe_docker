# -*- coding: utf-8 -*-
"""Testcases for cssutils.css.CSSComment"""

import xml
import test_cssrule
import cssutils.css

class CSSCommentTestCase(test_cssrule.CSSRuleTestCase):

    def setUp(self):
        super(CSSCommentTestCase, self).setUp()
        self.r = cssutils.css.CSSComment()
        self.rRO = cssutils.css.CSSComment(readonly=True)
        self.r_type = cssutils.css.CSSComment.COMMENT
        self.r_typeString = 'COMMENT'

    def test_init(self):
        "CSSComment.type and init"
        super(CSSCommentTestCase, self).test_init()

    def test_csstext(self):
        "CSSComment.cssText"
        tests = {
            u'/*öäüß€ÖÄÜ*/': u'/*\xf6\xe4\xfc\xdf\u20ac\xd6\xc4\xdc*/',
            u'/*x*/': None,
            u'/* x */': None,
            u'/*\t12\n*/': None,
            u'/* /* */': None,
            u'/* \\*/': None,
            u'/*"*/': None,
            u'''/*"
            */''': None,
            u'/** / ** //*/': None
            }
        self.do_equal_r(tests) # set cssText
        tests.update({
            u'/*x': u'/*x*/',
            u'\n /*': u'/**/',
            })
        self.do_equal_p(tests) # parse

        tests = {
            u'/* */ ': xml.dom.InvalidModificationErr,
            u'/* *//**/': xml.dom.InvalidModificationErr,
            u'/* */1': xml.dom.InvalidModificationErr,
            u'/* */ */': xml.dom.InvalidModificationErr,
            u'  */ /* ': xml.dom.InvalidModificationErr,
            u'*/': xml.dom.InvalidModificationErr,
            u'@x /* x */': xml.dom.InvalidModificationErr
            }
        self.do_raise_r(tests) # set cssText
        # no raising of error possible?
        # self.do_raise_p(tests) # parse

    def test_InvalidModificationErr(self):
        "CSSComment.cssText InvalidModificationErr"
        self._test_InvalidModificationErr(u'/* comment */')

    def test_reprANDstr(self):
        "CSSComment.__repr__(), .__str__()"
        text = '/* test */'

        s = cssutils.css.CSSComment(cssText=text)

        s2 = eval(repr(s))
        self.assertTrue(isinstance(s2, s.__class__))
        self.assertTrue(text == s2.cssText)

if __name__ == '__main__':
    import unittest
    unittest.main()
