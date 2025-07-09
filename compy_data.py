
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
    import pandas as pd
except ImportError:
    print("Could not find pandas. Install with 'pip3 install pandas'")
    exit(-1)
import logging
from collections import Counter, namedtuple
try:
    import requests
except ImportError:
    print("Could not find requests. Install with 'pip3 install requests'")
    exit(-1)
try:
    import qrcode
except ImportError:
    print("Could not find qrcode. Install with 'pip3 install qrcode'")
    exit(-1)
import hashlib
import math
import random
import re
from packaging.version import Version
try:
    import country_converter
    assert Version(country_converter.version.__version__) >= Version("1.2")
except ImportError:
    print("Could not find country_converter. Install with 'pip3 install country_converter'")
    exit(-1)
except AssertionError:
    print("country_converter found with version", country_converter.version.__version__, "but version >= 1.2 required, please update it.")
    exit(-1)
import os
import json
import glob
from datetime import datetime, timedelta, time
from io import BytesIO
import flask
try:
    import weasyprint as wp
except ImportError:
    print("Could not find weasyprint. Install with 'pip3 install weasyprint'")
    exit(-1)
import base64
from PIL import Image
from io import BytesIO
import numpy as np
import regex
import sys

import athlete
from compy_config import CompyConfig

import compy_utilities as u

INVALID_DATE="0000-00-00"
INVALID_TIME="99:99"
DISCIPLINES=["FIM", "CNF", "CWT", "CWTB", "STA", "DNF", "DYN", "DYNB"]
FEDERATIONS=["aida", "cmas"]

