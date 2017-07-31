"""
Serializers for Stone data types.

Currently, only JSON is officially supported, but there's an experimental
msgpack integration. If possible, serializers should be kept separate from the
RPC format.

This module should be dropped into a project that requires the use of Stone. In
the future, this could be imported from a pre-installed Python package, rather
than being added to a project.
"""

from __future__ import absolute_import, unicode_literals

import base64
import collections
import datetime
import functools
import json
import re
import six
import time

try:
    from . import stone_base as bb  # noqa: F401 # pylint: disable=unused-import
    from . import stone_validators as bv
except (SystemError, ValueError):
    # Catch errors raised when importing a relative module when not in a package.
    # This makes testing this file directly (outside of a package) easier.
    import stone_validators as bb  # type: ignore # noqa: F401 # pylint: disable=unused-import
    import stone_validators as bv  # type: ignore

_MYPY = False
if _MYPY:
    import typing  # noqa: F401 # pylint: disable=import-error,unused-import,useless-suppression


# ------------------------------------------------------------------------
class StoneEncoderInterface(object):
    """
    Interface defining a stone object encoder.
    """

    def encode(self, validator, value):
        # type: (bv.Validator, typing.Any) -> typing.Any
        """
        Validate ``value`` using ``validator`` and return the encoding.

        Args:
            validator: the ``stone_validators.Validator`` used to validate
                ``value``
            value: the object to encode

        Returns:
            The encoded object. This is implementation-defined.

        Raises:
            stone_validators.ValidationError: Raised if ``value`` (or one
                of its sub-values).
        """
        raise NotImplementedError

# ------------------------------------------------------------------------
class StoneSerializerBase(StoneEncoderInterface):

    def __init__(self, alias_validators=None):
        # type: (typing.Mapping[bv.Validator, typing.Callable[[typing.Any], None]]) -> None
        """
        Constructor, `obviously
        <http://www.geekalerts.com/ew-hand-sanitizer/>`.

        Args:
            alias_validators (``typing.Mapping``, optional): A mapping of
                custom validation callables in the format
                ``{stone_validators.Validator:
                typing.Callable[[typing.Any], None], ...}``. These callables must
                raise a ``stone_validators.ValidationError`` on failure.
                Defaults to ``None``.
        """
        self._alias_validators = {}  # type: typing.Dict[bv.Validator, typing.Callable[[typing.Any], None]] # noqa: E501

        if alias_validators is not None:
            self._alias_validators.update(alias_validators)

    @property
    def alias_validators(self):
        """
        A ``typing.Mapping`` of custom validation callables in the format
        ``{stone_validators.Validator: typing.Callable[typing.Any],
        ...}``.
        """
        return self._alias_validators

    def encode(self, validator, value):
        return self.encode_sub(validator, value)

    def encode_sub(self, validator, value):
        # type: (bv.Validator, typing.Any) -> typing.Any
        """
        Callback intended to be called by other ``encode`` methods to
        delegate encoding of sub-values. Arguments have the same semantics
        as with the ``encode`` method.
        """
        if isinstance(validator, bv.List):
            # Because Lists are mutable, we always validate them during
            # serialization
            validate_f = validator.validate
            encode_f = self.encode_list
        elif isinstance(validator, bv.Nullable):
            validate_f = validator.validate
            encode_f = self.encode_nullable
        elif isinstance(validator, bv.Primitive):
            validate_f = validator.validate
            encode_f = self.encode_primitive
        elif isinstance(validator, bv.Struct):
            if isinstance(validator, bv.StructTree):
                validate_f = validator.validate
                encode_f = self.encode_struct_tree
            else:
                # Fields are already validated on assignment
                validate_f = validator.validate_type_only
                encode_f = self.encode_struct
        elif isinstance(validator, bv.Union):
            # Fields are already validated on assignment
            validate_f = validator.validate_type_only
            encode_f = self.encode_union
        else:
            raise bv.ValidationError('Unsupported data type {}'.format(type(validator).__name__))

        validate_f(value)

        return encode_f(validator, value)

    def encode_list(self, validator, value):
        # type: (bv.List, typing.Any) -> typing.Any
        """
        Callback for serializing a ``stone_validators.List``. Arguments
        have the same semantics as with the ``encode`` method.
        """
        raise NotImplementedError

    def encode_nullable(self, validator, value):
        # type: (bv.Nullable, typing.Any) -> typing.Any
        """
        Callback for serializing a ``stone_validators.Nullable``.
        Arguments have the same semantics as with the ``encode`` method.
        """
        raise NotImplementedError

    def encode_primitive(self, validator, value):
        # type: (bv.Primitive, typing.Any) -> typing.Any
        """
        Callback for serializing a ``stone_validators.Primitive``.
        Arguments have the same semantics as with the ``encode`` method.
        """
        raise NotImplementedError

    def encode_struct(self, validator, value):
        # type: (bv.Struct, typing.Any) -> typing.Any
        """
        Callback for serializing a ``stone_validators.Struct``. Arguments
        have the same semantics as with the ``encode`` method.
        """
        raise NotImplementedError

    def encode_struct_tree(self, validator, value):
        # type: (bv.StructTree, typing.Any) -> typing.Any
        """
        Callback for serializing a ``stone_validators.StructTree``.
        Arguments have the same semantics as with the ``encode`` method.
        """
        raise NotImplementedError

    def encode_union(self, validator, value):
        # type: (bv.Union, bb.Union) -> typing.Any
        """
        Callback for serializing a ``stone_validators.Union``. Arguments
        have the same semantics as with the ``encode`` method.
        """
        raise NotImplementedError

