"""
Defines classes to represent each Stone type in Python. These classes should
be used to validate Python objects and normalize them for a given type.

The data types defined here should not be specific to an RPC or serialization
format.

This module should be dropped into a project that requires the use of Stone. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.
"""

from __future__ import absolute_import, unicode_literals

from abc import ABCMeta, abstractmethod
import datetime
import math
import numbers
import re
import six

_MYPY = False
if _MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression

# See <http://python3porting.com/differences.html#buffer>
if six.PY3:
    _binary_types = (bytes, memoryview)  # noqa: E501,F821 # pylint: disable=undefined-variable,useless-suppression
else:
    _binary_types = (bytes, buffer)  # noqa: E501,F821 # pylint: disable=undefined-variable,useless-suppression


class ValidationError(Exception):
    """Raised when a value doesn't pass validation by its validator."""

    def __init__(self, message, parent=None):
        """
        Args:
            message (str): Error message detailing validation failure.
            parent (str): Adds the parent as the closest reference point for
                the error. Use :meth:`add_parent` to add more.
        """
        super(ValidationError, self).__init__(message)
        self.message = message
        self._parents = []
        if parent:
            self._parents.append(parent)

    def add_parent(self, parent):
        """
        Args:
            parent (str): Adds the parent to the top of the tree of references
                that lead to the validator that failed.
        """
        self._parents.append(parent)

    def __str__(self):
        """
        Returns:
            str: A descriptive message of the validation error that may also
                include the path to the validator that failed.
        """
        if self._parents:
            return '{}: {}'.format('.'.join(self._parents[::-1]), self.message)
        else:
            return self.message

    def __repr__(self):
        # Not a perfect repr, but includes the error location information.
        return 'ValidationError(%r)' % six.text_type(self)


def generic_type_name(v):
    """Return a descriptive type name that isn't Python specific. For example,
    an int value will return 'integer' rather than 'int'."""
    if isinstance(v, numbers.Integral):
        # Must come before real numbers check since integrals are reals too
        return 'integer'
    elif isinstance(v, numbers.Real):
        return 'float'
    elif isinstance(v, (tuple, list)):
        return 'list'
    elif isinstance(v, six.string_types):
        return 'string'
    elif v is None:
        return 'null'
    else:
        return type(v).__name__