class CompyData:

    def __init__(self, db, app):
        self.id_ = None
        self.db_ = db
        self.app_ = app
        self.name_ = "undefined"
        self.special_ranking_name_ = "Newcomer"
        self.config_ = CompyConfig()
        self.version_ = None
        self.lane_style_ = "numeric"
        self.comp_type_ = FEDERATIONS[0]
        self.comp_file_ = ''
        self.start_date_ = None
        self.end_date_ = None
        self.nrs_ = None
        self.sponsor_img_ = None
        self.disciplines_ = 0
        self.selected_country_ = None
        self.publish_results_ = False

        self.NR = namedtuple("NR", ["federation", "country", "cls", "gender", "discipline"])

        self.name_ = "undefined"

        with self.app_.app_context():
            #self.updateNationalRecords();
            # try and find it first
            c_id = self.db_.execute("SELECT id FROM competition WHERE name=?", self.name_)
            if c_id is not None:
                self.load(c_id[0][0])
            else:
                self.save()

    @property
    def version(self):
        if self.version_ is None:
            base_path = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(base_path, 'VERSION'), 'r') as f:
                self.version_ = str(f.read().strip())
        return self.version_

    @property
    def name(self):
        return self.name_

    @property
    def special_ranking_name(self):
        return self.special_ranking_name_

    @property
    def publish_results(self):
        return self.publish_results_

    @property
    def config(self):
        return self.config_

    @property
    def lane_style(self):
        return self.lane_style_

    def changeLaneStyle(self, lane_style):
        allowed_lane_styles = ["numeric", "alphabetic"]
        if lane_style not in allowed_lane_styles:
            return 1
        self.lane_style_ = lane_style
        self.save()
        return 0

    @property
    def comp_type(self):
        return self.comp_type_

    def changeCompType(self, comp_type):
        if comp_type not in FEDERATIONS:
            return 1
        self.comp_type_ = comp_type
        self.save()
        return 0

    def laneStyleConverter(self, lane, invert=False):
        if invert:
            if self.lane_style_ == "alphabetic":
                return ord(lane) - 64
            else: # numeric
                return int(lane)
        else:
            if self.lane_style_ == "alphabetic":
                return chr(lane + 64)
            else: # numeric
                return str(lane)

    @property
    def comp_file(self):
        return self.comp_file_

    @property
    def number_of_athletes(self):
        db_out = self.db_.execute("SELECT COUNT(*) FROM competition_athlete WHERE competition_id=?", self.id_)
        if db_out is None:
            return 0
        else:
            return db_out[0][0]

    @property
    def start_date(self):
        return self.start_date_

    @property
    def end_date(self):
        return self.end_date_

    @property
    def disciplines(self):
        return self.getDisciplinesFromInt(self.disciplines_)

    @property
    def sponsor_img_data(self):
        if self.sponsor_img_ is None:
            return ""
        else:
            return self.sponsor_img_["data"]

    @property
    def countries(self):
        if self.id_ is None:
            return None
        c_data = self.db_.execute('''SELECT DISTINCT athlete.country FROM athlete
                                     INNER JOIN competition_athlete
                                     ON athlete.id==competition_athlete.athlete_id
                                     WHERE competition_athlete.competition_id==?''',
                         self.id_)
        if c_data is None:
            return []
        return [c[0] for c in c_data]

    @property
    def sponsor_img_width(self):
        if self.sponsor_img_ is None:
            return 0
        else:
            aspect_ratio = self.sponsor_img_["aspect_ratio"]
            if aspect_ratio < 1:
                return 19.*self.sponsor_img_["aspect_ratio"]
            else:
                return 19.

    @property
    def sponsor_img_height(self):
        if self.sponsor_img_ is None:
            return 0
        else:
            aspect_ratio = self.sponsor_img_["aspect_ratio"]
            if aspect_ratio > 1:
                return 5./self.sponsor_img_["aspect_ratio"]
            else:
                return 5.

    @property
    def selected_country(self):
        if self.selected_country_ is None:
            return "none"
        else:
            return self.selected_country_

    @property
    def nr(self):
        if self.nrs_ is None:
            nrs = self.db_.execute('''SELECT country, class, gender, discipline, value
                                      FROM records
                                      WHERE federation=?''',
                                   self.comp_type)
            if nrs is None:
                return None
            self.nrs_ = {}
            for nr in nrs:
                self.nrs_[self.NR(self.comp_type, nr[0], nr[1], nr[2], nr[3])] = nr[4]
        return self.nrs_

    def changeSponsorImage(self, img_content):
        self.sponsor_img_ = {}
        img_base64 = base64.b64encode(img_content).decode('utf-8')
        self.sponsor_img_["data"] = 'data:image/png;base64,' + img_base64
        img = Image.open(BytesIO(img_content))
        width, height = img.size # in pixels
        self.sponsor_img_["aspect_ratio"] = float(width)*5./float(height)/19. # < 1 if too high, > 1 if too wide
        self.save()

    def compFileChange(self, comp_file):
        self.comp_file_ = comp_file
        self.refresh()

    def refresh(self):
        # special ranking ids of athletes
        srd_ids = None
        if self.id_ is not None:
            sr_ids = self.db_.execute(
                '''SELECT a.id FROM athlete a
                   INNER JOIN competition_athlete ca ON a.id == ca.athlete_id
                   WHERE ca.special_ranking AND ca.competition_id==?''',
                self.id_)
            self.db_.execute('''DELETE FROM start
                                WHERE competition_athlete_id IN (
                                    SELECT competition_athlete_id FROM start
                                    INNER JOIN competition_athlete
                                    ON start.competition_athlete_id == competition_athlete.id
                                    WHERE competition_athlete.competition_id == ?)''',
                             self.id_)
            self.db_.execute("DELETE FROM competition_athlete WHERE competition_id=?", self.id_)
        # read first sheet (start & end date)
        if not os.path.exists(self.comp_file_):
            logging.error("File '%s' does not exist", self.comp_file_)
            return
        df = pd.read_excel(self.comp_file_, sheet_name="Event")
        i = 0
        for l in df[df.keys()[0]]:
            if l == "Starts:":
                self.start_date_ = df[df.keys()[1]][i]
            if l == "Ends:":
                self.end_date_ = df[df.keys()[1]][i]
            if l == "Disciplines:":
                self.disciplines_ = self.disciplineListToInt(df[df.keys()[1]][i].split(","))
            i += 1
        logging.debug("Start date: %s. End date: %s", self.start_date_, self.end_date_)

        # read second sheet (list of athletes)
        df = pd.read_excel(self.comp_file_, sheet_name="Athletes and Judges", skiprows=1)
        for i,r in df.iterrows():
            a = athlete.Athlete.fromArgs(r['Id'], r['FirstName'], r['LastName'], r['Gender'], r['Country'], r['Club'] if 'club' in r else "", self.db_)
            logging.debug("Athlete: %s %s %s %s %s", r['Id'], r['FirstName'], r['LastName'], r['Gender'], r['Country'])
            a.associateWithComp(self.id_)
        logging.debug("Number of athletes: %d", self.number_of_athletes)

        if sr_ids is not None:
            for sr in sr_ids:
                self.setRegistration(sr[0], True, False, "specialranking")

        self.save()

        ap_lambda = lambda x, y, d, self: None if math.isnan(x) else (int(x)*60+float(y) if d=="STA" else float(x))
        self.db_.execute('''DELETE FROM block WHERE competition_id == ?''',
                         self.id_)
        for day in self.getDaysExcel(self.start_date, self.end_date):
            df = pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1)
            blocks = {}
            day_db = day.replace('-', '')
            for i,r in df.iterrows():
                dis = r['Discipline']
                if not dis in blocks.keys():
                    self.db_.execute('''INSERT INTO block
                                        (competition_id, day, disciplines)
                                        VALUES (?, ?, ?)''',
                                     (self.id_, day_db, self.disciplineListToInt([dis])))
                    blocks[dis] = self.db_.last_index
            for i,r in df.iterrows():
                aida_id = r['Diver Id']
                ca_id = self.db_.execute('''SELECT competition_athlete.id FROM competition_athlete
                                            INNER JOIN athlete
                                            ON competition_athlete.athlete_id == athlete.id
                                            WHERE athlete.aida_id=? AND competition_athlete.competition_id == ?''',
                                         (aida_id, self.id_))
                dis = r['Discipline']
                ap = ap_lambda(r['Meters or Min'], r['Sec(STA only)'], dis, self)
                ot = self.parseTime(r['OT'])
                lane = int(r['Zone'])
                rp = ap_lambda(r['Meters or Min.1'], r['Sec(STA only).1'], dis, self)
                card = r['Card']
                pen_other = float(r['Pen(other)']) if not math.isnan(r['Pen(other)']) else 0.
                penalty = float(r['Pen(UNDER AP)']) + pen_other
                remarks = r['Remarks']
                if remarks == "DNS":
                    rp = float('nan')
                    card = "nan"
                    penalty = "nan"
                block = blocks[dis]
                print(block, dis, blocks)
                if rp is not None:
                    self.db_.execute('''INSERT INTO start
                                        (competition_athlete_id, discipline, lane, OT, AP, day,
                                         rp, card, penalty, remarks, block)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                     (ca_id[0][0], dis, lane, u.convTime(ot), ap, u.convDay(day), rp, card, penalty, remarks, block))
                else:
                    self.db_.execute('''INSERT INTO start
                                        (competition_athlete_id, discipline, lane, OT, AP, day, block)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                     (ca_id[0][0], dis, lane, u.convTime(ot), ap, u.convDay(day), block))

    def getNationalRecordsAida(self):
        empty_req = requests.post('https://www.aidainternational.org/public_pages/all_national_records.php', data={})
        html = empty_req.text
        start = html.find('id="nationality"')
        start = html.find('<option', start)
        end = html.find('</select>', start)
        nationalities = str.splitlines(html[start:end])
        p = re.compile("<option.*value=\"([0-9]+)\">(.*)</option>")
        country_value_map = {}
        cc = country_converter.CountryConverter()
        for n in nationalities:
            result = p.search(n)
            if result:
                country_value_map[cc.convert(result.group(2), to = 'IOC')] = result.group(1)
        nrs = {}
        for c_ioc, c_str in country_value_map.items():
            data = {
                'nationality': str(c_str),
                'discipline': '',
                'gender': '',
                'apply': ''
            }
            req = requests.post('https://www.aidainternational.org/public_pages/all_national_records.php', data=data)
            html = req.text
            start = html.find('<tbody>')
            start = html.find('<tr>', start)
            end = html.find('</tbody>', start)
            entries = str.splitlines(html[start:end])[:-1]
            p = re.compile("<td>(.*)</td>")
            for i in range(int(len(entries)/10)):
                gender = p.search(entries[i*10 + 2]).group(1)
                dis = p.search(entries[i*10 + 3]).group(1)
                res_str = p.search(entries[i*10 + 4]).group(1)
                result = 0.
                if dis == "STA":
                    p_dis = re.compile("([0-9]+):([0-9][0-9])")
                    res_re = p_dis.search(res_str)
                    result = float(res_re.group(1))*60.0 + float(res_re.group(2))
                else:
                    p_dis = re.compile("[0-9]+")
                    result = float(p_dis.search(res_str).group(0))
                points = float(p.search(entries[i*10 + 6]).group(1))
                nrs[self.NR(federation="aida", country=c_ioc, cls="", gender=gender, discipline=dis)] = result
        logging.debug("National records:")
        logging.debug("Country | Gender | Discipline | Result | Points")
        for key, val in nrs.items():
            logging.debug("%s | %s | %s | %s | %d", key.country, key.gender, key.discipline, val)
        logging.debug("-----------------")
        return nrs

    def setRegistration(self, athlete_id, special_ranking, change_type, warn=True):
        found = False
        if self.number_of_athletes == 0:
            logging.warning("Data not initialized yet in setRegistration")
            return 1
        try:
            type_map = {'specialranking': 'special_ranking', 'paid': 'paid', 'medicalchecked': 'medical_checked', 'registered': 'registered'}
            if not change_type in type_map:
                return 0
            self.db_.execute(
                '''UPDATE competition_athlete SET {}=?
                   WHERE competition_id==? AND athlete_id==?'''.format(type_map[change_type]),
                (special_ranking, self.id_, athlete_id))
            return 0
        except sqlite3.Error as e:
            if warn:
                logging.warning("Tried setting " + change_type + " (" + str(special_ranking) + ") to athlete with id '" + athlete_id + "' but this id could not be found")
            return 1

    def getSavedCompetitions(self):
        os.chdir(self.config.storage_folder)
        saved_comp_info = []
        comps = self.db_.execute("SELECT id, name, save_date FROM competition")
        if comps is None:
            return None
        for comp in comps:
            saved_comp_info.append({"comp_id": comp[0], "name": comp[1], "save_date": comp[2]})
        return sorted(saved_comp_info, key=lambda ci: ci["save_date"], reverse=True)

    def changeName(self, new_name, overwrite):
        comp_id = self.db_.execute("SELECT id FROM competition WHERE name=?", new_name)
        if not comp_id is None and not overwrite:
            return [1, self.name_]
        else:
            self.name_ = new_name
            if comp_id is None:
                self.id_ = None
            else:
                self.id_ = comp_id[0][0]
            self.save()
            return [0, self.name_]

    def save(self):
        # force version update
        self.version_ = None
        if self.id_ is None:
            self.db_.execute('''INSERT INTO competition
                                (name, save_date, version, lane_style, comp_type, comp_file, start_date,
                                 end_date, disciplines)
                                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                             (self.name_, datetime.now().isoformat(), self.version,
                              self.lane_style, self.comp_type, self.comp_file,
                              self.start_date_, self.end_date_, self.disciplines_))
            self.id_ = self.db_.last_index
        sponsor_img_data = ""
        if self.sponsor_img_ is not None:
            sponsor_img_data = self.sponsor_img_["data"]
        self.db_.execute('''UPDATE competition
                            SET name=?, save_date=?, version=?, lane_style=?, comp_type=?, comp_file=?,
                            start_date=?, end_date=?, sponsor_img=?, selected_country=?,
                            special_ranking_name=?, disciplines=? WHERE id=?''',
                         (self.name_, datetime.now().isoformat(), self.version, self.lane_style, self.comp_type,
                          self.comp_file, self.start_date_, self.end_date_, sponsor_img_data,
                          self.selected_country_, self.special_ranking_name, self.disciplines_,
                          self.id_))
        logging.debug("Saved competition: " + self.name)

    def load(self, comp_id):
        #TODO on load find self.id_ if not, reset to None
        load_data = self.db_.execute('''SELECT name, version, lane_style, comp_type, comp_file,
                                        start_date, end_date, sponsor_img, selected_country,
                                        special_ranking_name, publish_results
                                        FROM competition WHERE id=?''',
                                     comp_id)
        if load_data is None:
            logging.error("Could not find save file with id '" + id + "'")
            return None
        else:
            self.id_ = comp_id
            comp_data = load_data[0]
            self.name_ = comp_data[0]
            self.version_ = comp_data[1]
            self.lane_style_ = comp_data[2]
            self.comp_type_ = comp_data[3]
            self.comp_file_ = comp_data[4]
            self.start_date_ = comp_data[5]
            self.end_date_ = comp_data[6]
            self.sponsor_img_ = {"data": comp_data[7], "aspect_ratio": 1} # TODO
            self.selected_country_ = comp_data[8]
            self.special_ranking_name_ = comp_data[9]
            self.publish_results_ = comp_data[10]
            dis = self.db_.execute('SELECT disciplines FROM block WHERE competition_id==?', (self.id_))
            self.disciplines_ = 0
            if dis is not None:
                for d in dis:
                    self.disciplines_ |= d[0]
            #self.getResultPDF('all', 'all', 'all', False, True)
            return self.name_

    def getDaysExcel(self, start_date, end_date):
        if start_date is None:
            return
        days = []
        d0 = datetime.strptime(start_date, '%Y-%m-%d')
        d1 = datetime.strptime(end_date, '%Y-%m-%d')
        delta = d1 - d0
        for i in range(delta.days + 1):
            yield (d0 + timedelta(days=i)).strftime('%Y-%m-%d')

    def getDays(self):
        days = self.db_.execute('''SELECT day FROM block WHERE competition_id==?''', self.id_)
        if days is None:
            return
        for day in days:
            yield u.convDay(day[0])

    def getBlocks(self):
        day_block_lane = {}
        for day in self.getDays():
            blocks = self.db_.execute('SELECT id, disciplines FROM block WHERE competition_id==? AND day==?', (self.id_, u.convDay(day)))
            if blocks is None:
                continue
            block_lane = {}
            for block in blocks:
                lanes = self.db_.execute('SELECT DISTINCT lane FROM start s WHERE s.block==? ORDER BY lane', block[0])
                if lanes is not None:
                    lanes = [self.laneStyleConverter(l[0]) for l in lanes]
                dis_s = self.disciplineIntToStr(block[1])
                block_lane[block[0]] = {'dis_s': dis_s, 'lanes': lanes}
            day_block_lane[day] = block_lane
        return day_block_lane

    def getDaysWithDisciplinesLanes(self, internal=False):
        dwd = {}
        for day in self.getDays():
            db_out = self.db_.execute('''SELECT DISTINCT discipline, lane FROM start s
                                         INNER JOIN competition_athlete ca
                                         ON s.competition_athlete_id == ca.id
                                         WHERE (ca.competition_id==? AND s.day==?)''',
                                      (self.id_, u.convDay(day)))
            if db_out is None:
                continue
            disciplines_on_day = list({d[0] for d in db_out})
            disciplines_w_lanes = {}
            for dis in disciplines_on_day:
                disciplines_w_lanes[dis] = [d[1] if internal else self.laneStyleConverter(d[1]) for d in db_out if d[0]==dis]
            dwd[day] = disciplines_w_lanes
        logging.debug("dwd:" + str(dwd))
        return dwd

    def getDisciplines(self):
        if self.disciplines is None:
            return []
        dwc = []
        # only aida has Overall and SpecialRanking
        if self.comp_type == "aida":
            dwc.append("Overall")
            # only add special_ranking result if we have at least one special_ranking
            has_special_ranking = self.db_.execute(
                '''SELECT id FROM competition_athlete
                WHERE competition_id==? AND special_ranking''',
                self.id_)
            if has_special_ranking is not None:
                dwc.append(self.special_ranking_name)
        dwc += self.disciplines
        return dwc

    def getCountries(self, for_result=False):
        countries = []
        if self.countries is None:
            return []
        if self.selected_country != "none":
            countries.append(self.selected_country)
        countries.append("International")
        if for_result:
            if self.comp_type == "cmas":
                # only add special_ranking result if we have at least one special_ranking
                has_special_ranking = self.db_.execute(
                    '''SELECT id FROM competition_athlete
                    WHERE competition_id==? AND special_ranking''',
                    self.id_)
                if has_special_ranking is not None:
                    countries.append(self.special_ranking_name)
        else:
            countries += self.countries
        return countries

    def getStartList(self, day, block):
        if self.comp_file is None:
            return None
        db_out = self.db_.execute('''
            SELECT a.first_name, a.last_name, a.country, s.AP, s.OT, s.lane, s.id, s.discipline, s.PB
            FROM start s
            INNER JOIN competition_athlete ca ON s.competition_athlete_id == ca.id
            INNER JOIN athlete a ON ca.athlete_id == a.id
            WHERE ca.competition_id==? AND s.block==? AND s.day==?''',
            (self.id_, block, u.convDay(day)))
        if db_out is None:
            return []
        startlist = [{'Name': r[0] + " " + r[1],
                      'Nationality': r[2],
                      'AP': self.convertPerformance(r[3], r[7]),
                      'PB': self.convertPerformance(r[8], r[7]),
                      'Warmup': self.getWTfromOT(u.convTime(r[4])),
                      'OT': u.convTime(r[4]),
                      'Lane': self.laneStyleConverter(r[5]),
                      'Discipline': r[7],
                      'Id': r[6]}
                      for r in db_out]
        startlist.sort(key=lambda r: (self.getMinFromTime(r['OT']), int(self.laneStyleConverter(r['Lane'], True))))

        br_out = self.db_.execute('''
            SELECT duration, idx
            FROM break
            WHERE competition_id == ? AND block == ? AND day == ?''',
            (self.id_, block, u.convDay(day)))
        if br_out is not None:
            for br in br_out:
                idx = int(br[1])
                if idx >= len(startlist):
                    continue
                br_time = str(int(br[0]/60)) + ":" + str(br[0]%60).zfill(2)
                startlist.insert(idx, {'Name': "Break", 'Nationality': "", 'AP': br_time, 'PB': '', 'Warmup': "",
                                       'OT': "", 'Lane': "", 'Discipline': "", 'Id': -1})

        return startlist

    def updateStartList(self, day, block, to_remove, startlist):
        day = self.cleanDay(day)
        block = self.cleanBlock(block)
        if block is None or day == INVALID_DATE:
            return -1
        to_remove = [int(tr) for tr in to_remove]
        # remove all starts from the start list that were removed and make sure they belong to this comp
        if len(to_remove) > 0:
            if len(to_remove) == 1:
                self.db_.execute(
                    '''DELETE FROM start WHERE id IN
                       (SELECT s.id FROM start s
                        INNER JOIN competition_athlete ca ON ca.id == s.competition_athlete_id
                        WHERE s.id == ? AND ca.competition_id == ?)''',
                    (to_remove[0], self.id_))
            else:
                rlist = str(tuple(to_remove))
                self.db_.execute(
                    '''DELETE FROM start WHERE id IN
                       (SELECT s.id FROM start s
                        INNER JOIN competition_athlete ca ON ca.id == s.competition_athlete_id
                        WHERE s.id IN ? AND ca.competition_id == ?''',
                    (rlist, self.id_))

        # remove all breaks
        self.db_.execute("DELETE FROM break WHERE competition_id == ? AND block == ? AND day == ?",
                         (self.id_, block, u.convDay(day)))

        for i in range(len(startlist)):
            if startlist[i]["Name"] == "Break":
                duration = self.getMinFromTime(self.cleanTime(startlist[i]["AP"]))
                self.db_.execute(
                    '''INSERT INTO break
                       (competition_id, block, day, duration, idx) VALUES (?, ?, ?, ?, ?)''',
                    (self.id_, block, u.convDay(day), duration, i))
            else: # start
                ca_id = int(startlist[i]["Id"])
                if ca_id < 0: # new start, in this case ca_id = - athlete_id
                    ca_id = self.db_.execute(
                        '''SELECT id FROM competition_athlete
                           WHERE athlete_id == ? AND competition_id == ?''',
                        (-ca_id, self.id_))
                else: # old start in this case ca_id = start_id
                    ca_id = self.db_.execute(
                        '''SELECT s.id FROM competition_athlete ca
                           INNER JOIN start s ON ca.id == s.competition_athlete_id
                           WHERE s.id == ? AND ca.competition_id == ?''',
                        (ca_id, self.id_))
                if ca_id is None:
                    log.warning("Invalid athlete not added to competition")
                    continue
                ot = self.cleanTime(startlist[i]["OT"])
                discipline = self.cleanDiscipline(startlist[i]['Discipline'], block)
                if discipline is None:
                    continue
                ap = self.cleanPerf(startlist[i]["AP"], discipline)
                pb = self.cleanPerf(startlist[i]["PB"], discipline)
                if discipline == "STA":
                    ap = self.getMinFromTime(ap)
                    pb = self.getMinFromTime(pb)
                lane = self.cleanNumber(self.laneStyleConverter(startlist[i]["Lane"], True)) # TODO min/max
                if int(startlist[i]["Id"]) < 0: # new start
                    self.db_.execute(
                        '''INSERT INTO start
                           (competition_athlete_id, discipline, block, lane, day, OT, AP, PB)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (ca_id[0][0], discipline, block, lane, u.convDay(day), u.convTime(ot), ap, pb));
                else: #update start
                    self.db_.execute(
                        '''UPDATE start SET
                           discipline=?, block=?, lane=?, day=?, OT=?, AP=?, PB=?
                           WHERE id == ?''',
                        (discipline, block, lane, u.convDay(day), u.convTime(ot), ap, pb, ca_id[0][0]));
        return 0

    def convertPerformance(self, val, dis):
        if val is None:
            return ""
        if dis == "STA":
            m = math.floor(int(val)/60)
            s = int(val) - m*60
            out = str(int(m)) + ":" + str(int(s)).zfill(2)
            return out
        else:
            return str(val)

    def getWTfromOT(self, ot):
        otf = self.getMinFromTime(ot)
        wtf = otf-45 # does not work if ot is close to midnight, but seriously?
        wt = str(math.floor(wtf/60)) + ":" + str(wtf%60).zfill(2)
        return wt

    def getStartListPDF(self, day="all", block="all", in_memory=False):
        if day=="all" and block=="all":
            day_block = self.getBlocks()
            files = []
            for d in day_block:
                for block in day_block[d].keys():
                    files.append(self.getStartListPDF(d, block, True))
            pages = []
            for doc in files:
                for page in doc.pages:
                    pages.append(page)
            merged_pdf = files[0].copy(pages)
            fname = os.path.join(self.config.download_folder, self.name + "_start_lists.pdf")
            merged_pdf.write_pdf(fname)
            return fname
        start_df = pd.DataFrame(self.getStartList(day, block))
        start_df.drop("Id", axis=1, inplace=True)
        blocks = self.getBlocks()
        block_disciplines = blocks[day][int(block)]['dis_s']
        if self.comp_type == "aida":
            start_df.drop("PB", axis=1, inplace=True)
        else:
            if block_disciplines != "STA":
                start_df.drop("AP", axis=1, inplace=True)
            else:
                start_df["AP"] = start_df.apply(lambda row: row["AP"] if row['Discipline'] == "STA" else "", axis=1)
        if block_disciplines.find(",") == -1:
            start_df.drop("Discipline", axis=1, inplace=True)
        html_string = start_df.to_html(index=False, justify="left", classes="df_table")
        day_obj = datetime.strptime(day, "%Y-%m-%d")
        human_day = day_obj.strftime("%d. %m. %Y")
        today = datetime.now().strftime("%d.%m.%Y")
        dis = self.db_.execute('SELECT disciplines FROM block WHERE competition_id==? AND id==?', (self.id_, block))
        if dis is None:
            return None
        disciplines = self.disciplineIntToStr(dis[0][0])
        html_string = """
            <html>
            <head>
            <style>
            table {{
                margin-left: 2cm;
            }}
            tr th:first-child {{
                padding-left:0px;
                text-align: left;
            }}
            tr td:first-child {{
                padding-left:0;
                text-align: left;
            }}
            th, td {{
                padding:5px 0px 2px 20px;
                text-align: center;
                border-bottom: 1px solid #ddd;
                font-size: 12px;
            }}
            @page {{
                margin: 4cm 1cm 6cm 1cm;
                size: A4;
                @top-right {{
                    content: counter(page) "/" counter(pages);
                }}
            }}
            header, footer {{
                position: fixed;
                left: 0;
                right: 0;
            }}
            header {{
                /* subtract @page margin */
                top: -4cm;
                height: 4cm;
                text-align: center;
                vertical-align: center;
            }}
            footer {{
                /* subtract @page margin */
                bottom: -6cm;
                height: 6cm;
                text-align: center;
                vertical-align: center;
            }}
            </style>
            </head>
            <body>
            <header>
                <h1>{}</h1>
                <h2>Start list {} - {}</h2>
            </header>
            {}
            <footer><img src="{}" style="width:{}cm; height:{}cm;"></footer>
            </body>
            </html>
            """.format(self.name, disciplines, human_day, html_string, self.sponsor_img_data, self.sponsor_img_width, self.sponsor_img_height)
        html = wp.HTML(string=html_string, base_url="/")
        #fname = os.path.join(self.config.download_folder, "test.html")
        #with open(fname, "w") as f:
        #    f.write(html_string)
        if in_memory:
            return html.render()
        else:
            fname = os.path.join(self.config.download_folder, self.name + "_start_list_" + day + "_" + disciplines.replace(', ', '_') + ".pdf")
            html.write_pdf(fname)
            return fname

    def getLaneList(self, day, block, lane):
        lane_db = self.laneStyleConverter(lane, True)
        db_out = self.db_.execute('''SELECT a.first_name, a.last_name, s.AP, s.OT, a.country, a.gender, a.id, s.id, s.PB, s.discipline, s.RP, s.card, s.remarks
                                     FROM athlete a
                                     INNER JOIN competition_athlete ca ON a.id == ca.athlete_id
                                     INNER JOIN start s ON s.competition_athlete_id == ca.id
                                     WHERE s.block == ? AND s.lane == ? AND s.day == ? AND ca.competition_id == ?
                                  ''',
                                  (block, lane_db, u.convDay(day), self.id_))
        if db_out is None:
            return None
        lane_list = [{'id': r[6],
                      's_id': r[7],
                      'OT': u.convTime(r[3]),
                      'Dis': r[9],
                      'Name': r[0] + " " + r[1],
                      'Nat': r[4],
                      'AP': self.convertPerformance(r[2], r[9]),
                      'PB': self.convertPerformance(r[8], r[9]),
                      'RP': self.convertPerformance(r[10], r[9]),
                      'Card': r[11],
                      'Remarks': r[12],
                      'NR': self.getNr(r[4], "", r[5], r[9], True)}
                       for r in db_out]
        lane_list.sort(key=lambda r: self.getMinFromTime(r['OT']))
        return lane_list

    def getNr(self, country, cls, gender, discipline, convert=False):
        nr = self.NR(self.comp_type, country, cls, gender, discipline)
        if self.nr is not None and nr in self.nr:
            if convert:
                return self.convertPerformance(self.nr.get(nr), discipline)
            else:
                self.nr.get(nr)
        else:
            return ""

    def getLaneListPDF(self, safety=False, day="all", block="all", lane="all", in_memory=False):
        if day=="all" and block=="all":
            blocks = self.getBlocks()
            files = []
            for day in blocks:
                for block in blocks[day].keys():
                    for lane in blocks[day][block]['lanes']:
                        files.append(self.getLaneListPDF(safety, day, block, lane, True))
            pages = []
            for doc in files:
                for page in doc.pages:
                    pages.append(page)
            merged_pdf = files[0].copy(pages)
            fname = os.path.join(self.config.download_folder, self.name + "_lane_lists.pdf")
            merged_pdf.write_pdf(fname)
            return fname
        lane_df = pd.DataFrame(self.getLaneList(day, block, lane))
        lane_df.drop("id", axis=1, inplace=True)
        lane_df.drop("s_id", axis=1, inplace=True)
        lane_df.drop("RP", axis=1, inplace=True)
        lane_df.drop("Card", axis=1, inplace=True)
        lane_df.drop("Remarks", axis=1, inplace=True)
        if safety:
            lane_df.drop("Nat", axis=1, inplace=True)
            lane_df.drop("NR", axis=1, inplace=True)

        blocks = self.getBlocks()
        block_str = blocks[day][int(block)]['dis_s']
        block_str_underscore = block_str.replace(', ', '_')
        has_multiple_dis = ',' in block_str

        if not has_multiple_dis:
            if self.comp_type == "cmas" and block_str != "STA":
                lane_df.drop("AP", axis=1, inplace=True)
            lane_df.drop("Dis", axis=1, inplace=True)
        if not safety:
            lane_df["RP"] = ""
            lane_df["Card"] = ""
            lane_df["Remarks"] = ""
        cols = lane_df.columns.tolist()
        if not safety:
            if self.comp_type == "aida":
                if has_multiple_dis:
                    cols = cols[0:5] + cols[7:] + cols[5:7]
                else:
                    cols = cols[0:4] + cols[6:] + cols[4:6]
            else:
                if block_str == "STA":
                    cols = ['OT', 'Name', 'Nat', 'AP', 'PB', 'RP', 'Card', 'Remarks', 'NR']
                elif has_multiple_dis:
                    cols = ['OT', 'Dis', 'Name', 'Nat', 'PB', 'RP', 'Card', 'Remarks', 'NR']
                else:
                    cols = ['OT', 'Name', 'Nat', 'PB', 'RP', 'Card', 'Remarks', 'NR']
        lane_df = lane_df[cols]
        df_html = lane_df.to_html(index=False, justify="left", classes="df_table")
        day_obj = datetime.strptime(day, "%Y-%m-%d")
        human_day = day_obj.strftime("%d. %m. %Y")
        html_string = """
            <html>
            <head>
            <style>
            table {
                width: 100%;
            }
            tr th:first-child {
                padding-left:0px;
            }
            tr td:first-child {
                padding-left:0px;
            }"""
        if safety:
            html_string += """
                h2 {
                    font-size: 4mm;
                }
                th, td {
                    padding:1mm 0mm 1mm 1mm;
                    text-align: center;
                    font-size: 4mm;
                    border-bottom: 1px solid #ddd;
                }"""
        else:
            html_string += """
                th, td {
                    padding:10px 0px 10px 20px;
                    text-align: center;
                    border-bottom: 1px solid #ddd;
                }"""
        html_string += """
            table th:nth-child(1) {
                width: 4%;
            }"""
        i = 2
        if has_multiple_dis:
            html_string += """
                table th:nth-child({}) {{
                    width: 4%;
                }}""".format(str(i))
            i += 1
        html_string += """
            table th:nth-child({}) {{
                width: 21%;
                text-align: left;
            }}
            table td:nth-child({}) {{
                text-align: left;
            }}
            table th:nth-child({}) {{
                width: 4%;
            }}
            table th:nth-child({}) {{
                width: 4%;
            }}
            """.format(str(i), str(i), str(i+1), str(i+2))
        i += 3
        if self.comp_type == "cmas" and block_str == "STA":
            html_string += """
                table th:nth-child({}) {{
                    width: 4%;
                }}
                """.format(str(i))
            i += 1
        if not safety:
            html_string += """
                table th:nth-child({}) {{
                    width: 10%;
                }}
                table th:nth-child({}) {{
                    width: 10%;
                }}
                table th:nth-child({}) {{
                    width: 39%;
                }}
                table th:nth-child({}) {{
                    width: 4%;
                }}
                table th:nth-child({}) {{
                    width: 4%;
                }}""".format(str(i), str(i+1), str(i+2), str(i+3), str(i+4))
            i += 5
        html_string += """
            header, footer {
                position: fixed;
                left: 0;
                right: 0;
            }"""
        if safety:
            html_string += """
                @page {{
                    margin: 1.5cm 0.5cm 0.5cm 0.5cm;
                    size: A5 portrait;
                    @top-right {{
                        content: counter(page) "/" counter(pages);
                    }}
                }}
                header {{
                    /* subtract @page margin */
                    top: -1.5cm;
                    height: 1.5cm;
                    text-align: center;
                    vertical-align: center;
                }}
                footer {{
                    /* subtract @page margin */
                    bottom: -0.5cm;
                    height: 0.5cm;
                    text-align: left;
                    vertical-align: center;
                }}
                </style>
                </head>
                <body>
                <header>
                    <h2>Safety lane list {} - lane {} - {}</h2>
                </header>
                {}
                <footer></footer>
                </body>
                </html>
                """.format(block_str, lane, human_day, df_html)
        else:
            html_string += """
                @page {{
                    margin: 4cm 1cm 1.5cm 2.5cm;
                    size: A4 landscape;
                    @top-right {{
                        counter(page) "/" counter(pages);
                    }}
                }}
                header {{
                    /* subtract @page margin */
                    top: -4cm;
                    height: 4cm;
                    text-align: center;
                    vertical-align: center;
                }}
                footer {{
                    /* subtract @page margin */
                    bottom: -1.5cm;
                    height: 1.5cm;
                    text-align: left;
                    vertical-align: center;
                }}
                </style>
                </head>
                <body>
                <header>
                    <h1>{}</h1>
                    <h2>Lane list {} - lane {} - {}</h2>
                </header>
                {}
                <footer><span style="margin-left:3mm">Judge Name:</span><span style="margin-left:8cm">Signature:</span></footer>
                </body>
                </html>
                """.format(self.name, block_str, lane, human_day, df_html)
        html = wp.HTML(string=html_string, base_url="/")
        fname = os.path.join(self.config.download_folder, "test.html")
        with open(fname, "w") as f:
            f.write(html_string)
        if in_memory:
            return html.render()
        else:
            fname = os.path.join(self.config.download_folder, self.name + "_lane_list_" + day + "_" + block_str_underscore + "_" + lane + ".pdf")
            html.write_pdf(fname)
            return fname

    def getResult(self, discipline, gender, country, with_empty=False):
        if self.comp_file is None:
            return None, None
        result = []
        result_keys = ['Rank', 'Name', 'Country']
        if self.comp_type == "cmas":
            result_keys.append('Club')
        if discipline == "Overall" or discipline == self.special_ranking_name:
            if self.comp_type == "cmas":
                logging.error("Attempted to get " + discipline + " ranking for cmas competition")
                return None, None
            cmd = '''SELECT ca.id, a.first_name, a.last_name, a.country, a.club,
                            s.rp, s.penalty, s.card, s.remarks, s.discipline
                     FROM start s
                     INNER JOIN competition_athlete ca ON s.competition_athlete_id == ca.id
                     INNER JOIN athlete a ON ca.athlete_id == a.id
                     WHERE a.gender == ? AND s.remarks IS NOT NULL AND ca.competition_id == ?'''
            args = (gender, self.id_)

            if country != 'International':
                cmd += " AND a.country = ?"
                args += (country, )
            if discipline == self.special_ranking_name:
                cmd += " AND ca.special_ranking"

            db_out = self.db_.execute(cmd, args)
            if db_out is None:
                return None, None

            res = {}
            for r in db_out:
                if not r[0] in res:
                    res[r[0]] = {'Rank': 0, 'Name': r[1] + " " + r[2], 'Country': r[3], 'Points': 0.}
                    for d in self.disciplines:
                        res[r[0]][d] = ''
                    if self.comp_type == "cmas":
                        res[r[0]]['Club'] = r[4]
                res[r[0]][r[9]] = 0 if r[7] == "RED" else self.convertPerformance(r[5], r[9])
                res[r[0]]['Points'] += self.computePoints(r[5], r[6], r[7], r[8], r[9])
            # remove all 0 points and format points to two decimals after comma
            to_remove = []
            for r in res:
                if res[r]['Points'] == 0.:
                    to_remove.append(r)
                else:
                    res[r]['Points'] = "%.2f" % res[r]['Points']
            for tr in to_remove:
                res.pop(tr)

            res_list = sorted(list(res.values()), key=lambda r: -float(r['Points']))
            # set ranks
            res_list[0]['Rank'] = 1
            for i in range(len(res_list)-1):
                if res_list[i]['Points'] != res_list[i+1]['Points']:
                    res_list[i+1]['Rank'] = i+2
                else:
                    res_list[i+1]['Rank'] = ""

            result_keys += self.disciplines + ["Points"]
            return res_list, result_keys
        else:
            cmd = '''SELECT a.first_name, a.last_name, a.country, a.club,
                            s.AP, s.RP, s.penalty, s.card, s.remarks, s.id, s.OT, a.gender, s.judge_remarks
                     FROM start s
                     INNER JOIN competition_athlete ca ON s.competition_athlete_id == ca.id
                     INNER JOIN athlete a ON ca.athlete_id == a.id
                     WHERE s.discipline == ? AND a.gender == ? and ca.competition_id == ?'''
            if not with_empty: # remove unset results if requested
                cmd += " AND s.remarks IS NOT NULL"
            args = (discipline, gender, self.id_)
            if country != 'International' and country != self.special_ranking_name:
                cmd += " AND a.country = ?"
                args += (country, )
            if self.comp_type == "cmas" and country == self.special_ranking_name:
                if self.selected_country == "none":
                    cmd += " AND ca.special_ranking"
                else:
                    cmd += " AND a.country = ? AND ca.special_ranking"
                    args += (self.selected_country, )
            db_out = self.db_.execute(cmd, args)

            if db_out is None:
                return [], []

            def check_nr(country, gender, rp, card):
                if rp is None or card != "WHITE":
                    return ""
                this_nr = self.getNr(country, "", gender, discipline)
                return ", <b>NR</b>" if  this_nr is not None and this_nr < rp else ""

            if self.comp_type == "aida":
                result = [{'Rank': i,
                           'Name': r[0] + " " + r[1],
                           'Country': r[2],
                           'AP_float': r[4],
                           'AP': self.convertPerformance(r[4], discipline),
                           'RP': self.convertPerformance(r[5], discipline) if r[8] != "DNS" else 0.,
                           'Penalty': r[6] if r[8] != "DNS" and r[5] is not None else "",
                           'Card': r[7] if r[8] != "DNS" and r[5] is not None else "",
                           'Remarks': (r[8] + check_nr(r[2], r[11], r[5], r[7])) if r[5] is not None or r[8] == "DNS" else "",
                           'JudgeRemarks': r[12],
                           'Points': ("%.2f" % self.computePoints(r[5], r[6], r[7], r[8], discipline)),
                           'Id': r[9],
                           'OT': u.convTime(r[10])}
                           for i,r in enumerate(db_out)]
                result_keys += ["AP", "RP", "Penalty", "Card", "Remarks", "Points", "JudgeRemarks"]

                # sorting according to rp (descending), card (white before others), ap (descending)
                result.sort(key=lambda r: self.sortResultsWeightsAida(r))
            else:
                result = [{'Rank': i,
                           'Name': r[0] + " " + r[1],
                           'Country': r[2],
                           'Club': r[3],
                           'RP': self.convertPerformance(r[5], discipline) if r[8] != "DNS" else 0.,
                           'Card': r[7] if r[8] != "DNS" else "",
                           'Remarks': r[8],
                           'Judge Remarks': r[12],
                           'Points': "%.2f" % self.computePoints(r[5], r[6], r[7], r[8], discipline),
                           'Id': r[9]}
                           for i,r in enumerate(db_out)]
                result_keys += ["RP", "Card", "Remarks", "JudgeRemarks"]

                # sorting according to rp (descending)
                result.sort(key=lambda r: (-float(r['Points']), 0 if r['Remarks'] != "DNS" else 1))

            cur_points = 1000000
            cur_ap = ""
            for i in range(len(result)):
                if float(result[i]["Points"]) == 0.:
                    result[i]["Rank"] = ""
                elif result[i]["Points"] == cur_points and (self.comp_type == "cmas" or result[i]["AP"] == cur_ap):
                    result[i]["Rank"] = ""
                else:
                    cur_points = result[i]["Points"]
                    if self.comp_type == "aida":
                        cur_ap = result[i]["AP"]
                    result[i]["Rank"] = i+1
            return result, result_keys

    def sortResultsWeightsAida(self, r):
        w0 = -float(r['Points'])
        w1 = 0
        w2 = -r['AP_float']
        if r['Card'] != "WHITE":
            w1 = 1
        if r['RP'] == "" or r['Remarks'] == "DNS":
            w1 = 2
            w2 = self.getMinFromTime(r['OT'])*100 + r['AP_float']
        return (w0, w1, w2)

    def computePoints(self, rp, penalty, card, remarks, discipline):
        if card == "RED" or remarks == "DNS" or rp is None:
            return 0.
        if self.comp_type == "CMAS":
            return rp - penalty
        else:
            if discipline == "STA":
                return int(rp)*0.2 - penalty
            elif discipline in ["DNF", "DYNB", "DYN"]:
                if self.comp_type == "aida":
                    return int(rp)*0.5 - penalty
                else:
                    return int(rp*2.)*0.25 - penalty
            else:
                return int(rp) - penalty

    def getResultPDF(self, discipline="all", gender="all", country="all", in_memory=False, top3=False):
        if discipline=="all" and gender=="all":
            dwd = self.getDaysWithDisciplinesLanes()
            files = []
            gender_list = ["F", "M"]
            if top3:
                gender_list = [gender_list] # if gender is a list, one pdf will contain both genders, for top 3
            for d in self.getDisciplines():
                for g in gender_list:
                    for c in self.getCountries(True):
                        pdf = self.getResultPDF(d, g, c, True, top3)
                        if pdf is not None:
                            files.append(pdf)
            pages = []
            for doc in files:
                for page in doc.pages:
                    pages.append(page)
            merged_pdf = files[0].copy(pages)
            fname = os.path.join(self.config.download_folder, self.name + "_results")
            if top3:
                fname += "_top3"
            fname += ".pdf"
            merged_pdf.write_pdf(fname)
            return fname

        html_string = """
            {}
            <header>
                <h1>{}</h1>
                <h2>Result {} - {}""".format(self.getHtmlHeader(), self.name, discipline, country)
        if top3:
            gender_list = gender # for top 3, this is ["F", "M"]
        else:
            gender_str = "Female" if gender == "F" else "Male"
            html_string += " - " + gender_str
            gender_list = [gender] # for all others a string
        html_string += """</h2>
            </header>
            """
        for g in gender_list:
            result, result_keys = self.getResult(discipline, g, country)
            result_df = pd.DataFrame(result)
            if len(result_df.index) == 0:
                return None
            if self.comp_type == "cmas":
                result_df.drop("Points", axis=1, inplace=True)
            if "Id" in result_df.columns.tolist():
                result_df.drop("Id", axis=1, inplace=True)
            if "AP_float" in result_df.columns.tolist():
                result_df.drop("AP_float", axis=1, inplace=True)
            if "OT" in result_df.columns.tolist():
                result_df.drop("OT", axis=1, inplace=True)
            if "Judge Remarks" in result_df.columns.tolist():
                result_df.drop("Judge Remarks", axis=1, inplace=True)
            if top3:
                gender_str = "Female" if g == "F" else "Male"
                html_string += "<h3>" + gender_str + "</h3>\n"
                # drop all entries where rank is > 3
                # first find one where this is true
                result_df['Rank'] = pd.to_numeric(result_df['Rank'], errors='coerce')
                remainder = result_df[(result_df['Rank'] > 3)]
                if len(remainder.index) != 0:
                    index_to_drop_after = remainder.idxmin(numeric_only=True)[0]
                    # keep only ones before
                    result_df = result_df.loc[:index_to_drop_after-1]
                # convert back to strings
                result_df['Rank'] = result_df['Rank'].replace(np.nan, 0).astype(int).astype(str).replace('0', '')
                # remove all Red cards
                result_df = result_df[(result_df['Card'] != "RED")]
            html_string += result_df.to_html(index=False, justify="left", classes="df_table") + "\n"
            html_string = html_string.replace("&lt;b&gt;", "<b>")
            html_string = html_string.replace("&lt;/b&gt;", "</b>")
        html_string += self.getHtmlFooter();

        html = wp.HTML(string=html_string, base_url="/")
        fname = os.path.join(self.config.download_folder, "test.html")
        with open(fname, "w") as f:
            f.write(html_string)
        if in_memory:
            return html.render()
        else:
            fname = os.path.join(self.config.download_folder, self.name + "_result_" + discipline + "_" + gender + "_" + country + ".pdf")
            html.write_pdf(fname)
            return fname

    def getHtmlHeader(self):
        html_header = """
            <html>
            <head>
            <style>
            table {
                width: 100%;
            }
            tr th:first-child {
                padding-left:0px;
                text-align: left;
            }
            tr td:first-child {
                padding-left:0px;
                text-align: left;
            }
            th, td {
                padding:20px 0px 5px 5px;
                text-align: center;
                font-size: 12px;
                border-bottom: 1px solid #ddd;
            }
            @page {
                margin: 4cm 1cm 6cm 1cm;
                size: A4;
                @top-right {
                    content: counter(page) "/" counter(pages);
                }
            }
            header, footer {
                position: fixed;
                left: 0;
                right: 0;
            }
            header {
                /* subtract @page margin */
                top: -4cm;
                height: 4cm;
                text-align: center;
                vertical-align: center;
            }
            footer {
                /* subtract @page margin */
                bottom: -6cm;
                height: 6cm;
                text-align: center;
                vertical-align: center;
            }
            h3 {
                padding-top: 1cm;
            }
            </style>
            </head>
            <body>"""
        return html_header

    def getHtmlFooter(self):
        html_footer = """
            <footer><img src="{}" style="width:{}cm; height:{}cm;"></footer>
            </body>
            </html>
            """.format(self.sponsor_img_data, self.sponsor_img_width, self.sponsor_img_height)
        return html_footer

    def changeSelectedCountry(self, country):
        if country == "none":
            self.selected_country_ = None
        else:
            if country in self.countries:
                self.selected_country_ = country
            else:
                return 1
        self.save()
        return 0

    def getBreaks(self, day):
        min_break = 24*60
        breaks_list = []
        found = False
        for d in self.getDays():
            if d == day:
                found = True
                break
        if not found:
            return None
        athletes = self.db_.execute(
            '''SELECT a.id, a.first_name, a.last_name FROM athlete a
               INNER JOIN competition_athlete ca ON ca.athlete_id == a.id
               WHERE ca.competition_id == ?''',
            self.id_)
        if athletes is None:
            return None
        for a in athletes:
            db_out = self.db_.execute(
                '''SELECT s.OT, s.discipline FROM start s
                   INNER JOIN competition_athlete ca ON s.competition_athlete_id == ca.id
                   WHERE s.day = ? AND ca.competition_id = ? AND ca.athlete_id == ?''',
                (u.convDay(day), self.id_, a[0]))
            if db_out is None:
                continue
            n = len(db_out)
            for i in range(n-1):
                this_break = {"Name": a[1] + " " + a[2]}
                this_break["Dis1"] = db_out[i][1]
                this_break["Dis2"] = db_out[i+1][1]
                this_break["OT1"] = u.convTime(db_out[i][0])
                this_break["OT2"] = u.convTime(db_out[i+1][0])
                time = self.getMinFromTime(this_break["OT2"]) - self.getMinFromTime(this_break["OT1"])
                min_break = min(min_break, time)
                this_break["Break"] = str(int(time/60)).zfill(2) + ":" + str(time%60).zfill(2)
                breaks_list.append(this_break)
        min_break = str(int(min_break/60)).zfill(2) + ":" + str(min_break%60).zfill(2)
        breaks_list = sorted(breaks_list, key=lambda d: d["Break"])
        return {"min_break": min_break, "breaks_list": breaks_list}

    def setOTs(self, data):
        ots = []
        for day in self.getDays():
            ots_on_day = self.db_.execute(
                '''SELECT DISTINCT s.OT from start s
                   INNER JOIN competition_athlete ca ON ca.id == s.competition_athlete_id
                   WHERE ca.competition_id == ? AND s.day == ?''',
                (self.id_, u.convDay(day)))
            if ots_on_day is None:
                continue
            dayc = ":".join(day.split("-"))
            ots += [dayc + ":" + u.convTime(ot[0]) + ":00" for ot in ots_on_day]
        data["ots"] = ots

    def setSpecialRankingName(self, data):
        data["special_ranking_name"] = self.special_ranking_name

    def changeSpecialRankingName(self, name):
        self.special_ranking_name_ = name
        self.save()

    def parseTime(self, date):
        if type(date) is time:
            return date.strftime('%H:%M')
        elif type(date) is str:
            return date
        else:
            return str(date)

    def formatSTA(self, minutes, seconds):
        if seconds == "" or math.isnan(seconds):
            return ""
        out = str(int(minutes)) + ":"
        if self.comp_type == "aida":
            out += str(int(seconds)).zfill(2)
        else:
            out += "%05.2f" % round(seconds, 2)
        return out

    # returns tuple with ca_id and if it athlete belongs to any other comp
    def isAthleteInCompetition(self, athlete_id):
        db_out = self.db_.execute(
            "SELECT id FROM competition_athlete WHERE competition_id==? AND athlete_id==?",
            (self.id_, athlete_id))
        if db_out is None:
            return None, None
        else:
            db_comps = self.db_.execute(
                "SELECT id FROM competition_athlete WHERE athlete_id==?",
                athlete_id)
            in_other_comp = len(db_comps) > 1
            return db_out[0][0], in_other_comp

    def deleteAthlete(self, ca_id, a_id, in_other_comp):
        self.db_.execute("DELETE FROM start WHERE competition_athlete_id=?", ca_id)
        self.db_.execute("DELETE FROM competition_athlete WHERE id=?", ca_id)
        if not in_other_comp:
            self.db_.execute("DELETE FROM athlete WHERE id=?", a_id)

    def getAthleteData(self, data):
        data["athletes"] = []
        athletes = self.db_.execute(
            '''SELECT a.id, a.first_name, a.last_name, a.gender, a.country, a.aida_id, a.club,
                      ca.special_ranking, ca.paid, ca.medical_checked, ca.registered
               FROM athlete a
               INNER JOIN competition_athlete ca ON ca.athlete_id == a.id
               WHERE ca.competition_id == ?''',
            self.id_)
        if athletes is None:
            return
        for a in athletes:
            data["athletes"].append(
                {"last_name": a[2], "first_name": a[1], "gender": a[3],
                 "country": a[4], "id": a[0], "aida_id": a[5],
                 "club": a[6], "special_ranking": a[7], "paid": a[8],
                 "medical_checked": a[9], "registered": a[10]})

    def addAthlete(self, first_name, last_name, gender, country, club, aida_id):
        country = self.cleanCountry(country)
        if country is None:
            return -1
        a_id = self.db_.execute(
            "SELECT id FROM athlete WHERE first_name == ? AND last_name == ? AND country == ?",
            (first_name, last_name, country))
        a = None
        # user added in other comp
        if a_id is not None:
            ca_id = self.db_.execute(
                "SELECT id FROM competition_athlete WHERE athlete_id == ? AND competition_id == ?",
                (a_id[0][0], self.id_))
            if ca_id is not None:
                return 1 # athlete already exists in current competition
            else:
                # not in current competition, so add it
                self.db_.execute(
                    '''INSERT INTO competition_athlete
                       (competition_id, athlete_id, special_ranking) VALUES(?, ?, ?)''',
                    (self.id_, a_id[0][0], False))
                # TODO check if rest of arguments are identical
                return 0
        else:
            a = athlete.Athlete.fromArgs(aida_id, first_name, last_name, gender, country, club, self.db_)
            a.associateWithComp(self.id_)
            return 0

    def cleanDiscipline(self, dis, block=None):
        # for a list, we check each element
        if isinstance(dis, list):
            for d in dis:
                res = self.cleanDiscipline(d, block)
                if res is None:
                    return None
            return dis

        if dis not in DISCIPLINES:
            return None
        else:
            if block is not None:
                dis_i = DISCIPLINES.index(dis)
                dis_in_block = self.db_.execute('SELECT disciplines FROM block WHERE id==?', block)
                if dis_in_block is None or (dis_in_block[0][0] & 1<<dis_i) == 0:
                    return None
            return dis

    def cleanCountry(self, country):
        country = regex.compile('[A-Z][A-Z][A-Z]$').match(str(country).strip())
        if country is None:
            return None
        else:
            return country[0]

    def cleanTime(self, time):
        ctime = regex.compile('[0-5]?\\d:[0-5]\\d$').match(str(time))
        if ctime is None:
            return INVALID_TIME
        else:
            return ctime[0]

    def cleanNumber(self, n, digits = 0, minval = -sys.float_info.max, maxval = sys.float_info.max):
        pstr = '^\\d+'
        if digits > 0:
            pstr += '.?'
        pstr += ''.join(['\\d?' for i in range(digits)])
        pattern = regex.compile(pstr)
        cn = pattern.match(str(n))
        if cn is None:
            return "0" if minval == -sys.float_info.max else str(minval)
        elif minval <= float(cn[0]) and float(cn[0]) <= maxval:
            return cn[0]
        else:
            return str(minval)

    def cleanPerf(self, perf, discipline):
        if discipline == "STA":
            return self.cleanTime(perf)
        elif self.comp_type == "aida" or discipline in ['CWT', 'CWTB', 'FIM', 'CNF']:
            return self.cleanNumber(perf, 0, 1)
        else: # cmas dynamic disciplines
            return self.cleanNumber(perf, 1, 1)

    def cleanBlock(self, block):
        block = int(block)
        block = self.db_.execute('SELECT id FROM block WHERE id==? AND competition_id==?', (block, self.id_))
        if block is not None:
            return block[0][0]
        else:
            return None

    def cleanDay(self, day, format_only = False):
        if format_only:
            day = str(day)
            res = True
            try:
                res = bool(datetime.strptime(day, "%Y-%m-%d"))
            except ValueError:
                res = False
            return day if res else INVALID_DATE
        else:
            if day in [d for d in self.getDays()]:
                return str(day)
            else:
                return INVALID_DATE

    def cleanCard(self, card):
        if card in ["WHITE", "YELLOW", "RED"]:
            return card
        return None

    def cleanPenalty(self, penalty):
        try:
            return float(penalty)
        except:
            return 0.

    def getMinFromTime(self, time_str):
        h_m = time_str.split(':')
        return int(h_m[0])*60 + int(h_m[1])

    def updateResult(self, s_id, rp, penalty, card, remarks, judge_remarks):
        s_id = int(s_id)
        penalty = self.cleanPenalty(penalty)
        card = self.cleanCard(card)
        if card is None:
            return 1
        # TODO sanity checks for card and remarks and discipline
        ap_dis = self.db_.execute(
                '''SELECT s.ap, s.discipline
                   FROM competition_athlete ca
                   INNER JOIN start s ON ca.id == s.competition_athlete_id
                   WHERE s.id == ?''',
                s_id)
        if ap_dis is not None:
            discipline = ap_dis[0][1]
            rp = self.cleanPerf(rp, discipline)
            if discipline == "STA":
                rp = self.getMinFromTime(rp)
            under_ap_penalty = self.getUnderApPenalty(ap_dis[0][0], rp, discipline, card) if self.comp_type == "aida" else 0
            self.db_.execute(
                '''UPDATE start SET rp = ?, penalty = ?, card = ?, remarks = ?, judge_remarks = ? WHERE id == ?''',
                (rp, under_ap_penalty + penalty, card, remarks, judge_remarks, s_id))
            return 0
        return 1

    def getUnderApPenalty(self, ap, rp, discipline, card):
        if card != "YELLOW":
            return 0
        factor = 1.
        if discipline == "STA":
            factor = 0.2
        elif discipline[0] == "D":
            factor = 0.5
        rp = float(rp)
        if rp < ap:
            return (ap - rp)*factor
        else:
            return 0.

    def updateNationalRecords(self):
        # Do check if country converter is >= 1.2
        try:
            self.nrs_ = self.getNationalRecordsAida()
            self.db_.execute("DELETE FROM records WHERE federation='aida'")
            for nr_key, nr_val in self.nrs_.items():
                self.db_.execute('''INSERT INTO records
                                 ('federation', 'country', 'class', 'gender', 'discipline', 'value')
                                 VALUES (?, ?, ?, ?, ?, ?)''',
                                 (nr_key.federation, nr_key.country, nr_key.cls, nr_key.gender,
                                 nr_key.discipline, nr_val))
        except Exception as e:
            logging.debug("Error", e)
            return 1
        return 0

    def isJudgeInCompetition(self, judge_id):
        db_out = self.db_.execute(
            "SELECT id FROM judge WHERE competition_id==? AND id==?",
            (self.id_, judge_id))
        if db_out is None:
            return None
        else:
            return db_out[0][0]

    def deleteJudge(self, judge_id):
        self.db_.execute("DELETE FROM judge WHERE id=?", judge_id)

    def getJudgeData(self, data):
        data["judges"] = []
        judges = self.db_.execute(
            '''SELECT id, first_name, last_name FROM judge WHERE competition_id == ?''',
            self.id_)
        if judges is None:
            return
        for j in judges:
            data["judges"].append(
                {"last_name": j[2], "first_name": j[1], "id": j[0]})

    def addJudge(self, first_name, last_name):
        a_id = self.db_.execute(
            "SELECT id FROM judge WHERE first_name == ? AND last_name == ? AND competition_id == ?",
            (first_name, last_name, self.id_))
        a = None
        # user already in this comp
        if a_id is not None:
            return 1;
        else:
            salt = random.randrange(sys.maxsize)
            j_id = self.db_.execute(
                "INSERT INTO judge (first_name, last_name, salt, competition_id) VALUES (?, ?, ?, ?)",
                (first_name, last_name, salt, self.id_))
            return 0

    def getJudgeQrCode(self, judge_id, url_root):
        db_out = self.db_.execute(
            "SELECT first_name, last_name, salt FROM judge WHERE competition_id==? AND id==?",
            (self.id_, judge_id))
        if db_out is None:
            return None
        else:
            jhash = self.getJudgeQrCodeHash(db_out[0][0], db_out[0][1], db_out[0][2], judge_id)
            # TODO make configurable
            url = url_root + "judge/" + str(self.id_) + "/" + str(judge_id)+"?hash=" + jhash
            qr_code = qrcode.make(url)
            ba = BytesIO()
            qr_code.save(ba, format='PNG')
            qr_code_base64 = "data:image/png;base64," + base64.b64encode(ba.getvalue()).decode('utf-8')
            return (qr_code_base64, db_out[0][0], db_out[0][1], url)

    def getJudgeQrCodeHash(self, first_name, last_name, salt, judge_id):
        return hashlib.sha256((first_name + last_name + str(salt) + str(judge_id)).encode('utf-8')).hexdigest()

    def getCompDataAndValidateJudge(self, comp_id, judge_id, judge_hash):
        try:
            assert(comp_id is not None)
            assert(judge_id is not None)
            self.id_ = int(comp_id)
            judge_id = int(judge_id)
            assert(judge_hash.isalnum())
        except:
            return None
        db_out = self.db_.execute(
            "SELECT first_name, last_name, salt FROM judge WHERE competition_id==? AND id==?",
            (self.id_, judge_id))
        db_out2 = self.db_.execute("SELECT name, comp_type FROM competition WHERE id==?", self.id_)
        if db_out is None or db_out2 is None:
            return None

        first_name = db_out[0][0]
        last_name = db_out[0][1]
        judge_hash_db = self.getJudgeQrCodeHash(first_name, last_name, db_out[0][2], judge_id)
        if judge_hash_db != judge_hash:
            return None

        return (db_out2[0][0], first_name, last_name, db_out2[0][1])

    def getAthleteResult(self, s_id):
        try:
            s_id = int(s_id)
        except:
            return None

        db_out = self.db_.execute(
            '''SELECT a.first_name, a.last_name, a.country, s.AP, s.RP, s.penalty, s.card,
                      s.remarks, s.OT, a.gender, s.judge_remarks, s.discipline, s.PB
               FROM start s
               INNER JOIN competition_athlete ca ON s.competition_athlete_id == ca.id
               INNER JOIN athlete a ON ca.athlete_id == a.id
               WHERE ca.competition_id == ? AND s.id == ?''',
            (self.id_, s_id))

        if db_out is None:
            return None

        discipline = db_out[0][11]
        return {'Name': db_out[0][0] + " " + db_out[0][1],
                'Country': db_out[0][2],
                'AP': self.convertPerformance(db_out[0][3], discipline),
                'Dis': discipline,
                'PB': self.convertPerformance(db_out[0][12], discipline),
                'RP': self.convertPerformance(db_out[0][4], discipline),
                'Penalty': db_out[0][5],
                'Card': db_out[0][6],
                'Remarks': db_out[0][7],
                'JudgeRemarks': db_out[0][10],
                'Id': s_id,
                'OT': u.convTime(db_out[0][8]),
                'NR': self.getNr(db_out[0][2], "", db_out[0][9], discipline, True),
                'Gender': db_out[0][9]}

    def cleanFederation(self, federation):
        if not federation in FEDERATIONS:
            return None
        else:
            return federation

    def getAllDisciplines(self, federation):
        federation = self.cleanFederation(federation)
        if federation is None:
            return None
        else:
            return DISCIPLINES

    def modifyBlock(self, day, disciplines, block, add):
        day = self.cleanDay(day, True)
        disciplines = self.cleanDiscipline(disciplines)
        dis_i = self.disciplineListToInt(disciplines)
        if add:
            # check if entry exists already, if yes, we don't allow another
            db_out = self.db_.execute('SELECT id FROM block WHERE competition_id==? AND day==? AND disciplines==?',
                                      (self.id_, u.convDay(day), dis_i))
            if db_out is None:
                self.db_.execute('INSERT INTO block (competition_id, day, disciplines) VALUES (?, ?, ?)',
                                 (self.id_, u.convDay(day), dis_i))
                return 0
            else:
                return 1
        else:
            block = self.cleanBlock(block)
            if block is None:
                return 2
            self.db_.execute(
                '''UPDATE block SET day=?, disciplines=?
                   WHERE competition_id==? AND id==?''',
                (u.convDay(day), dis_i, self.id_, block))
            return 0

    def removeBlock(self, block):
        block = self.cleanBlock(block)
        if block is None:
            return 1
        self.db_.execute('DELETE FROM block WHERE id==? AND competition_id==?', (block, self.id_))
        return 0

    def getDisciplinesFromInt(self, dis_i):
        dis = []
        for bit, d in enumerate(DISCIPLINES):
            if dis_i & 1<<bit:
                dis.append(d)
        return dis

    def disciplineIntToStr(self, dis_i):
        return ", ".join(self.getDisciplinesFromInt(dis_i))

    def disciplineListToInt(self, dis):
        return sum([1<<DISCIPLINES.index(d) for d in dis])

    def getFourStarts(self, current):
        comp = "<=" if current else ">"
        order = "DESC" if current else "ASC"
        cmd = '''SELECT a.first_name, a.last_name, a.country, s.OT, s.lane, s.remarks
                 FROM start s
                 INNER JOIN competition_athlete ca
                 ON s.competition_athlete_id == ca.id
                 INNER JOIN athlete a
                 ON a.id = ca.athlete_id
                 WHERE s.day*10000+s.OT == (
                    SELECT s.day*10000+s.OT
                    FROM start s
                    INNER JOIN competition_athlete ca
                    ON s.competition_athlete_id == ca.id
                    INNER JOIN athlete a
                    ON a.id = ca.athlete_id
                    WHERE ca.competition_id = ? AND s.day*10000+s.OT {} ?
                    ORDER BY s.day {}, s.OT {}
                    LIMIT 1)
                 ORDER BY s.lane
                 LIMIT 4'''.format(comp, order, order)
        min_shift = 3 if self.comp_type == "cmas" else 2
        now = datetime.now() + timedelta(minutes=min_shift)
        today = now.year*10000 + now.month*100 + now.day
        time = now.hour*100 + now.minute
        db_out = self.db_.execute(cmd, (self.id_, today*10000 + time))
        if db_out is None:
            return None
        else:
            return [{'name': d[0] + " " + d[1],
                     'country': d[2],
                     'OT': u.convTime(d[3]),
                     'lane': self.laneStyleConverter(d[4]),
                     'dns': d[5] == "DNS"}
                     for d in db_out]

    def updatePublishResults(self, publish_results):
        # clean received data
        publish_results = 1 if publish_results == True else 0
        self.db_.execute("UPDATE competition SET publish_results=?  WHERE id==?", (publish_results, self.id_))
        self.publish_results_ = publish_results == 1
        return 0
