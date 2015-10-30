# -*- coding: utf-8 -*-
import os
import tempfile
import time
import socket
import httplib
import unittest
import smtplib
import json
import urllib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate, formataddr
from email.header import Header
from email import Encoders

import lathermail
import lathermail.db


class InvalidStatus(Exception):
    def __init__(self, response):
        super(InvalidStatus, self).__init__("Invalid status {}.\n{}".format(response.status_code, response.data))
        self.response = response
        self.code = response.status_code


class SendEmailError(Exception):
    """ Exception, raised in case send is failed.
    """


class BaseTestCase(unittest.TestCase):

    inbox = "inbox"
    password = "password"
    port = 2525
    server = None
    db_name = "lathermail_test_db"
    prefix = "/api/0"
    _db_fd = None
    _db_file = None

    @classmethod
    def setUpClass(cls):
        conf = lathermail.app.config

        if os.getenv("LATHERMAIL_TEST_DB_TYPE", "sqlite") == "mongo":
            conf["DB_URI"] = conf["SQLALCHEMY_DATABASE_URI"] = "mongodb://localhost/%s" % cls.db_name
        else:
            cls._db_fd, cls._db_file = tempfile.mkstemp()
            conf["DB_URI"] = conf["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s" % cls._db_file

        lathermail.init_app()
        cls.c = lathermail.app.test_client()
        super(BaseTestCase, cls).setUpClass()
        cls.server = SmtpServerRunner(cls.db_name)
        cls.server.start(cls.port)

    @classmethod
    def tearDownClass(cls):
        super(BaseTestCase, cls).tearDownClass()
        cls.server.stop()
        if cls._db_fd is not None:
            os.close(cls._db_fd)
            os.unlink(cls._db_file)

    def setUp(self):
        lathermail.db.switch_db(self.db_name)
        super(BaseTestCase, self).setUp()

    def tearDown(self):
        from lathermail.db import drop_database

        with lathermail.app.app_context():
            drop_database(self.db_name)

    def request(self, method, url, params=None, raise_errors=True, parse_json=True, **kwargs):
        method = method.lower()
        new_kwargs = {"headers": {"X-Mail-Inbox": self.inbox, "X-Mail-Password": self.password}}
        new_kwargs.update(kwargs)
        func = getattr(self.c, method.lower())
        if params:
            params = _prepare_params(params)
            if method in ("get", "delete"):
                new_kwargs["query_string"] = urllib.urlencode(params)
            else:
                new_kwargs["data"] = params

        rv = func(self.prefix + url, **new_kwargs)
        if parse_json:
            try:
                rv.json = json.loads(rv.data)
            except ValueError as e:
                if rv.status_code != httplib.NO_CONTENT:
                    print "JSON decode error: {}, data:\n{}".format(e, rv.data)
                rv.json = None
        if raise_errors and rv.status_code >= 400:
            raise InvalidStatus(rv)
        return rv

    def get(self, url, params=None, **kwargs):
        return self.request("get", url, params, **kwargs)

    def delete(self, url, params=None, **kwargs):
        return self.request("delete", url, params, **kwargs)

    def send(self, user=None, password=None, subject="test", body="Hello"):
        smtp_send_email("test1@example.com", subject, "me@example.com", body,
                        user=user or self.inbox, password=password or self.password, port=self.port)


def _prepare_params(params):
    def convert(v):
        if isinstance(v, unicode):
            return v.encode("utf-8")
        if isinstance(v, str):
            return v
        return str(v)
    return {convert(k): convert(v) for k, v in params.iteritems()}


def prepare_send_to_field(name_email_pairs):
    return u", ".join([formataddr((str(Header(name, "utf-8")), email))
                       for name, email in name_email_pairs]).encode("utf-8")


def content_disposition(filename):
    return 'attachment; filename="{0}"'.format(Header(filename, "utf-8"))


def smtp_send_email(email, subject, from_addr, body, server_host="127.0.0.1", user=None, password=None,
                     emails=None, attachments=None, port=0):
    msg = MIMEMultipart()
    msg['To'] = email
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['Date'] = formatdate(localtime=True)
    msg.attach(MIMEText(body, _charset="utf8"))
    for name, data in attachments or []:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(data)
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', content_disposition(name))
        msg.attach(part)
    try:
        s = smtplib.SMTP(server_host, port)
        if user and password:
            s.login(user, password)
        if emails is None:
            emails = [email]
        s.sendmail(from_addr, emails, msg.as_string())
        s.quit()
        #print(u"Sent email to [%s] from [%s] with subject [%s]", email, from_addr, subject)
    except (smtplib.SMTPConnectError, smtplib.SMTPException, IOError), e:
        print(u"Sending email error to [%s] from [%s] with subject [%s]:\n%s", email, from_addr, subject, e)
        raise SendEmailError(e)


class SmtpServerRunner(object):

    def __init__(self, db_name):
        self._process = None
        self.db_name = db_name

    def start(self, port=2025):
        from lathermail.db import message_handler
        from lathermail.smtp import serve_smtp
        from multiprocessing import Process

        def wrapper(**kwargs):
            lathermail.db.switch_db(self.db_name)
            serve_smtp(**kwargs)

        p = Process(target=wrapper, kwargs=dict(handler=message_handler, port=port))
        p.daemon = True
        p.start()
        self._process = p
        self.wait_start(port)

    def stop(self):
        self._process.terminate()

    def wait_start(self, port):
        timeout = 0.1
        host_port = ("127.0.0.1", port)
        for i in range(10):
            try:
                sock = socket.create_connection(host_port, timeout=timeout)
            except Exception:
                time.sleep(timeout)
                continue
            else:
                sock.close()
                return
        raise Exception("Can't connect to %s" % str(host_port))
