# -*- coding: utf-8 -*-
import logging
from flask import Flask


app = Flask(__name__)

app.config.from_object("lathermail.default_settings")
app.config.from_envvar("LATHERMAIL_SETTINGS", silent=True)
app.config.from_pyfile("lathermail.conf", silent=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)-16s:%(asctime)-s:%(message)s")

from . import db
from .api import api_bp
from .web import static_bp


def init_app():
    db.init(app)
    app.register_blueprint(api_bp)
    app.register_blueprint(static_bp)
