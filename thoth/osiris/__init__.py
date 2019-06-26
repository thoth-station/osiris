"""Osiris: Build log aggregator."""

import os
import urllib3
from thoth.osiris import __about__
from thoth.common.openshift import OpenShift

# disable InsecureReqestWarnings produces upon OpenShift client initialization
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


ABOUT = dict()

with open(__about__.__file__) as f:
    exec(f.read(), ABOUT)


__name__ = "osiris"
__version__ = ABOUT["__version__"]

DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEFAULT_OC_LOG_LEVEL = os.getenv("OC_LOG_LEVEL", 6)
DEFAULT_OC_PROJECT = os.getenv("OC_PROJECT", None)
_OPENSHIFT_NAMESPACE = os.getenv("THOTH_MIDDLETIER_NAMESPACE", None)
# OpenShift client
_OPENSHIFT_CLIENT = None


def get_oc_client() -> OpenShift:
    """Initialize OpenShift client.

    This function can be used within OpenShift cluster or locally by providing
    required credentials.
    """
    global _OPENSHIFT_CLIENT

    if _OPENSHIFT_CLIENT is None:  # client is not re-initialized if there are no changes

        # initialize openshift client for the current namespace
        _OPENSHIFT_CLIENT = OpenShift(middletier_namespace=_OPENSHIFT_NAMESPACE)

    return _OPENSHIFT_CLIENT
