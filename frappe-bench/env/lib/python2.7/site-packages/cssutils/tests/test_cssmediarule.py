"""Testcases for cssutils.css.CSSMediaRule"""

import xml.dom
import test_cssrule
import cssutils

class CSSMediaRuleTestCase(test_cssrule.CSSRuleTestCase):

    def setUp(self):
        super(CSSMediaRuleTestCase, self).setUp()
        self.r = cssutils.css.CSSMediaRule()
        self.rRO = cssutils.css.CSSMediaRule(readonly=True)
        self.r_type = cssutils.css.CSSMediaRule.MEDIA_RULE
        self.r_typeString = 'MEDIA_RULE'
        # for tests
        self.stylerule = cssutils.css.CSSStyleRule()
        self.stylerule.cssText = u'a {}'
        
    def test_init(self):
        "CSSMediaRule.__init__()"
        super(CSSMediaRuleTestCase, self).test_init()

        r = cssutils.css.CSSMediaRule()
        self.assertEqual(cssutils.css.CSSRuleList, type(r.cssRules))
        self.assertEqual([], r.cssRules)
        self.assertEqual(u'', r.cssText)
        self.assertEqual(cssutils.stylesheets.MediaList, type(r.media))
        self.assertEqual('all', r.media.mediaText)
        self.assertEqual(None, r.name)

        r = cssutils.css.CSSMediaRule(mediaText='print', name='name')
        self.assertEqual(cssutils.css.CSSRuleList, type(r.cssRules))
        self.assertEqual([], r.cssRules)
        self.assertEqual(u'', r.cssText)
        self.assertEqual(cssutils.stylesheets.MediaList, type(r.media))
        self.assertEqual('print', r.media.mediaText)
        self.assertEqual('name', r.name)

        # only possible to set @... similar name
        self.assertRaises(xml.dom.InvalidModificationErr, self.r._setAtkeyword, 'x')

    def test_iter(self):
        "CSSMediaRule.__iter__()"
        m = cssutils.css.CSSMediaRule()
        m.cssText = '''@media all { /*1*/a { left: 0} b{ top:0} }'''
        types = [cssutils.css.CSSRule.COMMENT,
                 cssutils.css.CSSRule.STYLE_RULE,
                 cssutils.css.CSSRule.STYLE_RULE]
        for i, rule in enumerate(m):
            self.assertEqual(rule, m.cssRules[i])
            self.assertEqual(rule.type, types[i])
            self.assertEqual(rule.parentRule, m)

    def test_refs(self):
        """CSSStylesheet references"""
        s = cssutils.parseString('@media all {a {color: red}}')
        r = s.cssRules[0]
        rules = r.cssRules
        self.assertEqual(r.cssRules[0].parentStyleSheet, s)
        self.assertEqual(rules[0].parentStyleSheet, s)

        # set cssText
        r.cssText = '@media all {a {color: blue}}'
        # not anymore: self.assertEqual(rules, r.cssRules)

        # set cssRules 
        r.cssRules = cssutils.parseString('''
            /**/
            @x;
            b {}').cssRules''').cssRules
        # new object
        self.assertNotEqual(rules, r.cssRules)
        for i, sr in enumerate(r.cssRules):
            self.assertEqual(sr.parentStyleSheet, s)
            self.assertEqual(sr.parentRule, r)
            
    def test_cssRules(self):
        "CSSMediaRule.cssRules"
        r = cssutils.css.CSSMediaRule()
        self.assertEqual([], r.cssRules)
        sr = cssutils.css.CSSStyleRule()
        r.cssRules.append(sr)
        self.assertEqual([sr], r.cssRules)
        ir = cssutils.css.CSSImportRule()
        self.assertRaises(xml.dom.HierarchyRequestErr, r.cssRules.append, ir)

        s = cssutils.parseString('@media all { /*1*/a {x:1} }')
        m = s.cssRules[0]
        self.assertEqual(2, m.cssRules.length)
        del m.cssRules[0]
        self.assertEqual(1, m.cssRules.length)
        m.cssRules.append('/*2*/')
        self.assertEqual(2, m.cssRules.length)
        m.cssRules.extend(cssutils.parseString('/*3*/x {y:2}').cssRules)
        self.assertEqual(4, m.cssRules.length)
        self.assertEqual(u'@media all {\n    a {\n        x: 1\n        }\n    /*2*/\n    /*3*/\n    x {\n        y: 2\n        }\n    }', 
                         m.cssText)
        
        for rule in m.cssRules:
            self.assertEqual(rule.parentStyleSheet, s)
            self.assertEqual(rule.parentRule, m)

    def test_cssText(self):
        "CSSMediaRule.cssText"
        style = '''{
    a {
        color: red
        }
    }'''

        mls = {
            u' (min-device-pixel-ratio: 1.3), (min-resolution: 1.3dppx) ': None,
            u' tv ': None,
            u' only tv ': None,
            u' not tv ': None,
            u' only tv and (color) ': None,
            u' only tv and(color)': u' only tv and (color) ',
            u' only tv and (color: red) ': None,
            u' only tv and (color: red) and (width: 100px) ': None,
            u' only tv and (color: red) and (width: 100px), tv ': None,
            u' only tv and (color: red) and (width: 100px), tv and (width: 20px) ': None,
            u' only tv and(color :red)and(  width :100px  )  ,tv and(width: 20px) ': 
                u' only tv and (color: red) and (width: 100px), tv and (width: 20px) ',
            u' (color: red) and (width: 100px), (width: 20px) ': None,
            u' /*1*/ only /*2*/ tv /*3*/ and /*4*/ (/*5*/ width) /*5*/ /*6*/, (color) and (height) ': None,
            u'(color)and(width),(height)': u' (color) and (width), (height) '
        }
        tests = {}
        for b, a in mls.items(): 
            if a is None:
                a = b
            tests[u'@media%s%s' % (b, style)] = u'@media%s%s' % (a, style)

        self.do_equal_p(tests)
        self.do_equal_r(tests)

        tests = {
            u'@media only tv{}': u'',
            u'@media not tv{}': u'',
            u'@media only tv and (color){}': u'',
            u'@media only tv and (color: red){}': u'',
            u'@media only tv and (color: red) and (width: 100px){}': u'',
            u'@media only tv and (color: red) and (width: 100px), tv{}': u'',
            u'@media only tv and (color: red) and (width: 100px), tv and (width: 20px){}': u'',
            u'@media (color: red) and (width: 100px), (width: 20px){}': u'',
            u'@media (width){}': u'',
            u'@media (width:10px){}': u'',
            u'@media (width), (color){}': u'',
            u'@media (width)  ,  (color),(height){}': u'',
            u'@media (width)  ,  (color) and (height){}': u'',
            u'@media (width) and (color){}': u'',
            u'@media all and (width){}': u'',
            u'@media all and (width:10px){}': u'',
            u'@media all and (width), (color){}': u'',
            u'@media all and (width)  ,  (color),(height){}': u'',
            u'@media all and (width)  ,  (color) and (height){}': u'',
            u'@media all and (width) and (color){}': u'',
            u'@media only tv and (width){}': u'',
            u'@media only tv and (width:10px){}': u'',
            u'@media only tv and (width), (color){}': u'',
            u'@media only tv and (width)  ,  (color),(height){}': u'',
            u'@media only tv and (width)  ,  (color) and (height){}': u'',
            u'@media only tv and (width) and (color){}': u'',

            u'@media only tv and (width) "name" {}': u'',
            u'@media only tv and (width:10px) "name" {}': u'',
            u'@media only tv and (width), (color){}': u'',
            u'@media only tv and (width)  ,  (color),(height){}': u'',
            u'@media only tv and (width)  ,  (color) and (height){}': u'',
            u'@media only tv and (width) and (color){}': u'',

            

            u'@media all "name"{}': u'',
            u'@media all {}': u'',
            u'@media/*x*/all{}': u'',
            u'@media all { a{ x: 1} }': u'@media all {\n    a {\n        x: 1\n        }\n    }',
            u'@media all "name" { a{ x: 1} }': u'@media all "name" {\n    a {\n        x: 1\n        }\n    }',
            u'@MEDIA all { a{x:1} }': u'@media all {\n    a {\n        x: 1\n        }\n    }',
            u'@\\media all { a{x:1} }': u'@media all {\n    a {\n        x: 1\n        }\n    }',
            u'@media all {@x some;a{color: red;}b{color: green;}}':
                u'''@media all {
    @x some;
    a {
        color: red
        }
    b {
        color: green
        }
    }''',
            u'@media all { @x{}}': u'@media all {\n    @x {\n        }\n    }',
            u'@media all "n" /**/ { @x{}}': 
                u'@media all "n" /**/ {\n    @x {\n        }\n    }',
            # comments
            u'@media/*1*//*2*/all/*3*//*4*/{/*5*/a{x:1}}': 
                u'@media /*1*/ /*2*/ all /*3*/ /*4*/ {\n    /*5*/\n    a {\n        x: 1\n        }\n    }',
            u'@media  /*1*/  /*2*/  all  /*3*/  /*4*/  {  /*5*/  a{ x: 1} }': 
                u'@media /*1*/ /*2*/ all /*3*/ /*4*/ {\n    /*5*/\n    a {\n        x: 1\n        }\n    }',
            # WS
            u'@media\n\t\f all\n\t\f {\n\t\f a{ x: 1}\n\t\f }': 
                u'@media all {\n    a {\n        x: 1\n        }\n    }',
            # @page rule inside @media
            u'@media all { @page { margin: 0; } }':
                u'@media all {\n    @page {\n        margin: 0\n        }\n    }',
            # nested media rules
            u'@media all { @media all { p { color: red; } } }':
                u'@media all {\n    @media all {\n        p {\n            '
                'color: red\n            }\n        }\n    }',
            }
        self.do_equal_p(tests)
        self.do_equal_r(tests)

        tests = {
            u'@media {}': xml.dom.SyntaxErr,
            u'@media;': xml.dom.SyntaxErr,
            u'@media/*only comment*/{}': xml.dom.SyntaxErr,
            u'@media all;': xml.dom.SyntaxErr,
            u'@media all "n";': xml.dom.SyntaxErr,
            u'@media all; @x{}': xml.dom.SyntaxErr,
            u'@media { a{ x: 1} }': xml.dom.SyntaxErr,
            u'@media "name" { a{ x: 1} }': xml.dom.SyntaxErr,
            u'@media "name" all { a{ x: 1} }': xml.dom.SyntaxErr,
            u'@media all { @charset "x"; a{}}': xml.dom.HierarchyRequestErr,
            u'@media all { @import "x"; a{}}': xml.dom.HierarchyRequestErr,
            u'@media all { , }': xml.dom.SyntaxErr,
            u'@media all {}EXTRA': xml.dom.SyntaxErr,
            u'@media ({}': xml.dom.SyntaxErr,
            u'@media (color{}': xml.dom.SyntaxErr,
            u'@media (color:{}': xml.dom.SyntaxErr,
            u'@media (color:red{}': xml.dom.SyntaxErr,
            u'@media (:red){}': xml.dom.SyntaxErr,
            u'@media (:){}': xml.dom.SyntaxErr,
            u'@media color:red){}': xml.dom.SyntaxErr,

            }
        self.do_raise_p(tests)
        self.do_raise_r(tests)

        tests = {
            # extra stuff
            '@media all { x{} } a{}': xml.dom.SyntaxErr,
            }
        self.do_raise_r(tests)

        m = cssutils.css.CSSMediaRule()
        m.cssText = u'''@media all {@x; /*1*/a{color: red;}}'''
        for r in m.cssRules:
            self.assertEqual(m, r.parentRule)
            self.assertEqual(m.parentStyleSheet, r.parentStyleSheet)

        cssutils.ser.prefs.useDefaults()

    def test_media(self):
        "CSSMediaRule.media"
        # see CSSImportRule.media

        # setting not allowed
        self.assertRaises(AttributeError,
                          self.r.__setattr__, 'media', None)
        self.assertRaises(AttributeError,
                          self.r.__setattr__, 'media', 0)

        # set mediaText instead
        self.r.media.mediaText = 'print'
        self.r.insertRule(self.stylerule)
        self.assertEqual(u'', self.r.cssText)
        cssutils.ser.prefs.keepEmptyRules = True
        self.assertEqual(u'@media print {\n    a {}\n    }', self.r.cssText)
        cssutils.ser.prefs.useDefaults()

    def test_name(self):
        "CSSMediaRule.name"
        r = cssutils.css.CSSMediaRule()
        r.cssText = '@media all "\\n\\"ame" {a{left: 0}}'

        self.assertEqual('\\n"ame', r.name)
        r.name = "n"
        self.assertEqual('n', r.name)
        self.assertEqual(u'@media all "n" {\n    a {\n        left: 0\n        }\n    }', 
                         r.cssText)
        r.name = '"'
        self.assertEqual('"', r.name)
        self.assertEqual(u'@media all "\\"" {\n    a {\n        left: 0\n        }\n    }',
                         r.cssText)

        r.name = ''
        self.assertEqual(None, r.name)
        self.assertEqual(u'@media all {\n    a {\n        left: 0\n        }\n    }',
                         r.cssText)

        r.name = None
        self.assertEqual(None, r.name)
        self.assertEqual(u'@media all {\n    a {\n        left: 0\n        }\n    }',
                         r.cssText)
                
        self.assertRaises(xml.dom.SyntaxErr, r._setName, 0)
        self.assertRaises(xml.dom.SyntaxErr, r._setName, 123)

    def test_deleteRuleIndex(self):
        "CSSMediaRule.deleteRule(index)"
        # see CSSStyleSheet.deleteRule
        m = cssutils.css.CSSMediaRule()
        m.cssText = u'''@media all {
            @a;
            /* x */
            @b;
            @c;
            @d;
        }'''
        self.assertEqual(5, m.cssRules.length)
        self.assertRaises(xml.dom.IndexSizeErr, m.deleteRule, 5)

        # end -1
        # check parentRule
        r = m.cssRules[-1]
        self.assertEqual(m, r.parentRule)
        m.deleteRule(-1)
        self.assertEqual(None, r.parentRule)

        self.assertEqual(4, m.cssRules.length)
        self.assertEqual(
            u'@media all {\n    @a;\n    /* x */\n    @b;\n    @c;\n    }', m.cssText)
        # beginning
        m.deleteRule(0)
        self.assertEqual(3, m.cssRules.length)
        self.assertEqual(u'@media all {\n    /* x */\n    @b;\n    @c;\n    }', m.cssText)
        # middle
        m.deleteRule(1)
        self.assertEqual(2, m.cssRules.length)
        self.assertEqual(u'@media all {\n    /* x */\n    @c;\n    }', m.cssText)
        # end
        m.deleteRule(1)
        self.assertEqual(1, m.cssRules.length)
        self.assertEqual(u'@media all {\n    /* x */\n    }', m.cssText)

    def test_deleteRule(self):
        "CSSMediaRule.deleteRule(rule)"
        m = cssutils.css.CSSMediaRule()
        m.cssText='''@media all {
            a { color: red; }
            b { color: blue; }
            c { color: green; }
        }'''
        s1, s2, s3 = m.cssRules
        
        r = cssutils.css.CSSStyleRule()
        self.assertRaises(xml.dom.IndexSizeErr, m.deleteRule, r)

        self.assertEqual(3, m.cssRules.length)
        m.deleteRule(s2)
        self.assertEqual(2, m.cssRules.length)
        self.assertEqual(m.cssText, '@media all {\n    a {\n        color: red\n        }\n    c {\n        color: green\n        }\n    }')
        self.assertRaises(xml.dom.IndexSizeErr, m.deleteRule, s2)

    def test_add(self):
        "CSSMediaRule.add()"
        # see CSSStyleSheet.add
        r = cssutils.css.CSSMediaRule()
        stylerule1 = cssutils.css.CSSStyleRule()
        stylerule2 = cssutils.css.CSSStyleRule()
        r.add(stylerule1)
        r.add(stylerule2)
        self.assertEqual(r.cssRules[0], stylerule1)
        self.assertEqual(r.cssRules[1], stylerule2)

    def test_insertRule(self):
        "CSSMediaRule.insertRule"
        # see CSSStyleSheet.insertRule
        r = cssutils.css.CSSMediaRule()
        charsetrule = cssutils.css.CSSCharsetRule('ascii')
        importrule = cssutils.css.CSSImportRule('x')
        namespacerule = cssutils.css.CSSNamespaceRule()
        pagerule = cssutils.css.CSSPageRule()
        unknownrule = cssutils.css.CSSUnknownRule('@x;')
        stylerule = cssutils.css.CSSStyleRule('a')
        stylerule.cssText = u'a { x: 1}'
        comment1 = cssutils.css.CSSComment(u'/*1*/')
        comment2 = cssutils.css.CSSComment(u'/*2*/')

        # hierarchy
        self.assertRaises(xml.dom.HierarchyRequestErr,
                          r.insertRule, charsetrule, 0)
        self.assertRaises(xml.dom.HierarchyRequestErr,
                          r.insertRule, importrule, 0)
        self.assertRaises(xml.dom.HierarchyRequestErr,
                          r.insertRule, namespacerule, 0)

        # start insert
        r.insertRule(stylerule, 0)
        self.assertEqual(r, stylerule.parentRule)
        self.assertEqual(r.parentStyleSheet, stylerule.parentStyleSheet)
        # before
        r.insertRule(comment1, 0)
        self.assertEqual(r, comment1.parentRule)
        self.assertEqual(r.parentStyleSheet, stylerule.parentStyleSheet)
        # end explicit
        r.insertRule(unknownrule, 2)
        self.assertEqual(r, unknownrule.parentRule)
        self.assertEqual(r.parentStyleSheet, stylerule.parentStyleSheet)
        # end implicit
        r.insertRule(comment2)
        self.assertEqual(r, comment2.parentRule)
        self.assertEqual(r.parentStyleSheet, stylerule.parentStyleSheet)
        self.assertEqual(
            '@media all {\n    /*1*/\n    a {\n        x: 1\n        }\n    @x;\n    /*2*/\n    }',
            r.cssText)

        # index
        self.assertRaises(xml.dom.IndexSizeErr,
                  r.insertRule, stylerule, -1)
        self.assertRaises(xml.dom.IndexSizeErr,
                  r.insertRule, stylerule, r.cssRules.length + 1)

    def test_InvalidModificationErr(self):
        "CSSMediaRule.cssText InvalidModificationErr"
        self._test_InvalidModificationErr(u'@media')

    def test_incomplete(self):
        "CSSMediaRule (incomplete)"
        tests = {
            u'@media all { @unknown;': # no }
                u'@media all {\n    @unknown;\n    }',
            u'@media all { a {x:"1"}': # no }
                u'@media all {\n    a {\n        x: "1"\n        }\n    }',
            u'@media all { a {x:"1"': # no }}
                u'@media all {\n    a {\n        x: "1"\n        }\n    }',
            u'@media all { a {x:"1': # no "}}
                u'@media all {\n    a {\n        x: "1"\n        }\n    }',
        }
        self.do_equal_p(tests) # parse

    def test_reprANDstr(self):
        "CSSMediaRule.__repr__(), .__str__()"
        mediaText='tv, print'
        
        s = cssutils.css.CSSMediaRule(mediaText=mediaText)
        
        self.assertTrue(mediaText in str(s))

        s2 = eval(repr(s))
        self.assertTrue(isinstance(s2, s.__class__))
        self.assertTrue(mediaText == s2.media.mediaText)


if __name__ == '__main__':
    import unittest
    unittest.main()
