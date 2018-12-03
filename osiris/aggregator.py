# Osiris: Build log aggregator.

"""Build aggregator."""

import hashlib

from thoth.storages import BuildLogsStore

from osiris import DEFAULT_OC_LOG_LEVEL
from osiris.exceptions import OCError
from osiris.utils import execute_command

# TODO: logging

ceph_store = BuildLogsStore()
ceph_store.connect()


def curl_build_log(build_id: str, log_level: int = DEFAULT_OC_LOG_LEVEL) -> str:
    """Curl OCP for build log for the given build.

    :raises OCError: In case of OC CLI failure.
    """
    log_command = f"oc logs {build_id} --loglevel {log_level}"

    out, err, ret_code = execute_command(log_command)

    if ret_code > 0:
        raise OCError(ret_code, payload=err.decode('utf-8'))

    return out.decode('utf-8')


def store_build_log(build_doc: dict) -> str:
    """Store the build log document in Ceph."""
    # TODO: logging
    blob = ceph_store.ceph.dict2blob(build_doc)
    build_id: str = build_doc['build_id']

    document_id: str = hashlib.sha256(build_id.encode('utf-8')).hexdigest()

    ceph_store.ceph.store_blob(blob, document_id)

    return document_id


def retrieve_build_log(build_id: str) -> dict:
    """Retrieve build log document from Ceph by its id."""
    # TODO: logging
    document_id: str = hashlib.sha256(build_id).hexdigest()

    return ceph_store.retrieve_document(document_id)
