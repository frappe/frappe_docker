"""Testcases for cssutils.css.CSSImportRule"""

import xml.dom
import test_cssrule
import cssutils

import basetest

class CSSImportRuleTestCase(test_cssrule.CSSRuleTestCase):

    def setUp(self):
        super(CSSImportRuleTestCase, self).setUp()
        self.r = cssutils.css.CSSImportRule()
        self.rRO = cssutils.css.CSSImportRule(readonly=True)
        self.r_type = cssutils.css.CSSImportRule.IMPORT_RULE
        self.r_typeString = 'IMPORT_RULE'

    def test_init(self):
        "CSSImportRule.__init__()"
        super(CSSImportRuleTestCase, self).test_init()

        # no init param
        self.assertEqual(None, self.r.href)
        self.assertEqual(None, self.r.hreftype)
        self.assertEqual(False, self.r.hrefFound)
        self.assertEqual(u'all', self.r.media.mediaText)
        self.assertEqual(
            cssutils.stylesheets.MediaList, type(self.r.media))
        self.assertEqual(None, self.r.name)
        self.assertEqual(cssutils.css.CSSStyleSheet, type(self.r.styleSheet))
        self.assertEqual(0, self.r.styleSheet.cssRules.length)
        self.assertEqual(u'', self.r.cssText)

        # all
        r = cssutils.css.CSSImportRule(href='href', mediaText='tv', name='name')
        self.assertEqual(u'@import url(href) tv "name";', r.cssText)
        self.assertEqual("href", r.href)
        self.assertEqual(None, r.hreftype)
        self.assertEqual(u'tv', r.media.mediaText)
        self.assertEqual(
            cssutils.stylesheets.MediaList, type(r.media))
        self.assertEqual('name', r.name)
        self.assertEqual(None, r.parentRule) # see CSSRule
        self.assertEqual(None, r.parentStyleSheet) # see CSSRule
        self.assertEqual(cssutils.css.CSSStyleSheet, type(self.r.styleSheet))
        self.assertEqual(0, self.r.styleSheet.cssRules.length)
        
        # href
        r = cssutils.css.CSSImportRule(u'x')
        self.assertEqual(u'@import url(x);', r.cssText)
        self.assertEqual('x', r.href)
        self.assertEqual(None, r.hreftype)

        # href + mediaText
        r = cssutils.css.CSSImportRule(u'x', u'print')
        self.assertEqual(u'@import url(x) print;', r.cssText)
        self.assertEqual('x', r.href)
        self.assertEqual('print', r.media.mediaText)

        # href + name
        r = cssutils.css.CSSImportRule(u'x', name=u'n')
        self.assertEqual(u'@import url(x) "n";', r.cssText)
        self.assertEqual('x', r.href)
        self.assertEqual('n', r.name)

        # href + mediaText + name
        r = cssutils.css.CSSImportRule(u'x', u'print', 'n')
        self.assertEqual(u'@import url(x) print "n";', r.cssText)
        self.assertEqual('x', r.href)
        self.assertEqual('print', r.media.mediaText)
        self.assertEqual('n', r.name)

        # media +name only
        self.r = cssutils.css.CSSImportRule(mediaText=u'print', name="n")
        self.assertEqual(cssutils.stylesheets.MediaList,
                         type(self.r.media))
        self.assertEqual(u'', self.r.cssText)
        self.assertEqual(u'print', self.r.media.mediaText)
        self.assertEqual(u'n', self.r.name)

        # only possible to set @... similar name
        self.assertRaises(xml.dom.InvalidModificationErr, self.r._setAtkeyword, 'x')

    def test_cssText(self):
        "CSSImportRule.cssText"
        tests = {
            # href string
            u'''@import "str";''': None,
            u'''@import"str";''': u'''@import "str";''',
            u'''@\\import "str";''': u'''@import "str";''',
            u'''@IMPORT "str";''': u'''@import "str";''',
            u'''@import 'str';''': u'''@import "str";''',
            u'''@import 'str' ;''': u'''@import "str";''',
            u'''@import "str";''': None,
            u'''@import "str"  ;''': u'''@import "str";''',
            ur'''@import "\""  ;''': ur'''@import "\"";''',
            u'''@import '\\'';''': ur'''@import "'";''',
            u'''@import '"';''': ur'''@import "\"";''',
            # href url
            u'''@import url(x.css);''': None,
            # nospace
            u'''@import url(")");''': u'''@import url(")");''',
            u'''@import url("\\"");''': u'''@import url("\\"");''',
            u'''@import url('\\'');''': u'''@import url("'");''',

            # href + media
            # all is removed
            u'''@import "str" all;''': u'''@import "str";''',
            u'''@import "str" tv, print;''': None,
            u'''@import"str"tv,print;''': u'''@import "str" tv, print;''',
            u'''@import "str" tv, print, all;''': u'''@import "str";''',
            u'''@import "str" handheld, all;''': u'''@import "str";''',
            u'''@import "str" all, handheld;''': u'''@import "str";''',
            u'''@import "str" not tv;''': None,
            u'''@import "str" only tv;''': None,
            u'''@import "str" only tv and (color: 2);''': None,

            # href + name
            u'''@import "str" "name";''': None,
            u'''@import "str" 'name';''': u'''@import "str" "name";''',
            u'''@import url(x) "name";''': None,
            u'''@import "str" "\\"";''': None,
            u'''@import "str" '\\'';''': u'''@import "str" "'";''',

            # href + media + name
            u'''@import"str"tv"name";''': u'''@import "str" tv "name";''',
            u'''@import\t\r\f\n"str"\t\t\r\f\ntv\t\t\r\f\n"name"\t;''': 
                u'''@import "str" tv "name";''',

            # comments
            u'''@import /*1*/ "str" /*2*/;''': None,
            u'@import/*1*//*2*/"str"/*3*//*4*/all/*5*//*6*/"name"/*7*//*8*/ ;': 
                u'@import /*1*/ /*2*/ "str" /*3*/ /*4*/ all /*5*/ /*6*/ "name" /*7*/ /*8*/;',
            u'@import/*1*//*2*/url(u)/*3*//*4*/all/*5*//*6*/"name"/*7*//*8*/ ;': 
                u'@import /*1*/ /*2*/ url(u) /*3*/ /*4*/ all /*5*/ /*6*/ "name" /*7*/ /*8*/;',
            u'@import/*1*//*2*/url("u")/*3*//*4*/all/*5*//*6*/"name"/*7*//*8*/ ;': 
                u'@import /*1*/ /*2*/ url(u) /*3*/ /*4*/ all /*5*/ /*6*/ "name" /*7*/ /*8*/;',
            # WS
            u'@import\n\t\f "str"\n\t\f tv\n\t\f "name"\n\t\f ;': 
                u'@import "str" tv "name";',
            u'@import\n\t\f url(\n\t\f u\n\t\f )\n\t\f tv\n\t\f "name"\n\t\f ;': 
                u'@import url(u) tv "name";',
            u'@import\n\t\f url("u")\n\t\f tv\n\t\f "name"\n\t\f ;': 
                u'@import url(u) tv "name";',
            u'@import\n\t\f url(\n\t\f "u"\n\t\f )\n\t\f tv\n\t\f "name"\n\t\f ;': 
                u'@import url(u) tv "name";',
            }
        self.do_equal_r(tests) # set cssText
        tests.update({
            u'@import "x.css" tv': '@import "x.css" tv;',
            u'@import "x.css"': '@import "x.css";', # no ;
            u"@import 'x.css'": '@import "x.css";', # no ;
            u'@import url(x.css)': '@import url(x.css);', # no ;
            u'@import "x;': '@import "x;";', # no "!
            })
        self.do_equal_p(tests) # parse

        tests = {
            u'''@import;''': xml.dom.SyntaxErr,
            u'''@import all;''': xml.dom.SyntaxErr,
            u'''@import all"name";''': xml.dom.SyntaxErr,
            u'''@import;''': xml.dom.SyntaxErr,
            u'''@import x";''': xml.dom.SyntaxErr,
            u'''@import "str" ,all;''': xml.dom.SyntaxErr,
            u'''@import "str" all,;''': xml.dom.SyntaxErr,
            u'''@import "str" all tv;''': xml.dom.SyntaxErr,
            u'''@import "str" "name" all;''': xml.dom.SyntaxErr,
            }
        self.do_raise_p(tests) # parse
        tests.update({
            u'@import "x.css"': xml.dom.SyntaxErr,
            u"@import 'x.css'": xml.dom.SyntaxErr,
            u'@import url(x.css)': xml.dom.SyntaxErr,
            u'@import "x.css" tv': xml.dom.SyntaxErr,
            u'@import "x;': xml.dom.SyntaxErr,
            u'''@import url("x);''': xml.dom.SyntaxErr,
            # trailing
            u'''@import "x";"a"''': xml.dom.SyntaxErr,
            # trailing S or COMMENT
            u'''@import "x";/**/''': xml.dom.SyntaxErr,
            u'''@import "x"; ''': xml.dom.SyntaxErr,
            })
        self.do_raise_r(tests) # set cssText

    def test_href(self):
        "CSSImportRule.href"
        # set
        self.r.href = 'x'
        self.assertEqual('x', self.r.href)
        self.assertEqual(u'@import url(x);', self.r.cssText)

        # http
        self.r.href = 'http://www.example.com/x?css=z&v=1'
        self.assertEqual('http://www.example.com/x?css=z&v=1' , self.r.href)
        self.assertEqual(u'@import url(http://www.example.com/x?css=z&v=1);',
                         self.r.cssText)

        # also if hreftype changed
        self.r.hreftype='string'
        self.assertEqual('http://www.example.com/x?css=z&v=1' , self.r.href)
        self.assertEqual(u'@import "http://www.example.com/x?css=z&v=1";',
                         self.r.cssText)
        
        # string escaping?
        self.r.href = '"'
        self.assertEqual(u'@import "\\"";', self.r.cssText)
        self.r.hreftype='url'
        self.assertEqual(u'@import url("\\"");', self.r.cssText)
        
        # url escaping?
        self.r.href = ')'
        self.assertEqual(u'@import url(")");', self.r.cssText)

        self.r.hreftype = 'NOT VALID' # using default
        self.assertEqual(u'@import url(")");', self.r.cssText)

    def test_hrefFound(self):
        "CSSImportRule.hrefFound"
        def fetcher(url):
            if url == u'http://example.com/yes': 
                return None, u'/**/'
            else:
                return None, None
            
        parser = cssutils.CSSParser(fetcher=fetcher)
        sheet = parser.parseString(u'@import "http://example.com/yes" "name"')
        
        r = sheet.cssRules[0]
        self.assertEqual(u'/**/'.encode(), r.styleSheet.cssText)
        self.assertEqual(True, r.hrefFound)
        self.assertEqual(u'name', r.name)
        
        r.cssText = '@import url(http://example.com/none) "name2";'
        self.assertEqual(u''.encode(), r.styleSheet.cssText)
        self.assertEqual(False, r.hrefFound)
        self.assertEqual(u'name2', r.name)

        sheet.cssText = '@import url(http://example.com/none);'
        self.assertNotEqual(r, sheet.cssRules[0])

    def test_hreftype(self):
        "CSSImportRule.hreftype"
        self.r = cssutils.css.CSSImportRule()

        self.r.cssText = '@import /*1*/url(org) /*2*/;'
        self.assertEqual('uri', self.r.hreftype)
        self.assertEqual(u'@import /*1*/ url(org) /*2*/;', self.r.cssText)

        self.r.cssText = '@import /*1*/"org" /*2*/;'
        self.assertEqual('string', self.r.hreftype)
        self.assertEqual(u'@import /*1*/ "org" /*2*/;', self.r.cssText)

        self.r.href = 'new'
        self.assertEqual(u'@import /*1*/ "new" /*2*/;', self.r.cssText)

        self.r.hreftype='uri'
        self.assertEqual(u'@import /*1*/ url(new) /*2*/;', self.r.cssText)

    def test_media(self):
        "CSSImportRule.media"
        self.r.href = 'x' # @import url(x)

        # media is readonly
        self.assertRaises(AttributeError, self.r.__setattr__, 'media', None)

        # but not static
        self.r.media.mediaText = 'print'
        self.assertEqual(u'@import url(x) print;', self.r.cssText)
        self.r.media.appendMedium('tv')
        self.assertEqual(u'@import url(x) print, tv;', self.r.cssText)

        # for generated rule
        r = cssutils.css.CSSImportRule(href='x')
        self.assertRaisesMsg(xml.dom.InvalidModificationErr, 
                             basetest.msg3x('''MediaList: Ignoring new medium cssutils.stylesheets.MediaQuery(mediaText=u'tv') as already specified "all" (set ``mediaText`` instead).'''), 
                             r.media.appendMedium, 'tv')
        self.assertEqual(u'@import url(x);', r.cssText)
        self.assertRaisesMsg(xml.dom.InvalidModificationErr, 
                             basetest.msg3x('''MediaList: Ignoring new medium cssutils.stylesheets.MediaQuery(mediaText=u'tv') as already specified "all" (set ``mediaText`` instead).'''), 
                             r.media.appendMedium, 'tv')
        self.assertEqual(u'@import url(x);', r.cssText)
        r.media.mediaText = 'tv' 
        self.assertEqual(u'@import url(x) tv;', r.cssText)
        r.media.appendMedium('print') # all + tv = all!
        self.assertEqual(u'@import url(x) tv, print;', r.cssText)

        # for parsed rule without initial media
        s = cssutils.parseString('@import url(x);')
        r = s.cssRules[0]
        
        self.assertRaisesMsg(xml.dom.InvalidModificationErr, 
                             basetest.msg3x('''MediaList: Ignoring new medium cssutils.stylesheets.MediaQuery(mediaText=u'tv') as already specified "all" (set ``mediaText`` instead).'''), 
                             r.media.appendMedium, 'tv')        
        self.assertEqual(u'@import url(x);', r.cssText)
        self.assertRaisesMsg(xml.dom.InvalidModificationErr, 
                             basetest.msg3x('''MediaList: Ignoring new medium cssutils.stylesheets.MediaQuery(mediaText=u'tv') as already specified "all" (set ``mediaText`` instead).'''), 
                             r.media.appendMedium, 'tv')
        self.assertEqual(u'@import url(x);', r.cssText)
        r.media.mediaText = 'tv' 
        self.assertEqual(u'@import url(x) tv;', r.cssText)
        r.media.appendMedium('print') # all + tv = all!
        self.assertEqual(u'@import url(x) tv, print;', r.cssText)

    def test_name(self):
        "CSSImportRule.name"
        r = cssutils.css.CSSImportRule('x', name='a000000')
        self.assertEqual('a000000', r.name)
        self.assertEqual(u'@import url(x) "a000000";', r.cssText)

        r.name = "n"
        self.assertEqual('n', r.name)
        self.assertEqual(u'@import url(x) "n";', r.cssText)
        r.name = '"'
        self.assertEqual('"', r.name)
        self.assertEqual(u'@import url(x) "\\"";', r.cssText)
        
        r.hreftype = 'string'
        self.assertEqual(u'@import "x" "\\"";', r.cssText)
        r.name = "123"
        self.assertEqual(u'@import "x" "123";', r.cssText)

        r.name = None
        self.assertEqual(None, r.name)
        self.assertEqual(u'@import "x";', r.cssText)

        r.name = ""
        self.assertEqual(None, r.name)
        self.assertEqual(u'@import "x";', r.cssText)
        
        self.assertRaises(xml.dom.SyntaxErr, r._setName, 0)
        self.assertRaises(xml.dom.SyntaxErr, r._setName, 123)

    def test_styleSheet(self):
        "CSSImportRule.styleSheet"
        def fetcher(url):
            if url == "/root/level1/anything.css": 
                return None, '@import "level2/css.css" "title2";'
            else:
                return None, 'a { color: red }'
            
        parser = cssutils.CSSParser(fetcher=fetcher)
        sheet = parser.parseString('''@charset "ascii";
                                   @import "level1/anything.css" tv "title";''', 
                                   href='/root/')
        
        self.assertEqual(sheet.href, '/root/')
        
        ir = sheet.cssRules[1]
        self.assertEqual(ir.href, 'level1/anything.css')
        self.assertEqual(ir.styleSheet.href, '/root/level1/anything.css')
        # inherits ascii as no self charset is set 
        self.assertEqual(ir.styleSheet.encoding, 'ascii')
        self.assertEqual(ir.styleSheet.ownerRule, ir)
        self.assertEqual(ir.styleSheet.media.mediaText, 'tv')
        self.assertEqual(ir.styleSheet.parentStyleSheet, None) # sheet
        self.assertEqual(ir.styleSheet.title, 'title')
        self.assertEqual(ir.styleSheet.cssText, 
                         '@charset "ascii";\n@import "level2/css.css" "title2";'.encode())

        ir2 = ir.styleSheet.cssRules[1]
        self.assertEqual(ir2.href, 'level2/css.css')
        self.assertEqual(ir2.styleSheet.href, '/root/level1/level2/css.css')
        # inherits ascii as no self charset is set 
        self.assertEqual(ir2.styleSheet.encoding, 'ascii')
        self.assertEqual(ir2.styleSheet.ownerRule, ir2)
        self.assertEqual(ir2.styleSheet.media.mediaText, 'all')
        self.assertEqual(ir2.styleSheet.parentStyleSheet, None) #ir.styleSheet
        self.assertEqual(ir2.styleSheet.title, 'title2')
        self.assertEqual(ir2.styleSheet.cssText, 
                         '@charset "ascii";\na {\n    color: red\n    }'.encode())

        sheet = cssutils.parseString('@import "CANNOT-FIND.css";')
        ir = sheet.cssRules[0]
        self.assertEqual(ir.href, "CANNOT-FIND.css")
        self.assertEqual(type(ir.styleSheet), cssutils.css.CSSStyleSheet)

        def fetcher(url):
            if url.endswith('level1.css'): 
                return None, u'@charset "ascii"; @import "level2.css";'.encode()
            else:
                return None, u'a { color: red }'.encode()
            
        parser = cssutils.CSSParser(fetcher=fetcher)
        
        sheet = parser.parseString('@charset "iso-8859-1";@import "level1.css";')
        self.assertEqual(sheet.encoding, 'iso-8859-1')

        sheet = sheet.cssRules[1].styleSheet
        self.assertEqual(sheet.encoding, 'ascii')

        sheet = sheet.cssRules[1].styleSheet
        self.assertEqual(sheet.encoding, 'ascii')

    def test_incomplete(self):
        "CSSImportRule (incomplete)"
        tests = {
            u'@import "x.css': u'@import "x.css";',
            u"@import 'x": u'@import "x";',
            # TODO:
            u"@import url(x": u'@import url(x);',
            u"@import url('x": u'@import url(x);',
            u'@import url("x;': u'@import url("x;");',
            u'@import url( "x;': u'@import url("x;");',
            u'@import url("x ': u'@import url("x ");',
            u'@import url(x ': u'@import url(x);',
            u'''@import "a
                @import "b";
                @import "c";''': u'@import "c";'
        }
        self.do_equal_p(tests, raising=False) # parse
        
    def test_InvalidModificationErr(self):
        "CSSImportRule.cssText InvalidModificationErr"
        self._test_InvalidModificationErr(u'@import')

    def test_reprANDstr(self):
        "CSSImportRule.__repr__(), .__str__()"
        href = 'x.css'
        mediaText = 'tv, print'
        name = 'name'
        s = cssutils.css.CSSImportRule(href=href, mediaText=mediaText, name=name)

        # str(): mediaText nor name are present here
        self.assertTrue(href in str(s))
        
        # repr()
        s2 = eval(repr(s))
        self.assertTrue(isinstance(s2, s.__class__))
        self.assertTrue(href == s2.href)
        self.assertTrue(mediaText == s2.media.mediaText)
        self.assertTrue(name == s2.name)


if __name__ == '__main__':
    import unittest
    unittest.main()
