# -*- coding: utf-8 -*-
"""Testcases for cssutils.CSSSerializer"""

import basetest
import cssutils
import sys


class PreferencesTestCase(basetest.BaseTestCase):
    """
    testcases for cssutils.serialize.Preferences
    """
    def setUp(self):
        cssutils.ser.prefs.useDefaults()
    
    def tearDown(self):
        cssutils.ser.prefs.useDefaults()
    
#    def testkeepUnkownAtRules(self):
#        "Preferences.keepUnkownAtRules"
#        # py >=2.6 only
#        # v = sys.version_info; if v[0]*10+v[1] >= 26:
#        from warnings import catch_warnings
#        with catch_warnings(record=True) as log:
#            x = cssutils.ser.prefs.keepUnkownAtRules
#        
#        if log:
#            # unpack the only member of log
#            warning, = log
#            self.assertEqual(warning.category, DeprecationWarning)
    
    def test_resolveVariables(self):
        "Preferences.resolveVariables"
        self.assertEqual(cssutils.ser.prefs.resolveVariables, True)
        
        cssutils.ser.prefs.resolveVariables = False
        
        vars = u'''
            @variables {
                c1: red;
                c2: #0f0;
                px: 1px 2px;
            }
        '''
        tests = {
            u'''a {\n    color: var(c1)\n    }''':
            u'''a {\n    color: red\n    }''',
            u'''a {\n    color: var(c1)\n; color: var(  c2   )    }''':
            u'''a {\n    color: red;\n    color: #0f0\n    }''',
            u'''a {\n    margin: var(px)\n    }''':
            u'''a {\n    margin: 1px 2px\n    }''',
            u'''@media all {
                a {
                    margin: var(px) var(px);
                    color: var(c1);
                    left: var(unknown)
                    }
            }''': 
            u'''@media all {\n    a {\n        margin: 1px 2px 1px 2px;\n        color: red;\n        left: var(unknown)\n        }\n    }''',
        }
        cssutils.ser.prefs.resolveVariables = True
        
        for test, exp in tests.items():
            s = cssutils.parseString(vars + test)
            self.assertEqual(exp.encode(), s.cssText)
            
        cssutils.ser.prefs.resolveVariables = True

            
    def test_useDefaults(self):
        "Preferences.useDefaults()"
        cssutils.ser.prefs.useMinified()
        cssutils.ser.prefs.useDefaults()
        self.assertEqual(cssutils.ser.prefs.defaultAtKeyword, True)
        self.assertEqual(cssutils.ser.prefs.defaultPropertyName, True)
        self.assertEqual(cssutils.ser.prefs.defaultPropertyPriority, True)
        self.assertEqual(cssutils.ser.prefs.importHrefFormat, None)
        self.assertEqual(cssutils.ser.prefs.indent, 4 * u' ')
        self.assertEqual(cssutils.ser.prefs.indentClosingBrace, True)
        self.assertEqual(cssutils.ser.prefs.keepAllProperties, True)
        self.assertEqual(cssutils.ser.prefs.keepComments, True)
        self.assertEqual(cssutils.ser.prefs.keepEmptyRules, False)
        self.assertEqual(cssutils.ser.prefs.keepUnknownAtRules, True)
        self.assertEqual(cssutils.ser.prefs.keepUsedNamespaceRulesOnly, False)
        self.assertEqual(cssutils.ser.prefs.lineNumbers, False)
        self.assertEqual(cssutils.ser.prefs.lineSeparator, u'\n')
        self.assertEqual(cssutils.ser.prefs.listItemSpacer, u' ')
        self.assertEqual(cssutils.ser.prefs.minimizeColorHash, True)
        self.assertEqual(cssutils.ser.prefs.omitLastSemicolon, True)
        self.assertEqual(cssutils.ser.prefs.omitLeadingZero, False)
        self.assertEqual(cssutils.ser.prefs.paranthesisSpacer, u' ')
        self.assertEqual(cssutils.ser.prefs.propertyNameSpacer, u' ')
        self.assertEqual(cssutils.ser.prefs.selectorCombinatorSpacer, u' ')
        self.assertEqual(cssutils.ser.prefs.spacer, u' ')
        self.assertEqual(cssutils.ser.prefs.validOnly, False)
        css = u'''
    /*1*/
    @import url(x) tv , print;
    @namespace prefix "uri";
    @namespace unused "unused";
    @media all {}
    @media all {
        a {}
    }
    @media   all  {
    a { color: red; }
        }
    @page     { left: 0; }
    a {}
    prefix|x, a  +  b  >  c  ~  d  ,  b { top : 1px ;
        font-family : arial ,'some'
        }
    '''
        parsedcss = u'''/*1*/
@import url(x) tv, print;
@namespace prefix "uri";
@namespace unused "unused";
@media all {
    a {
        color: red
        }
    }
@page {
    left: 0
    }
prefix|x, a + b > c ~ d, b {
    top: 1px;
    font-family: arial, "some"
    }'''
        s = cssutils.parseString(css)
        self.assertEqual(s.cssText, parsedcss.encode())
        
        tests = {
            u'0.1 .1 0.1px .1px 0.1% .1% +0.1 +.1 +0.1px +.1px +0.1% +.1% -0.1 -.1 -0.1px -.1px -0.1% -.1%': 
            u'0.1 0.1 0.1px 0.1px 0.1% 0.1% +0.1 +0.1 +0.1px +0.1px +0.1% +0.1% -0.1 -0.1 -0.1px -0.1px -0.1% -0.1%' 
        }
        cssutils.ser.prefs.useDefaults()
        for test, exp in tests.items():
            s = cssutils.parseString(u'a{x:%s}' % test)
            self.assertEqual((u'a {\n    x: %s\n    }' % exp).encode(), s.cssText)


    def test_useMinified(self):
        "Preferences.useMinified()"
        cssutils.ser.prefs.useDefaults()
        cssutils.ser.prefs.useMinified()
        self.assertEqual(cssutils.ser.prefs.defaultAtKeyword, True)
        self.assertEqual(cssutils.ser.prefs.defaultPropertyName, True)
        self.assertEqual(cssutils.ser.prefs.importHrefFormat, 'string')
        self.assertEqual(cssutils.ser.prefs.indent, u'')
        self.assertEqual(cssutils.ser.prefs.keepAllProperties, True)
        self.assertEqual(cssutils.ser.prefs.keepComments, False)
        self.assertEqual(cssutils.ser.prefs.keepEmptyRules, False)
        self.assertEqual(cssutils.ser.prefs.keepUnknownAtRules, False)
        self.assertEqual(cssutils.ser.prefs.keepUsedNamespaceRulesOnly, True)
        self.assertEqual(cssutils.ser.prefs.lineNumbers, False)
        self.assertEqual(cssutils.ser.prefs.lineSeparator, u'')
        self.assertEqual(cssutils.ser.prefs.listItemSpacer, u'')
        self.assertEqual(cssutils.ser.prefs.omitLastSemicolon, True)
        self.assertEqual(cssutils.ser.prefs.omitLeadingZero, True)
        self.assertEqual(cssutils.ser.prefs.paranthesisSpacer, u'')
        self.assertEqual(cssutils.ser.prefs.propertyNameSpacer, u'')
        self.assertEqual(cssutils.ser.prefs.selectorCombinatorSpacer, u'')
        self.assertEqual(cssutils.ser.prefs.spacer, u'')
        self.assertEqual(cssutils.ser.prefs.validOnly, False)
        
        css = u'''
    /*1*/
    @import   url(x) tv , print;
    @namespace   prefix "uri";
    @namespace   unused "unused";
    @media  all {}
    @media  all {
        a {}
    }
    @media all "name" {
        a { color: red; }
    }
    @page:left {
    left: 0
    }
    a {}
    prefix|x, a + b > c ~ d , b { top : 1px ;
        font-family : arial ,  'some'
        }
    @x  x;
    '''
        s = cssutils.parseString(css)
        cssutils.ser.prefs.keepUnknownAtRules = True
        self.assertEqual(s.cssText,
            u'''@import"x"tv,print;@namespace prefix"uri";@media all"name"{a{color:red}}@page :left{left:0}prefix|x,a+b>c~d,b{top:1px;font-family:arial,"some"}@x x;'''.encode() 
            )
        cssutils.ser.prefs.keepUnknownAtRules = False
        self.assertEqual(s.cssText,
            u'''@import"x"tv,print;@namespace prefix"uri";@media all"name"{a{color:red}}@page :left{left:0}prefix|x,a+b>c~d,b{top:1px;font-family:arial,"some"}'''.encode()
            )
        # Values
        valuetests = {
            u'  a  a1  a-1  a-1a  ': 'a a1 a-1 a-1a',
            u'a b 1 c 1em d -1em e': u'a b 1 c 1em d -1em e',
            u'  1em  /  5  ': u'1em/5',
            u'1em/5': u'1em/5',
            u'a 0 a .0 a 0.0 a -0 a -.0 a -0.0 a +0 a +.0 a +0.0':
                u'a 0 a 0 a 0 a 0 a 0 a 0 a 0 a 0 a 0',
            u'a  0px  a  .0px  a  0.0px  a  -0px  a  -.0px  a  -0.0px  a  +0px  a  +.0px  a  +0.0px ':
                u'a 0 a 0 a 0 a 0 a 0 a 0 a 0 a 0 a 0',
            u'a  1  a  .1  a  1.0  a  0.1  a  -1  a  -.1  a  -1.0  a  -0.1  a  +1  a  +.1  a  +1.0':
                u'a 1 a .1 a 1 a .1 a -1 a -.1 a -1 a -.1 a +1 a +.1 a +1',
            u'  url(x)  f()': 'url(x) f()',
            u'#112233': '#123',
            u'#112234': '#112234',
            u'#123': '#123',
            u'#123 url() f()': '#123 url() f()',
            u'1 +2 +3 -4': u'1 +2 +3 -4', # ?
            u'0.1 .1 0.1px .1px 0.1% .1% +0.1 +.1 +0.1px +.1px +0.1% +.1% -0.1 -.1 -0.1px -.1px -0.1% -.1%':
            u'.1 .1 .1px .1px .1% .1% +.1 +.1 +.1px +.1px +.1% +.1% -.1 -.1 -.1px -.1px -.1% -.1%'
        }
        for test, exp in valuetests.items():
            s = cssutils.parseString(u'a{x:%s}' % test)
            self.assertEqual((u'a{x:%s}' % exp).encode(), s.cssText)

        
            
    def test_defaultAtKeyword(self):
        "Preferences.defaultAtKeyword"
        s = cssutils.parseString(u'@im\\port "x";')
        self.assertEqual(u'@import "x";'.encode(), s.cssText)
        cssutils.ser.prefs.defaultAtKeyword = True
        self.assertEqual(u'@import "x";'.encode(), s.cssText)
        cssutils.ser.prefs.defaultAtKeyword = False
        self.assertEqual(u'@im\\port "x";'.encode(), s.cssText)
        
    def test_defaultPropertyName(self):
        "Preferences.defaultPropertyName"
        cssutils.ser.prefs.keepAllProperties = False

        # does not actually work as once the name is set it is used also
        # if used with a backslash in it later...

        s = cssutils.parseString(ur'a { c\olor: green; }')
        self.assertEqual(u'a {\n    color: green\n    }'.encode(), s.cssText)
        cssutils.ser.prefs.defaultPropertyName = True
        self.assertEqual(u'a {\n    color: green\n    }'.encode(), s.cssText)
        cssutils.ser.prefs.defaultPropertyName = False
        self.assertEqual(u'a {\n    c\\olor: green\n    }'.encode(), s.cssText)

        s = cssutils.parseString(u'a { color: red; c\olor: green; }')
        self.assertEqual(u'a {\n    c\\olor: green\n    }'.encode(), s.cssText)
        cssutils.ser.prefs.defaultPropertyName = False
        self.assertEqual(u'a {\n    c\\olor: green\n    }'.encode(), s.cssText)
        cssutils.ser.prefs.defaultPropertyName = True
        self.assertEqual(u'a {\n    color: green\n    }'.encode(), s.cssText)
        
    def test_defaultPropertyPriority(self):
        "Preferences.defaultPropertyPriority"
        css = u'a {\n    color: green !IM\\portant\n    }'
        s = cssutils.parseString(css)
        self.assertEqual(s.cssText, u'a {\n    color: green !important\n    }'.encode())
        cssutils.ser.prefs.defaultPropertyPriority = False
        self.assertEqual(s.cssText, css.encode())
        
    def test_importHrefFormat(self):
        "Preferences.importHrefFormat"
        r0 = cssutils.css.CSSImportRule()
        r0.cssText=u'@import url("not");'
        r1 = cssutils.css.CSSImportRule()
        r1.cssText=u'@import "str";'
        self.assertEqual(u'@import url(not);', r0.cssText)
        self.assertEqual(u'@import "str";', r1.cssText)

        cssutils.ser.prefs.importHrefFormat = 'string'
        self.assertEqual(u'@import "not";', r0.cssText)
        self.assertEqual(u'@import "str";', r1.cssText)

        cssutils.ser.prefs.importHrefFormat = 'uri'
        self.assertEqual(u'@import url(not);', r0.cssText)
        self.assertEqual(u'@import url(str);', r1.cssText)

        cssutils.ser.prefs.importHrefFormat = 'not defined'
        self.assertEqual(u'@import url(not);', r0.cssText)
        self.assertEqual(u'@import "str";', r1.cssText)
        
    def test_indent(self):
        "Preferences.ident"
        s = cssutils.parseString(u'a { left: 0 }')
        exp4 = u'''a {
    left: 0
    }'''
        exp1 = u'''a {
 left: 0
 }'''
        cssutils.ser.prefs.indent = ' '
        self.assertEqual(exp1.encode(), s.cssText)
        cssutils.ser.prefs.indent = 4* ' '
        self.assertEqual(exp4.encode(), s.cssText)

    def test_indentClosingBrace(self):
        "Preferences.indentClosingBrace"
        s = cssutils.parseString(u'@media all {a {left: 0}} b { top: 0 }')
        expT = u'''@media all {
    a {
        left: 0
        }
    }
b {
    top: 0
    }'''
        expF = u'''@media all {
    a {
        left: 0
    }
}
b {
    top: 0
}'''
        cssutils.ser.prefs.useDefaults()
        self.assertEqual(expT.encode(), s.cssText)
        cssutils.ser.prefs.indentClosingBrace = False
        self.assertEqual(expF.encode(), s.cssText)
        
    def test_keepAllProperties(self):
        "Preferences.keepAllProperties"
        css = '''a {
            color: pink;
            color: red;
            c\olor: blue;
            c\olor: green;
            }'''
        s = cssutils.parseString(css)
        # keep only last
        cssutils.ser.prefs.keepAllProperties = False
        self.assertEqual(u'a {\n    color: green\n    }'.encode(), s.cssText)
        # keep all
        cssutils.ser.prefs.keepAllProperties = True
        self.assertEqual(u'a {\n    color: pink;\n    color: red;\n    c\olor: blue;\n    c\olor: green\n    }'.encode(), s.cssText)
        
    def test_keepComments(self):
        "Preferences.keepComments"
        s = cssutils.parseString('/*1*/ a { /*2*/ }')
        cssutils.ser.prefs.keepComments = False
        self.assertEqual(''.encode(), s.cssText)
        cssutils.ser.prefs.keepEmptyRules = True
        self.assertEqual('a {}'.encode(), s.cssText)
        
    def test_keepEmptyRules(self):
        "Preferences.keepEmptyRules"
        # CSSStyleRule
        css = u'''a {}
a {
    /*1*/
    }
a {
    color: red
    }'''
        s = cssutils.parseString(css)
        cssutils.ser.prefs.useDefaults()
        cssutils.ser.prefs.keepEmptyRules = True
        self.assertEqual(css.encode(), s.cssText)
        cssutils.ser.prefs.keepEmptyRules = False
        self.assertEqual(u'a {\n    /*1*/\n    }\na {\n    color: red\n    }'.encode(),
                         s.cssText)
        cssutils.ser.prefs.keepComments = False
        self.assertEqual(u'a {\n    color: red\n    }'.encode(), s.cssText)

        # CSSMediaRule
        css = u'''@media tv {
    }
@media all {
    /*1*/
    }
@media print {
    a {}
    }
@media print {
    a {
        /*1*/
        }
    }
@media all {
    a {
        color: red
        }
    }'''
        s = cssutils.parseString(css)
        cssutils.ser.prefs.useDefaults()
        cssutils.ser.prefs.keepEmptyRules = True
   #     self.assertEqual(css, s.cssText)
        cssutils.ser.prefs.keepEmptyRules = False
        self.assertEqual('''@media all {
    /*1*/
    }
@media print {
    a {
        /*1*/
        }
    }
@media all {
    a {
        color: red
        }
    }'''.encode(), s.cssText)
        cssutils.ser.prefs.keepComments = False
        self.assertEqual('''@media all {
    a {
        color: red
        }
    }'''.encode(), s.cssText)
        
    def test_keepUnknownAtRules(self):
        "Preferences.keepUnknownAtRules"
        tests = {
            u'''@three-dee {
              @background-lighting {
                azimuth: 30deg;
                elevation: 190deg;
              }
              h1 { color: red }
            }
            h1 { color: blue }''': (u'''@three-dee {
    @background-lighting {
        azimuth: 30deg;
        elevation: 190deg;
        } h1 {
        color: red
        }
    }
h1 {
    color: blue
    }''', u'''h1 {
    color: blue
    }''')
        }
        for test in tests:
            s = cssutils.parseString(test)
            expwith, expwithout = tests[test]
            cssutils.ser.prefs.keepUnknownAtRules = True
            self.assertEqual(s.cssText, expwith.encode())
            cssutils.ser.prefs.keepUnknownAtRules = False
            self.assertEqual(s.cssText, expwithout.encode())
            
    def test_keepUsedNamespaceRulesOnly(self):
        "Preferences.keepUsedNamespaceRulesOnly"
        tests = {
            # default == prefix => both are combined
            '@namespace p "u"; @namespace "u"; p|a, a {top: 0}':
                ('@namespace "u";\na, a {\n    top: 0\n    }',
                 '@namespace "u";\na, a {\n    top: 0\n    }'),
            '@namespace "u"; @namespace p "u"; p|a, a {top: 0}':
                ('@namespace p "u";\np|a, p|a {\n    top: 0\n    }',
                 '@namespace p "u";\np|a, p|a {\n    top: 0\n    }'),
            # default and prefix
            '@namespace p "u"; @namespace "d"; p|a, a {top: 0}':
                ('@namespace p "u";\n@namespace "d";\np|a, a {\n    top: 0\n    }',
                 '@namespace p "u";\n@namespace "d";\np|a, a {\n    top: 0\n    }'),
            # prefix only
            '@namespace p "u"; @namespace "d"; p|a {top: 0}':
                ('@namespace p "u";\n@namespace "d";\np|a {\n    top: 0\n    }',
                 '@namespace p "u";\np|a {\n    top: 0\n    }'),
            # default only
            '@namespace p "u"; @namespace "d"; a {top: 0}':
                ('@namespace p "u";\n@namespace "d";\na {\n    top: 0\n    }',
                 '@namespace "d";\na {\n    top: 0\n    }'),
            # prefix-ns only
            '@namespace p "u"; @namespace d "d"; p|a {top: 0}':
                ('@namespace p "u";\n@namespace d "d";\np|a {\n    top: 0\n    }',
                 '@namespace p "u";\np|a {\n    top: 0\n    }'),
        }
        for test in tests:
            s = cssutils.parseString(test)
            expwith, expwithout = tests[test]
            cssutils.ser.prefs.keepUsedNamespaceRulesOnly = False
            self.assertEqual(s.cssText, expwith.encode())
            cssutils.ser.prefs.keepUsedNamespaceRulesOnly = True
            self.assertEqual(s.cssText, expwithout.encode())
        
    def test_lineNumbers(self):
        "Preferences.lineNumbers"

        s = cssutils.parseString('a {top: 1; left: 2}')
        exp0 = '''a {
    top: 1;
    left: 2
    }'''
        exp1 = '''1: a {
2:     top: 1;
3:     left: 2
4:     }'''
        self.assertEqual(False, cssutils.ser.prefs.lineNumbers)
        self.assertEqual(exp0.encode(), s.cssText)
        cssutils.ser.prefs.lineNumbers = True
        self.assertEqual(True, cssutils.ser.prefs.lineNumbers)
        self.assertEqual(exp1.encode(), s.cssText)

    def test_lineSeparator(self):
        "Preferences.lineSeparator"
        s = cssutils.parseString('a { x:1;y:2}')
        self.assertEqual('a {\n    x: 1;\n    y: 2\n    }'.encode(), s.cssText)
        # cannot be indented as no split possible
        cssutils.ser.prefs.lineSeparator = u''
        self.assertEqual('a {x: 1;y: 2    }'.encode(), s.cssText)
        # no valid css but should work
        cssutils.ser.prefs.lineSeparator = u'XXX'
        self.assertEqual('a {XXX    x: 1;XXX    y: 2XXX    }'.encode(), s.cssText)

    def test_listItemSpacer(self):
        "Preferences.listItemSpacer"
        cssutils.ser.prefs.keepEmptyRules = True
        
        css = '''
        @import "x" print, tv;
a, b {}'''
        s = cssutils.parseString(css)
        self.assertEqual(u'@import "x" print, tv;\na, b {}'.encode(), s.cssText)
        cssutils.ser.prefs.listItemSpacer = u''
        self.assertEqual(u'@import "x" print,tv;\na,b {}'.encode(), s.cssText)

    def test_minimizeColorHash(self):
        "Preferences.minimizeColorHash"
        css = 'a { color: #ffffff }'
        s = cssutils.parseString(css)
        self.assertEqual(u'a {\n    color: #fff\n    }'.encode(), s.cssText)
        cssutils.ser.prefs.minimizeColorHash = False
        self.assertEqual(u'a {\n    color: #ffffff\n    }'.encode(), s.cssText)
        
    def test_omitLastSemicolon(self):
        "Preferences.omitLastSemicolon"
        css = 'a { x: 1; y: 2 }'
        s = cssutils.parseString(css)
        self.assertEqual(u'a {\n    x: 1;\n    y: 2\n    }'.encode(), s.cssText)
        cssutils.ser.prefs.omitLastSemicolon = False
        self.assertEqual(u'a {\n    x: 1;\n    y: 2;\n    }'.encode(), s.cssText)
        
    def test_normalizedVarNames(self):
        "Preferences.normalizedVarNames"
        cssutils.ser.prefs.resolveVariables = False
        
        css = '@variables { A: 1 }'
        s = cssutils.parseString(css)
        self.assertEqual(u'@variables {\n    a: 1\n    }'.encode(), s.cssText)
        cssutils.ser.prefs.normalizedVarNames = False
        self.assertEqual(u'@variables {\n    A: 1\n    }'.encode(), s.cssText)

        cssutils.ser.prefs.resolveVariables = True

    def test_paranthesisSpacer(self):
        "Preferences.paranthesisSpacer"
        css = 'a { x: 1; y: 2 }'
        s = cssutils.parseString(css)
        self.assertEqual(u'a {\n    x: 1;\n    y: 2\n    }'.encode(), s.cssText)
        cssutils.ser.prefs.paranthesisSpacer = u''
        self.assertEqual(u'a{\n    x: 1;\n    y: 2\n    }'.encode(), s.cssText)
        
    def test_propertyNameSpacer(self):
        "Preferences.propertyNameSpacer"
        css = 'a { x: 1; y: 2 }'
        s = cssutils.parseString(css)
        self.assertEqual(u'a {\n    x: 1;\n    y: 2\n    }'.encode(), s.cssText)
        cssutils.ser.prefs.propertyNameSpacer = u''
        self.assertEqual(u'a {\n    x:1;\n    y:2\n    }'.encode(), s.cssText)
        
    def test_selectorCombinatorSpacer(self):
        "Preferences.selectorCombinatorSpacer"
        s = cssutils.css.Selector(selectorText='a+b>c~d  e')
        self.assertEqual(u'a + b > c ~ d e', s.selectorText)
        cssutils.ser.prefs.selectorCombinatorSpacer = u''
        self.assertEqual(u'a+b>c~d e', s.selectorText)
        
    def test_spacer(self):
        cssutils.ser.prefs.spacer = u''
        tests = {
            u'@font-face {a:1}': u'@font-face {\n    a: 1\n    }',
            u'@import  url( a );': u'@import url(a);',
            u'@media  all{a{color:red}}': u'@media all {\n    a {\n        color: red\n        }\n    }',
            u'@namespace "a";': u'@namespace"a";',
            u'@namespace a  "a";': u'@namespace a"a";',
            u'@page  :left {   a  :1  }': u'@page :left {\n    a: 1\n    }',
            u'@x  x;': u'@x x;',
            u'@import"x"tv': u'@import"x"tv;' # ?
            }
        for css, exp in tests.items():
            self.assertEqual(exp.encode(), cssutils.parseString(css).cssText)
            
    def test_validOnly(self):
        "Preferences.validOnly"
        # Property
        p = cssutils.css.Property('color', '1px')
        self.assertEqual(p.cssText, 'color: 1px')
        p.value = '1px'
        cssutils.ser.prefs.validOnly = True
        self.assertEqual(p.cssText, '')
        cssutils.ser.prefs.validOnly = False
        self.assertEqual(p.cssText, 'color: 1px')
        
        # CSSStyleDeclaration has no actual property valid
        # but is empty if containing invalid Properties only
        s = cssutils.css.CSSStyleDeclaration()
        s.cssText = u'left: x;top: x'
        self.assertEqual(s.cssText, u'left: x;\ntop: x')
        cssutils.ser.prefs.validOnly = True
        self.assertEqual(s.cssText, u'')

        cssutils.ser.prefs.useDefaults()
        cssutils.ser.prefs.keepComments = False
        cssutils.ser.prefs.validOnly = True
        tests = {
            u'h1 { color: red; rotation: 70minutes }': 'h1 {\n    color: red;\n    }',
            u'''img { float: left }       /* correct CSS 2.1 */
img { float: left here }  /* "here" is not a value of 'float' */
img { background: "red" } /* keywords cannot be quoted */
img { border-width: 3 }   /* a unit must be specified for length values */''': 'img {\n    float: left\n    }'
            
        }
        self.do_equal_p(tests, raising=False)
        

