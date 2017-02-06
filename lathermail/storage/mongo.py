#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import logging

from flask.ext.pymongo import PyMongo, DESCENDING

from . import ALLOWED_QUERY_FIELDS, SUFFIX_CONTAINS
from .. import app
from ..mail import convert_message_to_dict, expand_message_fields
from ..utils import utcnow


log = logging.getLogger(__name__)
mongo = PyMongo()


def init_app_for_db(application):
    mongo.init_app(application)


def switch_db(name):
    """ Hack to switch Flask-Pymongo db
    :param name: db name
    """
    with app.app_context():
        app.extensions['pymongo'][mongo.config_prefix] = mongo.cx, mongo.cx[name]


def message_handler(*args, **kwargs):
    msg = convert_message_to_dict(*args, **kwargs)
    msg["created_at"] = utcnow()
    with app.app_context():
        mongo.db.messages.insert(msg)


def find_messages(password, inbox=None, fields=None, limit=0, include_attachment_bodies=False):
    messages = list(_iter_messages(password, inbox, fields, limit, include_attachment_bodies))
    if messages:
        ids = [m["_id"] for m in messages]
        mongo.db.messages.update({"_id": {"$in": ids}, "read": False},
                                 {"$set": {"read": True}}, multi=True)
    return messages


def _iter_messages(password, inbox=None, fields=None, limit=0, include_attachment_bodies=False):
    query = _prepare_query(password, inbox, fields)
    for message in mongo.db.messages.find(query).sort("created_at", DESCENDING).limit(limit):
        yield expand_message_fields(message, include_attachment_bodies)


def remove_messages(password, inbox=None, fields=None):
    query = _prepare_query(password, inbox, fields)
    return mongo.db.messages.remove(query)["n"]


def get_inboxes(password):
    return mongo.db.messages.find({"password": password}).distinct("inbox")


def _prepare_query(password, inbox=None, fields=None):
    query = {}
    if password is not None:
        query["password"] = password
    if inbox is not None:
        query["inbox"] = inbox

    if fields:
        for field, value in fields.items():
            if field in ALLOWED_QUERY_FIELDS and value is not None:
                if field.endswith(SUFFIX_CONTAINS):
                    field = field[:-len(SUFFIX_CONTAINS)]
                    query[field] = {"$regex": re.escape(value)}
                else:
                    query[field] = value

        if fields.get("created_at_gt") is not None:
            query["created_at"] = {"$gt": fields["created_at_gt"]}
        if fields.get("created_at_lt") is not None:
            query["created_at"] = {"$lt": fields["created_at_lt"]}
        if fields.get("subject_contains"):
            query["subject"] = {"$regex": re.escape(fields["subject_contains"])}

    return query


@app.before_first_request
def _ensure_index():
    log.info("Ensuring DB has indexes")
    for field in list(ALLOWED_QUERY_FIELDS) + ["created_at"]:
        mongo.db.messages.ensure_index(field)


def drop_database(name):
    mongo.cx.drop_database(name)
