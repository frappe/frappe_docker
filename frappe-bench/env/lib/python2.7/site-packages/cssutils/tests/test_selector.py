"""Testcases for cssutils.css.selector.Selector.

what should happen here?
    - star 7 hack::
        x*
        does not validate but works in IE>5 and FF, does it???

"""
import xml.dom
import basetest
import cssutils

class SelectorTestCase(basetest.BaseTestCase):

    def setUp(self):
        self.r = cssutils.css.Selector('*')

    def test_init(self):
        "Selector.__init__()"
        s = cssutils.css.Selector('*')
        self.assertEqual((None, '*'), s.element)
        self.assertEqual({}, s._namespaces.namespaces)
        self.assertEqual(None, s.parent)
        self.assertEqual('*', s.selectorText)
        self.assertEqual((0,0,0,0), s.specificity)
        self.assertEqual(True, s.wellformed)

        s = cssutils.css.Selector(('p|b', {'p': 'URI'}) )
        self.assertEqual(('URI', 'b'), s.element)
        self.assertEqual({'p': 'URI'}, s._namespaces.namespaces)
        self.assertEqual(None, s.parent)
        self.assertEqual('p|b', s.selectorText)
        self.assertEqual((0,0,0,1), s.specificity)
        self.assertEqual(True, s.wellformed)

        self.assertRaisesEx(xml.dom.NamespaceErr, cssutils.css.Selector, 'p|b')

    def test_element(self):
        "Selector.element (TODO: RESOLVE)"
        tests = {
            '*': (None, '*'),
            'x': (None, 'x'),
            '\\x': (None, '\\x'),
            '|x': (u'', 'x'),
            '*|x': (cssutils._ANYNS, 'x'),
            'ex|x': (u'example', 'x'),
            'a x': (None, 'x'),
            'a+x': (None, 'x'),
            'a>x': (None, 'x'),
            'a~x': (None, 'x'),
            'a+b~c x': (None, 'x'),
            'x[href]': (None, 'x'),
            'x[href="123"]': (None, 'x'),
            'x:hover': (None, 'x'),
            'x:first-letter': (None, 'x'), # TODO: Really?
            'x::first-line': (None, 'x'), # TODO: Really?
            'x:not(href)': (None, 'x'), # TODO: Really?

            '#id': None,
            '.c': None,
            'x#id': (None, 'x'),
            'x.c': (None, 'x')
        }
        for test, ele in tests.items():
            s = cssutils.css.Selector((test,{'ex': 'example'}))
            self.assertEqual(ele, s.element)

    def test_namespaces(self):
        "Selector.namespaces"
        namespaces = [
            {'p': 'other'}, # no default
            {'': 'default', 'p': 'other'}, # with default
            {'': 'default', 'p': 'default' } # same default
            ]
        tests = {
            # selector: with default, no default, same default
            '*': ('*', '*', '*'),
            'x': ('x', 'x', 'x'),
            '|*': ('|*', '|*', '|*'),
            '|x': ('|x', '|x', '|x'),
            '*|*': ('*|*', '*|*', '*|*'),
            '*|x': ('*|x', '*|x', '*|x'),
            'p|*': ('p|*', 'p|*', '*'),
            'p|x': ('p|x', 'p|x', 'x'),
            'x[a][|a][*|a][p|a]': ('x[a][a][*|a][p|a]',
                                   'x[a][a][*|a][p|a]',
                                   'x[a][a][*|a][a]')
        }
        for sel, exp in tests.items():
            for i, result in enumerate(exp):
                s = cssutils.css.Selector((sel, namespaces[i]))
                self.assertEqual(result, s.selectorText)

        # add to CSSStyleSheet
        sheet = cssutils.css.CSSStyleSheet()
        sheet.cssText = '@namespace p "u"; a { color: green }'

        r = sheet.cssRules[1]

        self.assertEqual(r.selectorText, u'a')

        # add default namespace
        sheet.namespaces[''] = 'a';
        self.assertEqual(r.selectorText, u'|a')

        del sheet.namespaces[''];
        self.assertEqual(r.selectorText, u'a')

