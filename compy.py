#!/usr/bin/python3
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#           ━━━━━━━━━━━━━
#            ┏┓┏┓┳┳┓┏┓┓┏
#            ┃ ┃┃┃┃┃┃┃┗┫
#            ┗┛┗┛┛ ┗┣┛┗┛
#           ━━━━━━━━━━━━━
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Competition organization tool
#  for freediving competitions.
#
#  Copyright 2023 - Arno Mayrhofer
#
#  Licensed under the GNU AGPL
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Authors:
#
#  - Arno Mayrhofer
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    from flask import Flask
except ImportError:
    print("Could not find flask. Install with 'pip3 install flask'")
    exit(-1)
import argparse
import logging
import os
try:
    import dotenv
except ImportError:
    print("Could not find dotenv. Install with 'pip3 install python-dotenv'")
    exit(-1)

import compy_flask
import compy_data
import compy_db
import compy_config

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

def compy(start_flask, init_db = False):
    parser = argparse.ArgumentParser(prog='Compy', description='User interface for freediving competitions')
    parser.add_argument('--init_db', action='store_true', help="Initialize database. WARNING: Deletes all data")
    parser.add_argument('--port', type=int, default=5000, help="Port to listen on (e.g. for a test instance next to a dev server)")
    args = parser.parse_args()

    init_db = init_db or args.init_db

    # load local environment; exported FLASK_* variables win over the file
    if not compy_config.loadEnvironment():
        logging.error("Could not load .env file, make sure it exists (e.g. by copying from .env_sample")
        exit(-1)

    app.config.from_prefixed_env()
    db = compy_db.CompyDB(app)

    if init_db:
        db.init_db()

    # bring databases created by older versions up to date (idempotent)
    db.migrate_db()

    # make sure a default competition exists on a fresh database;
    # per-request CompyData objects are created inside CompyFlask
    with app.app_context():
        compy_data.CompyData.ensureDefaultCompetition(db, app)

    compy_flask.CompyFlask(app, db, start_flask, args.port)

start_flask = __name__ == '__main__'
compy(start_flask)
