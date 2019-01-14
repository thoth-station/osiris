"""Osiris: Build log aggregator."""

import os

from osiris import __about__


ABOUT = dict()

with open(__about__.__file__) as f:
    exec(f.read(), ABOUT)


__name__ = 'osiris'
__version__ = ABOUT['__version__']


# Environment variables

DEFAULT_OC_LOG_LEVEL = os.getenv('OC_LOG_LEVEL', 6)
