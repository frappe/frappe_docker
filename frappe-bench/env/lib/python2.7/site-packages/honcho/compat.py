"""
Compatibility layer and utilities, mostly for proper Windows and Python 3
support.
"""
import sys

# This works for both 32 and 64 bit Windows
ON_WINDOWS = 'win32' in str(sys.platform).lower()

# Python 3 hasn't iteritems, we should use items instead
try:
    {}.iteritems
except AttributeError:
    def iteritems(data):
        return data.items()
else:
    def iteritems(data):
        return data.iteritems()

# Python 3 hasn't xrange, we should use range instead
try:
    xrange = xrange
except NameError:
    xrange = range

# Python 3 does not have StringIO, we should use the io module instead
try:
    from StringIO import StringIO  # noqa
except ImportError:
    from io import StringIO  # noqa

# Python 3 renamed ConfigParser to configparser
try:
    from ConfigParser import ConfigParser  # noqa
except ImportError:
    from configparser import ConfigParser  # noqa

# Python 3 exposed quote as public API in the shlex module
try:
    from pipes import quote as shellquote  # noqa
except ImportError:
    from shlex import quote as shellquote  # noqa

# Python 3 renamed Queue to queue
try:
    from Queue import Queue, Empty  # noqa
except ImportError:
    from queue import Queue, Empty  # noqa

# Python <2.7 doesn't have OrderedDict in the collections module
try:
    from collections import OrderedDict  # noqa
except ImportError:
    from ordereddict import OrderedDict  # noqa
