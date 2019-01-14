
"""Build aggregator."""

import hashlib

from boto3.resources.factory import ServiceResource
from botocore.paginate import Paginator

from typing import Tuple, Union

from thoth.storages.result_base import ResultStorageBase

from osiris import DEFAULT_OC_LOG_LEVEL

from osiris.exceptions import OCError
from osiris.exceptions import OCAuthenticationError
from osiris.utils import execute_command

from osiris.schema.build import BuildLog
from osiris.schema.build import BuildInfo, BuildInfoSchema
from osiris.schema.build import BuildInfoPagination

# TODO: logging


class _BuildLogsAggregator(ResultStorageBase):

    RESULT_TYPE = 'build_aggregator'

    __PAGINATION_TOKEN__ = None
    __COUNT__ = 0

    def __init__(self, *args, **kwargs):

        super(_BuildLogsAggregator, self).__init__(*args, **kwargs)

    def connect(self):

        super().connect()

        # noinspection PyProtectedMember
        _BuildLogsAggregator.__COUNT__ = sum(
            1 for _ in
            self.ceph._s3.Bucket(self.ceph.bucket)  # pylint: disable=protected-access
                .objects
                .filter(Prefix=self.prefix)
                .all()
        )

    def store_build_data(self, build_doc: dict):
        """Store the build log document in Ceph."""
        blob = self.ceph.dict2blob(build_doc)
        build_id: str = build_doc['build_id']

        document_id: str = hashlib.sha256(build_id.encode('utf-8')).hexdigest()

        self.ceph.store_blob(blob, document_id)

        _BuildLogsAggregator.__COUNT__ += 1

    def retrieve_build_data(self,
                            build_id: str,
                            log_only=False) -> Union[Tuple[BuildLog, ],
                                                     Tuple[BuildLog, BuildInfo]]:
        """Retrieve build log document from Ceph by its id."""
        document_id: str = hashlib.sha256(build_id.encode('utf-8')).hexdigest()

        build_doc: dict = self.retrieve_document(document_id)
        build_log = BuildLog(raw=build_doc.pop('build_log'))

        ret: tuple = (build_log, )

        if not log_only:
            build_info, _ = BuildInfoSchema().load(build_doc)

            ret = build_log, build_info

        return ret

    def paginate_build_data(self, page: int) -> BuildInfoPagination:
        """Paginate build information stored in Ceph."""
        if page == 1:
            # reset pagination
            _BuildLogsAggregator.__PAGINATION_TOKEN__ = None

        result_list = []

        if self.__COUNT__ > 0:

            # noinspection PyProtectedMember
            resource: ServiceResource = self.ceph._s3  # pylint: disable=protected-access

            s3_client = resource.meta.client

            paginator: Paginator = s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.ceph.bucket,
                Prefix=self.ceph.prefix,
                PaginationConfig={
                    'MaxItems': BuildInfoPagination.RESULTS_PER_PAGE,
                    'StartingToken': self.__PAGINATION_TOKEN__
                }
            )

            for page in page_iterator:
                for obj in page['Contents']:
                    _, key = obj['Key'].rsplit('/', 1)

                    result_list.append(self.ceph.retrieve_document(key))

                    _BuildLogsAggregator.__PAGINATION_TOKEN__ = page_iterator.resume_token

        build_info_pagination = BuildInfoPagination(
            result_list,
            total=self.__COUNT__,
        )

        return build_info_pagination

    @staticmethod
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


build_aggregator = _BuildLogsAggregator()
build_aggregator.connect()
