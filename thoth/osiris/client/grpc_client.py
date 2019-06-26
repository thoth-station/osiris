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

"""Thoth Osiris gRPC client."""

import os

from concurrent import futures
import time
import math
import logging

import grpc


import opentracing
from jaeger_client import Config as JaegerConfig
from jaeger_client.metrics.prometheus import PrometheusMetricsFactory
from jaeger_client import Config

from grpc_opentracing import open_tracing_server_interceptor
from grpc_opentracing.grpcext import intercept_server

from thoth.common import init_logging

from thoth.osiris import __version__
from thoth.osiris.configuration import Configuration, init_jaeger_tracer

import thoth.osiris.osiris_pb2 as osiris_pb2
import thoth.osiris.osiris_pb2_grpc as osiris_pb2_grpc


# Configure global application logging using Thoth's init_logging.
init_logging(logging_env_var_start="OSIRIS_LOG_")

_LOGGER = logging.getLogger("osiris")
_LOGGER.setLevel(logging.DEBUG if bool(int(os.getenv("OSIRIS_DEBUG", 0))) else logging.INFO)

_LOGGER.info(f"This is Osiris gRPC client v{__version__}")
_LOGGER.debug("DEBUG mode is enabled!")


def main():
    # read in certificate
    # TODO: Find out the certificates
    with open("server.crt", "rb") as f:
        trusted_certs = f.read()

    # create credentials
    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)

    # TODO: Make Changes here
    with grpc.secure_channel(f"osiris-grpc-goern-thoth-dev.cloud.paas.psi.redhat.com", credentials) as channel:
        osiris = osiris_pb2_grpc.OsirisOsiris(channel)
        e = osiris_pb2.Empty()

        info = osiris.Info(e)


if __name__ == "__main__":
    main()
