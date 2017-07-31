"""Testcases for cssutils.css.selectorlist.SelectorList."""

import xml.dom
import basetest
import cssutils
from cssutils.css.selectorlist import SelectorList

class SelectorListTestCase(basetest.BaseTestCase):

    def setUp(self):
        self.r = SelectorList()

    def test_init(self):
        "SelectorList.__init__() and .length"
        s = SelectorList()
        self.assertEqual(0, s.length)

        s = SelectorList('a, b')
        self.assertEqual(2, s.length)
        self.assertEqual(u'a, b', s.selectorText)

        s = SelectorList(selectorText='a')
        self.assertEqual(1, s.length)
        self.assertEqual(u'a', s.selectorText)

        s = SelectorList(selectorText=('p|a', {'p': 'uri'})) # n-dict
        self.assertEqual(1, s.length)
        self.assertEqual(u'p|a', s.selectorText)

        s = SelectorList(selectorText=('p|a', (('p', 'uri'),))) # n-tuples
        self.assertEqual(1, s.length)
        self.assertEqual(u'p|a', s.selectorText)

    def test_parentRule(self):
        "Selector.parentRule"
        def check(style):
            self.assertEqual(style, style.selectorList.parentRule)
            for sel in style.selectorList:
                self.assertEqual(style.selectorList, sel.parent)
        
        style = cssutils.css.CSSStyleRule('a, b')
        check(style)

        # add new selector
        style.selectorList.append(cssutils.css.Selector('x'))
        check(style)

        # replace selectorList
        style.selectorList = cssutils.css.SelectorList('x')
        check(style)

        # replace selectorText
        style.selectorText = ('x, y')
        check(style)
            
    def test_appendSelector(self):
        "SelectorList.appendSelector() and .length"
        s = SelectorList()
        s.appendSelector('a')
        self.assertEqual(1, s.length)

        self.assertRaises(xml.dom.InvalidModificationErr,
                          s.appendSelector, 'b,')
        self.assertEqual(1, s.length)

        self.assertEqual(u'a', s.selectorText)

        s.append('b')
        self.assertEqual(2, s.length)
        self.assertEqual(u'a, b', s.selectorText)

        s.append('a')
        self.assertEqual(2, s.length)
        self.assertEqual(u'b, a', s.selectorText)
        
        # __setitem__    
        self.assertRaises(IndexError, s.__setitem__, 4, 'x')
        s[1] = 'c'
        self.assertEqual(2, s.length)
        self.assertEqual(u'b, c', s.selectorText)
        # TODO: remove duplicates?
#        s[0] = 'c'
#        self.assertEqual(1, s.length)
#        self.assertEqual(u'c', s.selectorText)

        s = SelectorList()
        s.appendSelector(('p|a', {'p': 'uri', 'x': 'xxx'}))
        self.assertEqual(u'p|a', s.selectorText)
        # x gets lost as not used
        self.assertRaises(xml.dom.NamespaceErr, s.append, 'x|a')
        # not set at all
        self.assertRaises(xml.dom.NamespaceErr, s.append, 'y|a')
        # but p is retained
        s.append('p|b')
        self.assertEqual(u'p|a, p|b', s.selectorText)

    def test_selectorText(self):
        "SelectorList.selectorText"
        s = SelectorList()
        s.selectorText = u'a, b'
        self.assertEqual(u'a, b', s.selectorText)
        self.assertRaises(xml.dom.SyntaxErr, s._setSelectorText, u',')
        # not changed as invalid!
        self.assertEqual(u'a, b', s.selectorText)

        tests = {
            u'*': None,
            u'/*1*/*': None,
            u'/*1*/*, a': None,
            u'a, b': None,
            u'a ,b': u'a, b',
            u'a , b': u'a, b',
            u'a, b, c': u'a, b, c',
            u'#a, x#a, .b, x.b': u'#a, x#a, .b, x.b',
            (u'[p|a], p|*', (('p', 'uri'),)): u'[p|a], p|*',
            }
        # do not parse as not complete
        self.do_equal_r(tests, att='selectorText')

        tests = {
            u'x|*': xml.dom.NamespaceErr,
            u'': xml.dom.SyntaxErr,
            u' ': xml.dom.SyntaxErr,
            u',': xml.dom.SyntaxErr,
            u'a,': xml.dom.SyntaxErr,
            u',a': xml.dom.SyntaxErr,
            u'/* 1 */,a': xml.dom.SyntaxErr,
            }
        # only set as not complete
        self.do_raise_r(tests, att='_setSelectorText')

    def test_reprANDstr(self):
        "SelectorList.__repr__(), .__str__()"
        sel=(u'a, p|b', { 'p': 'uri'})
        
        s = cssutils.css.SelectorList(selectorText=sel)

        self.assertTrue(sel[0] in str(s))

        s2 = eval(repr(s))
        self.assertTrue(isinstance(s2, s.__class__))
        self.assertEqual(sel[0], s2.selectorText)


if __name__ == '__main__':
    import unittest
    unittest.main()
