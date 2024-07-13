
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

import logging
from flask import Flask, render_template, request, send_file, Response
from os import path, mkdir
from werkzeug.utils import secure_filename
try:
    import country_converter
except ImportError:
    print("Could not find country_converter. Install with 'pip3 install country_converter'")
    exit(-1)

class CompyFlask:

    def __init__(self, app, data):

        self.data_ = data
        self.app_ = app

        app.config['UPLOAD_FOLDER'] = self.data_.config.upload_folder

        @app.route('/', methods=['GET'])
        def main():
            all_countries = country_converter.CountryConverter().data["IOC"].dropna().to_list()
            first_records = None #foo.get_records(Federation.AIDA, all_countries[0], Gender.FEMALE)
            content = {"version": self.data_.version,
                       "competitions": self.data_.getSavedCompetitions(),
                       "comp_name": self.data_.name,
                       "all_countries": all_countries,
                       "record_sta": None}
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

        @app.route('/change_special_ranking_name', methods=['POST'])
        def changeSpecialRankingName():
            return self.changeSpecialRankingName()

        @app.route('/change_special_ranking', methods=['POST'])
        def changeSpecialRanking():
            return self.changeSpecialRanking()

        @app.route('/load_comp', methods=['POST'])
        def loadComp():
            return self.loadComp()

        @app.route('/start_list', methods=['GET'])
        def startList():
            return self.startList()

        @app.route('/start_list_pdf', methods=['GET'])
        def startListPDF():
            return self.startListPDF()

        @app.route('/breaks', methods=['GET'])
        def breaks():
            return self.breaks()

        @app.route('/lane_list', methods=['GET'])
        def laneList():
            return self.laneList()

        @app.route('/lane_list_pdf', methods=['GET'])
        def laneListPDF():
            return self.laneListPDF()

        @app.route('/result', methods=['GET'])
        def result():
            return self.result(False)

        @app.route('/result_pdf', methods=['GET'])
        def resultPDF():
            return self.result(True)

        @app.route('/change_lane_style', methods=['POST'])
        def changeLaneStyle():
            return self.changeLaneStyle()

        @app.route('/change_comp_type', methods=['POST'])
        def changeCompType():
            return self.changeCompType()

        @app.route('/change_selected_country', methods=['POST'])
        def changeSelectedCountry():
            return self.changeSelectedCountry()

        @app.route('/athlete', methods=['DELETE', 'POST'])
        def athlete():
            print(">>>>", request.method)
            if request.method == 'DELETE':
                return self.deleteAthlete()
            elif request.method == 'POST':
                return self.addAthlete()

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
                self.data_.getAthleteData(data)
                self.setSubmenuData(data)
                self.data_.setOTs(data)
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

    def changeSpecialRanking(self):
        content = request.json
        if "id" not in content and "checked" not in content:
            logging.debug("Post request to change_special_ranking without id and checked")
            return {}, 400
        athlete_id = content["id"]
        is_special_ranking = content["checked"]
        if self.data_.setSpecialRanking(athlete_id, is_special_ranking) == 0:
            data = {"status": "success", "status_msg": "Successfully updated athlete with id '" + athlete_id + "' to value '" + str(is_special_ranking) + "'"}
        else:
            data = {"status": "success", "status_msg": "Failed to update athlete with id '" + athlete_id + "' to value '" + str(is_special_ranking) + "'"}
        data["disciplines"] = self.data_.getDisciplines()
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
        if "comp_id" not in content:
            logging.debug("Post request to load_comp without comp_id")
            return {}, 400
        comp_id = content["comp_id"]
        comp_name = self.data_.load(comp_id)
        data = {}
        self.data_.getAthleteData(data)
        data["comp_name"] = comp_name
        self.setSubmenuData(data)
        self.data_.setSpecialRankingName(data)
        self.data_.setOTs(data)
        data["lane_style"] = self.data_.lane_style
        data["comp_type"] = self.data_.comp_type
        data["selected_country"] = self.data_.selected_country
        data["status"] = "success"
        data["status_msg"] = "Loaded competition with name " + comp_name
        logging.debug("Loaded comp " + comp_name + " with " + str(self.data_.number_of_athletes) + " athletes")
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

    def breaks(self):
        day = request.args.get('day')
        if day is None:
            logging.debug("Get request to breaks without day")
            return {}, 400
        data = {}
        breaks = self.data_.getBreaks(day)
        if not breaks is None:
            data["min_break"] = breaks["min_break"]
            data["breaks_list"] = breaks["breaks_list"]
            data["status"] = "success"
            data["status_msg"] = "Transfered breaks for " + day
            return data, 200
        else:
            logging.debug("Could not get breaks for " + day)
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

    def changeCompType(self):
        content = request.json
        if "comp_type" not in content:
            logging.debug("Change request for comp type missing variable")
            return {}, 400
        option = content["comp_type"]
        if self.data_.changeCompType(option) == 0:
            data = {}
            data["days_with_disciplines_lanes"] = self.data_.getDaysWithDisciplinesLanes()
            data["status_msg"] = "Successfully changed comp type"
            data["status"] = "success"
            return data, 200
        else:
            logging.debug("Invalid comp type")
            return {}, 400

    def changeSelectedCountry(self):
        content = request.json
        if "selected_country" not in content:
            logging.debug("Change request for selected country missing variable")
            return {}, 400
        option = content["selected_country"]
        if self.data_.changeSelectedCountry(option) == 0:
            data = {}
            self.setSubmenuData(data)
            data["status_msg"] = "Successfully changed selected country"
            data["status"] = "success"
            return data, 200
        else:
            logging.debug("Invalid country selected")
            return {}, 400

    def setSubmenuData(self, data):
        data["days_with_disciplines_lanes"] = self.data_.getDaysWithDisciplinesLanes()
        data["disciplines"] = self.data_.getDisciplines()
        data["countries"] = self.data_.getCountries()
        data["result_countries"] = self.data_.getCountries(True)

    def result(self, pdf):
        discipline = request.args.get('discipline')
        gender = request.args.get('gender')
        country = request.args.get('country')
        req_type = request.args.get('type')
        if (discipline is None or gender is None or country is None) and (req_type is None or not pdf):
            logging.debug("Get request to result without discipline, gender, country or type")
            return {}, 400
        data = {}
        if pdf:
            if req_type == "all":
                result_pdf = self.data_.getResultPDF()
            elif req_type == "top3":
                result_pdf = self.data_.getResultPDF("all", "all", "all", False, True)
            elif req_type == "single" or req_type is None:
                result_pdf = self.data_.getResultPDF(discipline, gender, country)
            if not result_pdf is None:
                logging.debug("Sending: " + result_pdf)
                return send_file(result_pdf, as_attachment=True)
        else:
            result, result_keys = self.data_.getResult(discipline, gender, country)
            if not result is None:
                data["result"] = result
                data["result_keys"] = result_keys
                data["status"] = "success"
                data["status_msg"] = "Transfered result for " + discipline + "/" + gender + " country: " + country
                return data, 200
        logging.debug("Could not get result for " + discipline + "/" + gender + " country: " + country)
        return {}, 400

    def changeSpecialRankingName(self):
        content = request.json
        if "special_ranking_name" not in content:
            logging.debug("Post request to change_special_ranking_name without special_ranking_name")
            return {}, 400
        special_ranking_name = content["special_ranking_name"]
        self.data_.changeSpecialRankingName(special_ranking_name)
        data = {"status": "success", "status_msg": "Successfully changed special ranking name to '" + special_ranking_name + "'"}
        self.setSubmenuData(data)
        return data, 200

    def deleteAthlete(self):
        athlete_id = request.args.get('athlete_id')
        if athlete_id is None:
            logging.info("Could not delete athlete without getting an id")
            return {}, 400
        try:
            athlete_id = int(athlete_id)
        except (ValueError, TypeError):
            logging.info("athlete id has wrong type")
            return {}, 400

        data = {}
        ca_id, in_other_comp = self.data_.isAthleteInCompetition(athlete_id)
        if ca_id is not None:
            self.data_.deleteAthlete(ca_id, athlete_id, in_other_comp)
            data = {"status": "success", "status_msg": "Successfully deleted athlete with id " + athlete_id + (" completely" if not in_other_comp else "")}
            self.data_.getAthleteData(data)
            self.setSubmenuData(data)
            self.data_.setOTs(data)
            return data, 200
        else:
            logging.info('Invalid athlete id provided')
            return {}, 400

    def addAthlete(self):
        content = request.json
        if False in [key in content for key in ['first_name', 'last_name', 'gender', 'country', 'club', 'aida_id']]:
            logging.info("Could not add athlete due to missing data")
            return {}, 400
        first_name = content['first_name']
        last_name = content['last_name']
        gender = content['gender']
        country = content['country']
        club = content['club']
        aida_id = content['aida_id']
        if first_name is None or last_name is None or gender not in ["M", "F"] or \
           country is None or club is None or aida_id is None:
            logging.info("Could not add athlete with incomplete information")
            return {}, 400
        status = self.data_.addAthlete(first_name, last_name, gender, country, club, aida_id)
        data = {}
        if status == 0:
            data = {"status": "success", "status_msg": "Successfully added athlete"}
            self.data_.getAthleteData(data)
            return data, 200
        elif status == 1:
            data = {"status": "error", "status_msg": "Athlete already exists"}
            return data, 200
