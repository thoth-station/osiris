"""Osiris: Build log aggregator."""

import os
import urllib3

from osiris import __about__

from thoth.common.openshift import OpenShift


# disable InsecureReqestWarnings produces upon OpenShift client initialization
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


ABOUT = dict()

with open(__about__.__file__) as f:
    exec(f.read(), ABOUT)


__name__ = 'osiris'
__version__ = ABOUT['__version__']


# Environment variables

DEFAULT_LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

DEFAULT_OC_LOG_LEVEL = os.getenv('OC_LOG_LEVEL', 6)
DEFAULT_OC_PROJECT = os.getenv('OC_PROJECT', None)


# OpenShift client

_OPENSHIFT_HOST = None
_OPENSHIFT_NAMESPACE = os.getenv("MIDDLETIER_NAMESPACE", None)

_OPENSHIFT_TOKEN = None
_OPENSHIFT_CLIENT = None
_OPENSHIFT_CONTEXT = None


def set_token(token: str):
    global _OPENSHIFT_TOKEN

    _OPENSHIFT_TOKEN = token


def set_context(context: str):
    global _OPENSHIFT_CONTEXT

    _OPENSHIFT_CONTEXT = context


def set_namespace(namespace: str):
    global _OPENSHIFT_NAMESPACE

    _OPENSHIFT_NAMESPACE = namespace


def new_oc_client() -> OpenShift:
    global _OPENSHIFT_CLIENT, \
           _OPENSHIFT_CONTEXT, \
           _OPENSHIFT_TOKEN, \
           _OPENSHIFT_HOST

    # initialize openshift client for the current namespace
    _OPENSHIFT_CLIENT = OpenShift(
        token=_OPENSHIFT_TOKEN,  # if None, get from environment / service account
        # context=_OPENSHIFT_CONTEXT,  # TODO
        middletier_namespace=_OPENSHIFT_NAMESPACE
    )

    _OPENSHIFT_HOST = _OPENSHIFT_CLIENT.ocp_client.configuration.host
    _OPENSHIFT_TOKEN = _OPENSHIFT_CLIENT.token

    return _OPENSHIFT_CLIENT


def get_oc_client() -> OpenShift:
    """Initialize OpenShift client.

    This function can be used within OpenShift cluster or locally by providing
    required credentials.
    """
    global _OPENSHIFT_CLIENT

    if _OPENSHIFT_CLIENT is not None:  # client is not re-initialized if there are no changes

        # check token
        has_changed = (
                _OPENSHIFT_CLIENT.token != _OPENSHIFT_TOKEN or
                # _OPENSHIFT_CLIENT.context != _OPENSHIFT_CONTEXT or  # TODO
                _OPENSHIFT_CLIENT.middletier_namespace != _OPENSHIFT_NAMESPACE
        )

        if has_changed:
            _OPENSHIFT_CLIENT = new_oc_client()

        # noinspection PyTypeChecker
        return _OPENSHIFT_CLIENT

    return new_oc_client()
