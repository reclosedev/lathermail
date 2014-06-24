lathermail
==========

SMTP Server with API for email testing inspired by `mailtrap <https://mailtrap.io/>`_ and
`maildump <https://github.com/ThiefMaster/maildump>`_

Requires MongoDB.


Usage::

    $ git clone ...
    $ cd lathermail
    $ virtualenv venv
    $ . venv/bin/activate
    $ python setup.py develop
    $ lathermail --help

    usage: lathermail [-h] [--api-host API_HOST] [--api-port API_PORT]
                      [--smtp-host SMTP_HOST] [--smtp-port SMTP_PORT]

    optional arguments:
      -h, --help            show this help message and exit
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

* `X-Mail-Inbox` - same as SMTP user
* `X-Mail-Password` - same as SMTP password

**GET /api/0/<message_id>**

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
                    "body": "you you \u043f\u0440\u0438\u0432\u0435\u0442 2",
                    "is_attachment": false,
                    "charset": "utf-8",
                    "filename": null,
                    "type": "text/plain",
                    "size": 16
                },
                {
                    "body": "file content",
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

**GET /api/0/**

Returns messages according to optional filters:

* `sender.name` - Name of sender
* `sender.address` - Email of sender
* `recipients.name` - Name of any of recipients
* `recipients.address` - Email of any of recipients
* `subject` - Message subject
* `subject_contains` - Any part of message subject
* `created_at_lt` - Filter messages created before this ISO formatted datetime
* `created_at_gt` - Filter messages created after this ISO formatted datetime
* `read` - Return only read emails when `True` or unread when `False`. All emails returned by default

Example::

    {
        "message_count": 3,
        "message_list": [
            {"_id": ..., "parts": [...], ...},  // same as single message
            {...},
            {...}
        ]
    }

**DELETE /api/0/<message_id>**

Deletes single message

**DELETE /api/0/**

Deletes all messages in inbox. Also, you can filter deletable messages like in **GET /api/0/**


Configuration
-------------
Copy lathermail.conf.example, modify it, export environment variable before starting::

    $ export LATHERMAIL_SETTINGS=/path/to/lathermail.conf
    $ lathermail


To run tests::

    $ python -m tests
