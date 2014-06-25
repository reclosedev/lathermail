#!/usr/bin/env python
# -*- coding: utf-8 -*-
import email
from email.header import decode_header
from email.utils import getaddresses


def convert_addresses(raw_header):
    result = []
    name_addr_pairs = getaddresses([raw_header])
    for name, addr in name_addr_pairs:

        result.append({"name": _header_to_unicode(name), "address": addr})
    return result


def convert_message_to_dict(to, sender, message, body, user, password):
    result = {
        "inbox": user,
        "password": password,
        "message_raw": body,
        "sender_raw": message["From"],
        "recipients_raw": message["To"],
        # for easy searching
        "sender": convert_addresses(message["From"])[0],
        "recipients": convert_addresses(message["To"]),
        "subject": _header_to_unicode(message["Subject"]),
        "read": False,
    }
    return result


def expand_message_fields(message_info, include_attachment_bodies=False):
    message = email.message_from_string(message_info["message_raw"])
    message_info["parts"] = list(_iter_parts(message, include_attachment_bodies))
    return message_info


def _iter_parts(message, include_attachment_bodies):
    parts = [message] if not message.is_multipart() else message.get_payload()

    for i, part in enumerate(parts):
        filename = part.get_filename()
        is_attachment = filename is not None
        if not include_attachment_bodies and is_attachment:
            body = None
        else:
            body = part.get_payload(decode=True)
        charset = part.get_content_charset()
        if charset:
            try:
                body = body.decode(charset)
            except Exception:
                pass

        yield {
            "index": i,
            "type": part.get_content_type(),
            "is_attachment": is_attachment,
            "filename": _header_to_unicode(filename) if filename else None,
            "charset": charset,
            "body": body,
            "size": len(body) if body else 0
        }


def _header_to_unicode(header):
    data, encoding = decode_header(header)[0]
    if encoding:
        data = data.decode(encoding)
    return data
