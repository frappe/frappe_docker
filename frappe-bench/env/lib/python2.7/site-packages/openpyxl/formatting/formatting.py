from __future__ import absolute_import
# Copyright (c) 2010-2017 openpyxl

from openpyxl.compat import OrderedDict
from openpyxl.descriptors import (
    Bool,
    String,
    Sequence,
    Alias,
)
from openpyxl.descriptors.excel import ExtensionList
from openpyxl.descriptors.serialisable import Serialisable

from .rule import Rule


class ConditionalFormatting(Serialisable):

    tagname = "conditionalFormatting"

    sqref = String()
    pivot = Bool(allow_none=True)
    cfRule = Sequence(expected_type=Rule)
    rules = Alias("cfRule")


    def __init__(self, sqref=None, pivot=None, cfRule=(), extLst=None):
        self.sqref = sqref
        self.pivot = pivot
        self.cfRule = cfRule


class ConditionalFormattingList(object):
    """Conditional formatting rules."""

    def __init__(self):
        self.cf_rules = OrderedDict()
        self.max_priority = 0

    def add(self, range_string, cfRule):
        """Add a rule such as ColorScaleRule, FormulaRule or CellIsRule

         The priority will be added automatically.
        """
        if not isinstance(cfRule, Rule):
            raise ValueError("Only instances of openpyxl.formatting.rule.Rule may be added")
        rule = cfRule
        self.max_priority += 1
        if not rule.priority:
            rule.priority = self.max_priority

        self.cf_rules.setdefault(range_string, []).append(rule)


    def __bool__(self):
        return bool(self.cf_rules)

    __nonzero = __bool__


    def __iter__(self):
        for cell_range, rules in self.cf_rules.items():
            yield ConditionalFormatting(sqref=cell_range, cfRule=rules)
