# -*- coding: utf-8 -*-
import dateutil.parser

from flask.ext.restful import reqparse, types

from lathermail.compat import unicode
from lathermail.storage import TEXT_FIELDS, SUFFIX_CONTAINS


def iso_date(value):
    return dateutil.parser.parse(value)


parser = reqparse.RequestParser()
parser.add_argument('X-Mail-Inbox', type=unicode, dest="inbox", location="headers")
parser.add_argument('X-Mail-Password', type=unicode, dest="password", location="headers", required=True)
for field in TEXT_FIELDS:
    parser.add_argument(field, type=unicode)
    parser.add_argument(field + SUFFIX_CONTAINS, type=unicode)
parser.add_argument("created_at_lt", type=iso_date)
parser.add_argument("created_at_gt", type=iso_date)
parser.add_argument("read", type=types.boolean)
