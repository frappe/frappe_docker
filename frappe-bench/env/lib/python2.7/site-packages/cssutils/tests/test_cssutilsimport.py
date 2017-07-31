"""Testcase for cssutils imports"""

before = len(locals()) # to check is only exp amount is imported
from cssutils import *
after = len(locals()) # to check is only exp amount is imported

import unittest

class CSSutilsImportTestCase(unittest.TestCase):

    def test_import_all(self):
        "from cssutils import *"
        import cssutils

        act = globals()
        exp = {'CSSParser': CSSParser,
               'CSSSerializer': CSSSerializer,
               'css': cssutils.css,
               'stylesheets': cssutils.stylesheets,
        }
        exptotal = before + len(exp) + 1
        # imports before + * + "after"
        self.assertTrue(after == exptotal, 'too many imported')

        found = 0
        for e in exp:
            self.assertTrue(e in act, '%s not found' %e)
            self.assertTrue(act[e] == exp[e], '%s not the same' %e)
            found += 1
        self.assertTrue(found == len(exp))

if __name__ == '__main__':
    import unittest
    unittest.main()
