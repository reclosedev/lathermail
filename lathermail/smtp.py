#!/usr/bin/env python
# -*- coding: utf-8 -*-
import email
import smtpd
import asyncore
import logging
import socket
import base64

log = logging.getLogger(__name__)


class SMTPChannelWithAuth(smtpd.SMTPChannel):

    def __init__(self, server, conn, addr):
        smtpd.SMTPChannel.__init__(self, server, conn, addr)
        self.user = None
        self.password = None
        self.fqdn = socket.getfqdn()

    def smtp_EHLO(self, arg):
        self.push("250-%s\r\n"
                  "250 AUTH PLAIN" % self.fqdn)

    def smtp_AUTH(self, arg):
        try:
            user, password = self.decode_plain_auth(arg)
        except ValueError:
            self.push("535 5.7.8  Authentication credentials invalid")
        else:
            self.push("235 2.7.0  Authentication Succeeded")
            self.user, self.password = user, password

    def smtp_MAIL(self, arg):
        if not (self.user and self.password):
            self.push("530 5.7.0  Authentication required")
            return
        smtpd.SMTPChannel.smtp_MAIL(self, arg)

    @staticmethod
    def decode_plain_auth(arg):
        user_password = arg.split()[-1]
        user_password = base64.b64decode(user_password)
        return user_password.split("\0", 3)[1:]


class InboxServer(smtpd.SMTPServer, object):

    def __init__(self, localaddr, handler):
        super(InboxServer, self).__init__(localaddr, None)
        self._handler = handler
        self._channel = None

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            conn, addr = pair
            self._channel = SMTPChannelWithAuth(self, conn, addr)

    def process_message(self, peer, mailfrom, rcpttos, data):
        log.info("Storing message to inbox: '{0}' (from: {1}, to: {2})".format(self._channel.user, mailfrom, rcpttos))
        message = email.message_from_string(data)
        return self._handler(to=rcpttos, sender=mailfrom, message=message, body=data,
                             user=self._channel.user, password=self._channel.password)


def serve_smtp(host="127.0.0.1", port=10252, handler=None):
    if handler is None:

        def handler(to, sender, *args):
            print to, sender

    InboxServer((host, port), handler)
    log.info("Running SMTP server on %s:%s", host, port)
    asyncore.loop()
