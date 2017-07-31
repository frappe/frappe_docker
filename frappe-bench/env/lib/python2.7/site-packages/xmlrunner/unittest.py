
from __future__ import absolute_import

import sys
# pylint: disable-msg=W0611
import unittest
from unittest import TextTestRunner
from unittest import TestResult, _TextTestResult
from unittest.result import failfast
from unittest.main import TestProgram
try:
    from unittest.main import USAGE_AS_MAIN
    TestProgram.USAGE = USAGE_AS_MAIN
except ImportError:
    pass

__all__ = (
    'unittest', 'TextTestRunner', 'TestResult', '_TextTestResult',
    'TestProgram', 'failfast')
