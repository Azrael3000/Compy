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

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

def compy(init_db=False):
    parser = argparse.ArgumentParser(prog='Compy', description='User interface for freediving competitions')
    parser.add_argument('--init_db', action='store_true', help="Initialize database. WARNING: Deletes all data")
    args = parser.parse_args()

    init_db = init_db or args.init_db

    # load local environment
    if not dotenv.load_dotenv():
        logging.error("Could not load .env file, make sure it exists (e.g. by copying from .env_sample")
        exit(-1)

    app.config.from_prefixed_env()
    db = compy_db.CompyDB(app)

    if init_db:
        db.init_db()

    data = compy_data.CompyData(db, app)

    compy_flask.CompyFlask(app, data)

if __name__ == '__main__':
    compy()
