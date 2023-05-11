#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
(c) Sergey Klyuykov <onegreyonewhite@mail.ru> 3 Nov 2021

Implements a single function, `parse`, which can parse various
kinds of time expressions.
"""

# MIT LICENSE
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__version__ = '1.7.0'

import typing
import re
from datetime import timedelta

try:
    from dateutil.relativedelta import relativedelta
    HAS_RELITIVE_TIMEDELTA = True
except ImportError:  # pragma: no cover
    HAS_RELITIVE_TIMEDELTA = False
    relativedelta = None  # type: ignore


SIGN = r'(?P<sign>[+|-]|\+)?'
YEARS = r'(?P<years>[\d.]+)\s*(?:ys?|yrs?.?|years?)'
MONTHS = r'(?P<months>[\d.]+)\s*(?:mos?.?|mths?.?|months?)'
WEEKS = r'(?P<weeks>[\d.]+)\s*(?:w|wks?|weeks?)'
DAYS = r'(?P<days>[\d.]+)\s*(?:d|dys?|days?)'
HOURS = r'(?P<hours>[\d.]+)\s*(?:h|hrs?|hours?)'
MINS = r'(?P<minutes>[\d.]+)\s*(?:m|(mins?)|(minutes?))'
SECS = r'(?P<seconds>[\d.]+)\s*(?:s|secs?|seconds?)'
MILLIS = r'(?P<milliseconds>[\d.]+)\s*(?:ms|msecs?|millis|milliseconds?)'
SEPARATORS = r'[,/]'
SECCLOCK = r':(?P<seconds>\d{2}(?:\.\d+)?)'
MINCLOCK = r'(?P<minutes>\d{1,2}):(?P<seconds>\d{2}(?:\.\d+)?)'
HOURCLOCK = r'(?P<hours>\d+):(?P<minutes>\d{2}):(?P<seconds>\d{2}(?:\.\d+)?)'
DAYCLOCK = (r'(?P<days>\d+):(?P<hours>\d{2}):'
            r'(?P<minutes>\d{2}):(?P<seconds>\d{2}(?:\.\d+)?)')

MULTIPLIERS = {
    'years': 60 * 60 * 24 * 365,
    'months': 60 * 60 * 24 * 30,
    'weeks': 60 * 60 * 24 * 7,
    'days': 60 * 60 * 24,
    'hours': 60 * 60,
    'minutes': 60,
    'seconds': 1,
    'milliseconds': 1e-3,
}


def OPT(x):
    return r'(?:{x})?'.format(x=x)


def OPTSEP(x):
    return r'(?:{x}\s*(?:{SEPARATORS}\s*)?)?'.format(x=x, SEPARATORS=SEPARATORS)


TIMEFORMATS = [
    (rf'{OPTSEP(YEARS)}\s*'
     rf'{OPTSEP(MONTHS)}\s*'
     rf'{OPTSEP(WEEKS)}\s*'
     rf'{OPTSEP(DAYS)}\s*'
     rf'{OPTSEP(HOURS)}\s*'
     rf'{OPTSEP(MINS)}\s*'
     rf'{OPT(SECS)}\s*'
     rf'{OPT(MILLIS)}'),
    rf'{OPTSEP(WEEKS)}\s*{OPTSEP(DAYS)}\s*{OPTSEP(HOURS)}\s*{OPTSEP(MINS)}\s*{OPT(SECS)}\s*{OPT(MILLIS)}',
    rf'{MINCLOCK}',
    rf'{OPTSEP(WEEKS)}\s*{OPTSEP(DAYS)}\s*{HOURCLOCK}',
    rf'{DAYCLOCK}',
    rf'{SECCLOCK}',
    rf'{YEARS}',
    rf'{MONTHS}',
]

COMPILED_SIGN = re.compile(r'\s*' + SIGN + r'\s*(?P<unsigned>.*)$')
COMPILED_TIMEFORMATS = [
    re.compile(r'\s*' + timefmt + r'\s*$', re.I)
    for timefmt in TIMEFORMATS
]


def _all_digits(mdict, delta_class):
    if HAS_RELITIVE_TIMEDELTA and issubclass(delta_class, relativedelta):
        if 'milliseconds' in mdict:
            mdict['microseconds'] = float(mdict.pop('milliseconds') or 0) * 1000
        return delta_class(**{k: float(v) for k, v in mdict.items() if v}).normalized()

    delta = delta_class(**{
        key: float(mdict.pop(key) or 0)
        for key in mdict.copy()
        if key in ('hours', 'minutes', 'days', 'milliseconds')
    })

    for time_type, value in mdict.items():
        if not value:
            continue
        if value.isdigit():
            delta += delta_class(seconds=MULTIPLIERS[time_type] * int(value, 10))
        elif value.replace('.', '', 1).isdigit():
            delta += delta_class(seconds=MULTIPLIERS[time_type] * float(value))

    return delta


def _interpret_as_minutes(sval, mdict):
    """
    Times like "1:22" are ambiguous; do they represent minutes and seconds
    or hours and minutes?  By default, parse assumes the latter.  Call
    this function after parsing out a dictionary to change that assumption.

    >>> import pprint
    >>> pprint.pprint(_interpret_as_minutes('1:24', {'seconds': '24', 'minutes': '1'}))
    {'hours': '1', 'minutes': '24'}
    """
    if sval.count(':') == 1 and '.' not in sval and (('hours' not in mdict) or (mdict['hours'] is None)) and (
            ('days' not in mdict) or (mdict['days'] is None)) and (('weeks' not in mdict) or (mdict['weeks'] is None)) \
            and (('months' not in mdict) or (mdict['months'] is None)) \
            and (('years' not in mdict) or (mdict['years'] is None)):
        mdict['hours'] = mdict['minutes']
        mdict['minutes'] = mdict['seconds']
        mdict.pop('seconds')
    return mdict


def _normilized_relativedelta(value: typing.Optional[timedelta]) -> typing.Optional[timedelta]:
    if isinstance(value, relativedelta):
        return value.normalized()
    return value


def _parse(
        sval: typing.Union[str, int, float],
        granularity: str = 'seconds',
        delta_class: typing.Type[timedelta] = timedelta
) -> typing.Optional[timedelta]:
    if isinstance(sval, (int, float)):
        return _normilized_relativedelta(delta_class(seconds=float(sval)))
    if sval.replace('.', '', 1).replace('-', '', 1).replace('+', '', 1).isdigit():
        return _normilized_relativedelta(delta_class(seconds=float(sval)))

    match = COMPILED_SIGN.match(sval)
    sign = -1 if match.groupdict()['sign'] == '-' else 1  # type: ignore
    sval = match.groupdict()['unsigned']  # type: ignore

    for timefmt in COMPILED_TIMEFORMATS:
        match = timefmt.match(sval)

        if not (match and match.group(0).strip()):
            continue

        mdict = match.groupdict()
        if granularity == 'minutes':
            mdict = _interpret_as_minutes(sval, mdict)

        return sign * _all_digits(mdict, delta_class)

    return timedelta(seconds=float(sval)) * sign


def enable_dateutil():
    global HAS_RELITIVE_TIMEDELTA
    assert relativedelta is not None, 'Module python-dateutil should be installed before.'
    HAS_RELITIVE_TIMEDELTA = True


def disable_dateutil():
    global HAS_RELITIVE_TIMEDELTA
    HAS_RELITIVE_TIMEDELTA = False


def parse(
        sval: typing.Union[str, int, float],
        granularity: str = 'seconds',
        raise_exception: bool = False,
        as_timedelta: bool = False,
) -> typing.Optional[typing.Union[int, float, timedelta, typing.NoReturn]]:
    """
    Parse a time expression, returning it as a number of seconds.  If
    possible, the return value will be an `int`; if this is not
    possible, the return will be a `float`.  Returns `None` if a time
    expression cannot be parsed from the given string.

    Arguments:
    - `sval`: the string value to parse
    - `granularity`: minimal type of digits after last colon (default is ``seconds``)
    - `raise_exception`: raise exception on parsing errors (default is ``False``)
    - `as_timedelta`: return ``datetime.timedelta`` object instead of ``int`` (default is ``False``)

    >>> parse('1:24')
    84
    >>> parse(':22')
    22
    >>> parse('1 minute, 24 secs')
    84
    >>> parse('1m24s')
    84
    >>> parse('1.2 minutes')
    72
    >>> parse('1.2 seconds')
    1.2

    Time expressions can be signed.

    >>> parse('- 1 minute')
    -60
    >>> parse('+ 1 minute')
    60

    If granularity is specified as ``minutes``, then ambiguous digits following
    a colon will be interpreted as minutes; otherwise they are considered seconds.

    >>> parse('1:30')
    90
    >>> parse('1:30', granularity='minutes')
    5400

    If ``as_timedelta`` is specified as ``True``, then return timedelta object.

    >>> parse('24h', as_timedelta=True)
    relativedelta(days=+1)
    >>> parse('48:00', as_timedelta=True, granularity='minutes')
    relativedelta(days=+2)

    If ``raise_exception`` is specified as ``True``, then exception will raised
    on failed parsing.

    >>> parse(':1.1.1', raise_exception=True)
    Traceback (most recent call last):
        ...
    ValueError: could not convert string to float: ':1.1.1'
    """
    try:
        value = _parse(sval, granularity, relativedelta if HAS_RELITIVE_TIMEDELTA and as_timedelta else timedelta)
        if not as_timedelta and value is not None:
            new_value = value.total_seconds()
            if new_value.is_integer():
                return int(new_value)
            else:
                return new_value
        return value
    except Exception:
        if raise_exception:
            raise
        return None