# ------------------------------------------------------------------------
class StoneToPythonPrimitiveSerializer(StoneSerializerBase):

    def __init__(self, alias_validators=None, for_msgpack=False, old_style=False):
        # type: (typing.Mapping[bv.Validator, typing.Callable[[typing.Any], None]], bool, bool) -> None # noqa: E501
        """
        Args:
            alias_validators (``typing.Mapping``, optional): Passed
                to ``StoneSerializer.__init__``. Defaults to ``None``.
            for_msgpack (bool, optional): See the like-named property.
                Defaults to ``False``.
            old_style (bool, optional): See the like-named property.
                Defaults to ``False``.
        """
        super(StoneToPythonPrimitiveSerializer, self).__init__(alias_validators=alias_validators)
        self._for_msgpack = for_msgpack
        self._old_style = old_style

    @property
    def for_msgpack(self):
        """
        EXPERIMENTAL: A flag associated with the serializer indicating
        whether objects produced by the ``encode`` method should be
        encoded for msgpack.

        """
        return self._for_msgpack

    @property
    def old_style(self):
        """
        A flag associated with the serializer indicating whether objects
        produced by the ``encode`` method should be encoded according to
        Dropbox's old or new API styles.
        """
        return self._old_style

    def encode_list(self, validator, value):
        validated_value = validator.validate(value)

        return [self.encode_sub(validator.item_validator, value_item) for value_item in
                validated_value]

    def encode_nullable(self, validator, value):
        if value is None:
            return None

        return self.encode_sub(validator.validator, value)

    def encode_primitive(self, validator, value):
        if validator in self.alias_validators:
            self.alias_validators[validator](value)

        if isinstance(validator, bv.Void):
            return None
        elif isinstance(validator, bv.Timestamp):
            return _strftime(value, validator.format)
        elif isinstance(validator, bv.Bytes):
            if self.for_msgpack:
                return value
            else:
                return base64.b64encode(value).decode('ascii')
        elif isinstance(validator, bv.Integer) \
                and isinstance(value, bool):
            # bool is sub-class of int so it passes Integer validation,
            # but we want the bool to be encoded as ``0`` or ``1``, rather
            # than ``False`` or ``True``, respectively
            return int(value)
        else:
            return value

    def encode_struct(self, validator, value):
        # Skip validation of fields with primitive data types because
        # they've already been validated on assignment
        d = collections.OrderedDict()  # type: typing.Dict[str, typing.Any]

        for field_name, field_validator in validator.definition._all_fields_:
            try:
                field_value = getattr(value, field_name)
            except AttributeError as exc:
                raise bv.ValidationError(exc.args[0])

            presence_key = '_%s_present' % field_name

            if field_value is not None \
                    and getattr(value, presence_key):
                # Only serialize struct fields that have been explicitly
                # set, even if there is a default
                try:
                    d[field_name] = self.encode_sub(field_validator, field_value)
                except bv.ValidationError as exc:
                    exc.add_parent(field_name)

                    raise
        return d

    def encode_struct_tree(self, validator, value):
        assert type(value) in validator.definition._pytype_to_tag_and_subtype_, \
            '%r is not a serializable subtype of %r.' % (type(value), validator.definition)

        tags, subtype = validator.definition._pytype_to_tag_and_subtype_[type(value)]

        assert len(tags) == 1, tags
        assert not isinstance(subtype, bv.StructTree), \
            'Cannot serialize type %r because it enumerates subtypes.' % subtype.definition

        if self.old_style:
            d = {
                tags[0]: self.encode_struct(subtype, value),
            }
        else:
            d = collections.OrderedDict()
            d['.tag'] = tags[0]
            d.update(self.encode_struct(subtype, value))

        return d

    def encode_union(self, validator, value):
        if value._tag is None:
            raise bv.ValidationError('no tag set')

        field_validator = validator.definition._tagmap[value._tag]
        is_none = isinstance(field_validator, bv.Void) \
            or (isinstance(field_validator, bv.Nullable)
                and value._value is None)

        def encode_sub(sub_validator, sub_value, parent_tag):
            try:
                encoded_val = self.encode_sub(sub_validator, sub_value)
            except bv.ValidationError as exc:
                exc.add_parent(parent_tag)

                raise
            else:
                return encoded_val

        if self.old_style:
            if field_validator is None:
                return value._tag
            elif is_none:
                return value._tag
            else:
                encoded_val = encode_sub(field_validator, value._value, value._tag)

                return {value._tag: encoded_val}
        elif is_none:
            return {'.tag': value._tag}
        else:
            encoded_val = encode_sub(field_validator, value._value, value._tag)

            if isinstance(field_validator, bv.Nullable):
                # We've already checked for the null case above,
                # so now we're only interested in what the
                # wrapped validator is
                field_validator = field_validator.validator

            if isinstance(field_validator, bv.Struct) \
                    and not isinstance(field_validator, bv.StructTree):
                d = collections.OrderedDict()  # type: typing.Dict[str, typing.Any]
                d['.tag'] = value._tag
                d.update(encoded_val)

                return d
            else:
                return collections.OrderedDict((
                    ('.tag', value._tag),
                    (value._tag, encoded_val),
                ))

