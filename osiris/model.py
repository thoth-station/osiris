# Osiris: Build log aggregator.


"""Flask API models."""

from http import HTTPStatus

from flask_restplus import fields
from flask_restplus.model import Model

from osiris import ABOUT
from osiris.utils import format_status_message


BUILD_STATUS_ALLOWED = {
    'UNKNOWN', 'INITIATED', 'STARTED', 'COMPLETED'
}


class HTTPStatusField(fields.Raw):

    __schema_type__ = 'dict'

    def __init__(self):
        example_status = HTTPStatus.OK

        super(HTTPStatusField, self).__init__(
            title="HTTPStatusField",
            description="Nested HTTPStatus field.",
            example={
                'code': example_status.value,
                'phrase': example_status.phrase,
                'description': example_status.description,
                'message': format_status_message(example_status)
            },
            required=True
        )

    def format(self, status: HTTPStatus):
        try:
            nested_field = {
                'code': status.value,
                'phrase': status.phrase,
                'description': status.description,
                'message': format_status_message(status)
            }
        except ValueError as e:
            msg = "Unable to marshal field HTTPStatusField with" \
                  "'{value}': {exc}"
            msg.format(value=status, exc=str(e))

            raise fields.MarshallingError(msg)

        return nested_field


class BuildInfoField(fields.Raw):

    __schema_type__ = 'dict'

    def __init__(self):

        super(BuildInfoField, self).__init__(
            title="BuildInfoField",
            description="Nested Build Information field.",
            example={
            },
            required=True
        )

    def format(self, status: HTTPStatus):
        try:
            nested_field = {
                'code': status.value,
                'phrase': status.phrase,
                'description': status.description,
                'message': format_status_message(status)
            }
        except ValueError as e:
            msg = "Unable to marshal field {field} with" \
                  "'{value}': {exc}"
            msg.format(
                field=self.__name__,
                value=status,
                exc=str(e))

            raise fields.MarshallingError(msg)

        return nested_field


class BuildStatusField(fields.Raw):

    __schema_type__ = 'string'

    def format(self, build_status: str):

        build_status = build_status.upper()

        if build_status not in BUILD_STATUS_ALLOWED:

            msg = "Unable to marshal field {field} with" \
                  "'{value}': {exc}"
            msg.format(
                field=self.__name__,
                value=build_status,
                exc="Invalid value of `build_status`")

            raise fields.MarshallingError(msg)

        return build_status


base_model = Model('base', {
    'name': fields.String(default=ABOUT['__title__']),
    'version': fields.String(default=ABOUT['__version__']),
    'status': HTTPStatusField
})


build_status_model = Model.inherit('build_status', base_model, {
    'build_id': fields.Integer(required=True),
    'build_status': BuildStatusField(required=True)
})


build_info_model = Model.inherit('build_info', build_status_model, {
    'build_info': BuildInfoField
})

