#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import datetime
import logging

from flask.ext.pymongo import PyMongo, DESCENDING

from . import app
from .mail import convert_message_to_dict, expand_message_fields

log = logging.getLogger(__name__)
mongo = PyMongo(app)


def switch_db(name):
    """ Hack to switch Flask-Pymongo db
    :param name: db name
    """
    with app.app_context():
        app.extensions['pymongo'][mongo.config_prefix] = mongo.cx, mongo.cx[name]


def message_handler(*args, **kwargs):
    msg = convert_message_to_dict(*args, **kwargs)
    msg["created_at"] = datetime.datetime.now()
    with app.app_context():
        mongo.db.messages.insert(msg)


def find_messages(password, inbox=None, fields=None, limit=0):
    messages = list(_iter_messages(password, inbox, fields, limit))
    if messages:
        ids = [m["_id"] for m in messages]
        mongo.db.messages.update({"_id": {"$in": ids}, "read": False},
                                 {"$set": {"read": True}}, multi=True)
    return messages


def _iter_messages(password, inbox=None, fields=None, limit=0):
    query = _prepare_query(password, inbox, fields)
    for message in mongo.db.messages.find(query).sort("created_at", DESCENDING).limit(limit):
        yield expand_message_fields(message)


def remove_messages(password, inbox=None, fields=None):
    query = _prepare_query(password, inbox, fields)
    return mongo.db.messages.remove(query)["n"]


_allowed_query_fields = {
    "_id", "recipients.name", "recipients.address",
    "sender.name", "sender.address", "subject", "read",
}


def _prepare_query(password, inbox=None, fields=None):
    query = {}
    if fields:
        for field, value in fields.items():
            if field in _allowed_query_fields and value is not None:
                query[field] = value

    query["password"] = password
    if inbox:
        query["inbox"] = inbox
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
    for field in list(_allowed_query_fields) + ["created_at"]:
        mongo.db.messages.ensure_index(field)
