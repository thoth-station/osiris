#!/usr/bin/env python3
# Osiris
# Copyright(C) 2019 Christoph Görn
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Implementation of API v1."""

import os
import logging
import typing
import requests
import connexion
import jaeger_client
from itertools import islice
from flask import url_for

from opentracing_instrumentation.client_hooks import install_all_patches

from thoth.common.openshift import OpenShift
from thoth.osiris import __version__
from .configuration import Configuration

from kubernetes.client import ApiClient
from kubernetes.client.models.v1_event import V1Event

from thoth.osiris import DEFAULT_OC_LOG_LEVEL
from thoth.osiris.schema.aggregator import build_aggregator

from thoth.osiris.response import request_accepted
from thoth.osiris.response import request_ok
from thoth.osiris.response import bad_request

from thoth.osiris.schema.build import BuildInfo, BuildInfoSchema, BuildLogSchema
from thoth.osiris.schema.build import BuildInfoPagination, BuildInfoPaginationSchema

from thoth.osiris.exceptions import OCError

from thoth.storages.exceptions import NotFoundError
from werkzeug.exceptions import HTTPException, InternalServerError

# Environment variables
DEFAULT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEFAULT_OC_LOG_LEVEL = os.getenv("OC_LOG_LEVEL", 6)
DEFAULT_OC_PROJECT = os.getenv("OC_PROJECT", None)
_OPENSHIFT_NAMESPACE = os.getenv("THOTH_MIDDLETIER_NAMESPACE", None)

PAGINATION_SIZE = 100
_LOGGER = logging.getLogger(__name__)
_OPENSHIFT = OpenShift()


def info_response() -> dict:
    """The response for info endpoint."""
    return {
        "version": __version__,
        "connexionVersion": connexion.__version__,
        "jaegerClientVersion": jaeger_client.__version__,
    }


def get_info():
    """Get information about the api service."""
    with Configuration.tracer.start_span("info_get") as span:
        span.log_kv({"event": "info_get", "osiris_api_version": __version__})

        # Automatically trace all requests made with 'requests' library.
        install_all_patches()

        with Configuration.tracer.start_span(
            "google_query", child_of=span
        ) as google_query_span:
            google_query_span.log_kv({"event": "query_google"})
            url = "http://google.com/"
            # Make the actual request to webserver.
            requests.get(url)

        return info_response(), 200, {"x-thoth-osiris-api-version": __version__}


def post_buildlog(
    _file_: str, output_format: str, handler: str = None, limit: int = None
):
    """Store received buildlog to ceph storage."""
    log_file = _file_.read()
    log_file = log_file.decode("utf-8")
    parameters = dict()
    parameters["build_log"] = log_file
    build_id = _file_.filename.replace(".log", "")
    build_info = BuildInfo(build_id=build_id, build_status="Unknown")
    build_doc, _ = BuildInfoSchema().dump(build_info)
    build_log_schema = BuildLogSchema()
    build_log, validation_errors = build_log_schema.load(
        {"data": log_file, "metadata": {"build_id": build_id}}
    )
    build_doc["build_log"] = build_log
    build_aggregator.store_build_data(build_doc)
    THOTH_BUILD_ANALYSER_OUTPUT = output_format
    response, status = schedule(parameters, THOTH_BUILD_ANALYSER_OUTPUT)

    return response, status, {"x-thoth-osiris-api-version": __version__}


def schedule(parameters: dict, THOTH_BUILD_ANALYSER_OUTPUT: str):
    response_analyse, status_analyse = _do_schedule(
        parameters,
        _OPENSHIFT.schedule_build_analyse,
        output_format=THOTH_BUILD_ANALYSER_OUTPUT,
    )
    response_dependencies, status_dependencies = _do_schedule(
        parameters,
        _OPENSHIFT.schedule_build_dependencies,
        output_format=THOTH_BUILD_ANALYSER_OUTPUT,
    )
    _LOGGER.info(
        "Build log analysis build_analyse_status: %s, build_dependencies_status: %s",
        status_analyse,
        status_dependencies,
    )
    return response_analyse, status_analyse


def _do_schedule(parameters: dict, runner: typing.Callable, **runner_kwargs):
    """Schedule the given job - a generic method for running any analyzer, solver, ..."""
    return (
        {
            "analysis_id": runner(**parameters, **runner_kwargs),
            "parameters": parameters,
            "cached": False,
        },
        202,
    )


def get_build_status_resource(build_id: str = None):
    """Returns Build status."""
    _, build_info = build_aggregator.retrieve_build_data(build_id)

    return request_ok(payload={"build_status": build_info.build_status})


def get_build_info_resource(build_id: str = None):
    """Build information endpoint."""
    schema = BuildInfoSchema()
    _, build_info = build_aggregator.retrieve_build_data(build_id)

    return request_ok(payload=schema.dump(build_info))


def get_build_info_listing_resource(page: int = 1):
    """Paginate build information documents stored in Ceph."""
    schema = BuildInfoPaginationSchema()
    paginated_data: BuildInfoPagination = build_aggregator.paginate_build_data(page)

    return request_ok(payload=schema.dump(paginated_data))


def get_build_log_resource(build_id: str = None):
    """Return logs stored by the given build."""
    build_log, = build_aggregator.retrieve_build_data(build_id, log_only=True)
    return request_ok(payload=build_log)


def put_build_log_resource(build_id: str = None):
    """Store logs for the given build in Ceph."""
    try:
        build_log, build_info = build_aggregator.retrieve_build_data(build_id)
        if build_log is not None and not int(connexion.request.args.get("force", 1)):

            return bad_request(
                errors={
                    "BuildLogExists": f"Build log `{build_id}` already exists"
                    " and `force` is not specified."
                }
            )

    except NotFoundError:
        # create the entry anyway without any metadata
        build_log = None
        build_info = BuildInfo(build_id=build_id, build_status="Unknown")
    if not build_log:
        build_doc, _ = BuildInfoSchema().dump(build_info)
        build_log_schema = BuildLogSchema()
        build_log, validation_errors = build_log_schema.load(connexion.request.json)

        if not build_info.build_complete():
            resp = bad_request(
                errors={"BuildNotCompleted": "Build has not been completed yet."},
                validation_errors=validation_errors,
            )

        else:
            if "build_id" not in build_log["metadata"]:
                build_log["metadata"]["build_id"] = build_id

            build_doc["build_log"] = build_log

            build_aggregator.store_build_data(build_doc)
    parameters = {"build_log": build_log}
    response, status = schedule(parameters, THOTH_BUILD_ANALYSER_OUTPUT="json")
    resp = request_ok(payload=response)

    return resp


def put_build_started_resource(build_id: str = None):
    """Trigger build start hook."""
    errors = {}

    build_schema = BuildInfoSchema()
    build_data: dict = connexion.request.json

    if build_data["build_id"] != build_id:
        errors["build_data"] = "`build_id` field does not match given url."

    validation_errors = build_schema.validate(build_data)

    if not errors:  # validation errors other than build_id are permitted for now
        # store in Ceph
        build_data["build_log"] = None
        build_aggregator.store_build_data(build_data)

        return request_accepted(errors=validation_errors)

    else:
        errors.update(validation_errors)

        return bad_request(errors=errors)


def put_build_started_event_resource(build_id: str = None):
    """Trigger build start hook."""
    build_schema = BuildInfoSchema()

    kube_client = ApiClient()

    event: V1Event = kube_client.deserialize(request, response_type="V1Event")
    build_data, validation_errors = build_schema.dump(
        BuildInfo.from_event(event, build_id)
    )

    # store in Ceph
    build_data["build_log"] = None
    build_aggregator.store_build_data(build_data)

    return request_accepted(errors=validation_errors)


def put_build_resource(build_id: str = None):
    """Trigger build start hook.

    Receiver hook for started builds.
    This endpoint expects data as returned by Thoth OpenShift API.
    Store received build information in ceph storage.
    """
    build_schema = BuildInfoSchema()

    build_data, validation_errors = build_schema.dump(
        BuildInfo.from_resource(connexion.request.json, build_id)
    )

    # store in Ceph
    build_data["build_log"] = None
    build_aggregator.store_build_data(build_data)

    return request_accepted(errors=validation_errors)


def put_build_completed_resource(build_id: str = None):
    """Trigger build completion hook."""
    log_level: int = connexion.request.args.get("log_level", DEFAULT_OC_LOG_LEVEL)

    build_data: dict = connexion.request.json
    validation_errors = _on_build_completed(
        build_id,
        build_data,
        get_build_log=connexion.request.args.get("mode", "remote") == "cluster",
        log_level=log_level,
    )

    return request_accepted(errors=validation_errors)


def put_build_completed_event_resource(self, build_id: str = None):  # pragma: no cover
    """Trigger build completion hook."""
    log_level: int = connexion.request.args.get("log_level", DEFAULT_OC_LOG_LEVEL)

    build_schema = BuildInfoSchema()

    kube_client = ApiClient()

    event: V1Event = kube_client.deserialize(request, response_type="V1Event")
    build_data, _ = build_schema.dump(BuildInfo.from_event(event, build_id))

    # TODO: handle validation errors
    validation_errors = _on_build_completed(
        build_id,
        build_data,
        get_build_log=connexion.request.args.get("mode", "remote") == "cluster",
        log_level=log_level,
    )

    return request_accepted(errors=validation_errors)


def put_build_completed_thoth_resource(build_id: str = None):  # pragma: no cover
    """Trigger build completion hook."""
    log_level: int = connexion.request.args.get("log_level", DEFAULT_OC_LOG_LEVEL)
    build_schema = BuildInfoSchema()
    build_data, _ = build_schema.dump(
        BuildInfo.from_resource(connexion.request.json, build_id)
    )
    validation_errors = _on_build_completed(
        build_id,
        build_data,
        get_build_log=connexion.request.args.get("mode", "remote") == "cluster",
        log_level=log_level,
    )

    return {"status": True}, 200, {"x-thoth-osiris-api-version": __version__}


def _on_build_completed(
    build_id: str,
    build_data: dict,
    get_build_log=False,
    log_level: int = DEFAULT_OC_LOG_LEVEL,
):
    """Update Ceph build data.

    :returns: validation errors produced by BuildInfoSchema schema validation.
    """
    build_schema = BuildInfoSchema()

    _LOGGER.info("Build schema %s", build_schema)

    build_info: BuildInfo
    build_data.update({"build_id": build_id})

    _LOGGER.info("Build data: %s, build id: %s", build_data, build_id)

    build_info = build_schema.load(build_data).data
    build_info.build_log_url = url_for(
        "/api/v1.thoth_osiris_api_v1_get_build_log_resource",
        build_id=build_id,
        _external=True,
    )
    build_doc, validation_errors = build_schema.dump(build_info)
    if get_build_log:
        # get build log from relevant pod (requires OpenShift authentication)
        build_log: str = build_aggregator.get_build_log(
            build_id, namespace=build_info.ocp_info.namespace, log_level=log_level
        )

        build_doc["build_log"] = build_log
    build_aggregator.store_build_data(build_doc)

    return validation_errors
