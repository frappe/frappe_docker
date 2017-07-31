from __future__ import absolute_import
from __future__ import division
# Copyright (c) 2010-2017 openpyxl

"""Manage Excel date weirdness."""

# Python stdlib imports
import datetime
from datetime import timedelta, tzinfo
from math import isnan
import re

from jdcal import (
    gcal2jd,
    jd2gcal,
    MJD_0
)


# constants
MAC_EPOCH = datetime.date(1904, 1, 1)
WINDOWS_EPOCH = datetime.date(1899, 12, 30)
CALENDAR_WINDOWS_1900 = sum(gcal2jd(WINDOWS_EPOCH.year, WINDOWS_EPOCH.month, WINDOWS_EPOCH.day))
CALENDAR_MAC_1904 = sum(gcal2jd(MAC_EPOCH.year, MAC_EPOCH.month, MAC_EPOCH.day))
SECS_PER_DAY = 86400

EPOCH = datetime.datetime.utcfromtimestamp(0)
W3CDTF_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
W3CDTF_REGEX = re.compile('(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(.(\d{2}))?Z?')


def datetime_to_W3CDTF(dt):
    """Convert from a datetime to a timestamp string."""
    return datetime.datetime.strftime(dt, W3CDTF_FORMAT)


def W3CDTF_to_datetime(formatted_string):
    """Convert from a timestamp string to a datetime object."""
    match = W3CDTF_REGEX.match(formatted_string)
    dt = [int(v) for v in match.groups()[:6]]
    return datetime.datetime(*dt)


def to_excel(dt, offset=CALENDAR_WINDOWS_1900):
    if isnan(dt.year): # Pandas supports Not a Date
        return
    jul = sum(gcal2jd(dt.year, dt.month, dt.day)) - offset
    if jul <= 60 and offset == CALENDAR_WINDOWS_1900:
        jul -= 1
    if hasattr(dt, 'time'):
        jul += time_to_days(dt)
    return jul


def from_excel(value, offset=CALENDAR_WINDOWS_1900):
    if value is None:
        return
    if 1 < value < 60 and offset == CALENDAR_WINDOWS_1900:
        value += 1
    parts = list(jd2gcal(MJD_0, value + offset - MJD_0))
    _, fraction = divmod(value, 1)
    jumped = (parts[-1] == 0 and fraction > 0)
    diff = datetime.timedelta(days=fraction)

    if 0 < abs(value) < 1:
        return days_to_time(diff)
    if not jumped:
        return datetime.datetime(*parts[:3]) + diff
    else:
        return datetime.datetime(*parts[:3] + [0])


class GMT(tzinfo):

    def utcoffset(self, dt):
        return timedelta(0)

    def dst(self, dt):
        return timedelta(0)

    def tzname(self,dt):
        return "GMT"

try:
    from datetime import timezone
    UTC = timezone(timedelta(0))
except ImportError:
    # Python 2.6
    UTC = GMT()


def time_to_days(value):
    """Convert a time value to fractions of day"""
    if value.tzinfo is not None:
        value = value.astimezone(UTC)
    return (
        (value.hour * 3600)
        + (value.minute * 60)
        + value.second
        + value.microsecond / 10**6
        ) / SECS_PER_DAY


def timedelta_to_days(value):
    """Convert a timedelta value to fractions of a day"""
    if not hasattr(value, 'total_seconds'):
        secs = (value.microseconds +
                (value.seconds + value.days * SECS_PER_DAY) * 10**6) / 10**6
    else:
        secs =value.total_seconds()
    return secs / SECS_PER_DAY


def days_to_time(value):
    mins, seconds = divmod(value.seconds, 60)
    hours, mins = divmod(mins, 60)
    return datetime.time(hours, mins, seconds, value.microseconds)