class CSSSerializerTestCase(basetest.BaseTestCase):
    """
    testcases for cssutils.CSSSerializer
    """
    def setUp(self):
        cssutils.ser.prefs.useDefaults()
    
    def tearDown(self):
        cssutils.ser.prefs.useDefaults()

    def test_canonical(self):
        tests = {
            u'''1''': u'''1''',
            # => remove +
            u'''+1''': u'''+1''',
            # 0 => remove unit
            u'''0''': u'''0''',
            u'''+0''': u'''0''',
            u'''-0''': u'''0''',
            u'''0.0''': u'''0''',
            u'''00.0''': u'''0''',
            u'''00.0px''': u'''0''',
            u'''00.0pc''': u'''0''',
            u'''00.0em''': u'''0''',
            u'''00.0ex''': u'''0''',
            u'''00.0cm''': u'''0''',
            u'''00.0mm''': u'''0''',
            u'''00.0in''': u'''0''',
            # 0 => keep unit
            u'''00.0%''': u'''0%''',
            u'''00.0ms''': u'''0ms''',
            u'''00.0s''': u'''0s''',
            u'''00.0khz''': u'''0khz''',
            u'''00.0hz''': u'''0hz''',
            u'''00.0khz''': u'''0khz''',
            u'''00.0deg''': u'''0deg''',
            u'''00.0rad''': u'''0rad''',
            u'''00.0grad''': u'''0grad''',
            u'''00.0xx''': u'''0xx''',
            # 11. 
            u'''a, 'b"', serif''': ur'''a, "b\"", serif''',
            # SHOULD: \[ => [ but keep!
            ur"""url('h)i') '\[\]'""": ur'''url("h)i") "\[\]"''',
            u'''rgb(18, 52, 86)''': u'''rgb(18, 52, 86)''',
            u'''#123456''': u'''#123456''',
            # SHOULD => #112233
            u'''#112233''': u'''#123''',
            # SHOULD => #000000
#            u'rgba(000001, 0, 0, 1)': u'#000'
            }
        for test, exp in tests.items():
            v = cssutils.css.PropertyValue(test)
            self.assertEqual(exp, v.cssText)


    def test_CSSStyleSheet(self):
        "CSSSerializer.do_CSSStyleSheet"
        css = u'/* κουρος */'
        sheet = cssutils.parseString(css)
        self.assertEqual(css, unicode(sheet.cssText, 'utf-8'))
        
        css = u'@charset "utf-8";\n/* κουρος */'
        sheet = cssutils.parseString(css)
        self.assertEqual(css, unicode(sheet.cssText, 'utf-8'))
        sheet.cssRules[0].encoding = 'ascii'
        self.assertEqual('@charset "ascii";\n/* \\3BA \\3BF \\3C5 \\3C1 \\3BF \\3C2  */'.encode(), 
                         sheet.cssText)
        
    def test_Property(self):
        "CSSSerializer.do_Property"

        name="color"
        value="red"
        priority="!important"

        s = cssutils.css.property.Property(
            name=name, value=value, priority=priority)
        self.assertEqual(u'color: red !important',
                    cssutils.ser.do_Property(s))

        s = cssutils.css.property.Property(
            name=name, value=value)
        self.assertEqual(u'color: red',
                    cssutils.ser.do_Property(s))

    def test_escapestring(self):
        "CSSSerializer._escapestring"
        #'"\a\22\27"'  
        css = ur'''@import url("ABC\a");
@import "ABC\a";
@import 'ABC\a';
a[href='"\a\22\27"'] {
    a: "\a\d\c";
    b: "\a \d \c ";
    c: "\"";
    d: "\22";
    e: '\'';
    f: "\\";
    g: "2\\ 1\ 2\\";
    content: '\27';
    }'''
#        exp = ur'''@import url("ABC\a ");
#@import "ABC\a";
#@import "ABC\a";
#a[href="\"\a\22\27\""] {
#    a: "\a\d\c";
#    b: "\a \d \c ";
#    c: "\"";
#    d: "\22";
#    e: "'";
#    f: "\\";
#    g: "2\\ 1\ 2\\";
#    content: "\27"
#    }'''
        exp = ur'''@import url("ABC\a ");
@import "ABC\a ";
@import "ABC\a ";
a[href="\"\a \"'\""] {
    a: "\a \d \c ";
    b: "\a \d \c ";
    c: "\"";
    d: "\"";
    e: "'";
    f: "\\";
    g: "2\\ 1\ 2\\";
    content: "'"
    }'''
        sheet = cssutils.parseString(css)
        self.assertEqual(sheet.cssText, exp.encode())
    
    
if __name__ == '__main__':
    import unittest
    unittest.main()
