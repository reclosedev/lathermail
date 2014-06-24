# -*- coding: utf-8 -*-
from flask import Blueprint
from flask.ext import restful
from flask.ext.restful import Resource

from .db import find_messages, remove_messages
from .validators import parser
from .representations import output_json

api_bp = Blueprint("api", __name__)
api = restful.Api(app=api_bp, prefix="/api/0")
api.representations.update({"application/json": output_json})


class MessageList(Resource):
    def get(self):
        args = parser.parse_args()
        messages = list(find_messages(args.password, args.inbox, args))
        return {'message_list': messages, 'message_count': len(messages)}

    def delete(self):
        args = parser.parse_args()
        remove_messages(args.password, args.inbox, args)
        return '', 204


class Message(Resource):
    def get(self, message_id):
        args = parser.parse_args()
        args["_id"] = message_id
        messages = list(find_messages(args.password, args.inbox, args, limit=1))
        if not messages:
            return {"error": "Message not found"}, 404
        return {"message_info": messages[0]}

    def delete(self, message_id):
        args = parser.parse_args()
        args["_id"] = message_id
        if remove_messages(args.password, args.inbox, args):
            return '', 204
        return {"error": "Message not found"}, 404


api.add_resource(MessageList, '/')
api.add_resource(Message, '/<ObjectId:message_id>')
