#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TODO use SqlAlchemy
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
    CREATE TABLE IF NOT EXISTS messages (
      _id PRIMARY KEY,
      inbox,
      password,
      message_raw,
      sender_raw,
      recipients_raw,
      subject,
      sender_name,
      sender_address,
      created_at date,
      read BOOLEAN
    );

    CREATE TABLE IF NOT EXISTS recipients (
      message_id TEXT,
      name text,
      address text,
      FOREIGN KEY(message_id) REFERENCES messages(_id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS ix_password ON messages (password);
    CREATE INDEX IF NOT EXISTS ix_inbox ON messages (inbox);
    CREATE INDEX IF NOT EXISTS ix_subject ON messages (subject);
    CREATE INDEX IF NOT EXISTS ix_created_at ON messages (created_at DESC);
    CREATE INDEX IF NOT EXISTS ix_sender_address ON messages (sender_address);
    CREATE INDEX IF NOT EXISTS ix_sender_name ON messages (sender_name);

    CREATE INDEX IF NOT EXISTS ix_rcpt_name ON recipients (name);
    CREATE INDEX IF NOT EXISTS ix_rcpt_address ON recipients (address);
    CREATE INDEX IF NOT EXISTS ix_rcpt_message_id ON recipients (message_id);
    """)


def init_app_for_db(application):
    app.url_map.converters['ObjectId'] = UnicodeConverter
    pass


def get_db():
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA synchronous = 0;")  # Super speed!
    con.row_factory = dict_factory
    return con


def dict_factory(cursor, row):
    return dict((col[0], row[idx]) for idx, col in enumerate(cursor.description))


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
            cur.execute(
                # don't worry, no SQL injections here
                "INSERT INTO messages (%s) VALUES (%s)" % (", ".join(keys), values_str),
                msg
            )
            for rcp in recipients:
                cur.execute(
                    "INSERT into recipients (message_id, name, address) VALUES (?, ?, ?)",
                    (msg["_id"], rcp["name"], rcp["address"])
                )
            db.commit()
        except Exception:
            import traceback
            traceback.print_exc()  # TODO


def find_messages(password, inbox=None, fields=None, limit=0, include_attachment_bodies=False):
    db = get_db()
    messages = list(_iter_messages(password, inbox, fields, limit, include_attachment_bodies, db=db))
    if messages:
        ids = tuple(m["_id"] for m in messages)
        sql = "UPDATE messages SET `read` = 1 WHERE _id in (%s)" % ",".join(["?"] * len(ids))
        db.execute(sql, ids)
        db.commit()
    return messages


def _iter_messages(password, inbox=None, fields=None, limit=0, include_attachment_bodies=False, db=None):
    query, parameters = _prepare_sql_query(password, inbox, fields, limit=limit)
    print query, parameters
    db = db or get_db()
    last_message = None
    for message in db.execute(query, parameters):
        if last_message is None:
            last_message = message
        if message["_id"] != last_message["_id"]:
            yield expand_message_fields(last_message, include_attachment_bodies)
            last_message = message

        last_message.setdefault("recipients", []).append({"name": message["name"], "address": message["address"]})

    if last_message:
        yield expand_message_fields(last_message, include_attachment_bodies)


def remove_messages(password, inbox=None, fields=None):
    query, values = _prepare_sql_query(password, inbox, fields, order=False, to_select="_id")
    sql = "DELETE FROM messages WHERE messages._id in (%s)" % query
    db = get_db()
    cur = db.cursor()
    cur.execute(sql, values)
    db.commit()
    return cur.rowcount


def get_inboxes(password):
    db = get_db()
    rows = db.execute("SELECT DISTINCT inbox from messages where password = ?", (password,))
    return [row["inbox"] for row in rows]


_allowed_query_fields = {
    "_id", "recipients.name", "recipients.address",
    "sender.name", "sender.address", "subject", "read",
}


def _prepare_sql_query(password, inbox=None, fields=None, limit=0, order=True, to_select="*"):
    query = {}  # field: [op, value]
    if password is not None:
        query["password"] = ["=", password]
    if inbox is not None:
        query["inbox"] = ["=", inbox]

    recipients_query = {}

    if fields:
        for field, value in fields.items():
            if field in _allowed_query_fields and value is not None:
                if field.startswith("recipients."):
                    sub_field = field.rsplit(".", 1)[1]
                    recipients_query[sub_field] = value
                else:
                    query[field] = ["=", value]

        if fields.get("created_at_gt") is not None:
            query["created_at"] = [">", fields["created_at_gt"]]
        if fields.get("created_at_lt") is not None:
            query["created_at"] = ["<", fields["created_at_lt"]]
        if fields.get("subject_contains"):
            query["subject"] = ["like", u"%{0}%".format(fields["subject_contains"])]

    if "read" in query:
        query["read"][1] = int(query["read"][1])

    keys = sorted(query.keys())
    where_str = " AND ".join("%s %s ?" % (key, query[key][0]) for key in keys)
    values = [query[key][1] for key in keys]

    if recipients_query:
        recipients_keys = sorted(recipients_query.keys())
        recipients_where = " AND ".join("%s = ?" % key for key in recipients_keys)
        recipients_sql = "SELECT message_id from recipients where %s" % recipients_where
        sql = """
          SELECT %s FROM messages
          JOIN recipients ON recipients.message_id=messages._id
          WHERE messages._id in (%s) AND %s
        """ % (to_select, recipients_sql, where_str)
        values = [recipients_query[key] for key in recipients_keys] + values
    else:
        sql = """
          SELECT %s FROM messages
          JOIN recipients ON recipients.message_id=messages._id
          WHERE %s
        """ % (to_select, where_str)

    if order:
        sql += "\nORDER BY created_at DESC"
    if limit:
        sql += "\nLIMIT %s" % limit

    return sql, values


def drop_database(name):
    os.remove(db_path)
