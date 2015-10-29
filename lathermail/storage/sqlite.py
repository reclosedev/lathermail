#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import uuid
import logging
import sqlite3

from werkzeug.routing import UnicodeConverter

from .. import app
from ..mail import convert_message_to_dict, expand_message_fields
from ..utils import utcnow


log = logging.getLogger(__name__)
db_path = "/tmp/tst.db"


@app.before_first_request
def create_tables():
    _create_tables()


def _create_tables():
    log.info("Ensuring DB has tables and indexes")

    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS `messages` (
      _id,
      inbox,
      password,
      message_raw,
      sender_raw,
      recipients_raw,
      subject,
      sender_name,
      sender_address,
      created_at date,
      `read` BOOLEAN
    );

    CREATE TABLE IF NOT EXISTS recipients (
      message_id REFERENCES messages (_id),
      name text,
      address text
    );
    """)
    # TODO indexes


def init_app_for_db(application):
    app.url_map.converters['ObjectId'] = UnicodeConverter
    pass


def get_db():
    con = sqlite3.connect(db_path)
    con.row_factory = dict_factory
    return con


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def switch_db(name):
    """ Hack to switch Flask-Pymongo db
    :param name: db name
    """
    _create_tables()


def message_handler(*args, **kwargs):
    msg = convert_message_to_dict(*args, **kwargs)
    msg["_id"] = str(uuid.uuid4())
    msg["created_at"] = utcnow()
    sender = msg.pop("sender")
    msg["sender_name"] = sender["name"]
    msg["sender_address"] = sender["address"]
    recipients = msg.pop("recipients")
    keys = sorted(msg.keys())
    values_str = ", ".join(":%s" % key for key in keys)

    with app.app_context():
        db = get_db()
        try:
            cur = db.cursor()
            cur.execute("INSERT INTO `messages` (%s) VALUES (%s)" % (", ".join(keys), values_str), msg)

            for rcp in recipients:
                cur.execute("INSERT into recipients (message_id, name, address) VALUES (?, ?, ?)",
                            (msg["_id"], rcp["name"], rcp["address"]))

            db.commit()
        except Exception:
            import traceback
            traceback.print_exc()  # TODO


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
    db = get_db()
    rows = db.execute("SELECT DISTINCT inbox from messages where password = ?", (password,))
    res = [row["inbox"] for row in rows]
    return res


_allowed_query_fields = {
    "_id", "recipients.name", "recipients.address",
    "sender.name", "sender.address", "subject", "read",
}


def _prepare_query(password, inbox=None, fields=None):
    query = {}
    if password is not None:
        query["password"] = password
    if inbox is not None:
        query["inbox"] = inbox

    if fields:
        for field, value in fields.items():
            if field in _allowed_query_fields and value is not None:
                query[field] = value

        if fields.get("created_at_gt") is not None:
            query["created_at"] = {"$gt": fields["created_at_gt"]}
        if fields.get("created_at_lt") is not None:
            query["created_at"] = {"$lt": fields["created_at_lt"]}
        if fields.get("subject_contains"):
            query["subject"] = {"$regex": re.escape(fields["subject_contains"])}

    return query


def drop_database(name):
    os.remove(db_path)
