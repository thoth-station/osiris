#!/bin/env python
# Osiris: Build log aggregator.

"""Observer module."""

import os
import requests
import urllib3

import kubernetes as k8s
from kubernetes.client.models.v1_event import V1Event as Event

from osiris.utils import noexcept
from osiris.schema.ocp import OCP
from osiris.schema.build import BuildInfo, BuildInfoSchema

# TODO: logging
# TODO: Discuss whether this module shouldbe standalone (multi-purpose module
#       used among other Thoth components, for example by registering callbacks and namespaces
#       to cover)

_OSIRIS_HOST = ""
_OSIRIS_BUILD_START_HOOK = "/build/start"
_OSIRIS_BUILD_COMPLETED_HOOK = "/build/complete"

_THOTH_DEPLOYMENT_NAME = os.getenv('THOTH_DEPLOYMENT_NAME', 'thoth-test-core')  # FIXME


urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

config = k8s.client.Configuration()
config.verify_ssl = False  # TODO: this should be fixed when running in cluster by load_incluster_config

k8s.config.load_kube_config(client_configuration=config)

api = k8s.client.ApiClient(config)
client = k8s.client.CoreV1Api(api)


@noexcept
def _is_pod_event(event: Event) -> bool:
    return event.involved_object.kind == 'Pod'


@noexcept
def _is_build_event(event: Event) -> bool:
    return event.reason in ['BuildStarted', 'BuildCompleted']  # TODO: check for valid event names


@noexcept
def _is_valid_event(event: Event) -> bool:
    return _is_pod_event(event) and _is_build_event(event)


if __name__ == "__main__":

    watch = k8s.watch.Watch()

    for streamed_event in watch.stream(client.list_namespaced_event,
                                       namespace=_THOTH_DEPLOYMENT_NAME):
        kube_event: Event = streamed_event['object']
        print(kube_event)

        if not _is_valid_event(kube_event):
            continue

        # TODO: speed things up by running async?

        # place build event on the osiris build endpoint
        ocp = OCP.from_event(kube_event)

        build_info = BuildInfo(
            build_id=kube_event.involved_object.name,  # TODO: discuss this, maybe uid, ceph document-id?
            build_status=kube_event.reason,
            build_url=ocp.link,
            ocp_info=ocp
        )

        schema = BuildInfoSchema()

        print("Passing build document to Osiris")
        requests.put(url=_OSIRIS_BUILD_START_HOOK, data=schema.dump(build_info))

