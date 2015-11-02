#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse
from threading import Thread

from lathermail import app, init_app
from lathermail.smtp import serve_smtp
from lathermail import db


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--db-uri", default=app.config["DB_URI"],
        help="DB URI, e.g. mongodb://localhost/lathermail, sqlite:////tmp/my.db"
    )
    parser.add_argument("--api-host", default=app.config["API_HOST"], help="API Host")
    parser.add_argument("--api-port", default=app.config["API_PORT"], type=int, help="API port")
    parser.add_argument("--smtp-host", default=app.config["SMTP_HOST"], help="SMTP host")
    parser.add_argument("--smtp-port", default=app.config["SMTP_PORT"], type=int, help="SMTP port")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--debug-smtp", action="store_true", help="Turn on SMTP debug info")
    args = parser.parse_args()

    if args.debug_smtp:
        import smtpd
        smtpd.DEBUGSTREAM = sys.stderr

    app.config["DB_URI"] = args.db_uri
    app.config["DEBUG_MODE"] = args.debug
    init_app()

    t = Thread(target=serve_smtp, kwargs=dict(handler=db.engine.message_handler,
                                              host=args.smtp_host, port=args.smtp_port))
    t.daemon = True
    t.start()

    app.run(debug=False, threaded=True, host=args.api_host, port=args.api_port)


if __name__ == "__main__":
    main()