# ------------------------------------------------------------------------
class StoneToJsonSerializer(StoneToPythonPrimitiveSerializer):

    def encode(self, validator, value):
        return json.dumps(super(StoneToJsonSerializer, self).encode(validator, value))

# --------------------------------------------------------------
# JSON Encoder
#
# These interfaces are preserved for backward compatibility and symmetry with deserialization
# functions.

def json_encode(data_type, obj, alias_validators=None, old_style=False):
    """Encodes an object into JSON based on its type.

    Args:
        data_type (Validator): Validator for obj.
        obj (object): Object to be serialized.
        alias_validators (Optional[Mapping[bv.Validator, Callable[[], None]]]):
            Custom validation functions. These must raise bv.ValidationError on
            failure.

    Returns:
        str: JSON-encoded object.

    This function will also do additional validation that wasn't done by the
    objects themselves:

    1. The passed in obj may not have been validated with data_type yet.
    2. If an object that should be a Struct was assigned to a field, its
       type has been validated, but the presence of all required fields
       hasn't been.
    3. If an object that should be a Union was assigned to a field, whether
       or not a tag has been set has not been validated.
    4. A list may have passed validation initially, but been mutated since.

    Example of serializing a struct to JSON:

    struct FileRef
       path String
       rev String

    > fr = FileRef()
    > fr.path = 'a/b/c'
    > fr.rev = '1234'
    > JsonEncoder.encode(fr)
    "{'path': 'a/b/c', 'rev': '1234'}"

    Example of serializing a union to JSON:

    union UploadMode
        add
        overwrite
        update FileRef

    > um = UploadMode()
    > um.set_add()
    > JsonEncoder.encode(um)
    '"add"'
    > um.update = fr
    > JsonEncoder.encode(um)
    "{'update': {'path': 'a/b/c', 'rev': '1234'}}"
    """
    for_msgpack = False
    serializer = StoneToJsonSerializer(alias_validators, for_msgpack, old_style)
    return serializer.encode(data_type, obj)

