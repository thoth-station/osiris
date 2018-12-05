# Osiris: Build log aggregator.

"""Build aggregator."""

import hashlib

from typing import Tuple, Union

from thoth.storages import BuildLogsStore

from osiris import DEFAULT_OC_LOG_LEVEL

from osiris.exceptions import OCError
from osiris.exceptions import OCAuthenticationError
from osiris.utils import execute_command

from osiris.schema.build import BuildLog
from osiris.schema.build import BuildInfo

# TODO: logging

build_store = BuildLogsStore()
build_store.connect()


def curl_build_log(build_id: str, log_level: int = DEFAULT_OC_LOG_LEVEL) -> str:
    """Curl OCP for build log for the given build.

    :raises OCError: In case of OC CLI failure.
    """

    out, err, ret_code = execute_command("oc whoami")

    if ret_code > 0:
        raise OCAuthenticationError(
            payload=err.decode('utf-8')
        )

    log_command = f"oc logs {build_id} --loglevel {log_level}"

    out, err, ret_code = execute_command(log_command)

    if ret_code > 0:
        raise OCError(ret_code, payload=err.decode('utf-8'))

    return out.decode('utf-8')


def store_build_log(build_doc: dict) -> str:
    """Store the build log document in Ceph."""
    # TODO: logging
    blob = build_store.ceph.dict2blob(build_doc)
    build_id: str = build_doc['build_id']

    document_id: str = hashlib.sha256(build_id.encode('utf-8')).hexdigest()

    build_store.ceph.store_blob(blob, document_id)

    return document_id


def retrieve_build_log(build_id: str,
                       log_only=False) -> Union[Tuple[BuildLog, ],
                                                Tuple[BuildLog, BuildInfo]]:
    """Retrieve build log document from Ceph by its id."""
    # TODO: logging
    document_id: str = hashlib.sha256(build_id.encode('utf-8')).hexdigest()

    build_doc: dict = build_store.retrieve_document(document_id)
    build_log = BuildLog(raw=build_doc.pop('build_log'))

    ret: tuple = (build_log, )

    if not log_only:
        build_info = BuildInfo(**build_doc)

        ret = build_log, build_info

    return ret
