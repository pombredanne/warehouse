from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from sqlalchemy.types import SchemaType, TypeDecorator
from sqlalchemy.types import Enum as SQLAEnum


class EnumSymbol(object):
    """
    Define a fixed symbol tied to a parent class.
    """

    def __init__(self, cls_, name, value, description):
        self.cls_ = cls_
        self.name = name
        self.value = value
        self.description = description

    def __reduce__(self):
        """
        Allow unpickling to return the symbol linked to the Enum class.
        """
        return getattr, (self.cls_, self.name)

    def __iter__(self):
        return iter([self.value, self.description])

    def __repr__(self):
        return "<%s>" % self.name


class EnumMeta(type):
    """
    Generate new Enum classes.
    """

    def __init__(cls, classname, bases, dict_):
        cls._reg = reg = cls._reg.copy()

        for key, val in dict_.items():
            if isinstance(val, tuple):
                sym = reg[val[0]] = EnumSymbol(cls, key, *val)
                setattr(cls, key, sym)

        super(EnumMeta, cls).__init__(classname, bases, dict_)
        #return type.__init__(cls, classname, bases, dict_)

    def __iter__(cls):
        return iter(cls._reg.values())


class EnumType(SchemaType, TypeDecorator):
    # pylint: disable=W0223

    def __init__(self, enum, *args, **kwargs):
        self.enum = enum
        self.impl = SQLAEnum(
                        *enum.values(),
                        name="ck%s" % re.sub(
                            "([A-Z])",
                            lambda m: "_" + m.group(1).lower(),
                            enum.__name__))

        super(EnumType, self).__init__(*args, **kwargs)

    def _set_table(self, table, column):
        # pylint: disable=W0212
        self.impl._set_table(table, column)

    def copy(self):
        return EnumType(self.enum)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self.enum.from_string(value.strip())


class Enum(object):
    """
    Declarative enumeration.
    """

    __metaclass__ = EnumMeta
    _reg = {}

    @classmethod
    def from_string(cls, value):
        try:
            return cls._reg[value]
        except KeyError:
            raise ValueError(
                    "Invalid value for %r: %r" %
                    (cls.__name__, value)
                )

    @classmethod
    def values(cls):
        return cls._reg.keys()

    @classmethod
    def db_type(cls):
        return EnumType(cls)
