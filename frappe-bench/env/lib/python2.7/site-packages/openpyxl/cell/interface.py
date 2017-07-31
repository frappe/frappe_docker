from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

from openpyxl.compat.abc import ABC
from abc import abstractmethod, abstractproperty


class AbstractCell(ABC):


    def __init__(self, value=None):
        self.value = value

    @abstractproperty
    def encoding(self):
        pass

    @abstractproperty
    def coordinate(self):
        pass

    @abstractproperty
    def base_date(self):
        pass

    @abstractproperty
    def guess_types(self):
        pass

    @abstractproperty
    def value(self):
        pass

    @abstractproperty
    def internal_value(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def offset(self, row=0, column=0):
        pass

    @abstractproperty
    def comment(self):
        pass

    @abstractproperty
    def style(self):
        pass

    @abstractproperty
    def number_format(self):
        pass

    @abstractproperty
    def is_date(self):
        pass

