import re
import json
import datetime
from urllib import quote

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


def content_disposition(filename, user_agent=None):
    filename = filename.encode("utf-8")
    older_msie_pattern = r"^.*MSIE ([0-8]{1,}[\.0-9]{0,}).*$"
    safari_pattern = r"^.*AppleWebKit.*$"
    user_agent = user_agent or ""

    if re.match(older_msie_pattern, user_agent, re.IGNORECASE):
        return "attachment;filename={0}".format(quote(filename))
    elif re.match(safari_pattern, user_agent, re.IGNORECASE):
        return "attachment;filename={0}".format(filename)
    return "attachment;filename*=utf-8''{0}".format(quote(filename))
