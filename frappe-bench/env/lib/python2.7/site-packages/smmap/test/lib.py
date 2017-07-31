"""Provide base classes for the test system"""
from unittest import TestCase
import os
import tempfile

__all__ = ['TestBase', 'FileCreator']


#{ Utilities

class FileCreator(object):

    """A instance which creates a temporary file with a prefix and a given size
    and provides this info to the user.
    Once it gets deleted, it will remove the temporary file as well."""
    __slots__ = ("_size", "_path")

    def __init__(self, size, prefix=''):
        assert size, "Require size to be larger 0"

        self._path = tempfile.mktemp(prefix=prefix)
        self._size = size

        fp = open(self._path, "wb")
        fp.seek(size - 1)
        fp.write(b'1')
        fp.close()

        assert os.path.getsize(self.path) == size

    def __del__(self):
        try:
            os.remove(self.path)
        except OSError:
            pass
        # END exception handling

    @property
    def path(self):
        return self._path

    @property
    def size(self):
        return self._size

#} END utilities


class TestBase(TestCase):

    """Foundation used by all tests"""

    #{ Configuration
    k_window_test_size = 1000 * 1000 * 8 + 5195
    #} END configuration

    #{ Overrides
    @classmethod
    def setUpAll(cls):
        # nothing for now
        pass

    # END overrides

    #{ Interface

    #} END interface
