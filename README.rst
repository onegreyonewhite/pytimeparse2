pytimeparse2: time expression parser
=====================================

.. image:: https://github.com/onegreyonewhite/pytimeparse2/actions/workflows/check.yml/badge.svg?branch=master
    :target: https://github.com/onegreyonewhite/pytimeparse2/actions
    :alt: Pipeline status

.. image:: https://badge.fury.io/py/pytimeparse2.svg
    :target: https://badge.fury.io/py/pytimeparse2


This is a `pytimeparse <https://github.com/wroberts/pytimeparse>`_ based project with the aim of optimizing functionality and providing stable support.

Copyright (c) 2021 Sergey Klyuykov <onegreyonewhite@mail.ru>

Licensed under the MIT License (see source file ``pytimeparse2.py`` for
details).

A small Python library to parse various kinds of time expressions,
inspired by
`this StackOverflow question <http://stackoverflow.com/questions/4628122/how-to-construct-a-timedelta-object-from-a-simple-string>`_.

The single function ``pytimeparse2.parse`` defined in the library parses time
expressions like the following:

- ``32m``
- ``2h32m``
- ``3d2h32m``
- ``1w3d2h32m``
- ``1w 3d 2h 32m``
- ``1 w 3 d 2 h 32 m``
- ``4:13``
- ``4:13:02``
- ``4:13:02.266``
- ``2:04:13:02.266``
- ``2 days,  4:13:02`` (``uptime`` format)
- ``2 days,  4:13:02.266``
- ``5hr34m56s``
- ``5 hours, 34 minutes, 56 seconds``
- ``5 hrs, 34 mins, 56 secs``
- ``2 days, 5 hours, 34 minutes, 56 seconds``
- ``1.2 m``
- ``1.2 min``
- ``1.2 mins``
- ``1.2 minute``
- ``1.2 minutes``
- ``172 hours``
- ``172 hr``
- ``172 h``
- ``172 hrs``
- ``172 hour``
- ``1.24 days``
- ``5 d``
- ``5 day``
- ``5 days``
- ``5.6 wk``
- ``5.6 week``
- ``5.6 weeks``

It returns the time as a number of seconds (an integer value if
possible, otherwise a floating-point number)::

    >>> from pytimeparse import parse
    >>> parse('1.2 minutes')
    72

For months and years, the library does not consider complications such as leap-
years and leap-seconds. Instead, it assumes "30 days for a month" and "365 days
for a year" as the basis for calculations with those units.

- ``2 mo``
- ``2 months``
- ``3y``
- ``3 years``
- ``1y2mo3w4d5h6m7s8ms``

For better capability with dates, use keyword ``as_timedelta=True`` which mark for function returns
value as ``datetime.timedelta`` or ``dateutil.relitivedelta.relativedelta`` (if installed)::

    >>> from pytimeparse import parse
    >>> parse('24h', as_timedelta=True)
    relativedelta(days=+1)

You can also forced disable dateutil support by calling ``disable_dateutil()`` before ``parse(...)``.
For returning support call ``enable_dateutil()``.

Notes
-----

A number of seconds can be converted back into a string using the
``datetime`` module in the standard library, as noted in
`this other StackOverflow question <http://stackoverflow.com/questions/538666/python-format-timedelta-to-string>`_::

    >>> from pytimeparse import parse
    >>> import datetime
    >>> parse('1 day, 14:20:16')
    138016
    >>> str(datetime.timedelta(seconds=138016))
    '1 day, 14:20:16'

Future work
-----------

1. Speed up with Cython for some python versions.
2. Use github actions for testing and releasing.
