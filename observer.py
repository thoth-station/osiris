#!/bin/env python
# Osiris: Build log aggregator.

"""Observer module."""

import ujson
import os
import requests
import urllib3

import daiquiri
import logging
import typing

from http import HTTPStatus
from requests.adapters import HTTPAdapter
from requests.adapters import Retry
from urllib.parse import urljoin

import kubernetes
from kubernetes.client.models.v1_event import V1Event as Event

from osiris.utils import noexcept
from osiris.schema.build import BuildInfo, BuildInfoSchema

daiquiri.setup(
    level=logging.DEBUG if os.getenv('DEBUG', 0) else logging.INFO,
)

urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)


_LOGGER = daiquiri.getLogger()

_OSIRIS_HOST = os.getenv("OSIRIS_HOST_NAME", "http://0.0.0.0")
_OSIRIS_PORT = os.getenv("OSIRIS_HOST_PORT", "5000")
_OSIRIS_BUILD_START_HOOK = "/build/started"
_OSIRIS_BUILD_COMPLETED_HOOK = "/build/completed"

_THOTH_DEPLOYMENT_NAME = os.getenv('THOTH_DEPLOYMENT_NAME')  # TODO: get from oc/kube config?

_KUBE_CONFIG = kubernetes.client.Configuration()
_KUBE_CONFIG.verify_ssl = False  # TODO: this should be fixed when running in cluster by load_incluster_config

_REQUESTS_MAX_RETRIES = 10


class RetrySession(requests.Session):

    def __init__(self,
                 adapter_prefixes: typing.List[str] = None,
                 status_forcelist: typing.Tuple[int] = (500, 502, 504),
                 method_whitelist: typing.List[str] = None):

        super(RetrySession, self).__init__()

        adapter_prefixes = adapter_prefixes or ["http://", "https://"]

        retry_config = Retry(
            total=_REQUESTS_MAX_RETRIES,
            connect=_REQUESTS_MAX_RETRIES,
            backoff_factor=5,  # determines sleep time
            status_forcelist=status_forcelist,
            method_whitelist=method_whitelist
        )
        retry_adapter = HTTPAdapter(max_retries=retry_config)

        for prefix in adapter_prefixes:
            self.mount(prefix, retry_adapter)


def new_observer() -> kubernetes.client.CoreV1Api:
    kubernetes.config.load_kube_config(client_configuration=_KUBE_CONFIG)

    kube_api = kubernetes.client.ApiClient(_KUBE_CONFIG)
    v1 = kubernetes.client.CoreV1Api(kube_api)

    return v1


@noexcept
def _is_pod_event(event: Event) -> bool:
    return event.involved_object.kind == 'Pod'


@noexcept
def _is_build_event(event: Event) -> bool:
    return event.involved_object.kind == 'Build'


@noexcept
def _is_osiris_event(event: Event) -> bool:
    # TODO: check for valid event names
    valid = _is_build_event(event) and event.reason in ['BuildStarted', 'BuildCompleted']

    _LOGGER.debug("[EVENT] Event is valid osiris event: %r", valid)

    return valid


if __name__ == "__main__":

    client = new_observer()
    watch = kubernetes.watch.Watch()

    with RetrySession() as session:

        put_request = requests.Request(
                url=':'.join([_OSIRIS_HOST, _OSIRIS_PORT]),
                method='PUT',
                headers={'content-type': 'application/json'}
        )

        for streamed_event in watch.stream(client.list_namespaced_event,
                                           namespace=_THOTH_DEPLOYMENT_NAME):

            kube_event: Event = streamed_event['object']

            _LOGGER.debug("[EVENT] New event received.")
            _LOGGER.debug("[EVENT] Event kind: %s", kube_event.kind)

            if not _is_osiris_event(kube_event):
                continue

            build_info = BuildInfo.from_event(kube_event)
            build_url = urljoin(_KUBE_CONFIG.host, build_info.ocp_info.self_link),

            schema = BuildInfoSchema()
            data, errors = schema.dump(build_info)

            osiris_endpoint = _OSIRIS_BUILD_COMPLETED_HOOK if build_info.build_complete() else _OSIRIS_BUILD_START_HOOK

            put_request.url = urljoin(put_request.url, osiris_endpoint)
            put_request.json = data

            prep_request = session.prepare_request(put_request)

            _LOGGER.debug("[EVENT] Event to be posted: %r", kube_event)
            _LOGGER.info("[EVENT] Posting event '%s' to: %s", kube_event.kind, put_request.url)

            resp = session.send(prep_request, timeout=60)

            if resp.status_code == HTTPStatus.ACCEPTED:

                _LOGGER.info("[EVENT] Success.")

            else:

                _LOGGER.info("[EVENT] Failure.")
                _LOGGER.info("[EVENT] Status: %d  Reason: %r",
                             resp.status_code, resp.reason)
