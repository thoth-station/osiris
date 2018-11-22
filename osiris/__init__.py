"""Osiris: Build log aggregator."""

from osiris import __about__


ABOUT = dict()

with open(__about__.__file__) as f:
    exec(f.read(), ABOUT)


