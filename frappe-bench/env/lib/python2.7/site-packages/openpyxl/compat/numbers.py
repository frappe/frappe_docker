from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

try:
    # Python 2
    long = long
except NameError:
    # Python 3
    long = int

from decimal import Decimal

NUMERIC_TYPES = (int, float, long, Decimal)


try:
    import numpy
    NUMPY = True
except ImportError:
    NUMPY = False


if NUMPY:
    NUMERIC_TYPES = NUMERIC_TYPES + (numpy.bool_, numpy.floating, numpy.integer)


try:
    import pandas
    PANDAS = True
except ImportError:
    PANDAS = False
