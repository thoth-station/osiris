"""API namespaces."""

from flask_restplus import Api

from osiris import ABOUT

from .build import api as build_namespace
from .probes import api as probes_namespace
from .config import api as config_namespace

from .model import app_data
from .model import response
from .model import status

api = Api(
    title=ABOUT['__title__'],
    description=ABOUT['__summary__'],
    version=ABOUT['__version__'],
    license=ABOUT['__license__'],
    contact=ABOUT['__author__'],
    contact_email=ABOUT['__email__']
)

api.add_namespace(build_namespace)
api.add_namespace(probes_namespace)
api.add_namespace(config_namespace)

api.add_model('status', status)
api.add_model('app_data', app_data)
api.add_model('response', response)
