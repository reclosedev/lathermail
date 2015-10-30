#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from . import app

db_uri = app.config.get("DB_URI")
if not db_uri:
    app.config["DB_URI"] = db_uri = "sqlite:///" + os.path.expanduser("~/.lathermail.db")

if db_uri.startswith("mongodb:/"):
    app.config["MONGO_URI"] = db_uri
    from .storage.mongo import *  # noqa
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    from .storage.alchemy import *  # noqa