#        r.selectorList.append('a')
#        self.assertEqual(r.selectorText, u'|a, a')
#        r.selectorList.append('*|a')
#        self.assertEqual(r.selectorText, u'|a, a, *|a')

    def test_default_namespace(self):
        "Selector.namespaces default"
        css = '''@namespace "default";
                a[att] { color:green; }
        '''
        sheet = cssutils.css.CSSStyleSheet()
        sheet.cssText = css
        self.assertEqual(sheet.cssText,
                         u'@namespace "default";\na[att] {\n    color: green\n    }'.encode())
        # use a prefix for default namespace, does not goes for atts!
        sheet.namespaces['p'] = 'default'
        self.assertEqual(sheet.cssText,
                         u'@namespace p "default";\np|a[att] {\n    color: green\n    }'.encode())

    def test_parent(self):
        "Selector.parent"
        sl = cssutils.css.SelectorList('a, b')
        for sel in sl:
            self.assertEqual(sl, sel.parent)

        newsel = cssutils.css.Selector('x')
        sl.append(newsel)
        self.assertEqual(sl, newsel.parent)

        newsel = cssutils.css.Selector('y')
        sl.appendSelector(newsel)
        self.assertEqual(sl, newsel.parent)

    def test_selectorText(self):
        "Selector.selectorText"
        tests = {
            # combinators
            u'a+b>c~e f': u'a + b > c ~ e f',
            u'a  +  b  >  c  ~  e   f': u'a + b > c ~ e f',
            u'a+b': u'a + b',
            u'a  +  b': 'a + b',
            u'a\n  +\t  b': 'a + b',
            u'a~b': u'a ~ b',
            u'a b': None,
            u'a   b': 'a b',
            u'a\nb': 'a b',
            u'a\tb': 'a b',
            u'a   #b': 'a #b',
            u'a   .b': 'a .b',
            u'a * b': None,
            # >
            u'a>b': u'a > b',
            u'a> b': 'a > b',
            u'a >b': 'a > b',
            u'a > b': 'a > b',
            # +
            u'a+b': u'a + b',
            u'a+ b': 'a + b',
            u'a +b': 'a + b',
            u'a + b': 'a + b',
            # ~
            u'a~b': u'a ~ b',
            u'a~ b': 'a ~ b',
            u'a ~b': 'a ~ b',
            u'a ~ b': 'a ~ b',

            # type selector
            u'a': None,
            u'h1-a_x__--': None,
            u'a-a': None,
            u'a_a': None,
            u'-a': None,
            u'_': None,
            u'-_': None,
            ur'-\72': u'-r',
            #ur'\25': u'%', # TODO: should be escaped!
            u'.a a': None,
            u'a1': None,
            u'a1-1': None,
            u'.a1-1': None,

            # universal
            u'*': None,
            u'*/*x*/': None,
            u'* /*x*/': None,
            u'*:hover': None,
            u'* :hover': None,
            u'*:lang(fr)': None,
            u'* :lang(fr)': None,
            u'*::first-line': None,
            u'* ::first-line': None,
            u'*[lang=fr]': None,
            u'[lang=fr]': None,

            # HASH
            u'''#a''': None,
            u'''#a1''': None,
            u'''#1a''': None, # valid to grammar but not for HTML
            u'''#1''': None, # valid to grammar but not for HTML
            u'''a#b''': None,
            u'''a #b''': None,
            u'''a#b.c''': None,
            u'''a.c#b''': None,
            u'''a #b.c''': None,
            u'''a .c#b''': None,

            # class
            u'ab': 'ab',
            u'a.b': None,
            u'a.b.c': None,
            u'.a1._1': None,

            # attrib
            u'''[x]''': None,
            u'''*[x]''': None,
            u'''a[x]''': None,
            u'''a[ x]''': 'a[x]',
            u'''a[x ]''': 'a[x]',
            u'''a [x]''': 'a [x]',
            u'''* [x]''': None, # is really * *[x]

            u'''a[x="1"]''': None,
            u'''a[x ="1"]''': 'a[x="1"]',
            u'''a[x= "1"]''': 'a[x="1"]',
            u'''a[x = "1"]''': 'a[x="1"]',
            u'''a[ x = "1"]''': 'a[x="1"]',
            u'''a[x = "1" ]''': 'a[x="1"]',
            u'''a[ x = "1" ]''': 'a[x="1"]',
            u'''a [ x = "1" ]''': 'a [x="1"]',

            u'''a[x~=a1]''': None,
            u'''a[x ~=a1]''': 'a[x~=a1]',
            u'''a[x~= a1]''': 'a[x~=a1]',
            u'''a[x ~= a1]''': 'a[x~=a1]',
            u'''a[ x ~= a1]''': 'a[x~=a1]',
            u'''a[x ~= a1 ]''': 'a[x~=a1]',
            u'''a[ x ~= a1 ]''': 'a[x~=a1]',
            u'''a [ x ~= a1 ]''': 'a [x~=a1]', # same as next!
            u'''a *[ x ~= a1 ]''': 'a *[x~=a1]',

            u'''a[x|=en]''': None,
            u'''a[x|= en]''': 'a[x|=en]',
            u'''a[x |=en]''': 'a[x|=en]',
            u'''a[x |= en]''': 'a[x|=en]',
            u'''a[ x |= en]''': 'a[x|=en]',
            u'''a[x |= en ]''': 'a[x|=en]',
            u'''a[ x |= en]''': 'a[x|=en]',
            u'''a [ x |= en]''': 'a [x|=en]',
            # CSS3
            u'''a[x^=en]''': None,
            u'''a[x$=en]''': None,
            u'''a[x*=en]''': None,

            u'''a[/*1*/x/*2*/]''': None,
            u'''a[/*1*/x/*2*/=/*3*/a/*4*/]''': None,
            u'''a[/*1*/x/*2*/~=/*3*/a/*4*/]''': None,
            u'''a[/*1*/x/*2*/|=/*3*/a/*4*/]''': None,

            # pseudo-elements
            u'a x:first-line': None,
            u'a x:first-letter': None,
            u'a x:before': None,
            u'a x:after': None,
            u'a x::selection': None,
            u'a:hover+b:hover>c:hover~e:hover f:hover':
                u'a:hover + b:hover > c:hover ~ e:hover f:hover',
            u'a:hover  +  b:hover  >  c:hover  ~  e:hover   f:hover':
                u'a:hover + b:hover > c:hover ~ e:hover f:hover',
            u'a::selection+b::selection>c::selection~e::selection f::selection':
                u'a::selection + b::selection > c::selection ~ e::selection f::selection',
            u'a::selection  +  b::selection  >  c::selection  ~  e::selection   f::selection':
                u'a::selection + b::selection > c::selection ~ e::selection f::selection',

            u'x:lang(de) y': None,
            u'x:nth-child(odd) y': None,
            # functional pseudo
            u'x:func(a + b-2px22.3"s"i)': None,
            u'x:func(1 + 1)': None,
            u'x:func(1+1)': u'x:func(1+1)',
            u'x:func(1   +   1)': u'x:func(1 + 1)',
            u'x:func(1-1)': u'x:func(1-1)',
            u'x:func(1  -  1)': u'x:func(1 -1)', # TODO: FIX!
            u'x:func(a-1)': u'x:func(a-1)',
            u'x:func(a -1px)': u'x:func(a -1px)',
            u'x:func(1px)': None,
            u'x:func(23.4)': None,
            u'x:func("s")': None,
            u'x:func(i)': None,

            # negation
            u':not(y)': None,
            u':not(   y  \t\n)': u':not(y)',
            u'*:not(y)': None,
            u'x:not(y)': None,
            u'.x:not(y)': None,
            u':not(*)': None,
            u':not(#a)': None,
            u':not(.a)': None,
            u':not([a])': None,
            u':not(:first-letter)': None,
            u':not(::first-letter)': None,

            # escapes
            ur'\74\72 td': 'trtd',
            ur'\74\72  td': 'tr td',
            ur'\74\000072 td': 'trtd',
            ur'\74\000072  td': 'tr td',

            # comments
            u'a/**/ b': None,
            u'a /**/b': None,
            u'a /**/ b': None,
            u'a  /**/ b': u'a /**/ b',
            u'a /**/  b': u'a /**/ b',

            # namespaces
            u'|e': None,
            u'*|e': None,
            u'*|*': None,
            (u'p|*', (('p', 'uri'),)): u'p|*',
            (u'p|e', (('p', 'uri'),)): u'p|e',
            (u'-a_x12|e', (('-a_x12', 'uri'),)): u'-a_x12|e',
            (u'*|b[p|a]', (('p', 'uri'),)): '*|b[p|a]',

            # case
            u'elemenT.clasS#iD[atT="valuE"]:noT(x)::firsT-linE':
                u'elemenT.clasS#iD[atT="valuE"]:not(x)::first-line'
            }
        # do not parse as not complete
        self.do_equal_r(tests, att='selectorText')

        tests = {
            u'x|a': xml.dom.NamespaceErr,
            (u'p|*', (('x', 'uri'),)): xml.dom.NamespaceErr,

            u'': xml.dom.SyntaxErr,
            u'1': xml.dom.SyntaxErr,
            u'-1': xml.dom.SyntaxErr,
            u'a*b': xml.dom.SyntaxErr,
            u'a *b': xml.dom.SyntaxErr,
            u'a* b': xml.dom.SyntaxErr,
            u'a/**/b': xml.dom.SyntaxErr,

            u'#': xml.dom.SyntaxErr,
            u'|': xml.dom.SyntaxErr,

            u':': xml.dom.SyntaxErr,
            u'::': xml.dom.SyntaxErr,
            u': a': xml.dom.SyntaxErr,
            u':: a': xml.dom.SyntaxErr,
            u':a()': xml.dom.SyntaxErr, # no value
            u'::a()': xml.dom.SyntaxErr, # no value
            u':::a': xml.dom.SyntaxErr,
            u':1': xml.dom.SyntaxErr,

            u'#.x': xml.dom.SyntaxErr,
            u'.': xml.dom.SyntaxErr,
            u'.1': xml.dom.SyntaxErr,
            u'.a.1': xml.dom.SyntaxErr,

            u'[a': xml.dom.SyntaxErr,
            u'a]': xml.dom.SyntaxErr,
            u'[a b]': xml.dom.SyntaxErr,
            u'[=b]': xml.dom.SyntaxErr,
            u'[a=]': xml.dom.SyntaxErr,
            u'[a|=]': xml.dom.SyntaxErr,
            u'[a~=]': xml.dom.SyntaxErr,
            u'[a=1]': xml.dom.SyntaxErr,

            u'a +': xml.dom.SyntaxErr,
            u'a >': xml.dom.SyntaxErr,
            u'a ++ b': xml.dom.SyntaxErr,
            u'a + > b': xml.dom.SyntaxErr,

            # functional pseudo
            u'*:lang(': xml.dom.SyntaxErr,
            u'*:lang()': xml.dom.SyntaxErr, # no arg

            # negation
            u'not(x)': xml.dom.SyntaxErr, # no valid function
            u':not()': xml.dom.SyntaxErr, # no arg
            u':not(x': xml.dom.SyntaxErr, # no )
            u':not(-': xml.dom.SyntaxErr, # not allowed
            u':not(+': xml.dom.SyntaxErr, # not allowed

            # only one selector!
            u',': xml.dom.InvalidModificationErr,
            u',a': xml.dom.InvalidModificationErr,
            u'a,': xml.dom.InvalidModificationErr,

            # @
            u'p @here': xml.dom.SyntaxErr, # not allowed

            }
        # only set as not complete
        self.do_raise_r(tests, att='_setSelectorText')

    def test_specificity(self):
        "Selector.specificity"
        selector = cssutils.css.Selector()

        # readonly
        def _set(): selector.specificity = 1
        self.assertRaisesMsg(AttributeError, "can't set attribute", _set)

        tests = {
            u'*': (0,0,0,0),
            u'li': (0,0,0,1),
            u'li:first-line': (0,0,0,2),
            u'ul li': (0,0,0,2),
            u'ul ol+li': (0,0,0,3),
            u'h1 + *[rel=up]': (0,0,1,1),
            u'ul ol li.red': (0,0,1,3),
            u'li.red.level': (0,0,2,1),
            u'#x34y': (0,1,0,0),

            u'UL OL LI.red': (0,0,1,3),
            u'LI.red.level': (0,0,2,1),
            u'#s12:not(FOO)': (0,1,0,1),
            u'button:not([DISABLED])': (0,0,1,1), #?
            u'*:not(FOO)': (0,0,0,1),

            # elements
            u'a+b': (0,0,0,2),
            u'a>b': (0,0,0,2),
            u'a b': (0,0,0,2),
            u'* a': (0,0,0,1),
            u'a *': (0,0,0,1),
            u'a * b': (0,0,0,2),

            u'a:hover': (0,0,0,1),

            u'a:first-line': (0,0,0,2),
            u'a:first-letter': (0,0,0,2),
            u'a:before': (0,0,0,2),
            u'a:after': (0,0,0,2),

            # classes and attributes
            u'.a': (0,0,1,0),
            u'*.a': (0,0,1,0),
            u'a.a': (0,0,1,1),
            u'.a.a': (0,0,2,0), # IE<7 False (0,0,1,0)
            u'a.a.a': (0,0,2,1),
            u'.a.b': (0,0,2,0),
            u'a.a.b': (0,0,2,1),
            u'.a .a': (0,0,2,0),
            u'*[x]': (0,0,1,0),
            u'*[x]': (0,0,1,0),
            u'*[x]': (0,0,1,0),
            u'*[x=a]': (0,0,1,0),
            u'*[x~=a]': (0,0,1,0),
            u'*[x|=a]': (0,0,1,0),
            u'*[x^=a]': (0,0,1,0),
            u'*[x*=a]': (0,0,1,0),
            u'*[x$=a]': (0,0,1,0),
            u'*[x][y]': (0,0,2,0),

            # ids
            u'#a': (0,1,0,0),
            u'*#a': (0,1,0,0),
            u'x#a': (0,1,0,1),
            u'.x#a': (0,1,1,0),
            u'a.x#a': (0,1,1,1),
            u'#a#a': (0,2,0,0), # e.g. html:id + xml:id
            u'#a#b': (0,2,0,0),
            u'#a #b': (0,2,0,0),
            }
        for text in tests:
            selector.selectorText = text
            self.assertEqual(tests[text], selector.specificity)

    def test_reprANDstr(self):
        "Selector.__repr__(), .__str__()"
        sel=u'a + b'

        s = cssutils.css.Selector(selectorText=sel)

        self.assertTrue(sel in str(s))

        s2 = eval(repr(s))
        self.assertTrue(isinstance(s2, s.__class__))
        self.assertTrue(sel == s2.selectorText)


if __name__ == '__main__':
    import unittest
    unittest.main()
