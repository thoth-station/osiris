# Osiris: Build log aggregator.


"""Flask API models."""

from flask_restplus import fields
from flask_restplus.model import Model


status = Model('status', {
    'code': fields.Integer,
    'phrase': fields.String,
    'description': fields.String,
    'message': fields.String
})


app_data = Model('app_data', {
    'name': fields.String,
    'version': fields.String,
})


response = Model('response', {
    'app_data': fields.Nested(app_data, attribute='data.app_data'),
    'status': fields.Nested(status, attribute='data.status'),

    'output': fields.Raw,
    'errors': fields.Raw,

    'payload': fields.Raw(attribute='data.payload'),
})
