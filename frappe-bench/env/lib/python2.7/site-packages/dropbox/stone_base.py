"""
Helpers for representing Stone data types in Python.

This module should be dropped into a project that requires the use of Stone. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.
"""

from __future__ import absolute_import, unicode_literals

try:
    from . import stone_validators as bv
except (SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import stone_validators as bv  # type: ignore

_MYPY = False
if _MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression


class Union(object):
    # TODO(kelkabany): Possible optimization is to remove _value if a
    # union is composed of only symbols.
    __slots__ = ['_tag', '_value']
    _tagmap = {}  # type: typing.Dict[typing.Text, bv.Validator]

    def __init__(self, tag, value=None):
        # type: (typing.Text, typing.Optional[typing.Any]) -> None
        assert tag in self._tagmap, 'Invalid tag %r.' % tag
        validator = self._tagmap[tag]
        if isinstance(validator, bv.Void):
            assert value is None, 'Void type union member must have None value.'
        elif isinstance(validator, (bv.Struct, bv.Union)):
            validator.validate_type_only(value)
        else:
            validator.validate(value)
        self._tag = tag
        self._value = value

    def __eq__(self, other):
        # Also need to check if one class is a subclass of another. If one union extends another,
        # the common fields should be able to be compared to each other.
        return (
            isinstance(other, Union) and
            (isinstance(self, other.__class__) or isinstance(other, self.__class__)) and
            self._tag == other._tag and self._value == other._value
        )

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self._tag, self._value))

class Route(object):

    def __init__(self, name, deprecated, arg_type, result_type, error_type, attrs):
        self.name = name
        self.deprecated = deprecated
        self.arg_type = arg_type
        self.result_type = result_type
        self.error_type = error_type
        assert isinstance(attrs, dict), 'Expected dict, got %r' % attrs
        self.attrs = attrs

    def __repr__(self):
        return 'Route({!r}, {!r}, {!r}, {!r}, {!r}, {!r})'.format(
            self.name,
            self.deprecated,
            self.arg_type,
            self.result_type,
            self.error_type,
            self.attrs)
