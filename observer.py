#!/bin/env python
# Osiris: Build log aggregator.

"""Observer module."""

import os
import requests
import urllib3

from urllib.parse import urljoin

import kubernetes as k8s
from kubernetes.client.models.v1_event import V1Event as Event

from osiris.utils import noexcept
from osiris.schema.ocp import OCP
from osiris.schema.build import BuildInfo, BuildInfoSchema

# TODO: logging
# TODO: Discuss whether this module shouldbe standalone (multi-purpose module
#       used among other Thoth components, for example by registering callbacks and namespaces
#       to cover)

urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

_OSIRIS_HOST = "http://0.0.0.0"  # FIXME
_OSIRIS_PORT = "5000"  # FIXME
_OSIRIS_BUILD_START_HOOK = "/build/start"
_OSIRIS_BUILD_COMPLETED_HOOK = "/build/complete"

_THOTH_DEPLOYMENT_NAME = os.getenv('THOTH_DEPLOYMENT_NAME', 'multipurpose')  # FIXME

_KUBE_CONFIG = k8s.client.Configuration()
_KUBE_CONFIG.verify_ssl = False  # TODO: this should be fixed when running in cluster by load_incluster_config


k8s.config.load_kube_config(client_configuration=_KUBE_CONFIG)

api = k8s.client.ApiClient(_KUBE_CONFIG)
client = k8s.client.CoreV1Api(api)


@noexcept
def _is_pod_event(event: Event) -> bool:
    return event.involved_object.kind == 'Pod'


@noexcept
def _is_build_event(event: Event) -> bool:
    return event.involved_object.kind == 'Build'


@noexcept
def _is_osiris_event(event: Event) -> bool:
    # TODO: check for valid event names
    return _is_build_event(event) and event.reason in ['BuildStarted', 'BuildCompleted']


if __name__ == "__main__":

    watch = k8s.watch.Watch()

    for streamed_event in watch.stream(client.list_namespaced_event,
                                       namespace=_THOTH_DEPLOYMENT_NAME):
        kube_event: Event = streamed_event['object']
        print(kube_event)

        if not _is_osiris_event(kube_event):
            continue

        # place build event on the osiris build endpoint
        ocp = OCP.from_event(kube_event)

        build_info = BuildInfo(
            build_id=kube_event.involved_object.name,  # TODO: discuss this, maybe uid, ceph document-id?
            build_status=kube_event.reason,
            build_url=urljoin(
                _KUBE_CONFIG.host, ocp.self_link
            ),
            ocp_info=ocp
        )

        schema = BuildInfoSchema()
        data, errors = schema.dump(build_info)

        endpoint = _OSIRIS_BUILD_COMPLETED_HOOK if build_info.build_complete() else _OSIRIS_BUILD_START_HOOK

        try:
            requests.put(
                url=urljoin(_OSIRIS_HOST + ":%s" % _OSIRIS_PORT, endpoint),
                json=data,
                headers={'content-type': 'application/json'}
            )

        except requests.exceptions.ConnectionError as exc:
            # TODO: Osiris might be down, stand idle till it wakes up (probe)?
            raise exc
