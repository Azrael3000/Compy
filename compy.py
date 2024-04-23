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
#  for AIDA International
#  competitions.
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

import compy_flask
import compy_data

logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser(prog='Compy', description='User interface for AIDA competitions')
#parser.add_argument('--data_file', type=str, default='', required=False)
#args = parser.parse_args()

app = Flask(__name__)
data = compy_data.CompyData()
compy_flask.CompyFlask(app, data)
