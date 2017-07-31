from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl


from .strings import (
    basestring,
    unicode,
    bytes,
    file,
    tempfile,
    safe_string,
    safe_repr,
    )
from .numbers import long, NUMERIC_TYPES

# Python 2.6
try:
    from collections import OrderedDict
except ImportError:
    from .odict import OrderedDict

try:
    range = xrange
except NameError:
    range = range

import warnings
from functools import wraps
import inspect


class DummyCode:

    pass


class deprecated(object):

    def __init__(self, reason):
        if inspect.isclass(reason) or inspect.isfunction(reason):
            raise TypeError("Reason for deprecation must be supplied")
        self.reason = reason

    def __call__(self, obj, *args, **kwargs):
        @wraps(obj)
        def new_func(*args, **kwargs):
            msg = "Call to deprecated function or class {0} ({1})".format(obj.__name__,
                                                               self.reason)
            if inspect.isfunction(obj):
                _code = self._wrap_function(obj)
            elif inspect.isclass(obj):
                _code = self._wrap_class(obj)

            warnings.warn_explicit(
                '{0}.'.format(msg),
                category=DeprecationWarning,
                filename=_code.co_filename,
                lineno=_code.co_firstlineno + 1
            )
            return obj(*args, **kwargs)
        return new_func

    def _wrap_function(self, obj):
        if hasattr(obj, 'func_code'):
            _code = obj.func_code
        else:
            _code = obj.__code__
        return _code

    def _wrap_class(self, obj):
        _code = DummyCode()
        _code.co_filename = obj.__module__
        _code.co_firstlineno = 0
        return _code