class Validator(object):
    """All primitive and composite data types should be a subclass of this."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def validate(self, val):
        """Validates that val is of this data type.

        Returns: A normalized value if validation succeeds.
        Raises: ValidationError
        """
        pass

    def has_default(self):
        return False

    def get_default(self):
        raise AssertionError('No default available.')


class Primitive(Validator):
    """A basic type that is defined by Stone."""
    # pylint: disable=abstract-method
    pass


class Boolean(Primitive):

    def validate(self, val):
        if not isinstance(val, bool):
            raise ValidationError('%r is not a valid boolean' % val)
        return val


class Integer(Primitive):
    """
    Do not use this class directly. Extend it and specify a 'minimum' and
    'maximum' value as class variables for a more restrictive integer range.
    """
    minimum = None  # type: typing.Optional[int]
    maximum = None  # type: typing.Optional[int]

    def __init__(self, min_value=None, max_value=None):
        """
        A more restrictive minimum or maximum value can be specified than the
        range inherent to the defined type.
        """
        if min_value is not None:
            assert isinstance(min_value, numbers.Integral), \
                'min_value must be an integral number'
            assert min_value >= self.minimum, \
                'min_value cannot be less than the minimum value for this ' \
                'type (%d < %d)' % (min_value, self.minimum)
            self.minimum = min_value
        if max_value is not None:
            assert isinstance(max_value, numbers.Integral), \
                'max_value must be an integral number'
            assert max_value <= self.maximum, \
                'max_value cannot be greater than the maximum value for ' \
                'this type (%d < %d)' % (max_value, self.maximum)
            self.maximum = max_value

    def validate(self, val):
        if not isinstance(val, numbers.Integral):
            raise ValidationError('expected integer, got %s'
                                  % generic_type_name(val))
        elif not (self.minimum <= val <= self.maximum):
            raise ValidationError('%d is not within range [%d, %d]'
                                  % (val, self.minimum, self.maximum))
        return val

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Int32(Integer):
    minimum = -2**31
    maximum = 2**31 - 1


class UInt32(Integer):
    minimum = 0
    maximum = 2**32 - 1


class Int64(Integer):
    minimum = -2**63
    maximum = 2**63 - 1


class UInt64(Integer):
    minimum = 0
    maximum = 2**64 - 1


class Real(Primitive):
    """
    Do not use this class directly. Extend it and optionally set a 'minimum'
    and 'maximum' value to enforce a range that's a subset of the Python float
    implementation. Python floats are doubles.
    """
    minimum = None  # type: typing.Optional[float]
    maximum = None  # type: typing.Optional[float]

    def __init__(self, min_value=None, max_value=None):
        """
        A more restrictive minimum or maximum value can be specified than the
        range inherent to the defined type.
        """
        if min_value is not None:
            assert isinstance(min_value, numbers.Real), \
                'min_value must be a real number'
            if not isinstance(min_value, float):
                try:
                    min_value = float(min_value)
                except OverflowError:
                    raise AssertionError('min_value is too small for a float')
            if self.minimum is not None and min_value < self.minimum:
                raise AssertionError('min_value cannot be less than the '
                                     'minimum value for this type (%f < %f)' %
                                     (min_value, self.minimum))
            self.minimum = min_value
        if max_value is not None:
            assert isinstance(max_value, numbers.Real), \
                'max_value must be a real number'
            if not isinstance(max_value, float):
                try:
                    max_value = float(max_value)
                except OverflowError:
                    raise AssertionError('max_value is too large for a float')
            if self.maximum is not None and max_value > self.maximum:
                raise AssertionError('max_value cannot be greater than the '
                                     'maximum value for this type (%f < %f)' %
                                     (max_value, self.maximum))
            self.maximum = max_value

    def validate(self, val):
        if not isinstance(val, numbers.Real):
            raise ValidationError('expected real number, got %s' %
                                  generic_type_name(val))
        if not isinstance(val, float):
            # This checks for the case where a number is passed in with a
            # magnitude larger than supported by float64.
            try:
                val = float(val)
            except OverflowError:
                raise ValidationError('too large for float')
        if math.isnan(val) or math.isinf(val):
            raise ValidationError('%f values are not supported' % val)
        if self.minimum is not None and val < self.minimum:
            raise ValidationError('%f is not greater than %f' %
                                  (val, self.minimum))
        if self.maximum is not None and val > self.maximum:
            raise ValidationError('%f is not less than %f' %
                                  (val, self.maximum))
        return val

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class Float32(Real):
    # Maximum and minimums from the IEEE 754-1985 standard
    minimum = -3.40282 * 10**38
    maximum = 3.40282 * 10**38


class Float64(Real):
    pass


class String(Primitive):
    """Represents a unicode string."""

    def __init__(self, min_length=None, max_length=None, pattern=None):
        if min_length is not None:
            assert isinstance(min_length, numbers.Integral), \
                'min_length must be an integral number'
            assert min_length >= 0, 'min_length must be >= 0'
        if max_length is not None:
            assert isinstance(max_length, numbers.Integral), \
                'max_length must be an integral number'
            assert max_length > 0, 'max_length must be > 0'
        if min_length and max_length:
            assert max_length >= min_length, 'max_length must be >= min_length'
        if pattern is not None:
            assert isinstance(pattern, six.string_types), \
                'pattern must be a string'

        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.pattern_re = None

        if pattern:
            try:
                self.pattern_re = re.compile(r"\A(?:" + pattern + r")\Z")
            except re.error as e:
                raise AssertionError('Regex {!r} failed: {}'.format(
                    pattern, e.args[0]))

    def validate(self, val):
        """
        A unicode string of the correct length and pattern will pass validation.
        In PY2, we enforce that a str type must be valid utf-8, and a unicode
        string will be returned.
        """
        if not isinstance(val, six.string_types):
            raise ValidationError("'%s' expected to be a string, got %s"
                                  % (val, generic_type_name(val)))
        if not six.PY3 and isinstance(val, str):
            try:
                val = val.decode('utf-8')
            except UnicodeDecodeError:
                raise ValidationError("'%s' was not valid utf-8")

        if self.max_length is not None and len(val) > self.max_length:
            raise ValidationError("'%s' must be at most %d characters, got %d"
                                  % (val, self.max_length, len(val)))
        if self.min_length is not None and len(val) < self.min_length:
            raise ValidationError("'%s' must be at least %d characters, got %d"
                                  % (val, self.min_length, len(val)))

        if self.pattern and not self.pattern_re.match(val):
            raise ValidationError("'%s' did not match pattern '%s'"
                                  % (val, self.pattern))
        return val


class Bytes(Primitive):

    def __init__(self, min_length=None, max_length=None):
        if min_length is not None:
            assert isinstance(min_length, numbers.Integral), \
                'min_length must be an integral number'
            assert min_length >= 0, 'min_length must be >= 0'
        if max_length is not None:
            assert isinstance(max_length, numbers.Integral), \
                'max_length must be an integral number'
            assert max_length > 0, 'max_length must be > 0'
        if min_length is not None and max_length is not None:
            assert max_length >= min_length, 'max_length must be >= min_length'

        self.min_length = min_length
        self.max_length = max_length

    def validate(self, val):
        if not isinstance(val, _binary_types):
            raise ValidationError("expected bytes type, got %s"
                                  % generic_type_name(val))
        elif self.max_length is not None and len(val) > self.max_length:
            raise ValidationError("'%s' must have at most %d bytes, got %d"
                                  % (val, self.max_length, len(val)))
        elif self.min_length is not None and len(val) < self.min_length:
            raise ValidationError("'%s' has fewer than %d bytes, got %d"
                                  % (val, self.min_length, len(val)))
        return val


class Timestamp(Primitive):
    """Note that while a format is specified, it isn't used in validation
    since a native Python datetime object is preferred. The format, however,
    can and should be used by serializers."""

    def __init__(self, fmt):
        """fmt must be composed of format codes that the C standard (1989)
        supports, most notably in its strftime() function."""
        assert isinstance(fmt, six.text_type), 'format must be a string'
        self.format = fmt

    def validate(self, val):
        if not isinstance(val, datetime.datetime):
            raise ValidationError('expected timestamp, got %s'
                                  % generic_type_name(val))
        elif val.tzinfo is not None and \
                val.tzinfo.utcoffset(val).total_seconds() != 0:
            raise ValidationError('timestamp should have either a UTC '
                                  'timezone or none set at all')
        return val


class Composite(Validator):
    """Validator for a type that builds on other primitive and composite
    types."""
    # pylint: disable=abstract-method
    pass


class List(Composite):
    """Assumes list contents are homogeneous with respect to types."""

    def __init__(self, item_validator, min_items=None, max_items=None):
        """Every list item will be validated with item_validator."""
        self.item_validator = item_validator
        if min_items is not None:
            assert isinstance(min_items, numbers.Integral), \
                'min_items must be an integral number'
            assert min_items >= 0, 'min_items must be >= 0'
        if max_items is not None:
            assert isinstance(max_items, numbers.Integral), \
                'max_items must be an integral number'
            assert max_items > 0, 'max_items must be > 0'
        if min_items is not None and max_items is not None:
            assert max_items >= min_items, 'max_items must be >= min_items'

        self.min_items = min_items
        self.max_items = max_items

    def validate(self, val):
        if not isinstance(val, (tuple, list)):
            raise ValidationError('%r is not a valid list' % val)
        elif self.max_items is not None and len(val) > self.max_items:
            raise ValidationError('%r has more than %s items'
                                  % (val, self.max_items))
        elif self.min_items is not None and len(val) < self.min_items:
            raise ValidationError('%r has fewer than %s items'
                                  % (val, self.min_items))
        return [self.item_validator.validate(item) for item in val]


class Struct(Composite):

    def __init__(self, definition):
        """
        Args:
            definition (class): A generated class representing a Stone struct
                from a spec. Must have a _fields_ attribute with the following
                structure:

                _fields_ = [(field_name, validator), ...]

                where
                    field_name: Name of the field (str).
                    validator: Validator object.
        """
        super(Struct, self).__init__()
        self.definition = definition

    def validate(self, val):
        """
        For a val to pass validation, val must be of the correct type and have
        all required fields present.
        """
        self.validate_type_only(val)
        self.validate_fields_only(val)
        return val

    def validate_fields_only(self, val):
        """
        To pass field validation, no required field should be missing.

        This method assumes that the contents of each field have already been
        validated on assignment, so it's merely a presence check.

        FIXME(kelkabany): Since the definition object does not maintain a list
        of which fields are required, all fields are scanned.
        """
        for field_name, _ in self.definition._all_fields_:
            if not hasattr(val, field_name):
                raise ValidationError("missing required field '%s'" %
                                      field_name)

    def validate_type_only(self, val):
        """
        Use this when you only want to validate that the type of an object
        is correct, but not yet validate each field.
        """
        # Since the definition maintains the list of fields for serialization,
        # we're okay with a subclass that might have extra information. This
        # makes it easier to return one subclass for two routes, one of which
        # relies on the parent class.
        if not isinstance(val, self.definition):
            raise ValidationError('expected type %s, got %s' %
                (self.definition.__name__, generic_type_name(val)))

    def has_default(self):
        return not self.definition._has_required_fields

    def get_default(self):
        assert not self.definition._has_required_fields, 'No default available.'
        return self.definition()


class StructTree(Struct):
    """Validator for structs with enumerated subtypes.

    NOTE: validate_fields_only() validates the fields known to this base
    struct, but does not do any validation specific to the subtype.
    """

    # See PyCQA/pylint#1043 for why this is disabled; this should show up
    # as a usless-suppression (and can be removed) once a fix is released
    def __init__(self, definition):  # pylint: disable=useless-super-delegation
        super(StructTree, self).__init__(definition)


class Union(Composite):

    def __init__(self, definition):
        """
        Args:
            definition (class): A generated class representing a Stone union
                from a spec. Must have a _tagmap attribute with the following
                structure:

                _tagmap = {field_name: validator, ...}

                where
                    field_name (str): Tag name.
                    validator (Validator): Tag value validator.
        """
        self.definition = definition

    def validate(self, val):
        """
        For a val to pass validation, it must have a _tag set. This assumes
        that the object validated that _tag is a valid tag, and that any
        associated value has also been validated.
        """
        self.validate_type_only(val)
        if not hasattr(val, '_tag') or val._tag is None:
            raise ValidationError('no tag set')
        return val

    def validate_type_only(self, val):
        """
        Use this when you only want to validate that the type of an object
        is correct, but not yet validate each field.

        We check whether val is a Python parent class of the definition. This
        is because Union subtyping works in the opposite direction of Python
        inheritance. For example, if a union U2 extends U1 in Python, this
        validator will accept U1 in places where U2 is expected.
        """
        if not issubclass(self.definition, type(val)):
            raise ValidationError('expected type %s or subtype, got %s' %
                (self.definition.__name__, generic_type_name(val)))


class Void(Primitive):

    def validate(self, val):
        if val is not None:
            raise ValidationError('expected NoneType, got %s' %
                                  generic_type_name(val))

    def has_default(self):
        return True

    def get_default(self):
        return None


class Nullable(Validator):

    def __init__(self, validator):
        assert isinstance(validator, (Primitive, Composite)), \
            'validator must be for a primitive or composite type'
        assert not isinstance(validator, Nullable), \
            'nullables cannot be stacked'
        assert not isinstance(validator, Void), \
            'void cannot be made nullable'
        self.validator = validator

    def validate(self, val):
        if val is None:
            return
        else:
            return self.validator.validate(val)

    def validate_type_only(self, val):
        """Use this only if Nullable is wrapping a Composite."""
        if val is None:
            return
        else:
            return self.validator.validate_type_only(val)

    def has_default(self):
        return True

    def get_default(self):
        return None
