
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
from flask import Flask, render_template, request, send_file, Response
from os import path, mkdir
from werkzeug.utils import secure_filename

class CompyFlask:

    def __init__(self, app, data):

        self.data_ = data
        self.app_ = app

        app.config['UPLOAD_FOLDER'] = self.data_.config.upload_folder

        @app.route('/', methods=['GET'])
        def main():
            content = {"version": self.data_.version,
                       "competitions": self.data_.getSavedCompetitions(),
                       "comp_name": self.data_.name}
            return render_template('template.html', **content)

        @app.route('/upload_file', methods=['POST'])
        def uploadFile():
            return self.uploadFile()

        @app.route('/upload_sponsor_img', methods=['POST'])
        def uploadSponsorImg():
            return self.uploadSponsorImg()

        @app.route('/change_comp_name', methods=['POST'])
        def changeCompName():
            return self.changeCompName()

        @app.route('/change_newcomer', methods=['POST'])
        def changeNewcomer():
            return self.changeNewcomer()

        @app.route('/load_comp', methods=['POST'])
        def loadComp():
            return self.loadComp()

        @app.route('/start_list', methods=['GET'])
        def startList():
            return self.startList()

        @app.route('/start_list_pdf', methods=['GET'])
        def startListPDF():
            return self.startListPDF()

        @app.route('/lane_list', methods=['GET'])
        def laneList():
            return self.laneList()

        @app.route('/lane_list_pdf', methods=['GET'])
        def laneListPDF():
            return self.laneListPDF()

        @app.route('/change_lane_style', methods=['POST'])
        def changeLaneStyle():
            return self.changeLaneStyle()

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
                fpath = path.join(self.app_.config['UPLOAD_FOLDER'], filename)
                data_file.save(fpath)
                self.data_.compFileChange(fpath)
                data["athletes"] = []
                for athlete in self.data_.athletes:
                    data["athletes"].append({"last_name": athlete.last_name, "first_name": athlete.first_name, "gender": athlete.gender, "country": athlete.country, "id": athlete.id})
                data["days_with_disciplines_lanes"] = self.data_.getDaysWithDisciplinesLanes()
        data["status_msg"] = status_msg
        return data, 200

    def uploadSponsorImg(self):
        if 'sponsor_img' not in request.files:
            logging.debug("Post request without image upload")
            return {}, 400
        logging.debug("Received sponsor image upload")
        img_file = request.files['sponsor_img']
        status_msg = ""
        data = {"status": "success"}
        if img_file.filename == '':
            logging.debug("Image upload with empty filename")
            status_msg = "No image uploaded due to empty filename"
        else:
            filename = secure_filename(img_file.filename)
            ext = path.splitext(filename)[1].lower()
            if ext != ".png":
                status_msg = "Image uploaded (" + filename + ") is not a *.png file"
            else:
                status_msg = "Image '" + filename + "' uploaded successfully"
                fpath = path.join(self.app_.config['UPLOAD_FOLDER'], filename)
                img_content = img_file.read()
                self.data_.changeSponsorImage(img_content)
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

    def changeCompName(self):
        content = request.json
        if "comp_name" not in content and "overwrite" not in content:
            logging.debug("Post request to change_comp_name without comp_name and overwrite")
            return {}, 400
        comp_name = content["comp_name"]
        overwrite = content["overwrite"]
        file_exists, name = self.data_.changeName(comp_name, overwrite)
        data = {}
        if file_exists == 0:
            data = {"status": "success", "status_msg": "Successfully changed competition name to '" + comp_name + "'", "file_exists": False, "prev_name": ""}
        else:
            data = {"status": "success", "status_msg": "File exists", "file_exists": True, "prev_name": name}
        return data, 200

    def loadComp(self):
        content = request.json
        if "comp_name" not in content:
            logging.debug("Post request to load_comp without comp_name")
            return {}, 400
        comp_name = content["comp_name"]
        self.data_.load(comp_name)
        data = {}
        data["athletes"] = []
        for athlete in self.data_.athletes:
            data["athletes"].append({"last_name": athlete.last_name, "first_name": athlete.first_name, "gender": athlete.gender, "country": athlete.country, "id": athlete.id, "newcomer": athlete.newcomer})
        data["comp_name"] = comp_name
        data["days_with_disciplines_lanes"] = self.data_.getDaysWithDisciplinesLanes()
        data["lane_style"] = self.data_.lane_style
        data["status"] = "success"
        data["status_msg"] = "Loaded competition with name " + comp_name
        logging.debug("Loaded comp " + comp_name + " with " + str(len(self.data_.athletes)) + " athletes")
        return data, 200

    def startList(self):
        day = request.args.get('day')
        discipline = request.args.get('discipline')
        if day is None or discipline is None:
            logging.debug("Get request to start_list without day and discipline")
            return {}, 400
        data = {}
        start_list = self.data_.getStartList(day, discipline)
        if not start_list is None:
            data["start_list"] = start_list
            data["status"] = "success"
            data["status_msg"] = "Transfered start list for " + day + ": " + discipline
            return data, 200
        else:
            logging.debug("Could not get start list for " + day + ": " + discipline)
            return {}, 400

    def startListPDF(self):
        day = request.args.get('day')
        discipline = request.args.get('discipline')
        req_type = request.args.get('type')
        if (day is None or discipline is None) and req_type is None:
            logging.debug("Get request to start_list without day, discipline or type")
            return {}, 400
        data = {}
        if req_type is not None and req_type == "all":
            start_list_pdf = self.data_.getStartListPDF()
        else:
            start_list_pdf = self.data_.getStartListPDF(day, discipline)
        if not start_list_pdf is None:
            logging.debug("Sending: " + start_list_pdf)
            return send_file(start_list_pdf, as_attachment=True)
        else:
            logging.debug("Could not get start list for " + day + ": " + discipline)
            return {}, 400

    def laneList(self):
        day = request.args.get('day')
        discipline = request.args.get('discipline')
        lane = request.args.get('lane')
        if day is None or discipline is None or lane is None:
            logging.debug("Get request to lane_list without day, discipline or lane")
            return {}, 400
        data = {}
        lane_list = self.data_.getLaneList(day, discipline, lane)
        if not lane_list is None:
            data["lane_list"] = lane_list
            data["status"] = "success"
            data["status_msg"] = "Transfered lane list for " + day + ": " + discipline + "/" + lane
            return data, 200
        else:
            logging.debug("Could not get lane list for " + day + ": " + discipline + "/" + lane)
            return {}, 400

    def laneListPDF(self):
        day = request.args.get('day')
        discipline = request.args.get('discipline')
        lane = request.args.get('lane')
        req_type = request.args.get('type')
        if (day is None or discipline is None or lane is None) and req_type is None:
            logging.debug("Get request to lane_list without day, discipline, lane or type")
            return {}, 400
        data = {}
        if req_type is not None and req_type == "all":
            lane_list_pdf = self.data_.getLaneListPDF()
        else:
            lane_list_pdf = self.data_.getLaneListPDF(day, discipline, lane)
        if not lane_list_pdf is None:
            logging.debug("Sending: " + lane_list_pdf)
            return send_file(lane_list_pdf, as_attachment=True)
        else:
            logging.debug("Could not get lane list for " + day + ": " + discipline + "/" + lane)
            return {}, 400

    def changeLaneStyle(self):
        content = request.json
        if "lane_style" not in content:
            logging.debug("Change request for lane style missing variable")
            return {}, 400
        option = content["lane_style"]
        if self.data_.changeLaneStyle(option) == 0:
            data = {}
            data["days_with_disciplines_lanes"] = self.data_.getDaysWithDisciplinesLanes()
            data["status_msg"] = "Successfully changed lane style"
            data["status"] = "success"
            return data, 200
        else:
            logging.debug("Invalid lane style")
            return {}, 400