def json_compat_obj_encode(
        data_type, obj, alias_validators=None, old_style=False,
        for_msgpack=False):
    """Encodes an object into a JSON-compatible dict based on its type.

    Args:
        data_type (Validator): Validator for obj.
        obj (object): Object to be serialized.

    Returns:
        An object that when passed to json.dumps() will produce a string
        giving the JSON-encoded object.

    See json_encode() for additional information about validation.
    """
    serializer = StoneToPythonPrimitiveSerializer(alias_validators, for_msgpack, old_style)
    return serializer.encode(data_type, obj)

# --------------------------------------------------------------
# JSON Decoder

def json_decode(
        data_type, serialized_obj, alias_validators=None, strict=True,
        old_style=False):
    """Performs the reverse operation of json_encode.

    Args:
        data_type (Validator): Validator for serialized_obj.
        serialized_obj (str): The JSON string to deserialize.
        alias_validators (Optional[Mapping[bv.Validator, Callable[[], None]]]):
            Custom validation functions. These must raise bv.ValidationError on
            failure.
        strict (bool): If strict, then unknown struct fields will raise an
            error, and unknown union variants will raise an error even if a
            catch all field is specified. strict should only be used by a
            recipient of serialized JSON if it's guaranteed that its Stone
            specs are at least as recent as the senders it receives messages
            from.

    Returns:
        The returned object depends on the input data_type.
            - Boolean -> bool
            - Bytes -> bytes
            - Float -> float
            - Integer -> long
            - List -> list
            - Nullable -> None or its wrapped type.
            - String -> unicode (PY2) or str (PY3)
            - Struct -> An instance of its definition attribute.
            - Timestamp -> datetime.datetime
            - Union -> An instance of its definition attribute.
    """
    try:
        deserialized_obj = json.loads(serialized_obj)
    except ValueError:
        raise bv.ValidationError('could not decode input as JSON')
    else:
        return json_compat_obj_decode(
            data_type, deserialized_obj, alias_validators, strict, old_style)


def json_compat_obj_decode(
        data_type, obj, alias_validators=None, strict=True, old_style=False,
        for_msgpack=False):
    """
    Decodes a JSON-compatible object based on its data type into a
    representative Python object.

    Args:
        data_type (Validator): Validator for serialized_obj.
        obj: The JSON-compatible object to decode based on data_type.
        strict (bool): If strict, then unknown struct fields will raise an
            error, and unknown union variants will raise an error even if a
            catch all field is specified. See json_decode() for more.

    Returns:
        See json_decode().
    """
    if isinstance(data_type, bv.Primitive):
        return _make_stone_friendly(
            data_type, obj, alias_validators, strict, True, for_msgpack)
    else:
        return _json_compat_obj_decode_helper(
            data_type, obj, alias_validators, strict, old_style, for_msgpack)


