
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

import logging
from flask import Flask, render_template, request
from os import path, mkdir
from werkzeug.utils import secure_filename

class CompyFlask:

    def __init__(self, app, data):

        self.data_ = data
        self.app_ = app

        app.config['UPLOAD_FOLDER'] = self.data_.config.upload_folder

        @app.route('/', methods=['GET'])
        def main():
            return render_template('template.html', version=self.data_.version)

        @app.route('/upload_file', methods=['POST'])
        def uploadFile():
            return self.uploadFile()

        @app.route('/change_newcomer', methods=['POST'])
        def changeNewcomer():
            return self.changeNewcomer()

        app.run()

    def uploadFile(self):
        if 'file' not in request.files:
            logging.debug("Post request without file upload")
            return {}, 400
        logging.debug("Received file upload")
        data_file = request.files['file']
        status_msg = ""
        data = {"status": "success"}
        if data_file.filename == '':
            logging.debug("File upload with empty filename")
            status_msg = "No file uploaded due to empty filename"
        else:
            filename = secure_filename(data_file.filename)
            ext = path.splitext(filename)[1].lower()
            if ext != ".xlsx":
                status_msg = "File uploaded (" + filename + ") is not a *.xlsx file"
            else:
                status_msg = "File '" + filename + "' uploaded successfully"
                data_file.save(path.join(self.app_.config['UPLOAD_FOLDER'], filename))
                self.data_.compFileChange(filename)
                data["athletes"] = []
                for athlete in self.data_.athletes:
                    data["athletes"].append({"last_name": athlete.last_name, "first_name": athlete.first_name, "gender": athlete.gender, "country": athlete.country, "id": athlete.id})
        data["status_msg"] = status_msg
        return data, 200

    def changeNewcomer(self):
        content = request.json
        if "id" not in content and "checked" not in content:
            logging.debug("Post request to change_newcomer without id and checked")
            return {}, 400
        athlete_id = content["id"]
        is_newcomer = content["checked"]
        if self.data_.setNewcomer(athlete_id, is_newcomer) == 0:
            data = {"status": "success", "status_msg": "Successfully updated athlete with id '" + athlete_id + "' to value '" + str(is_newcomer) + "'"}
        else:
            data = {"status": "success", "status_msg": "Failed to update athlete with id '" + athlete_id + "' to value '" + str(is_newcomer) + "'"}
        return data, 200
