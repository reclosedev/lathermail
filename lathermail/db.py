#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging


engine = None


def init(app):
    global engine

    db_uri = app.config["DB_URI"]
    if db_uri.startswith("mongodb:/"):
        app.config["MONGO_URI"] = db_uri
        from .storage import mongo
        engine = mongo
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        from .storage import alchemy
        engine = alchemy

    logging.info("Using '%s' DB engine. URI: '%s'", engine.__name__, db_uri)
    engine.init_app_for_db(app)