def _json_compat_obj_decode_helper(
        data_type, obj, alias_validators, strict, old_style, for_msgpack):
    """
    See json_compat_obj_decode() for argument descriptions.
    """
    if isinstance(data_type, bv.StructTree):
        return _decode_struct_tree(
            data_type, obj, alias_validators, strict, for_msgpack)
    elif isinstance(data_type, bv.Struct):
        return _decode_struct(
            data_type, obj, alias_validators, strict, old_style, for_msgpack)
    elif isinstance(data_type, bv.Union):
        if old_style:
            return _decode_union_old(
                data_type, obj, alias_validators, strict, for_msgpack)
        else:
            return _decode_union(
                data_type, obj, alias_validators, strict, for_msgpack)
    elif isinstance(data_type, bv.List):
        return _decode_list(
            data_type, obj, alias_validators, strict, old_style, for_msgpack)
    elif isinstance(data_type, bv.Nullable):
        return _decode_nullable(
            data_type, obj, alias_validators, strict, old_style, for_msgpack)
    elif isinstance(data_type, bv.Primitive):
        # Set validate to false because validation will be done by the
        # containing struct or union when the field is assigned.
        return _make_stone_friendly(
            data_type, obj, alias_validators, strict, False, for_msgpack)
    else:
        raise AssertionError('Cannot handle type %r.' % data_type)


def _decode_struct(
        data_type, obj, alias_validators, strict, old_style, for_msgpack):
    """
    The data_type argument must be a Struct.
    See json_compat_obj_decode() for argument descriptions.
    """
    if obj is None and data_type.has_default():
        return data_type.get_default()
    elif not isinstance(obj, dict):
        raise bv.ValidationError('expected object, got %s' %
                                 bv.generic_type_name(obj))
    if strict:
        for key in obj:
            if (key not in data_type.definition._all_field_names_ and
                    not key.startswith('.tag')):
                raise bv.ValidationError("unknown field '%s'" % key)
    ins = data_type.definition()
    _decode_struct_fields(
        ins, data_type.definition._all_fields_, obj, alias_validators, strict,
        old_style, for_msgpack)
    # Check that all required fields have been set.
    data_type.validate_fields_only(ins)
    return ins


def _decode_struct_fields(
        ins, fields, obj, alias_validators, strict, old_style, for_msgpack):
    """
    Args:
        ins: An instance of the class representing the data type being decoded.
            The object will have its fields set.
        fields: A tuple of (field_name: str, field_validator: Validator)
        obj (dict): JSON-compatible dict that is being decoded.
        strict (bool): See :func:`json_compat_obj_decode`.

    Returns:
        None: `ins` has its fields set based on the contents of `obj`.
    """
    for name, field_data_type in fields:
        if name in obj:
            try:
                v = _json_compat_obj_decode_helper(
                    field_data_type, obj[name], alias_validators, strict,
                    old_style, for_msgpack)
                setattr(ins, name, v)
            except bv.ValidationError as e:
                e.add_parent(name)
                raise
        elif field_data_type.has_default():
            setattr(ins, name, field_data_type.get_default())


def _decode_union(data_type, obj, alias_validators, strict, for_msgpack):
    """
    The data_type argument must be a Union.
    See json_compat_obj_decode() for argument descriptions.
    """
    val = None
    if isinstance(obj, six.string_types):
        # Handles the shorthand format where the union is serialized as only
        # the string of the tag.
        tag = obj
        if tag in data_type.definition._tagmap:
            val_data_type = data_type.definition._tagmap[tag]
            if not isinstance(val_data_type, (bv.Void, bv.Nullable)):
                raise bv.ValidationError(
                    "expected object for '%s', got symbol" % tag)
            if tag == data_type.definition._catch_all:
                raise bv.ValidationError(
                    "unexpected use of the catch-all tag '%s'" % tag)
        else:
            if not strict and data_type.definition._catch_all:
                tag = data_type.definition._catch_all
            else:
                raise bv.ValidationError("unknown tag '%s'" % tag)
    elif isinstance(obj, dict):
        tag, val = _decode_union_dict(
            data_type, obj, alias_validators, strict, for_msgpack)
    else:
        raise bv.ValidationError("expected string or object, got %s" %
                                 bv.generic_type_name(obj))
    return data_type.definition(tag, val)


