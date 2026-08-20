
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

import hmac
import logging
import time
from datetime import timedelta
from functools import wraps
from compy_data import CompyData
from compy_config import CompyConfig
from flask import Flask, render_template, request, send_file, Response, make_response, session, redirect, url_for
from os import path, mkdir
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.routing import IntegerConverter
try:
    import country_converter
except ImportError:
    print("Could not find country_converter. Install with 'pip3 install country_converter'")
    exit(-1)

class CompyFlask:
    """HTTP layer of Compy.

    This object holds no competition state. Every request builds its own
    CompyData (see getData) from the comp_id sent by the client, so any
    number of admin tabs, judge phones, clock displays and result pages can
    run concurrently without stepping on each other.
    """

    class SignedIntConverter(IntegerConverter):
        regex = r'-?\d+'

    def __init__(self, app, db, start_flask):

        self.app_ = app
        self.db_ = db
        self.config_ = CompyConfig()

        app.config['UPLOAD_FOLDER'] = self.config_.upload_folder
        app.url_map.converters['signed_int'] = self.SignedIntConverter

        # admin sessions are stored in a cookie signed with SECRET_KEY;
        # the cookie is not readable by page javascript and not sent on
        # cross-site requests (basic CSRF protection)
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        # one login lasts a full competition day
        app.permanent_session_lifetime = timedelta(hours=12)

        if not app.config.get('ADMIN_PASSWORD_HASH') and not app.config.get('ADMIN_PASSWORD'):
            logging.error("Neither FLASK_ADMIN_PASSWORD_HASH nor FLASK_ADMIN_PASSWORD is set "
                          "in the .env file; logging in to the admin interface is not possible")

        def admin_required(f):
            """Only allow the request if this browser has an admin session.

            The admin page itself redirects to the login form, all other
            (api) endpoints return 401 so the frontend can react.
            """
            @wraps(f)
            def wrapper(*args, **kwargs):
                if session.get('is_admin'):
                    return f(*args, **kwargs)
                if request.method == 'GET' and request.path == '/admin':
                    return redirect(url_for('login'))
                return self.unauthorized()
            return wrapper

        @app.route('/admin', methods=['GET'])
        @admin_required
        def admin():
            return self.admin()

        @app.route('/admin/login', methods=['GET', 'POST'])
        def login():
            return self.login()

        @app.route('/admin/logout', methods=['GET'])
        def logout():
            return self.logout()

        @app.route('/upload_file', methods=['POST'])
        @admin_required
        def uploadFile():
            return self.uploadFile()

        @app.route('/store_results', methods=['POST'])
        @admin_required
        def storeResults():
            return self.storeResults()

        @app.route('/upload_sponsor_img', methods=['POST'])
        @admin_required
        def uploadSponsorImg():
            return self.uploadSponsorImg()

        @app.route('/competition', methods=['POST', 'DELETE'])
        @admin_required
        def changeCompName():
            if request.method == 'POST':
                return self.changeCompName()
            elif request.method == 'DELETE':
                return self.deleteComp()

        @app.route('/change_special_ranking_name', methods=['POST'])
        @admin_required
        def changeSpecialRankingName():
            return self.changeSpecialRankingName()

        @app.route('/change_registration', methods=['POST'])
        @admin_required
        def changeRegistration():
            return self.changeRegistration()

        @app.route('/load_comp', methods=['POST'])
        @admin_required
        def loadComp():
            return self.loadComp()

        @app.route('/start_list', methods=['GET', 'PUT'])
        @admin_required
        def startList():
            if request.method == 'GET':
                return self.startList()
            elif request.method == 'PUT':
                return self.updateStartList()

        @app.route('/start_list_pdf', methods=['GET'])
        @admin_required
        def startListPDF():
            return self.startListPDF()

        @app.route('/breaks', methods=['GET'])
        @admin_required
        def breaks():
            return self.breaks()

        @app.route('/lane_list', methods=['GET'])
        @admin_required
        def laneList():
            return self.laneList()

        @app.route('/lane_list_pdf', methods=['GET'])
        @admin_required
        def laneListPDF():
            return self.laneListPDF()

        @app.route('/result', methods=['GET', 'PUT'])
        def result():
            if request.method == 'GET':
                # admin page only
                if not session.get('is_admin'):
                    return self.unauthorized()
                return self.result(False)
            elif request.method == 'PUT':
                # used by the admin page and by judge phones;
                # updateResult checks the admin session or the judge hash
                return self.updateResult()

        @app.route('/result_pdf', methods=['GET'])
        @admin_required
        def resultPDF():
            return self.result(True)

        @app.route('/change_lane_style', methods=['POST'])
        @admin_required
        def changeLaneStyle():
            return self.changeLaneStyle()

        @app.route('/change_comp_type', methods=['POST'])
        @admin_required
        def changeCompType():
            return self.changeCompType()

        @app.route('/change_selected_country', methods=['POST'])
        @admin_required
        def changeSelectedCountry():
            return self.changeSelectedCountry()

        @app.route('/judge', methods=['DELETE', 'POST'])
        @admin_required
        def judge():
            if request.method == 'DELETE':
                return self.deleteJudge()
            elif request.method == 'POST':
                return self.addJudge()

        @app.route('/judge/qr_code', methods=['GET'])
        @admin_required
        def judgeQrCode():
            return self.getJudgeQrCode()

        @app.route('/judges', methods=['GET'])
        @admin_required
        def judges():
            return self.getJudges()

        @app.route('/athlete', methods=['DELETE', 'POST'])
        @admin_required
        def athlete():
            if request.method == 'DELETE':
                return self.deleteAthlete()
            elif request.method == 'POST':
                return self.addAthlete()

        @app.route('/athletes', methods=['GET'])
        @admin_required
        def athletes():
            return self.getAthletes()

        @app.route('/national_records', methods=['GET'])
        @admin_required
        def nationalRecords():
            return self.nationalRecords()

        @app.route('/aida/settings', methods=['POST'])
        @admin_required
        def aidaSettings():
            return self.aidaSettings()

        @app.route('/aida/test', methods=['POST'])
        @admin_required
        def aidaTest():
            return self.aidaTest()

        @app.route('/aida/sync', methods=['POST'])
        @admin_required
        def aidaSync():
            return self.aidaSync()

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
        @admin_required
        def disciplines(federation):
            return self.disciplines(federation)

        @app.route('/block', methods=['POST', 'UPDATE', 'DELETE'])
        @admin_required
        def block():
            if request.method == 'POST':
                return self.modifyBlock(True)
            elif request.method == 'UPDATE':
                return self.modifyBlock(False)
            elif request.method == 'DELETE':
                return self.deleteBlock()

        @app.route('/clock/<int:comp_id>/<int:current>/<signed_int:offset>', methods=['GET'])
        def clock(comp_id, current, offset):
            return self.getClock(comp_id, current, offset)

        @app.route('/publish_results', methods=['UPDATE'])
        @admin_required
        def publish_results():
            return self.updatePublishResults()

        @app.route('/results', methods=['GET'])
        def results():
            return self.results()

        @app.route('/results_list', methods=['GET'])
        def resultsList():
            return self.resultsList()

        if start_flask:
            app.run()

    def version(self):
        # the version is cached on the CompyData class after the first read
        return CompyData(self.db_, self.app_).version

    def uploadFile(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
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
                comp.compFileChange(fpath)
                comp.getAthleteData(data)
                comp.getJudgeData(data)
                self.setSubmenuData(comp, data)
                comp.setOTs(data)
        data["status_msg"] = status_msg
        return data, 200

    def storeResults(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
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
                fpath = path.join(self.app_.config['UPLOAD_FOLDER'], filename)
                data_file.save(fpath)
                ret, file = comp.storeResults(fpath)
                if ret == 0:
                    return send_file(file, as_attachment=True)
        data["status_msg"] = status_msg
        return data, 200

    def uploadSponsorImg(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
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
                img_content = img_file.read()
                comp.changeSponsorImage(img_content)
        data["status_msg"] = status_msg
        return data, 200

    def changeRegistration(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if "id" not in content and "checked" not in content and "type" not in content:
            logging.debug("Post request to change_registration without id, type and checked")
            return {}, 400
        athlete_id = content["id"]
        is_checked = content["checked"]
        change_type = content["type"]
        if comp.setRegistration(athlete_id, is_checked, change_type) == 0:
            data = {"status": "success", "status_msg": "Successfully updated athlete with id '" + athlete_id + "' to value '" + str(is_checked) + "'"}
        else:
            data = {"status": "success", "status_msg": "Failed to update athlete with id '" + athlete_id + "' to value '" + str(is_checked) + "'"}
        data["disciplines"] = comp.getDisciplines()
        return data, 200

    def changeCompName(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if "comp_name" not in content and "overwrite" not in content:
            logging.debug("Post request to change_comp_name without comp_name and overwrite")
            return {}, 400
        comp_name = content["comp_name"]
        overwrite = content["overwrite"]
        data = comp.changeName(comp_name, overwrite)
        data['status'] = 'success'
        if data['file_exists']:
            data["status_msg"] = "File exists"
            data["prev_name"] = data['name']
        else:
            data["status_msg"] = "Successfully changed competition name to '" + comp_name + "'"
            data["prev_name"] = ""
        return data, 200

    def loadComp(self):
        content = request.json
        if "comp_id" not in content:
            logging.debug("Post request to load_comp without comp_id")
            return {}, 400
        comp = self.getData(request)
        if comp is None or not comp.isValid:
            return self.badRequest("Failed to load competition")
        comp_name = comp.name
        data = {}
        comp.getAthleteData(data)
        comp.getJudgeData(data)
        data["comp_name"] = comp_name
        self.setSubmenuData(comp, data)
        comp.setSpecialRankingName(data)
        comp.setOTs(data)
        data["lane_style"] = comp.lane_style
        data["comp_type"] = comp.comp_type
        data["selected_country"] = comp.selected_country
        data["publish_results"] = comp.publish_results
        comp.getAidaStatus(data)
        data["status"] = "success"
        data["status_msg"] = "Loaded competition with name " + comp_name
        logging.debug("Loaded comp " + comp_name + " with " + str(comp.number_of_athletes) + " athletes")
        return data, 200

    def startList(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        day = request.args.get('day')
        block = request.args.get('block')
        if day is None or block is None:
            logging.debug("Get request to start_list without day and block")
            return {}, 400
        data = {}
        start_list = comp.getStartList(day, block)
        if not start_list is None:
            data["start_list"] = start_list
            data["status"] = "success"
            data["status_msg"] = "Transfered start list for " + day + ": " + block
            return data, 200
        else:
            logging.debug("Could not get start list for " + day + ": " + block)
            return {}, 400

    def updateStartList(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if not self.dictHas(content, {'day', 'block', 'to_remove', 'startlist'}):
            logging.debug("Put request to start_list missing content: " + str(content.keys()))
            return {}, 400
        day = content["day"]
        block = content["block"]
        to_remove = content["to_remove"]
        startlist = content["startlist"]
        ret = comp.updateStartList(day, block, to_remove, startlist)
        start_list = comp.getStartList(day, block)
        if ret == 0 and not start_list is None:
            data = {"status": "success", "status_msg": "Successfully updated start list", "start_list": start_list}
            comp.setOTs(data)
            data["days_with_disciplines_lanes"] = comp.getDaysWithDisciplinesLanes()
            data["blocks"] = comp.getBlocks()
            return data, 200
        elif ret != 0 and not start_list is None:
            data = {"status": "success", "status_msg": "Failed database update", "start_list": start_list}
            return data, 400
        else:
            logging.debug("Could not update start list for " + day + " & " + block)
            return {}, 400

    def startListPDF(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        day = request.args.get('day')
        block = request.args.get('block')
        req_type = request.args.get('type')
        if (day is None or block is None) and req_type is None:
            logging.debug("Get request to start_list without day, block or type")
            return {}, 400
        data = {}
        if req_type is not None and req_type == "all":
            start_list_pdf = comp.getStartListPDF()
        else:
            start_list_pdf = comp.getStartListPDF(day, block)
        if not start_list_pdf is None:
            logging.debug("Sending: " + start_list_pdf)
            return send_file(start_list_pdf, as_attachment=True)
        else:
            logging.debug("Could not get start list for " + str(day) + ": " + str(block))
            return {}, 400

    def breaks(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        day = request.args.get('day')
        if day is None:
            logging.debug("Get request to breaks without day")
            return {}, 400
        data = {}
        breaks = comp.getBreaks(day)
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
        # TODO move to laneListNew once the query from compy.js has been updated
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        day = request.args.get('day')
        block = request.args.get('block')
        lane = request.args.get('lane')
        if day is None or block is None or lane is None:
            logging.debug("Get request to lane_list without day, block or lane")
            return {}, 400
        ret, content = comp.getLaneList(day, block, lane)
        if content is not None:
            content["status"] = "success"
            content["status_msg"] = "Transfered lane list for " + day + ": " + block + "/" + lane
            return content, 200
        else:
            logging.debug("Could not get lane list for " + day + ": " + block + "/" + lane)
            return {}, 400

    def laneListNew(self, comp):
        return self.handleRequest(request, ['day', 'block', 'lane'], CompyData.getLaneList, comp)

    def laneListPDF(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        day = request.args.get('day')
        block = request.args.get('block')
        lane = request.args.get('lane')
        req_type = request.args.get('type')
        if (day is None or block is None or lane is None) and req_type is None:
            logging.debug("Get request to lane_list without day, block, lane or type")
            return {}, 400
        data = {}
        if req_type is not None and (req_type == "all" or req_type == "safety"):
            lane_list_pdf = comp.getLaneListPDF(req_type == "safety")
        else:
            lane_list_pdf = comp.getLaneListPDF(False, day, block, lane)
        if not lane_list_pdf is None:
            logging.debug("Sending: " + lane_list_pdf)
            return send_file(lane_list_pdf, as_attachment=True)
        else:
            logging.debug("Could not get lane list for " + str(day) + ": " + str(block) + "/" + str(lane))
            return {}, 400

    def changeLaneStyle(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if "lane_style" not in content:
            logging.debug("Change request for lane style missing variable")
            return {}, 400
        option = content["lane_style"]
        if comp.changeLaneStyle(option) == 0:
            data = {}
            data["days_with_disciplines_lanes"] = comp.getDaysWithDisciplinesLanes()
            data["blocks"] = comp.getBlocks()
            data["status_msg"] = "Successfully changed lane style"
            data["status"] = "success"
            return data, 200
        else:
            logging.debug("Invalid lane style")
            return {}, 400

    def changeCompType(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if "comp_type" not in content:
            logging.debug("Change request for comp type missing variable")
            return {}, 400
        option = content["comp_type"]
        if comp.changeCompType(option) == 0:
            data = {}
            self.setSubmenuData(comp, data)
            data["status_msg"] = "Successfully changed comp type"
            data["status"] = "success"
            return data, 200
        else:
            logging.debug("Invalid comp type")
            return {}, 400

    def changeSelectedCountry(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if "selected_country" not in content:
            logging.debug("Change request for selected country missing variable")
            return {}, 400
        option = content["selected_country"]
        if comp.changeSelectedCountry(option) == 0:
            data = {}
            self.setSubmenuData(comp, data)
            data["status_msg"] = "Successfully changed selected country"
            data["status"] = "success"
            return data, 200
        else:
            logging.debug("Invalid country selected")
            return {}, 400

    def setSubmenuData(self, comp, data):
        data["days_with_disciplines_lanes"] = comp.getDaysWithDisciplinesLanes()
        data["blocks"] = comp.getBlocks()
        data["disciplines"] = comp.getDisciplines()
        data["countries"] = comp.getCountries()
        data["result_countries"] = comp.getCountries(True)

    def dictHas(self, d, keys):
        if isinstance(keys, set):
            return d.keys() >= keys
        else:
            return keys in d

    def result(self, pdf):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        discipline = request.args.get('discipline')
        gender = request.args.get('gender')
        country = request.args.get('country')
        req_type = request.args.get('type')
        if (discipline is None or gender is None or country is None) and (req_type is None or not pdf):
            logging.debug("Get request to result without discipline, gender, country or type")
            return {}, 400
        if pdf:
            if req_type == "all":
                result_pdf = comp.getResultPDF()
            elif req_type == "top3":
                result_pdf = comp.getResultPDF("all", "all", "all", False, True)
            elif req_type == "single" or req_type is None:
                result_pdf = comp.getResultPDF(discipline, gender, country)
            if not result_pdf is None:
                logging.debug("Sending: " + result_pdf)
                return send_file(result_pdf, as_attachment=True)
        else:
            return self.getResultDiscipline(request, comp)
        logging.debug("Could not get result for " + str(discipline) + "/" + str(gender) + " country: " + str(country))
        return {}, 400

    def getResultDiscipline(self, request, comp):
        return self.handleRequest(request, ['discipline', 'gender', 'country'], CompyData.getResult, comp)

    def updateResult(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        # results are entered by the admin page (session cookie) or by a
        # judge phone (judge id + hash in the request body)
        if not session.get('is_admin') and not self.isValidJudge(request, comp):
            return self.unauthorized()
        content, status = self.handleRequest(request, ['id', 'rp', 'penalty', 'card', 'remarks', 'judge_remarks'], CompyData.updateResult, comp)
        if status != 200:
            logging.debug("Failed to set result")
            return self.badRequest("Failed to set result")
        if self.dictHas(request.json, {"discipline", "gender", "country"}):
            return self.getResultDiscipline(request, comp)
        else:
            return self.handleRequest(request, ['id'], CompyData.getAthleteResult, comp)

    def changeSpecialRankingName(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if "special_ranking_name" not in content:
            logging.debug("Post request to change_special_ranking_name without special_ranking_name")
            return {}, 400
        special_ranking_name = content["special_ranking_name"]
        comp.changeSpecialRankingName(special_ranking_name)
        data = {"status": "success", "status_msg": "Successfully changed special ranking name to '" + special_ranking_name + "'"}
        self.setSubmenuData(comp, data)
        return data, 200

    def deleteJudge(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
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
        judge_id = comp.isJudgeInCompetition(judge_id)
        if judge_id is not None:
            comp.deleteJudge(judge_id)
            data = {"status": "success", "status_msg": "Successfully deleted judge with id " + str(judge_id)}
            comp.getJudgeData(data)
            return data, 200
        else:
            logging.info('Invalid judge id provided')
            return {}, 400

    def getJudgeQrCode(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
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
        judge_id = comp.isJudgeInCompetition(judge_id)
        if judge_id is not None:
            qr_data = comp.getJudgeQrCode(judge_id, request.url_root)
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
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if False in [key in content for key in ['first_name', 'last_name']]:
            logging.info("Could not add judge due to missing data")
            return {}, 400
        first_name = content['first_name']
        last_name = content['last_name']
        if first_name is None or last_name is None:
            logging.info("Could not add judge with incomplete information")
            return {}, 400
        status = comp.addJudge(first_name, last_name)
        data = {}
        if status == 0:
            data = {"status": "success", "status_msg": "Successfully added judge"}
            comp.getJudgeData(data)
            return data, 200
        elif status == 1:
            data = {"status": "error", "status_msg": "Judge already exists"}
            comp.getJudgeData(data)
            return data, 200

    def getJudges(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        data = {"status": "success", "status_msg": "Successfully received judge data"}
        comp.getJudgeData(data)
        return data, 200

    def deleteAthlete(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
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
        ca_id, in_other_comp = comp.isAthleteInCompetition(athlete_id)
        if ca_id is not None:
            comp.deleteAthlete(ca_id, athlete_id, in_other_comp)
            data = {"status": "success", "status_msg": "Successfully deleted athlete with id " + str(athlete_id) + (" completely" if not in_other_comp else "")}
            comp.getAthleteData(data)
            self.setSubmenuData(comp, data)
            comp.setOTs(data)
            return data, 200
        else:
            logging.info('Invalid athlete id provided')
            return {}, 400

    def addAthlete(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
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
        status = comp.addAthlete(first_name, last_name, gender, country, club, aida_id)
        data = {}
        if status == 0:
            data = {"status": "success", "status_msg": "Successfully added athlete"}
            comp.getAthleteData(data)
            return data, 200
        elif status == 1:
            data = {"status": "error", "status_msg": "Athlete already exists"}
            return data, 200
        else:
            logging.info("Could not add athlete due to invalid arguments")
            return {}, 400

    def getAthletes(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        data = {"status": "success", "status_msg": "Successfully received athlete data"}
        comp.getAthleteData(data)
        return data, 200

    def nationalRecords(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        ret, content = comp.updateNationalRecords()
        if ret != 0:
            # like the /aida routes: 200 with an admin-readable message
            msg = (content or {}).get("error_msg",
                                      "Updating the records failed")
            return {"status": "error", "status_msg": msg}, 200
        return {"status": "success",
                "status_msg": "National records updated"}, 200

    def aidaSettings(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if "aida_event_id" not in content:
            logging.debug("Post request to aida/settings without aida_event_id")
            return {}, 400
        ret, data = comp.setAidaSettings(content.get("aida_event_id"),
                                         content.get("aida_api_key"))
        if ret == 0:
            data["status"] = "success"
            data["status_msg"] = "Saved AIDA API settings"
        else:
            data["status"] = "error"
            data["status_msg"] = data.pop("error_msg")
        return data, 200

    def aidaTest(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        ret, data = comp.testAidaConnection()
        if ret == 0:
            data["status"] = "success"
            data["status_msg"] = ("Connection OK: '" + data["event_name"]
                                  + "' with " + str(len(data["days"]))
                                  + " day(s): " + ", ".join(data["days"]))
        else:
            data["status"] = "error"
            data["status_msg"] = data.pop("error_msg")
        return data, 200

    def aidaSync(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        ret, data = comp.syncFromAida()
        if ret != 0:
            return {"status": "error",
                    "status_msg": data["error_msg"]}, 200
        msg = ("Sync from AIDA complete: "
               + str(data["athletes_added"]) + " athlete(s) added, "
               + str(data["athletes_updated"]) + " updated; "
               + str(data["starts_added"]) + " start(s) added, "
               + str(data["starts_updated"]) + " updated; "
               + str(data["days_synced"]) + " day(s)")
        if len(data["only_local"]) > 0:
            msg += ("<br>Only in Compy (kept, not on AIDA): "
                    + ", ".join(data["only_local"]))
        for warning in data["warnings"]:
            msg += "<br>Warning: " + warning
        data["status"] = "success"
        data["status_msg"] = msg
        # the sync changes athletes, blocks and starts: refresh everything
        # the admin page displays, like an excel upload does
        comp.getAthleteData(data)
        comp.getJudgeData(data)
        self.setSubmenuData(comp, data)
        comp.setOTs(data)
        return data, 200

    def getJudgeComp(self, comp_id, judge_id, return_json = False):
        judge_hash = request.args.get('hash')
        # the judge page gets its own CompyData; validating or loading it can
        # not interfere with any other page that is open at the same time
        comp = CompyData(self.db_, self.app_, comp_id)
        ret, comp_data = comp.getCompDataAndValidateJudge(comp_id, judge_id, judge_hash)
        if comp_data is None:
            content = {"version": self.version()}
            return make_response(render_template('404.html', **content), 404)

        comp_name = comp_data['comp_name']
        first_name = comp_data['first_name']
        last_name = comp_data['last_name']
        federation = comp_data['federation']

        content = {"version": comp.version,
                   "comp_id": comp_id,
                   "comp_name": comp_name,
                   "judge_id": judge_id,
                   "judge_hash": judge_hash,
                   "judge_first_name": first_name,
                   "judge_last_name": last_name,
                   "federation": federation,
                   "days_with_disciplines_lanes": comp.getDaysWithDisciplinesLanes(),
                   "blocks": comp.getBlocks()}
        if return_json:
            return content, 200
        else:
            return render_template('judge.html', **content)

    def isValidJudge(self, request, comp):
        try:
            comp_id = self.parse(request, 'comp_id')
            judge_id = self.parse(request, 'judge_id')
            judge_hash = self.parse(request, 'judge_hash')
        except:
            return False
        ret, content = comp.getCompDataAndValidateJudge(comp_id, judge_id, judge_hash)
        return ret == 0

    def getJudgeAthletes(self):
        comp = self.getData(request)
        if comp is None or not self.isValidJudge(request, comp):
            content = {"version": self.version()}
            return make_response(render_template('404.html', **content), 404)

        return self.laneListNew(comp)

    def getJudgeAthleteResult(self):
        comp = self.getData(request)
        if comp is None or not self.isValidJudge(request, comp):
            logging.debug("Not a valid judge")
            return {}, 400

        return self.handleRequest(request, ['s_id'], CompyData.getAthleteResult, comp)

    def disciplines(self, federation):
        comp = CompyData(self.db_, self.app_)
        disciplines = comp.getAllDisciplines(federation)
        if disciplines is None:
            return {}, 400
        else:
            data = {"status": "success", "disciplines": disciplines}
            return data, 200

    def modifyBlock(self, add):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
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
        ret = comp.modifyBlock(day, disciplines, block, add)
        data = None
        if ret == 0:
            data = {"status": "success", "status_msg": "Successfully updated block"}
        elif ret == 1:
            data = {"status": "success", "status_msg": "Could not add block, already exists"}
        elif ret == 2:
            data = {"status": "success", "status_msg": "Could not edit block, does not exist"}
        if data is not None:
            data["days_with_disciplines_lanes"] = comp.getDaysWithDisciplinesLanes()
            data["blocks"] = comp.getBlocks()
            return data, 200
        else:
            return {}, 400

    def deleteBlock(self):
        comp = self.getData(request)
        if comp is None:
            return self.badRequest("Failed to load competition")
        content = request.json
        if False in [key in content for key in ['block']]:
            logging.info("Could not remove block due to missing data")
            return {}, 400
        block = content['block']
        if block is None:
            logging.info("Could not remove block with incomplete information")
            return {}, 400
        ret = comp.removeBlock(block)
        data = None
        if ret == 0:
            data = {"status": "success", "status_msg": "Successfully removed block"}
        elif ret == 1:
            data = {"status": "success", "status_msg": "Could not remove block, does not exist"}
        if data is not None:
            data["days_with_disciplines_lanes"] = comp.getDaysWithDisciplinesLanes()
            data["blocks"] = comp.getBlocks()
            return data, 200
        else:
            return {}, 400

    def getClock(self, comp_id, current, offset):
        current = (current+1) % 2
        # the clock page gets its own CompyData, so the periodic reload of an
        # open clock display no longer changes any global state
        comp = CompyData(self.db_, self.app_, comp_id)
        if not comp.isValid:
            return {}, 400
        alist = comp.getFourStarts(current == 0, offset)
        if alist is None:
            current = (current+1) % 2
            alist = comp.getFourStarts(current == 0, offset)
        url = request.base_url
        refresh_url = url[:url.rfind('/', 0, url.rfind('/'))+1] + str(current) + "/" + str(offset)
        content = {"comp_name": comp.name,
                   "comp_id": comp_id,
                   "alist": alist,
                   "current": current,
                   "refresh_url": refresh_url,
                   "offset": offset}
        return render_template('clock.html', **content)

    def checkAdminPassword(self, password):
        """Compare a login attempt against the configured admin password.

        FLASK_ADMIN_PASSWORD_HASH (a werkzeug password hash, recommended
        for deployments) takes precedence over the plain text
        FLASK_ADMIN_PASSWORD. Both comparisons are constant time. If
        neither is configured, logging in is not possible.
        """
        pw_hash = self.app_.config.get('ADMIN_PASSWORD_HASH')
        if pw_hash:
            return check_password_hash(pw_hash, password)
        pw = self.app_.config.get('ADMIN_PASSWORD')
        if pw:
            return hmac.compare_digest(str(pw).encode('utf-8'), password.encode('utf-8'))
        return False

    def login(self):
        if session.get('is_admin'):
            return redirect(url_for('admin'))
        error = None
        if request.method == 'POST':
            password = request.form.get('password', '')
            if self.checkAdminPassword(password):
                session.clear()
                session['is_admin'] = True
                session.permanent = True
                logging.info("Admin login from " + str(request.remote_addr))
                return redirect(url_for('admin'))
            # throttle brute force attempts
            time.sleep(1)
            logging.warning("Failed admin login attempt from " + str(request.remote_addr))
            error = "Wrong password"
        content = {"version": self.version(), "error": error}
        return make_response(render_template('login.html', **content), 401 if error else 200)

    def logout(self):
        session.clear()
        return redirect(url_for('login'))

    def unauthorized(self):
        return {"status": "error", "error_msg": "Authentication required"}, 401

    def admin(self):
        all_countries = country_converter.CountryConverter().data["IOC"].dropna().to_list()
        # the admin frontend loads competition 1 after the page is ready, so
        # pre-fill the name field with that competition
        comp = CompyData(self.db_, self.app_, 1)
        content = {"version": comp.version,
                   "competitions": comp.getSavedCompetitions(),
                   "comp_name": comp.name,
                   "all_countries": all_countries,
                   "record_sta": None}
        return render_template('template.html', **content)

    def results(self):
        comp = self.getData(request, published_only = True)
        if comp is None:
            return self.badRequest("Failed to load competition")
        ret, content = comp.getResultContent()
        return render_template('results.html', **content)

    def updatePublishResults(self):
        return self.handleRequest(request, ['publish_results'], CompyData.updatePublishResults)

    def resultsList(self):
        return self.handleRequest(request, ['discipline', 'gender', 'country'], CompyData.getResultList, published_only = True)

    def handleRequest(self, request, args, func, comp = None, published_only = False):
        if comp is None:
            comp = self.getData(request, published_only)
        if comp is None:
            return self.badRequest("Failed to load competition to call " + func.__name__)

        if args is not None:
            try:
                args_val = [self.parse(request, arg) for arg in args]
            except RuntimeError as re:
                return self.badRequest(re)
            except:
                return {}, 400
            ret, content = func(comp, *args_val)
        else:
            ret, content = func(comp)
        if ret == 0:
            if content is None:
                content = {"status": "success", "status_msg": "Successfully called " + func.__name__}
            else:
                content |= {"status": "success", "status_msg": "Successfully called " + func.__name__}
            return content, 200
        else:
            return self.badRequest("Failed to call " + func.__name__)

    def badRequest(self, msg):
        return {"status": "error", "error_msg": msg}, 400

    def getData(self, request, published_only = False):
        """Build the CompyData for this request from its comp_id.

        The comp_id is taken from the json body, form data or query string.
        Returns None if a comp_id was provided but no matching (or, with
        published_only, no published) competition exists. Without a comp_id
        an empty CompyData is returned for endpoints that do not need a
        loaded competition (e.g. national records).
        """
        try:
            comp_id = self.parse(request, 'comp_id', True)
            if comp_id == "" or comp_id == "null":
                comp_id = None
        except Exception as e:
            logging.debug(e)
            return None
        data = CompyData(self.db_, self.app_, comp_id, published_only)
        if comp_id is not None and not data.isValid:
            return None
        return data

    def parse(self, request, key, allow_none = False):
        content = None
        found = False
        if request.is_json:
            try:
                content = request.json[key]
                found = True
            except:
                pass
        if not found and key in request.form:
            content = request.form[key]
            found = True
        if not found:
            try:
                content = request.args.get(key)
            except:
                raise RuntimeError("Could not get key " + key + " from request object")
        if content is None and not allow_none:
            raise RuntimeError("Could key " + key + " from request object is not set")
        return content

    def deleteComp(self):
        comp = CompyData(self.db_, self.app_)
        comp_id = request.json.get('comp_id')
        ret, data = comp.deleteComp(comp_id)
        return data
