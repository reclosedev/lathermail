.. image:: https://travis-ci.org/reclosedev/lathermail.svg?branch=master
    :target: https://travis-ci.org/reclosedev/lathermail

.. image:: https://coveralls.io/repos/reclosedev/lathermail/badge.svg?branch=master&service=github
    :target: https://coveralls.io/github/reclosedev/lathermail?branch=master

lathermail
==========

SMTP Server with API for email testing inspired by `mailtrap <https://mailtrap.io/>`_ and
`maildump <https://github.com/ThiefMaster/maildump>`_

Can store messages in MongoDB or any SQLAlchemy supported DB (e.g., sqlite). Supports Python 2.7, 3.4, 3.5, pypy.



Usage::

    $ virtualenv venv  # or mkvirutalenv lathermail
    $ . venv/bin/activate
    $ pip install lathermail
    $ lathermail --help

    usage: lathermail [-h] [--db-uri DB_URI] [--api-host API_HOST]
                      [--api-port API_PORT] [--smtp-host SMTP_HOST]
                      [--smtp-port SMTP_PORT]

    optional arguments:
      -h, --help            show this help message and exit
      --db-uri DB_URI       DB URI, e.g. mongodb://localhost/lathermail,
                            sqlite:////tmp/my.db (default:
                            sqlite:///~/.lathermail.db)
      --api-host API_HOST   API Host (default: 127.0.0.1)
      --api-port API_PORT   API port (default: 5000)
      --smtp-host SMTP_HOST
                            SMTP host (default: 127.0.0.1)
      --smtp-port SMTP_PORT
                            SMTP port (default: 2525)


It will start SMTP server and API server in single process.

Inboxes are identified by SMTP user/password pairs. lathermail intended to be used in single project environment.

To send email, just use SMTP client with auth support.


API
---

To request API, you must provide headers:

* ``X-Mail-Password`` - same as SMTP password
* ``X-Mail-Inbox`` - same as SMTP user. Optional, work with all inboxes if not specified

**GET /api/0/inboxes/**

Returns list of inboxes for passed ``X-Mail-Password``::

    {
        "inbox_list": [
            "first",
            "second",
            "third"
        ],
        "inbox_count": 3
    }


**GET /api/0/messages/<message_id>**

Returns single message. Example::

    {
        "message_info": {
            "message_raw": "Content-Type: multipart/mixed; boundary=\"===============3928630509694630745==...",
            "password": "password",
            "sender": {
                "name": "Me",
                "address": "asdf@exmapl.com"
            },
            "recipients": [
                {
                    "name": "Rcpt1",
                    "address": "rcpt1@example.com"
                },
                {
                    "name": "Rcpt2",
                    "address": "rcpt2@example.com"
                },
                {
                    "name": "",
                    "address": "rcpt3@example.com"
                }
            ],
            "recipients_raw": "=?utf-8?q?Rcpt1?= <rcpt1@example.com>,\n =?utf-8?q?Rcpt2?= <rcpt2@example.com>, rcpt3@example.com",
            "created_at": "2014-06-24T15:28:35.045000+00:00",
            "sender_raw": "Me <asdf@exmapl.com>",
            "parts": [
                {
                    "index": 0,
                    "body": "you you \u043f\u0440\u0438\u0432\u0435\u0442 2",
                    "is_attachment": false,
                    "charset": "utf-8",
                    "filename": null,
                    "type": "text/plain",
                    "size": 16
                },
                {
                    "index": 1,
                    "body": null,
                    "is_attachment": true,
                    "charset": null,
                    "filename": "t\u0430\u0441\u0434est.txt",
                    "type": "application/octet-stream",
                    "size": 12
                }
            ],
            "inbox": "inbox",
            "_id": "53a960e3312f9156b7c92c5b",
            "subject": "Test subject \u0445\u044d\u043b\u043b\u043e\u0443 2",
            "read": false
        }
    }

Attachments in message have ``body`` = null. To download file, use following method.


**GET /api/0/messages/<message_id>/attachments/<attachment_index>**

Returns file from message. Works in browsers.


**GET /api/0/messages/**

Returns messages according to optional filters:

* ``sender.name`` - Name of sender
* ``sender.address`` - Email of sender
* ``recipients.name`` - Name of any of recipients
* ``recipients.address`` - Email of any of recipients
* ``subject`` - Message subject
* Add ``_contains`` suffix to any field above to search substring match,
  e.g.: ``subject_contains``, ``recipients.address_contains``
* ``created_at_lt`` - Filter messages created before this ISO formatted datetime
* ``created_at_gt`` - Filter messages created after this ISO formatted datetime
* ``read`` - Return only read emails when `True` or unread when `False`. All emails returned by default

Example::

    {
        "message_count": 3,
        "message_list": [
            {"_id": ..., "parts": [...], ...},  // same as single message
            {...},
            {...}
        ]
    }

**DELETE /api/0/messages/<message_id>**

Deletes single message

**DELETE /api/0/messages/**

Deletes all messages in inbox. Also, you can filter deletable messages like in **GET /api/0/**


Configuration
-------------
Copy lathermail.conf.example, modify it, export environment variable before starting::

    $ export LATHERMAIL_SETTINGS=/path/to/lathermail.conf
    $ lathermail


To run tests::

    $ python -m tests