def _decode_union_dict(data_type, obj, alias_validators, strict, for_msgpack):
    if '.tag' not in obj:
        raise bv.ValidationError("missing '.tag' key")
    tag = obj['.tag']
    if not isinstance(tag, six.string_types):
        raise bv.ValidationError(
            'tag must be string, got %s' % bv.generic_type_name(tag))

    if tag not in data_type.definition._tagmap:
        if not strict and data_type.definition._catch_all:
            return data_type.definition._catch_all, None
        else:
            raise bv.ValidationError("unknown tag '%s'" % tag)
    if tag == data_type.definition._catch_all:
        raise bv.ValidationError(
            "unexpected use of the catch-all tag '%s'" % tag)

    val_data_type = data_type.definition._tagmap[tag]
    if isinstance(val_data_type, bv.Nullable):
        val_data_type = val_data_type.validator
        nullable = True
    else:
        nullable = False

    if isinstance(val_data_type, bv.Void):
        if strict:
            # In strict mode, ensure there are no extraneous keys set. In
            # non-strict mode, we accept that other keys may be set due to a
            # change of the void type to another.
            if tag in obj:
                if obj[tag] is not None:
                    raise bv.ValidationError('expected null, got %s' %
                                             bv.generic_type_name(obj[tag]))
            for key in obj:
                if key != tag and key != '.tag':
                    raise bv.ValidationError("unexpected key '%s'" % key)
        val = None
    elif isinstance(val_data_type,
                    (bv.Primitive, bv.List, bv.StructTree, bv.Union)):
        if tag in obj:
            raw_val = obj[tag]
            try:
                val = _json_compat_obj_decode_helper(
                    val_data_type, raw_val, alias_validators, strict, False, for_msgpack)
            except bv.ValidationError as e:
                e.add_parent(tag)
                raise
        else:
            # Check no other keys
            if nullable:
                val = None
            else:
                raise bv.ValidationError("missing '%s' key" % tag)
        for key in obj:
            if key != tag and key != '.tag':
                raise bv.ValidationError("unexpected key '%s'" % key)
    elif isinstance(val_data_type, bv.Struct):
        if nullable and len(obj) == 1:  # only has a .tag key
            val = None
        else:
            # assume it's not null
            raw_val = obj
            try:
                val = _json_compat_obj_decode_helper(
                    val_data_type, raw_val, alias_validators, strict, False,
                    for_msgpack)
            except bv.ValidationError as e:
                e.add_parent(tag)
                raise
    else:
        assert False, type(val_data_type)
    return tag, val


