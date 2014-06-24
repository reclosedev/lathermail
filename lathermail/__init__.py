# -*- coding: utf-8 -*-
import logging
from flask import Flask

app = Flask(__name__)

app.config.from_object("lathermail.default_settings")
app.config.from_envvar("LATHERMAIL_SETTINGS", silent=True)
app.config.from_pyfile("lathermail.conf", silent=True)

logging.basicConfig(level=logging.INFO)

from . import db
from .api import api_bp
app.register_blueprint(api_bp)
