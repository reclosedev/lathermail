#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function

import uuid
import logging

from sqlalchemy import event
from werkzeug.routing import UnicodeConverter
from flask.ext.sqlalchemy import SQLAlchemy

from . import ALLOWED_QUERY_FIELDS, SUFFIX_CONTAINS
from .. import app
from ..mail import convert_message_to_dict, expand_message_fields
from ..utils import utcnow, as_utc


log = logging.getLogger(__name__)
db = SQLAlchemy(app)


class Message(db.Model):
    __tablename__ = 'messages'
    _id = db.Column(db.String, primary_key=True)
    inbox = db.Column(db.String, index=True)
    password = db.Column(db.String, index=True)
    message_raw = db.Column(db.Binary)
    sender_raw = db.Column(db.String)
    recipients_raw = db.Column(db.String)
    subject = db.Column(db.String, index=True)
    sender_name = db.Column(db.String, index=True)
    sender_address = db.Column(db.String, index=True)
    created_at = db.Column(db.DateTime(), index=True)
    read = db.Column(db.Boolean)


class Recipient(db.Model):
    __tablename__ = 'recipients'
    name = db.Column(db.String, primary_key=True, index=True)
    address = db.Column(db.String, primary_key=True, index=True)
    message_id = db.Column(db.String, db.ForeignKey('messages._id', ondelete="CASCADE"), primary_key=True, index=True)
    message = db.relationship("Message", backref="recipients")


_message_fields = [column.name for column in Message.__table__.columns]


def init_app_for_db(application):
    if app.config.get("DEBUG_MODE"):
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    db.init_app(application)
    application.url_map.converters['ObjectId'] = UnicodeConverter

    if application.config["DB_URI"].startswith("sqlite"):
        @event.listens_for(db.engine, "connect")
        def _on_engine_connect(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            if application.config.get("SQLITE_FAST_SAVE"):
                cursor.execute("PRAGMA synchronous = 0")
            cursor.close()

    _create_tables()


def message_handler(*args, **kwargs):
    msg = convert_message_to_dict(*args, **kwargs)
    msg["_id"] = str(uuid.uuid4())
    msg["created_at"] = utcnow()
    sender = msg.pop("sender")
    msg["sender_name"] = sender["name"]
    msg["sender_address"] = sender["address"]
    recipients = msg.pop("recipients")

    with app.app_context():
        try:
            message = Message(**msg)
            message.recipients = [Recipient(name=rcp["name"], address=rcp["address"]) for rcp in recipients]
            db.session.add(message)
            db.session.commit()
        except Exception:
            import traceback
            traceback.print_exc()  # TODO


def get_inboxes(password):
    rows = db.session.query(Message.inbox).distinct(Message.inbox).filter_by(password=password)
    return [row.inbox for row in rows]


def find_messages(password, inbox=None, fields=None, limit=0, include_attachment_bodies=False):
    messages = list(_iter_messages(password, inbox, fields, limit, include_attachment_bodies))
    if messages:
        ids = (m["_id"] for m in messages)
        Message.query.filter(Message._id.in_(ids)).update({Message.read: True}, synchronize_session=False)
        db.session.commit()
    return messages


def remove_messages(password, inbox=None, fields=None):
    message_ids_query = _prepare_sql_query(
        password, inbox, fields,
        order=False, to_select=Message._id, load_recipients=False
    )
    count = Message.query.filter(Message._id.in_(message_ids_query)).delete(False)
    db.session.commit()
    return count


def _iter_messages(password, inbox=None, fields=None, limit=0, include_attachment_bodies=False):
    query = _prepare_sql_query(password, inbox, fields, limit=limit)
    for message in query.all():
        message = _convert_sa_message_to_dict(message)
        yield expand_message_fields(message, include_attachment_bodies)


def _convert_sa_message_to_dict(message):
    result = dict((name, getattr(message, name)) for name in _message_fields)
    result["recipients"] = [{"name": rcpt.name, "address": rcpt.address} for rcpt in message.recipients]
    result["sender"] = {"name": result.pop("sender_name"), "address": result.pop("sender_address")}
    result["created_at"] = as_utc(result["created_at"])
    return result


def _prepare_sql_query(password, inbox=None, fields=None, limit=0, order=True, to_select=Message, load_recipients=True):
    filters = []
    if password is not None:
        filters.append(Message.password == password)
    if inbox is not None:
        filters.append(Message.inbox == inbox)

    if fields:
        for field, value in fields.items():
            if field in ALLOWED_QUERY_FIELDS and value is not None:
                is_contains = False
                if field.endswith(SUFFIX_CONTAINS):
                    is_contains = True
                    field = field[:-len(SUFFIX_CONTAINS)]

                if field.startswith("recipients."):
                    sub_field = field.rsplit(".", 1)[1]
                    attr = getattr(Recipient, sub_field)
                else:
                    attr = getattr(Message, field.replace(".", "_"))
                if is_contains:
                    filters.append(attr.contains(value))
                else:
                    filters.append(attr == value)

        if fields.get("created_at_gt") is not None:
            filters.append(Message.created_at > fields["created_at_gt"])
        if fields.get("created_at_lt") is not None:
            filters.append(Message.created_at < fields["created_at_lt"])

    query = db.session.query(to_select).join(Recipient).filter(db.and_(*filters))
    if load_recipients:
        query = query.options(db.contains_eager(Message.recipients))
    if order:
        query = query.order_by(Message.created_at.desc())
    if limit:
        query = query.limit(limit)
    return query


def drop_database(name):
    db.drop_all()


@app.before_first_request
def _init():
    _create_tables()


def switch_db(name):
    _create_tables()


def _create_tables():
    log.info("Ensuring DB has tables and indexes")
    db.create_all()
