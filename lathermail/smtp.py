#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asynchat
import email
import smtpd
import ssl
import asyncore
import logging
import socket
import base64

from lathermail.compat import bytes

log = logging.getLogger(__name__)


class SMTPChannel(smtpd.SMTPChannel, object):

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
        self.seen_greeting = arg
        parts = [self.fqdn, "AUTH PLAIN"]
        if self.__server.ssl_ctx and not isinstance(self.__conn, ssl.SSLSocket):
            parts.append("STARTTLS")
        for i, feature in enumerate(parts):
            is_last = i == len(parts) - 1
            parts[i] = "250%s%s" % ((" " if is_last else "-"), feature)
        self.push("\r\n".join(parts))

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

    def smtp_STARTTLS(self, arg):
        if arg:
            self.push('501 Syntax error (no parameters allowed)')
        elif self.__server.ssl_ctx and not isinstance(self.__conn, ssl.SSLSocket):
            self.push('220 Ready to start TLS')
            self.__conn.settimeout(30)
            self.__conn = self.__server.ssl_ctx.wrap_socket(self.__conn, server_side=True)
            self.__conn.settimeout(None)
            # re-init channel
            asynchat.async_chat.__init__(self, self.__conn)
            self.__line = []
            self.__state = self.COMMAND
            self.__greeting = 0
            self.__mailfrom = None
            self.__rcpttos = []
            self.__data = ''
            log.debug('Peer: %s - negotiated TLS: %s', repr(self.__addr), repr(self.__conn.cipher()))
        else:
            self.push('454 TLS not available due to temporary reason')

    @staticmethod
    def decode_plain_auth(arg):
        user_password = arg.split()[-1]
        user_password = base64.b64decode(bytes(user_password, "ascii"))
        return user_password.split(b"\0", 3)[1:]


class InboxServer(smtpd.SMTPServer, object):

    def __init__(self, localaddr, handler, ssl_ctx=None, tls_only=False):
        self.ssl_ctx = ssl_ctx
        self.tls_only = tls_only
        super(InboxServer, self).__init__(localaddr, None)
        self._handler = handler
        self._channel_by_peer = {}

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            conn, addr = pair
            log.info("Incoming connection from %s", repr(addr))
            if self.ssl_ctx and self.tls_only:
                conn = self.ssl_ctx.wrap_socket(conn, server_side=True)
                log.debug("Peer: %s - negotiated TLS: %s", repr(addr), repr(conn.cipher()))
            # Since there is no way to pass channel or additional data (user, password) to process_message()
            # we have dict of channels indexed by peers. It's cleaned on channel close()
            self._channel_by_peer[addr] = SMTPChannel(self, conn, addr, on_close=self._on_channel_close)

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
    asyncore.loop()
