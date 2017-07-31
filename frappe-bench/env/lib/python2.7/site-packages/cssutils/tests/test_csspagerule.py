"""Testcases for cssutils.css.CSSPageRule"""

import xml.dom
import test_cssrule
import cssutils

class CSSPageRuleTestCase(test_cssrule.CSSRuleTestCase):

    def setUp(self):
        super(CSSPageRuleTestCase, self).setUp()
        
        cssutils.ser.prefs.useDefaults()
        self.r = cssutils.css.CSSPageRule()
        self.rRO = cssutils.css.CSSPageRule(readonly=True)
        self.r_type = cssutils.css.CSSPageRule.PAGE_RULE#
        self.r_typeString = 'PAGE_RULE'

    def tearDown(self):
        cssutils.ser.prefs.useDefaults()
            
    def test_init(self):
        "CSSPageRule.__init__()"
        super(CSSPageRuleTestCase, self).test_init()

        r = cssutils.css.CSSPageRule()
        self.assertEqual(u'', r.selectorText)
        self.assertEqual(cssutils.css.CSSStyleDeclaration, type(r.style))
        self.assertEqual(r, r.style.parentRule)

        # until any properties
        self.assertEqual(u'', r.cssText)

        # only possible to set @... similar name
        self.assertRaises(xml.dom.InvalidModificationErr, self.r._setAtkeyword, 'x')

        def checkrefs(ff):
            self.assertEqual(ff, ff.style.parentRule)
            for p in ff.style:
                self.assertEqual(ff.style, p.parent)
                
        checkrefs(cssutils.css.CSSPageRule(
                    style=cssutils.css.CSSStyleDeclaration('font-family: x')))
        
        r = cssutils.css.CSSPageRule()
        r.cssText = '@page { font-family: x }'
        checkrefs(r)
        
        r = cssutils.css.CSSPageRule()
        r.style.setProperty('font-family', 'y')
        checkrefs(r)

        r = cssutils.css.CSSPageRule()
        r.style['font-family'] = 'z'
        checkrefs(r)

        r = cssutils.css.CSSPageRule()
        r.style.fontFamily = 'a'
        checkrefs(r)

    def test_InvalidModificationErr(self):
        "CSSPageRule.cssText InvalidModificationErr"
        self._test_InvalidModificationErr(u'@page')
        tests = {
            u'@pag {}': xml.dom.InvalidModificationErr,
            }
        self.do_raise_r(tests)

    def test_incomplete(self):
        "CSSPageRule (incomplete)"
        tests = {
            u'@page :left { ':
                u'', # no } and no content
            u'@page :left { color: red':
                u'@page :left {\n    color: red\n    }', # no }
        }
        self.do_equal_p(tests) # parse

    def test_cssText(self):
        "CSSPageRule.cssText"
        EXP = u'@page %s {\n    margin: 0\n    }'
        tests = {
            u'@page {}': u'',
            u'@page:left{}': u'',
            u'@page :right {}': u'',
            u'@page {margin:0;}': u'@page {\n    margin: 0\n    }',

            u'@page name { margin: 0 }': EXP % u'name',
            u'@page name:left { margin: 0 }': EXP % u'name:left',
            u'@page name:right { margin: 0 }': EXP % u'name:right',
            u'@page name:first { margin: 0 }': EXP % u'name:first',
            u'@page :left { margin: 0 }': EXP % u':left',
            u'@page:left { margin: 0 }': EXP % u':left',
            u'@page :right { margin: 0 }': EXP % u':right',
            u'@page :first { margin: 0 }': EXP % u':first',
            u'@page :UNKNOWNIDENT { margin: 0 }': EXP % u':UNKNOWNIDENT',

            u'@PAGE:left{margin:0;}': u'@page :left {\n    margin: 0\n    }',
            u'@\\page:left{margin:0;}': u'@page :left {\n    margin: 0\n    }',

            # comments
            u'@page/*1*//*2*/:left/*3*//*4*/{margin:0;}':
                u'@page /*1*/ /*2*/ :left /*3*/ /*4*/ {\n    margin: 0\n    }',
            # WS
            u'@page:left{margin:0;}':
                u'@page :left {\n    margin: 0\n    }',
            u'@page\n\r\f\t :left\n\r\f\t {margin:0;}':
                u'@page :left {\n    margin: 0\n    }',
                
            # MarginRule
            u'@page {    @top-right {        content: "2"        }    }':
                u'@page {\n    @top-right {\n        content: "2"\n        }\n    }',
            u'@page {padding: 1cm; margin: 1cm; @top-left {content: "1"}@top-right {content: "2";left: 1}}':
                u'@page {\n    padding: 1cm;\n    margin: 1cm;\n    @top-left {\n        content: "1"\n        }\n    @top-right {\n        content: "2";\n        left: 1\n        }\n    }',
            u'@page {@top-right { content: "1a"; content: "1b"; x: 1 }@top-right { content: "2"; y: 2 }}':
                u'''@page {\n    @top-right {
        content: "1a";
        content: "1b";
        x: 1;
        content: "2";
        y: 2
        }\n    }''',
        
        }
        self.do_equal_r(tests)
        self.do_equal_p(tests)

        tests = {
            # auto is not allowed
            u'@page AUto {}': xml.dom.SyntaxErr,
            u'@page AUto:left {}': xml.dom.SyntaxErr,
            
            u'@page : {}': xml.dom.SyntaxErr,
            u'@page :/*1*/left {}': xml.dom.SyntaxErr,
            u'@page : left {}': xml.dom.SyntaxErr,
            u'@page :left :right {}': xml.dom.SyntaxErr,
            u'@page :left a {}': xml.dom.SyntaxErr,
            # no S between IDENT and PSEUDO
            u'@page a :left  {}': xml.dom.SyntaxErr,

            u'@page :left;': xml.dom.SyntaxErr,
            u'@page :left }': xml.dom.SyntaxErr,
            }
        self.do_raise_p(tests) # parse
        tests.update({
            # false selector
            u'@page :right :left {}': xml.dom.SyntaxErr, # no }
            u'@page :right X {}': xml.dom.SyntaxErr, # no }
            u'@page X Y {}': xml.dom.SyntaxErr, # no }
            
            u'@page :left {': xml.dom.SyntaxErr, # no }
            # trailing
            u'@page :left {}1': xml.dom.SyntaxErr, # no }
            u'@page :left {}/**/': xml.dom.SyntaxErr, # no }
            u'@page :left {} ': xml.dom.SyntaxErr, # no }
            })
        self.do_raise_r(tests) # set cssText

    def test_cssText2(self):
        "CSSPageRule.cssText 2"
        r = cssutils.css.CSSPageRule()
        s = u'a:left'
        r.selectorText = s 
        self.assertEqual(r.selectorText, s)

        st = 'size: a4'
        r.style = st
        self.assertEqual(r.style.cssText, st)

        # invalid selector
        self.assertRaises(xml.dom.SyntaxErr, r._setStyle, '$')
        self.assertEqual(r.selectorText, s)
        self.assertEqual(r.style.cssText, st)

        self.assertRaises(xml.dom.SyntaxErr, r._setCssText, '@page $ { color: red }')
        self.assertEqual(r.selectorText, s)
        self.assertEqual(r.style.cssText, st)


        # invalid style
        self.assertRaises(xml.dom.SyntaxErr, r._setSelectorText, '$')
        self.assertEqual(r.selectorText, s)
        self.assertEqual(r.style.cssText, st)

        self.assertRaises(xml.dom.SyntaxErr, r._setCssText, '@page b:right { x }')
        self.assertEqual(r.selectorText, s)
        self.assertEqual(r.style.cssText, st)

    def test_selectorText(self):
        "CSSPageRule.selectorText"
        r = cssutils.css.CSSPageRule()
        r.selectorText = u'a:left'
        self.assertEqual(r.selectorText, u'a:left')
        
        tests = {
            u'': u'',
            u'name': None,
            u':left': None,
            u':right': None,
            u':first': None,
            u':UNKNOWNIDENT': None,
            u'name:left': None,
            u' :left': u':left',
            u':left': u':left',
            u'/*1*/:left/*a*/': u'/*1*/ :left /*a*/',
            u'/*1*/ :left /*a*/ /*b*/': None,
            u':left/*a*/': u':left /*a*/',
            u'/*1*/:left': u'/*1*/ :left',
            }
        self.do_equal_r(tests, att='selectorText')

        tests = {
            u':': xml.dom.SyntaxErr,
            u':/*1*/left': xml.dom.SyntaxErr,
            u': left': xml.dom.SyntaxErr,
            u':left :right': xml.dom.SyntaxErr,
            u':left a': xml.dom.SyntaxErr,
            u'name :left': xml.dom.SyntaxErr,
            }
        self.do_raise_r(tests, att='_setSelectorText')

    def test_specificity(self):
        "CSSPageRule.specificity"
        r = cssutils.css.CSSPageRule()
        tests = {
            u'': (0, 0, 0),
            u'name': (1, 0, 0),
            u':first': (0, 1, 0),
            u':left': (0, 0, 1),
            u':right': (0, 0, 1),
            u':UNKNOWNIDENT': (0, 0, 1),
            u'name:first': (1, 1, 0),
            u'name:left': (1, 0, 1),
            u'name:right': (1, 0, 1),
            u'name:X': (1, 0, 1)
        }
        for sel, exp in tests.items():
            r.selectorText = sel
            self.assertEqual(r.specificity, exp)
            
            r = cssutils.css.CSSPageRule()
            r.cssText = u'@page %s {}' % sel
            self.assertEqual(r.specificity, exp)

    def test_cssRules(self):
        "CSSPageRule.cssRules"
        s = cssutils.parseString(u'@page {}')
        p = s.cssRules[0]
        
        self.assertEqual(len(p.cssRules), 0)
        
        # add and insert
        m1 = cssutils.css.MarginRule(u'@top-left', u'color: red')
        i = p.add(m1)
        self.assertEqual(i, 0)
        self.assertEqual(len(p.cssRules), 1)

        m3 = cssutils.css.MarginRule()
        m3.cssText = u'@top-right { color: blue }'
        i = p.insertRule(m3)
        self.assertEqual(i, 1)
        self.assertEqual(len(p.cssRules), 2)

        m2 = cssutils.css.MarginRule()
        m2.margin = u'@top-center'
        m2.style = u'color: green'
        i = p.insertRule(m2, 1)
        self.assertEqual(i, 1)
        self.assertEqual(len(p.cssRules), 3)

        self.assertEqual(p.cssText, u'''@page {
    @top-left {
        color: red
        }
    @top-center {
        color: green
        }
    @top-right {
        color: blue
        }
    }''')
        
        # keys and dict index
        self.assertEqual(u'@top-left' in p, True)
        self.assertEqual(u'@bottom-left' in p, False)
        
        self.assertEqual(p.keys(), [u'@top-left', 
                                    u'@top-center', 
                                    u'@top-right'])
        
        self.assertEqual(p[u'@bottom-left'], None)
        self.assertEqual(p[u'@top-left'].cssText, u'color: red')
        p[u'@top-left'] = u'color: #f00'
        self.assertEqual(p[u'@top-left'].cssText, u'color: #f00')
        
        # delete
        p.deleteRule(m2)
        self.assertEqual(len(p.cssRules), 2)
        self.assertEqual(p.cssText, u'''@page {
    @top-left {
        color: #f00
        }
    @top-right {
        color: blue
        }
    }''')

        p.deleteRule(0)
        self.assertEqual(len(p.cssRules), 1)        
        self.assertEqual(m3, p.cssRules[0])
        self.assertEqual(p.cssText, u'''@page {
    @top-right {
        color: blue
        }
    }''')

        del p['@top-right']
        self.assertEqual(len(p.cssRules), 0)
                
    
    def test_style(self):
        "CSSPageRule.style (and references)"
        r = cssutils.css.CSSPageRule()
        s1 = r.style
        self.assertEqual(r, s1.parentRule)
        self.assertEqual(u'', s1.cssText)
        
        # set rule.cssText
        r.cssText = '@page { font-family: x1 }'
        self.assertNotEqual(r.style, s1)
        self.assertEqual(r, r.style.parentRule)
        self.assertEqual(r.cssText, u'@page {\n    font-family: x1\n    }')
        self.assertEqual(r.style.cssText, u'font-family: x1')
        self.assertEqual(s1.cssText, u'')
        s2 = r.style
        
        # set invalid rule.cssText
        try: 
            r.cssText = '@page { $ }'
        except xml.dom.SyntaxErr, e:
            pass
        self.assertEqual(r.style, s2)
        self.assertEqual(r, r.style.parentRule)
        self.assertEqual(r.cssText, u'@page {\n    font-family: x1\n    }')
        self.assertEqual(r.style.cssText, u'font-family: x1')
        self.assertEqual(s2.cssText, u'font-family: x1')
        s3 = r.style

        # set rule.style.cssText
        r.style.cssText = 'font-family: x2'
        self.assertEqual(r.style, s3)
        self.assertEqual(r, r.style.parentRule)
        self.assertEqual(r.cssText, u'@page {\n    font-family: x2\n    }')
        self.assertEqual(r.style.cssText, u'font-family: x2')

        # set new style object s2
        s2 = cssutils.css.CSSStyleDeclaration('font-family: y1')
        r.style = s2
        self.assertEqual(r.style, s2)
        self.assertEqual(r, s2.parentRule)
        self.assertEqual(r.cssText, u'@page {\n    font-family: y1\n    }')
        self.assertEqual(s2.cssText, u'font-family: y1')
        self.assertEqual(r.style.cssText, u'font-family: y1')
        self.assertEqual(s3.cssText, u'font-family: x2') # old

        # set s2.cssText
        s2.cssText = 'font-family: y2'
        self.assertEqual(r.style, s2)
        self.assertEqual(r.cssText, u'@page {\n    font-family: y2\n    }')
        self.assertEqual(r.style.cssText, u'font-family: y2')
        self.assertEqual(s3.cssText, u'font-family: x2') # old
        # set invalid s2.cssText
        try: 
            s2.cssText = '$'
        except xml.dom.SyntaxErr, e:
            pass
        self.assertEqual(r.style, s2)
        self.assertEqual(r.cssText, u'@page {\n    font-family: y2\n    }')
        self.assertEqual(r.style.cssText, u'font-family: y2')
        self.assertEqual(s3.cssText, u'font-family: x2') # old

        # set r.style with text
        r.style = 'font-family: z'
        self.assertNotEqual(r.style, s2)
        self.assertEqual(r.cssText, u'@page {\n    font-family: z\n    }')
        self.assertEqual(r.style.cssText, u'font-family: z')

    def test_properties(self):
        "CSSPageRule.style properties"
        r = cssutils.css.CSSPageRule()
        r.style.cssText = '''
        margin-top: 0;
        margin-right: 0;
        margin-bottom: 0;
        margin-left: 0;
        margin: 0;

        page-break-before: auto;
        page-break-after: auto;
        page-break-inside: auto;

        orphans: 3;
        widows: 3;
        '''
        exp = u'''@page {
    margin-top: 0;
    margin-right: 0;
    margin-bottom: 0;
    margin-left: 0;
    margin: 0;
    page-break-before: auto;
    page-break-after: auto;
    page-break-inside: auto;
    orphans: 3;
    widows: 3
    }'''
        self.assertEqual(exp, r.cssText)

    def test_reprANDstr(self):
        "CSSPageRule.__repr__(), .__str__()"
        sel=u':left'
        
        s = cssutils.css.CSSPageRule(selectorText=sel)
        
        self.assertTrue(sel in str(s))

        s2 = eval(repr(s))
        self.assertTrue(isinstance(s2, s.__class__))
        self.assertTrue(sel == s2.selectorText)


if __name__ == '__main__':
    import unittest
    unittest.main()
