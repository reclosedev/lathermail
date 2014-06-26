# -*- coding: utf-8 -*-
import logging
from flask import Flask


app = Flask(__name__)

app.config.from_object("lathermail.default_settings")
app.config.from_envvar("LATHERMAIL_SETTINGS", silent=True)
app.config.from_pyfile("lathermail.conf", silent=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)-16s:%(asctime)-s:%(message)s")

from . import db
from .db import mongo
from .api import api_bp


def init_app():
    mongo.init_app(app)
    app.register_blueprint(api_bp)
