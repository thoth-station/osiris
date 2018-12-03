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


response = Model('response', {
    'name': fields.String,
    'version': fields.String,
    'status': fields.Nested(status),

    'output': fields.Raw,
    'errors': fields.Raw,

    'payload': fields.Raw,
})
