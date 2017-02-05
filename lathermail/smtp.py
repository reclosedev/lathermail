#!/usr/bin/env python
# -*- coding: utf-8 -*-
import email
import smtpd
import asyncore
import logging
import socket
import base64

from lathermail.compat import bytes

log = logging.getLogger(__name__)


class SMTPChannelWithAuth(smtpd.SMTPChannel, object):

    def __init__(self, server, conn, addr, on_close=lambda s: None):
        smtpd.SMTPChannel.__init__(self, server, conn, addr)
        self.user = None
        self.password = None
        self.fqdn = socket.getfqdn()
        self._addr = addr
        self._on_close = on_close

    def close(self):
        smtpd.SMTPChannel.close(self)
        try:
            self._on_close(self._addr)
        except:
            log.exception("Exception in on_close for %s:", self._addr)

    def smtp_EHLO(self, arg):
        self.push("250-%s\r\n"
                  "250 AUTH PLAIN" % self.fqdn)
        self.seen_greeting = arg

    def smtp_AUTH(self, arg):
        try:
            user, password = self.decode_plain_auth(arg)
        except ValueError:
            self.push("535 5.7.8  Authentication credentials invalid")
        else:
            self.push("235 2.7.0  Authentication Succeeded")
            self.user, self.password = user.decode("ascii"), password.decode("ascii")

    def smtp_MAIL(self, arg):
        if not (self.user and self.password):
            self.push("530 5.7.0  Authentication required")
            return
        smtpd.SMTPChannel.smtp_MAIL(self, arg)

    @staticmethod
    def decode_plain_auth(arg):
        user_password = arg.split()[-1]
        user_password = base64.b64decode(bytes(user_password, "ascii"))
        return user_password.split(b"\0", 3)[1:]


class InboxServer(smtpd.SMTPServer, object):

    def __init__(self, localaddr, handler):
        super(InboxServer, self).__init__(localaddr, None)
        self._handler = handler
        self._channel_by_peer = {}

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            conn, addr = pair
            log.info("Incoming connection from %s", repr(addr))
            # Since there is no way to pass channel or additional data (user, password) to process_message()
            # we have dict of channels indexed by peers. It's cleaned on channel close()
            self._channel_by_peer[addr] = SMTPChannelWithAuth(self, conn, addr, on_close=self._on_channel_close)

    def process_message(self, peer, mailfrom, rcpttos, data):
        channel = self._channel_by_peer.get(peer)
        if not channel:
            log.error("No channel found for peer %s. Channels dump: %s", peer, self._channel_by_peer)
            return "451 Internal confusion"

        log.info("Storing message: inbox: '%s', from: %r, to: %r, peer: %r",
                 channel.user, mailfrom, rcpttos, peer)
        message = email.message_from_string(data)
        return self._handler(to=rcpttos, sender=mailfrom, message=message, body=data,
                             user=channel.user, password=channel.password)

    def _on_channel_close(self, peer):
        self._channel_by_peer.pop(peer, None)
        log.info("Remove channel for peer: %s. Active channels: %s", peer, len(self._channel_by_peer))


def serve_smtp(host="127.0.0.1", port=10252, handler=None):
    if handler is None:

        def handler(to, sender, *args):
            print("{0} <- {1}".format(to, sender))

    InboxServer((host, port), handler)
    log.info("Running SMTP server on %s:%s", host, port)
    while True:
        try:
            asyncore.loop(use_poll=True, count=10)
        except:
            log.exception("Error in loop:")
