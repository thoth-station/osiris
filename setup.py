import os

from setuptools import find_packages
from setuptools import setup

BASE_DIR = os.path.dirname(__file__)

# When executing the setup.py, we need to be able to import ourselves, this
# means that we need to add the src/ directory to the sys.path.
ABOUT = dict()
with open(os.path.join(BASE_DIR, 'osiris', '__about__.py')) as f:
    exec(f.read(), ABOUT)

with open('requirements.txt') as f:
    REQUIREMENTS = f.readlines()

setup(
    name=ABOUT['__title__'],
    version=ABOUT['__version__'],

    author=ABOUT['__author__'],
    author_email=ABOUT['__email__'],
    url=ABOUT['__uri__'],

    license=ABOUT['__license__'],

    description=ABOUT['__summary__'],
    long_description="Osiris API is a service that accompanies project Thoth and performs"
                     "build log aggregation and analysis. Osiris integrates with OpenShift"
                     "and kubernetes.",

    classifiers=[
        "Development Status :: 2 - Pre-Alpha"
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Utilities",
    ],
    packages=find_packages(exclude=["tests"]),

    install_requires=REQUIREMENTS
)