def _decode_union_old(data_type, obj, alias_validators, strict, for_msgpack):
    """
    The data_type argument must be a Union.
    See json_compat_obj_decode() for argument descriptions.
    """
    val = None
    if isinstance(obj, six.string_types):
        # Union member has no associated value
        tag = obj
        if tag in data_type.definition._tagmap:
            val_data_type = data_type.definition._tagmap[tag]
            if not isinstance(val_data_type, (bv.Void, bv.Nullable)):
                raise bv.ValidationError(
                    "expected object for '%s', got symbol" % tag)
        else:
            if not strict and data_type.definition._catch_all:
                tag = data_type.definition._catch_all
            else:
                raise bv.ValidationError("unknown tag '%s'" % tag)
    elif isinstance(obj, dict):
        # Union member has value
        if len(obj) != 1:
            raise bv.ValidationError('expected 1 key, got %s' % len(obj))
        tag = list(obj)[0]
        raw_val = obj[tag]
        if tag in data_type.definition._tagmap:
            val_data_type = data_type.definition._tagmap[tag]
            if isinstance(val_data_type, bv.Nullable) and raw_val is None:
                val = None
            elif isinstance(val_data_type, bv.Void):
                if raw_val is None or not strict:
                    # If raw_val is None, then this is the more verbose
                    # representation of a void union member. If raw_val isn't
                    # None, then maybe the spec has changed, so check if we're
                    # in strict mode.
                    val = None
                else:
                    raise bv.ValidationError('expected null, got %s' %
                                             bv.generic_type_name(raw_val))
            else:
                try:
                    val = _json_compat_obj_decode_helper(
                        val_data_type, raw_val, alias_validators, strict, True,
                        for_msgpack)
                except bv.ValidationError as e:
                    e.add_parent(tag)
                    raise
        else:
            if not strict and data_type.definition._catch_all:
                tag = data_type.definition._catch_all
            else:
                raise bv.ValidationError("unknown tag '%s'" % tag)
    else:
        raise bv.ValidationError("expected string or object, got %s" %
                                 bv.generic_type_name(obj))
    return data_type.definition(tag, val)


def _decode_struct_tree(data_type, obj, alias_validators, strict, for_msgpack):
    """
    The data_type argument must be a StructTree.
    See json_compat_obj_decode() for argument descriptions.
    """
    subtype = _determine_struct_tree_subtype(data_type, obj, strict)
    return _decode_struct(
        subtype, obj, alias_validators, strict, False, for_msgpack)


def _determine_struct_tree_subtype(data_type, obj, strict):
    """
    Searches through the JSON-object-compatible dict using the data type
    definition to determine which of the enumerated subtypes `obj` is.
    """
    if '.tag' not in obj:
        raise bv.ValidationError("missing '.tag' key")
    if not isinstance(obj['.tag'], six.string_types):
        raise bv.ValidationError('expected string, got %s' %
                                 bv.generic_type_name(obj['.tag']),
                                 parent='.tag')

    # Find the subtype the tags refer to
    full_tags_tuple = (obj['.tag'],)
    if full_tags_tuple in data_type.definition._tag_to_subtype_:
        subtype = data_type.definition._tag_to_subtype_[full_tags_tuple]
        if isinstance(subtype, bv.StructTree):
            raise bv.ValidationError("tag '%s' refers to non-leaf subtype" %
                                     ('.'.join(full_tags_tuple)))
        return subtype
    else:
        if strict:
            # In strict mode, the entirety of the tag hierarchy should
            # point to a known subtype.
            raise bv.ValidationError("unknown subtype '%s'" %
                                     '.'.join(full_tags_tuple))
        else:
            # If subtype was not found, use the base.
            if data_type.definition._is_catch_all_:
                return data_type
            else:
                raise bv.ValidationError(
                    "unknown subtype '%s' and '%s' is not a catch-all" %
                    ('.'.join(full_tags_tuple), data_type.definition.__name__))


def _decode_list(
        data_type, obj, alias_validators, strict, old_style, for_msgpack):
    """
    The data_type argument must be a List.
    See json_compat_obj_decode() for argument descriptions.
    """
    if not isinstance(obj, list):
        raise bv.ValidationError(
            'expected list, got %s' % bv.generic_type_name(obj))
    return [
        _json_compat_obj_decode_helper(
            data_type.item_validator, item, alias_validators, strict,
            old_style, for_msgpack)
        for item in obj]


def _decode_nullable(
        data_type, obj, alias_validators, strict, old_style, for_msgpack):
    """
    The data_type argument must be a Nullable.
    See json_compat_obj_decode() for argument descriptions.
    """
    if obj is not None:
        return _json_compat_obj_decode_helper(
            data_type.validator, obj, alias_validators, strict, old_style,
            for_msgpack)
    else:
        return None


