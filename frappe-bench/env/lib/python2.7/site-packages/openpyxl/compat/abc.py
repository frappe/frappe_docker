from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl


try:
    from abc import ABC
except ImportError:
    from abc import ABCMeta
    ABC = ABCMeta('ABC', (object, ), {})
