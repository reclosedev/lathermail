# -*- coding: utf-8 -*-
import dateutil.parser

from flask.ext.restful import reqparse, types

from lathermail.compat import unicode


def iso_date(value):
    return dateutil.parser.parse(value)


parser = reqparse.RequestParser()
parser.add_argument('X-Mail-Inbox', type=unicode, dest="inbox", location="headers")
parser.add_argument('X-Mail-Password', type=unicode, dest="password", location="headers", required=True)
parser.add_argument("sender.name", type=unicode)
parser.add_argument("sender.address", type=unicode)
parser.add_argument("recipients.name", type=unicode)
parser.add_argument("recipients.address", type=unicode)
parser.add_argument("subject", type=unicode)
parser.add_argument("subject_contains", type=unicode)
parser.add_argument("created_at_lt", type=iso_date)
parser.add_argument("created_at_gt", type=iso_date)
parser.add_argument("read", type=types.boolean)
