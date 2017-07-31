"""Testcases for cssutils.css.CSSPageRule"""
__version__ = '$Id: test_csspagerule.py 1869 2009-10-17 19:37:40Z cthedot $'

import xml.dom
import test_cssrule
import cssutils

class CSSVariablesRuleTestCase(test_cssrule.CSSRuleTestCase):

    def setUp(self):
        super(CSSVariablesRuleTestCase, self).setUp()
        self.r = cssutils.css.CSSVariablesRule()
        self.rRO = cssutils.css.CSSVariablesRule(readonly=True)
        self.r_type = cssutils.css.CSSPageRule.VARIABLES_RULE
        self.r_typeString = 'VARIABLES_RULE'
        
        cssutils.ser.prefs.resolveVariables = False

    def test_init(self):
        "CSSVariablesRule.__init__()"
        super(CSSVariablesRuleTestCase, self).test_init()

        r = cssutils.css.CSSVariablesRule()
        self.assertEqual(cssutils.css.CSSVariablesDeclaration, 
                         type(r.variables))
        self.assertEqual(r, r.variables.parentRule)

        # until any variables
        self.assertEqual(u'', r.cssText)

        # only possible to set @... similar name
        self.assertRaises(xml.dom.InvalidModificationErr, 
                          self.r._setAtkeyword, 'x')

    def test_InvalidModificationErr(self):
        "CSSVariablesRule.cssText InvalidModificationErr"
        self._test_InvalidModificationErr(u'@variables')
        tests = {
            u'@var {}': xml.dom.InvalidModificationErr,
            }
        self.do_raise_r(tests)

    def test_incomplete(self):
        "CSSVariablesRule (incomplete)"
        tests = {
            u'@variables { ':
                u'', # no } and no content
            u'@variables { x: red':
                u'@variables {\n    x: red\n    }', # no }
        }
        self.do_equal_p(tests) # parse

    def test_cssText(self):
        "CSSVariablesRule"
        EXP = u'@variables {\n    margin: 0\n    }'
        tests = {
             u'@variables {}': u'',
             u'@variables     {margin:0;}': EXP,
             u'@variables     {margin:0}': EXP,
             u'@VaRIables {   margin    :   0   ;    }': EXP,
            u'@\\VaRIables {    margin : 0    }': EXP,

            u'@variables {a:1;b:2}': 
                u'@variables {\n    a: 1;\n    b: 2\n    }',

            # comments
            u'@variables   /*1*/   {margin:0;}': 
                u'@variables /*1*/ {\n    margin: 0\n    }',
            u'@variables/*1*/{margin:0;}': 
                u'@variables /*1*/ {\n    margin: 0\n    }',
            }
        self.do_equal_r(tests)
        self.do_equal_p(tests)

    def test_media(self):
        "CSSVariablesRule.media"
        r = cssutils.css.CSSVariablesRule()
        self.assertRaises(AttributeError, r.__getattribute__, 'media')
        self.assertRaises(AttributeError, r.__setattr__, 'media', '?')
        
    def test_variables(self):
        "CSSVariablesRule.variables"                
        r = cssutils.css.CSSVariablesRule(
                 variables=cssutils.css.CSSVariablesDeclaration('x: 1'))
        self.assertEqual(r, r.variables.parentRule)

        # cssText
        r = cssutils.css.CSSVariablesRule()
        r.cssText = u'@variables { x: 1 }'
        vars1 = r.variables
        self.assertEqual(r, r.variables.parentRule)
        self.assertEqual(vars1, r.variables)
        self.assertEqual(r.variables.cssText, u'x: 1')
        self.assertEqual(r.cssText, u'@variables {\n    x: 1\n    }')
        
        r.cssText = u'@variables {y:2}'
        self.assertEqual(r, r.variables.parentRule)
        self.assertNotEqual(vars1, r.variables)
        self.assertEqual(r.variables.cssText, u'y: 2')
        self.assertEqual(r.cssText, u'@variables {\n    y: 2\n    }')

        vars2 = r.variables
        
        # fail
        try:
            r.cssText = u'@variables {$:1}'
        except xml.dom.DOMException, e:
            pass

        self.assertEqual(vars2, r.variables)
        self.assertEqual(r.variables.cssText, u'y: 2')
        self.assertEqual(r.cssText, u'@variables {\n    y: 2\n    }')

        # var decl
        vars3 = cssutils.css.CSSVariablesDeclaration('z: 3')
        r.variables = vars3

        self.assertEqual(r, r.variables.parentRule)
        self.assertEqual(vars3, r.variables)
        self.assertEqual(r.variables.cssText, u'z: 3')
        self.assertEqual(r.cssText, u'@variables {\n    z: 3\n    }')

        # string
        r.variables = 'a: x'
        self.assertNotEqual(vars3, r.variables)
        self.assertEqual(r, r.variables.parentRule)
        self.assertEqual(r.variables.cssText, u'a: x')
        self.assertEqual(r.cssText, u'@variables {\n    a: x\n    }')
        vars4 = r.variables

        # string fail
        try:
            r.variables = '$: x'
        except xml.dom.DOMException, e:
            pass
        self.assertEqual(vars4, r.variables)
        self.assertEqual(r, r.variables.parentRule)
        self.assertEqual(r.variables.cssText, u'a: x')
        self.assertEqual(r.cssText, u'@variables {\n    a: x\n    }')
        
        
    def test_reprANDstr(self):
        "CSSVariablesRule.__repr__(), .__str__()"
        r = cssutils.css.CSSVariablesRule()
        r.cssText = '@variables { xxx: 1 }'
        self.assertTrue('xxx' in str(r))

        r2 = eval(repr(r))
        self.assertTrue(isinstance(r2, r.__class__))
        self.assertTrue(r.cssText == r2.cssText)


if __name__ == '__main__':
    import unittest
    unittest.main()
