import json
import datetime

from flask import make_response
from bson import Timestamp, ObjectId


def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data, indent=4, cls=MongoEncoder), code)
    resp.headers.extend(headers or {})
    return resp


class MongoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, Timestamp):
            return "Timestamp({}, {})".format(obj.as_datetime().isoformat(), obj.inc)
        elif isinstance(obj, ObjectId):
            return str(obj)
        elif hasattr(obj, "to_json"):
            return obj.to_json()
        else:
            return super(MongoEncoder, self).default(obj)
