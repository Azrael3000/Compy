
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
from flask import Flask, render_template, request, send_file, Response, make_response, current_app
from os import path, mkdir
from werkzeug.utils import secure_filename
try:
    import country_converter
except ImportError:
    print("Could not find country_converter. Install with 'pip3 install country_converter'")
    exit(-1)

class CompyFlask:

    def __init__(self, app, data, start_flask):

        self.data_ = data
        self.app_ = app

        app.config['UPLOAD_FOLDER'] = self.data_.config.upload_folder

        @app.route('/admin', methods=['GET'])
        def admin():
            return self.admin()

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

        @app.route('/start_list', methods=['GET', 'PUT'])
        def startList():
            if request.method == 'GET':
                return self.startList()
            elif request.method == 'PUT':
                return self.updateStartList()

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

        @app.route('/result', methods=['GET', 'PUT'])
        def result():
            if request.method == 'GET':
                return self.result(False)
            elif request.method == 'PUT':
                return self.updateResult()

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

        @app.route('/judge', methods=['DELETE', 'POST'])
        def judge():
            if request.method == 'DELETE':
                return self.deleteJudge()
            elif request.method == 'POST':
                return self.addJudge()

        @app.route('/judge/qr_code', methods=['GET'])
        def judgeQrCode():
            return self.getJudgeQrCode()

        @app.route('/judges', methods=['GET'])
        def judges():
            return self.getJudges()

        @app.route('/athlete', methods=['DELETE', 'POST'])
        def athlete():
            if request.method == 'DELETE':
                return self.deleteAthlete()
            elif request.method == 'POST':
                return self.addAthlete()

        @app.route('/athletes', methods=['GET'])
        def athletes():
            return self.getAthletes()

        @app.route('/national_records', methods=['GET'])
        def nationalRecords():
            return self.nationalRecords()

        @app.route('/judge/<int:comp_id>/<int:judge_id>', methods=['GET'])
        def judgeComp(comp_id, judge_id):
            return self.getJudgeComp(comp_id, judge_id)

        @app.route('/judge_json/<int:comp_id>/<int:judge_id>', methods=['GET'])
        def judgeJsonComp(comp_id, judge_id):
            return self.getJudgeComp(comp_id, judge_id, True)

        @app.route('/judge/athletes', methods=['GET'])
        def judgeAthlete():
            return self.getJudgeAthletes()

        @app.route('/judge/athlete/result', methods=['GET'])
        def judgeAthleteResult():
            if request.method == 'GET':
                return self.getJudgeAthleteResult()

        @app.route('/disciplines/<federation>', methods=['GET'])
        def disciplines(federation):
            return self.disciplines(federation)

        @app.route('/block', methods=['POST', 'UPDATE', 'DELETE'])
        def block():
            if request.method == 'POST':
                return self.modifyBlock(True)
            elif request.method == 'UPDATE':
                return self.modifyBlock(False)
            elif request.method == 'DELETE':
                return self.deleteBlock()

        @app.route('/clock/<int:comp_id>/<int:current>', methods=['GET'])
        def clock(comp_id, current):
            return self.getClock(comp_id, current)

        if start_flask:
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
                self.data_.getJudgeData(data)
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
        self.data_.getJudgeData(data)
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
        block = request.args.get('block')
        if day is None or block is None:
            logging.debug("Get request to start_list without day and block")
            return {}, 400
        data = {}
        start_list = self.data_.getStartList(day, block)
        if not start_list is None:
            data["start_list"] = start_list
            data["status"] = "success"
            data["status_msg"] = "Transfered start list for " + day + ": " + block
            return data, 200
        else:
            logging.debug("Could not get start list for " + day + ": " + block)
            return {}, 400

    def updateStartList(self):
        content = request.json
        if not self.dictHas(content, {'day', 'block', 'to_remove', 'startlist'}):
            logging.debug("Put request to start_list missing content: " + str(content.keys()))
            return {}, 400
        day = content["day"]
        block = content["block"]
        to_remove = content["to_remove"]
        startlist = content["startlist"]
        ret = self.data_.updateStartList(day, block, to_remove, startlist)
        start_list = self.data_.getStartList(day, block)
        if ret == 0 and not start_list is None:
            data = {"status": "success", "status_msg": "Successfully updated start list", "start_list": start_list}
            return data, 200
        elif ret != 0 and not start_list is None:
            data = {"status": "success", "status_msg": "Failed database update", "start_list": start_list}
            return data, 400
        else:
            logging.debug("Could not update start list for " + day + " & " + block)
            return {}, 400

    def startListPDF(self):
        day = request.args.get('day')
        block = request.args.get('block')
        req_type = request.args.get('type')
        if (day is None or block is None) and req_type is None:
            logging.debug("Get request to start_list without day, block or type")
            return {}, 400
        data = {}
        if req_type is not None and req_type == "all":
            start_list_pdf = self.data_.getStartListPDF()
        else:
            start_list_pdf = self.data_.getStartListPDF(day, block)
        if not start_list_pdf is None:
            logging.debug("Sending: " + start_list_pdf)
            return send_file(start_list_pdf, as_attachment=True)
        else:
            logging.debug("Could not get start list for " + day + ": " + block)
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
        block = request.args.get('block')
        lane = request.args.get('lane')
        if day is None or block is None or lane is None:
            logging.debug("Get request to lane_list without day, block or lane")
            return {}, 400
        data = {}
        lane_list = self.data_.getLaneList(day, block, lane)
        if not lane_list is None:
            data["lane_list"] = lane_list
            data["status"] = "success"
            data["status_msg"] = "Transfered lane list for " + day + ": " + block + "/" + lane
            return data, 200
        else:
            logging.debug("Could not get lane list for " + day + ": " + block + "/" + lane)
            return {}, 400

    def laneListPDF(self):
        day = request.args.get('day')
        block = request.args.get('block')
        lane = request.args.get('lane')
        req_type = request.args.get('type')
        if (day is None or block is None or lane is None) and req_type is None:
            logging.debug("Get request to lane_list without day, block, lane or type")
            return {}, 400
        data = {}
        if req_type is not None and (req_type == "all" or req_type == "safety"):
            lane_list_pdf = self.data_.getLaneListPDF(req_type == "safety")
        else:
            lane_list_pdf = self.data_.getLaneListPDF(False, day, block, lane)
        if not lane_list_pdf is None:
            logging.debug("Sending: " + lane_list_pdf)
            return send_file(lane_list_pdf, as_attachment=True)
        else:
            logging.debug("Could not get lane list for " + day + ": " + block + "/" + lane)
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
            data["blocks"] = self.data_.getBlocks()
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
            data["blocks"] = self.data_.getBlocks()
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
        data["blocks"] = self.data_.getBlocks()
        data["disciplines"] = self.data_.getDisciplines()
        data["countries"] = self.data_.getCountries()
        data["result_countries"] = self.data_.getCountries(True)

    def dictHas(self, d, keys):
        if isinstance(keys, set):
            return d.keys() >= keys
        else:
            return keys in d

    def result(self, pdf):
        discipline = request.args.get('discipline')
        gender = request.args.get('gender')
        country = request.args.get('country')
        req_type = request.args.get('type')
        if (discipline is None or gender is None or country is None) and (req_type is None or not pdf):
            logging.debug("Get request to result without discipline, gender, country or type")
            return {}, 400
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
            return self.getResultDiscipline(discipline, gender, country)
        logging.debug("Could not get result for " + discipline + "/" + gender + " country: " + country)
        return {}, 400

    def getResultDiscipline(self, discipline, gender, country):
        result, result_keys = self.data_.getResult(discipline, gender, country, True)
        data = {}
        if not result is None:
            data["result"] = result
            data["result_keys"] = result_keys
            data["status"] = "success"
            data["status_msg"] = "Transfered result for " + discipline + "/" + gender + " country: " + country
            return data, 200

    def updateResult(self):
        content = request.json
        if not self.dictHas(content, {"id", "rp", "penalty", "card", "remarks", "judge_remarks"}):
            breakpoint()
            logging.debug("Put request to result without discipline, gender, country, id, rp, penalty, card, remarks, judge_remarks")
            return {}, 400
        s_id = content["id"]
        rp = content["rp"]
        penalty = content["penalty"]
        card = content["card"]
        remarks = content["remarks"]
        judge_remarks = content["judge_remarks"]
        res = self.data_.updateResult(s_id, rp, penalty, card, remarks, judge_remarks)
        if res == 1:
            logging.debug("Failed to set result")
            return {}, 400
        if self.dictHas(content, {"discipline", "gender", "country"}):
            discipline = content["discipline"]
            gender = content["gender"]
            country = content["country"]
            return self.getResultDiscipline(discipline, gender, country)
        else:
            data = self.data_.getAthleteResult(s_id)
            if data is None:
                logging.debug("Get request to athlete result failed.")
                return {}, 400

            data["status"] = "success"
            data["status_msg"] = "Completed request for athlete result of " + data["Name"]
            return data, 200

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

    def deleteJudge(self):
        judge_id = request.json.get('judge_id')
        if judge_id is None:
            logging.info("Could not delete judge without getting an id")
            return {}, 400
        try:
            judge_id = int(judge_id)
        except (ValueError, TypeError):
            logging.info("judge id has wrong type")
            return {}, 400

        data = {}
        judge_id = self.data_.isJudgeInCompetition(judge_id)
        if judge_id is not None:
            self.data_.deleteJudge(judge_id)
            data = {"status": "success", "status_msg": "Successfully deleted judge with id " + str(judge_id)}
            self.data_.getJudgeData(data)
            return data, 200
        else:
            logging.info('Invalid judge id provided')
            return {}, 400

    def getJudgeQrCode(self):
        judge_id = request.args.get('judge_id')
        if judge_id is None:
            logging.info("Could not get judge qr code without getting an id")
            return {}, 400
        try:
            judge_id = int(judge_id)
        except (ValueError, TypeError):
            logging.info("judge id has wrong type")
            return {}, 400

        data = {}
        judge_id = self.data_.isJudgeInCompetition(judge_id)
        if judge_id is not None:
            qr_data = self.data_.getJudgeQrCode(judge_id, request.url_root)
            if qr_data is None:
                logging.info('Could not get qr code for judge with id ' + str(judge_id))
                return {}, 400
            else:
                data = {"status": "success", "status_msg": "Successfully got judge qr_code with id " + str(judge_id), "judge_qr_code": qr_data[0], "judge_first_name": qr_data[1], "judge_last_name": qr_data[2], "judge_url": qr_data[3]}
                return data, 200
        else:
            logging.info('Invalid judge id provided')
            return {}, 400

    def addJudge(self):
        content = request.json
        if False in [key in content for key in ['first_name', 'last_name']]:
            logging.info("Could not add judge due to missing data")
            return {}, 400
        first_name = content['first_name']
        last_name = content['last_name']
        if first_name is None or last_name is None:
            logging.info("Could not add judge with incomplete information")
            return {}, 400
        status = self.data_.addJudge(first_name, last_name)
        data = {}
        if status == 0:
            data = {"status": "success", "status_msg": "Successfully added judge"}
            self.data_.getJudgeData(data)
            return data, 200
        elif status == 1:
            data = {"status": "error", "status_msg": "Judge already exists"}
            self.data_.getJudgeData(data)
            return data, 200

    def getJudges(self):
        data = {"status": "success", "status_msg": "Successfully received judge data"}
        self.data_.getJudgeData(data)
        return data, 200

    def deleteAthlete(self):
        athlete_id = request.json.get('athlete_id')
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
            data = {"status": "success", "status_msg": "Successfully deleted athlete with id " + str(athlete_id) + (" completely" if not in_other_comp else "")}
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

    def getAthletes(self):
        data = {"status": "success", "status_msg": "Successfully received athlete data"}
        self.data_.getAthleteData(data)
        return data, 200

    def nationalRecords(self):
        status = self.data_.updateNationalRecords()
        if status == 0:
            return {"status": "success", "status_msg": "Successfully updated national records"}, 200
        else:
            return {"status": "error", "status_msg": "Error while updating national records"}, 500

    def getJudgeComp(self, comp_id, judge_id, return_json = False):
        judge_hash = request.args.get('hash')
        comp_data = self.data_.getCompDataAndValidateJudge(comp_id, judge_id, judge_hash)
        if comp_data is None:
            content = {"version": self.data_.version}
            return make_response(render_template('404.html', **content), 404)

        comp_name = comp_data[0]
        first_name = comp_data[1]
        last_name = comp_data[2]
        federation = comp_data[3]

        self.data_.load(comp_id)

        content = {"version": self.data_.version,
                   "comp_id": comp_id,
                   "comp_name": comp_name,
                   "judge_id": judge_id,
                   "judge_hash": judge_hash,
                   "judge_first_name": first_name,
                   "judge_last_name": last_name,
                   "federation": federation,
                   "days_with_disciplines_lanes": self.data_.getDaysWithDisciplinesLanes(),
                   "blocks": self.data_.getBlocks()}
        if return_json:
            return content, 200
        else:
            return render_template('judge.html', **content)

    def isValidJudge(self):
        judge_hash = request.args.get('judge_hash')
        judge_id = request.args.get('judge_id')
        comp_id = request.args.get('comp_id')

        comp_data = self.data_.getCompDataAndValidateJudge(comp_id, judge_id, judge_hash)
        return comp_data is not None

    def getJudgeAthletes(self):
        if not self.isValidJudge():
            content = {"version": self.data_.version}
            return make_response(render_template('404.html', **content), 404)

        return self.laneList()

    def getJudgeAthleteResult(self):
        if not self.isValidJudge():
            logging.debug("Not a valid judge")
            return {}, 400

        day = request.args.get('day')
        block = request.args.get('block')
        lane = request.args.get('lane')
        s_id = request.args.get('s_id')
        if day is None or block is None or lane is None or s_id is None:
            logging.debug("Get request to athlete result without day, block, lane or start id")
            return {}, 400

        data = self.data_.getAthleteResult(s_id)
        if data is None:
            logging.debug("Get request to athlete result failed.")
            return {}, 400

        data["status"] = "success"
        data["status_msg"] = "Completed request for athlete result of " + data["Name"]
        return data, 200

    def disciplines(self, federation):
        disciplines = self.data_.getAllDisciplines(federation)
        if disciplines is None:
            return {}, 400
        else:
            data = {"status": "success", "disciplines": disciplines}
            return data, 200

    def modifyBlock(self, add):
        content = request.json
        if False in [key in content for key in ['day', 'dis', 'block']]:
            logging.info("Could not add/edit block due to missing data")
            return {}, 400
        day = content['day']
        disciplines = content['dis']
        block = content['block']
        if disciplines is None or day is None or (not add and block is None):
            logging.info("Could not add/edit block with incomplete information")
            return {}, 400
        ret = self.data_.modifyBlock(day, disciplines, block, add)
        data = None
        if ret == 0:
            data = {"status": "success", "status_msg": "Successfully updated block"}
        elif ret == 1:
            data = {"status": "success", "status_msg": "Could not add block, already exists"}
        elif ret == 2:
            data = {"status": "success", "status_msg": "Could not edit block, does not exist"}
        if data is not None:
            data["days_with_disciplines_lanes"] = self.data_.getDaysWithDisciplinesLanes()
            data["blocks"] = self.data_.getBlocks()
            return data, 200
        else:
            return {}, 400

    def deleteBlock(self):
        content = request.json
        if False in [key in content for key in ['block']]:
            logging.info("Could not remove block due to missing data")
            return {}, 400
        block = content['block']
        if block is None:
            logging.info("Could not remove block with incomplete information")
            return {}, 400
        ret = self.data_.removeBlock(block)
        data = None
        if ret == 0:
            data = {"status": "success", "status_msg": "Successfully removed block"}
        elif ret == 1:
            data = {"status": "success", "status_msg": "Could not remove block, does not exist"}
        if data is not None:
            data["days_with_disciplines_lanes"] = self.data_.getDaysWithDisciplinesLanes()
            data["blocks"] = self.data_.getBlocks()
            return data, 200
        else:
            return {}, 400

    def getClock(self, comp_id, current):
        current = (current+1) % 2
        comp_name = self.data_.load(comp_id)
        alist = self.data_.getFourStarts(current == 0)
        if alist is None:
            current = (current+1) % 2
            alist = self.data_.getFourStarts(current == 0)
        if comp_name != None:
            refresh_url = request.base_url[:request.base_url.rfind('/')+1] + str(current)
            content = {"comp_name": comp_name,
                       "comp_id": comp_id,
                       "alist": alist,
                       "current": current,
                       "refresh_url": refresh_url}
            return render_template('clock.html', **content)
        else:
            return {}, 400

    def admin(self):
        auth = request.args.get('auth')
        if auth != current_app.config["SECRET_KEY"][:6]:
            content = {"version": self.data_.version}
            return make_response(render_template('404.html', **content), 404)
        all_countries = country_converter.CountryConverter().data["IOC"].dropna().to_list()
        first_records = None #foo.get_records(Federation.AIDA, all_countries[0], Gender.FEMALE)
        content = {"version": self.data_.version,
                   "competitions": self.data_.getSavedCompetitions(),
                   "comp_name": self.data_.name,
                   "all_countries": all_countries,
                   "record_sta": None}
        return render_template('template.html', **content)
