# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import Blueprint, Response, request
from flask.ext import restful
from flask.ext.restful import Resource

from . import db
from .validators import parser
from .representations import output_json, content_disposition


api_bp = Blueprint("api", __name__)
api = restful.Api(app=api_bp, prefix="/api/0")
api.representations.update({"application/json": output_json})


class MessageList(Resource):
    def get(self):
        args = parser.parse_args()
        messages = list(db.engine.find_messages(args.password, args.inbox, args))
        return {'message_list': messages, 'message_count': len(messages)}

    def delete(self):
        args = parser.parse_args()
        db.engine.remove_messages(args.password, args.inbox, args)
        return '', 204


class Message(Resource):
    def get(self, message_id):
        args = parser.parse_args()
        args["_id"] = message_id
        messages = list(db.engine.find_messages(args.password, args.inbox, args, limit=1))
        if not messages:
            return {"error": "Message not found"}, 404
        return {"message_info": messages[0]}

    def delete(self, message_id):
        args = parser.parse_args()
        args["_id"] = message_id
        if db.engine.remove_messages(args.password, args.inbox, args):
            return '', 204
        return {"error": "Message not found"}, 404


class Attachment(Resource):
    def get(self, message_id, attachment_index):
        args = {"_id": message_id}
        messages = list(db.engine.find_messages(None, fields=args, limit=1, include_attachment_bodies=True))
        if not messages:
            return {"error": "Message not found"}, 404

        try:
            part = messages[0]["parts"][attachment_index]
        except IndexError:
            pass
        else:
            if part["filename"]:
                return Response(
                    part["body"], mimetype=part["type"],
                    headers={"Content-Disposition": content_disposition(part["filename"],
                                                                        request.environ.get('HTTP_USER_AGENT'))}
                )

        return {"error": "Attachment not found"}, 404


class InboxList(Resource):
    def get(self):
        args = parser.parse_args()
        inboxes = db.engine.get_inboxes(args.password)
        return {'inbox_list': inboxes, 'inbox_count': len(inboxes)}


api.add_resource(MessageList, '/messages/')
api.add_resource(Message, '/messages/<ObjectId:message_id>')
api.add_resource(Attachment, '/messages/<ObjectId:message_id>/attachments/<int:attachment_index>')
api.add_resource(InboxList, '/inboxes/')
