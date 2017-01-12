#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import email
from email.header import decode_header
from email.utils import getaddresses

from .compat import bytes, IS_PY3, unicode


def convert_addresses(raw_header):
    result = []
    name_addr_pairs = getaddresses([raw_header])
    for name, addr in name_addr_pairs:

        result.append({"name": _header_to_unicode(name), "address": addr})
    return result


def convert_message_to_dict(to, sender, message, body, user, password):
    from_addr = message.get("From") or sender
    to = message.get("To") or ",".join(to)
    subject = message.get("Subject") or ""

    result = {
        "inbox": user,
        "password": password,
        "message_raw": bytes(body, "utf8"),
        "sender_raw": from_addr,
        "recipients_raw": to,
        # for easy searching
        "sender": convert_addresses(from_addr)[0],
        "recipients": convert_addresses(to),
        "subject": _header_to_unicode(subject),
        "read": False,
    }
    return result


def expand_message_fields(message_info, include_attachment_bodies=False):
    raw = message_info["message_raw"]
    if IS_PY3:
        raw = raw.decode("utf8")
    message = email.message_from_string(raw)
    message_info["parts"] = list(_iter_parts(message, include_attachment_bodies))
    return message_info


def _iter_parts(message, include_attachment_bodies):
    parts = [message] if not message.is_multipart() else message.walk()

    index = 0
    for part in parts:
        filename = part.get_filename() or part.get("content-id")
        is_attachment = filename is not None
        if not include_attachment_bodies and is_attachment:
            body = None
        else:
            body = part.get_payload(decode=True)
        if not is_attachment and not body:
            continue

        charset = part.get_content_charset()
        if charset:
            try:
                body = body.decode(charset)
            except Exception:
                pass

        yield {
            "index": index,
            "type": part.get_content_type(),
            "is_attachment": is_attachment,
            "filename": _header_to_unicode(filename) if filename else None,
            "charset": charset,
            "body": body,
            "size": len(body) if body else 0
        }
        index += 1


def _header_to_unicode(header):
    data, encoding = decode_header(header)[0]
    if encoding:
        data = data.decode(encoding)
    return data