def _make_stone_friendly(
        data_type, val, alias_validators, strict, validate, for_msgpack):
    """
    Convert a Python object to a type that will pass validation by its
    validator.

    Validation by ``alias_validators`` is performed even if ``validate`` is
    false.
    """
    if isinstance(data_type, bv.Timestamp):
        try:
            ret = datetime.datetime.strptime(val, data_type.format)
        except (TypeError, ValueError) as e:
            raise bv.ValidationError(e.args[0])
    elif isinstance(data_type, bv.Bytes):
        if for_msgpack:
            if isinstance(val, six.text_type):
                ret = val.encode('utf-8')
            else:
                ret = val
        else:
            try:
                ret = base64.b64decode(val)
            except TypeError:
                raise bv.ValidationError('invalid base64-encoded bytes')
    elif isinstance(data_type, bv.Void):
        if strict and val is not None:
            raise bv.ValidationError("expected null, got value")
        return None
    else:
        if validate:
            data_type.validate(val)
        ret = val
    if alias_validators is not None and data_type in alias_validators:
        alias_validators[data_type](ret)
    return ret

# Adapted from:
# http://code.activestate.com/recipes/306860-proleptic-gregorian-dates-and-strftime-before-1900/
# Remove the unsupposed "%s" command. But don't do it if there's an odd
# number of %s before the s because those are all escaped. Can't simply
# remove the s because the result of %sY should be %Y if %s isn't
# supported, not the 4 digit year.
_ILLEGAL_S = re.compile(r'((^|[^%])(%%)*%s)')

def _findall(text, substr):
    # Also finds overlaps
    sites = []
    i = 0

    while 1:
        j = text.find(substr, i)

        if j == -1:
            break

        sites.append(j)
        i = j + 1

    return sites

# Every 28 years the calendar repeats, except through century leap years
# where it's 6 years. But only if you're using the Gregorian calendar. ;)
def _strftime(dt, fmt):
    try:
        return dt.strftime(fmt)
    except ValueError:
        if not six.PY2 or dt.year > 1900:
            raise

    if _ILLEGAL_S.search(fmt):
        raise TypeError("This strftime implementation does not handle %s")

    year = dt.year

    # For every non-leap year century, advance by 6 years to get into the
    # 28-year repeat cycle
    delta = 2000 - year
    off = 6 * (delta // 100 + delta // 400)
    year = year + off

    # Move to around the year 2000
    year = year + ((2000 - year) // 28) * 28
    timetuple = dt.timetuple()
    s1 = time.strftime(fmt, (year,) + timetuple[1:])
    sites1 = _findall(s1, str(year))

    s2 = time.strftime(fmt, (year + 28,) + timetuple[1:])
    sites2 = _findall(s2, str(year + 28))

    sites = []

    for site in sites1:
        if site in sites2:
            sites.append(site)

    s = s1
    syear = '%4d' % (dt.year,)

    for site in sites:
        s = s[:site] + syear + s[site + 4:]

    return s


try:
    import msgpack
except ImportError:
    pass
else:
    msgpack_compat_obj_encode = functools.partial(json_compat_obj_encode,
                                                  for_msgpack=True)

    def msgpack_encode(data_type, obj):
        return msgpack.dumps(
            msgpack_compat_obj_encode(data_type, obj), encoding='utf-8')

    msgpack_compat_obj_decode = functools.partial(json_compat_obj_decode,
                                                  for_msgpack=True)

    def msgpack_decode(
            data_type, serialized_obj, alias_validators=None, strict=True):
        # We decode everything as utf-8 because we want all object keys to be
        # unicode. Otherwise, we need to do a lot more refactoring to make
        # json/msgpack share the same code. We expect byte arrays to fail
        # decoding, but when they don't, we have to convert them to bytes.
        deserialized_obj = msgpack.loads(
            serialized_obj, encoding='utf-8', unicode_errors='ignore')
        return msgpack_compat_obj_decode(
            data_type, deserialized_obj, alias_validators, strict)
