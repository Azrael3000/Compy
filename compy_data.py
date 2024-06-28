
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
import requests
import re
import math
try:
    import country_converter
except ImportError:
    print("Could not find country_converter. Install with 'pip3 install country_converter'")
    exit(-1)
import os
import json
import glob
from datetime import datetime, timedelta, time
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

import athlete
from compy_config import CompyConfig

disciplines=["FIM", "CNF", "CWT", "CWTB", "STA", "DNF", "DYN", "DYNB"]

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
        self.comp_type_ = "aida"
        self.comp_file_ = ''
        self.start_date_ = None
        self.end_date_ = None
        self.athletes_ = []
        self.nrs_ = None
        self.sponsor_img_ = None
        self.disciplines_ = 0
        self.selected_country_ = None

        self.NR = namedtuple("NR", ["country", "gender", "discipline"])

        self.name_ = "undefined"

        with self.app_.app_context():
            # try and find it first
            c_id = self.db_.execute("SELECT id FROM competition WHERE name=?", self.name_)
            if c_id is not None:
                self.load(c_id[0][0])
            else:
                self.save()

    @property
    def version(self):
        if self.version_ is None:
            with open('VERSION', 'r') as f:
                self.version_ = str(f.read().strip())
        return self.version_

    @property
    def name(self):
        return self.name_

    @property
    def special_ranking_name(self):
        return self.special_ranking_name_

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
        allowed_comp_types = ["aida", "cmas"]
        if comp_type not in allowed_comp_types:
            return 1
        self.comp_type_ = comp_type
        self.save()
        return 0

    def laneStyleConverter(self, lane):
        if self.lane_style_ == "alphabetic":
            return chr(lane + 64)
        else: # numeric
            return str(lane)

    @property
    def comp_file(self):
        return self.comp_file_

    @property
    def athletes(self):
        return self.athletes_

    @property
    def number_of_athletes(self):
        return len(self.athletes_)

    @property
    def start_date(self):
        return self.start_date_

    @property
    def end_date(self):
        return self.end_date_

    @property
    def disciplines(self):
        dis = []
        for bit, d in enumerate(disciplines):
            if self.disciplines_ | 1<<bit:
                dis.append(d)
        return dis

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
        c_data = self.db_.execute('''SELECT athlete.country FROM athlete
                                     INNER JOIN competition_athlete
                                     ON athlete.id==competition_athlete.athlete_id
                                     WHERE competition_athlete.competition_id==?''',
                         self.id_)
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
        if self.id_ is not None:
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
                self.disciplines_ = sum([1<<disciplines.index(d) for d in df[df.keys()[1]][i].split(",")])
            i += 1
        logging.debug("Start date: %s. End date: %s", self.start_date_, self.end_date_)

        # read second sheet (list of athletes)
        df = pd.read_excel(self.comp_file_, sheet_name="Athletes and Judges", skiprows=1)
        athletes_old = self.athletes_.copy()
        self.athletes_ = [athlete.Athlete.fromArgs(r['Id'], r['FirstName'], r['LastName'], r['Gender'], r['Country'], r['Club'] if 'club' in r else "", self.db_) for i,r in df.iterrows()]
        [logging.debug("Athlete: %s %s %s %s %s", r['Id'], r['FirstName'], r['LastName'], r['Gender'], r['Country']) for i,r in df.iterrows()]
        logging.debug("Number of athletes: %d", len(self.athletes_))
        for a in self.athletes:
            a.associateWithComp(self.id_)

        for a in athletes_old:
            if a.special_ranking:
                logging.debug("set special_ranking:", a.aida_id, a.first_name)
                self.setSpecialRanking(a.aida_id, True)

        # Do check if country converter is >= 1.2
        # only update if new nationalities are available (or forced)
        #self.nrs_ = self.getNationalRecords()

        self.save()

        self.db_.execute('''DELETE FROM start
                            WHERE competition_athlete_id IN (
                                SELECT competition_athlete_id FROM start
                                INNER JOIN competition_athlete
                                ON start.competition_athlete_id == competition_athlete.id
                                WHERE competition_athlete.competition_id == ?)''',
                         self.id_)

        ap_lambda = lambda x, y, d, self: self.formatSTA(x, y) if d=="STA" else str(x)
        for day in self.getDays():
            df = pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1)
            for i,r in df.iterrows():
                aida_id = r['Diver Id']
                ca_id = self.db_.execute('''SELECT competition_athlete.id FROM competition_athlete
                                            INNER JOIN athlete
                                            ON competition_athlete.athlete_id == athlete.id
                                            WHERE athlete.aida_id=?''',
                                         aida_id)
                dis = r['Discipline']
                ap = ap_lambda(r['Meters or Min'], r['Sec(STA only)'], dis, self)
                ot = self.parseTime(r['OT'])
                lane = int(r['Zone'])
                self.db_.execute('''INSERT INTO start
                                    (competition_athlete_id, discipline, lane, OT, AP, day)
                                    VALUES (?, ?, ?, ?, ?, ?)''',
                                 (ca_id[0][0], dis, lane, ot, ap, day))

    def getNationalRecords(self):
        empty_req = requests.post('https://www.aidainternational.org/public_pages/all_national_records.php', data={})
        html = empty_req.text
        start = html.find('id="nationality"')
        start = html.find('<option', start)
        end = html.find('</select>', start)
        nationalities = str.splitlines(html[start:end])
        p = re.compile("\<option.*value=\"([0-9]+)\">(.*)\</option\>")
        country_value_map = {}
        cc = country_converter.CountryConverter()
        for n in nationalities:
            result = p.search(n)
            if result:
                country_value_map[cc.convert(result.group(2), to = 'IOC')] = result.group(1)
        nrs = {}
        for c in self.countries:
            data = {
                'nationality': str(country_value_map[c]),
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
            p = re.compile("\<td\>(.*)\</td\>")
            for i in range(int(len(entries)/10)):
                gender = p.search(entries[i*10 + 2]).group(1)
                dis = p.search(entries[i*10 + 3]).group(1)
                result = p.search(entries[i*10 + 4]).group(1)
                points = float(p.search(entries[i*10 + 6]).group(1))
                nrs[self.NR(country=c, gender=gender, discipline=dis)] = [result, points]
        logging.debug("National records:")
        logging.debug("Country | Gender | Discipline | Result | Points")
        for key, val in nrs.items():
            logging.debug("%s | %s | %s | %s | %d", key.country, key.gender, key.discipline, val[0], val[1])
        logging.debug("-----------------")
        return nrs

    def setSpecialRanking(self, athlete_id, special_ranking):
        found = False
        if len(self.athletes_) == 0:
            logging.warning("Data not initialized yet in setSpecialRanking")
            return 1
        for a in self.athletes_:
            if a.aida_id == athlete_id:
                a.setSpecialRanking(special_ranking)
                self.save()
                found = True
                return 0
        if not found:
            logging.warning("Tried setting special_ranking (" + str(special_ranking) + ") to athlete with id '" + athlete_id + "' but this id could not be found")
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
                            special_ranking_name=? WHERE id=?''',
                         (self.name_, datetime.now().isoformat(), self.version, self.lane_style, self.comp_type,
                          self.comp_file, self.start_date_, self.end_date_, sponsor_img_data,
                          self.selected_country_, self.special_ranking_name, self.id_))
        logging.debug("Saved competition: " + self.name)

    def load(self, comp_id):
        #TODO on load find self.id_ if not, reset to None
        load_data = self.db_.execute('''SELECT name, version, lane_style, comp_type, comp_file,
                                        start_date, end_date, sponsor_img, selected_country,
                                        special_ranking_name, disciplines
                                        FROM competition WHERE id=?''',
                                     comp_id)
        if load_data is None:
            logging.error("Could not find save file with id '" + id + "'")
            return ""
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
            self.disciplines_ = comp_data[10]
            load_data = self.db_.execute("SELECT athlete_id FROM competition_athlete WHERE competition_id=?",
                                         comp_id)
            if load_data is None:
                self.athletes_ = []
            else:
                self.athletes_ = [athlete.Athlete.fromDb(a_id[0], self.db_) for a_id in load_data]
                for a in self.athletes:
                    a.associateWithComp(self.id_)
            #self.getResultPDF('all', 'all', 'all', False, True)
            return self.name_

    def getDays(self):
        if self.start_date is None:
            return
        days = []
        d0 = datetime.strptime(self.start_date, '%Y-%m-%d')
        d1 = datetime.strptime(self.end_date, '%Y-%m-%d')
        delta = d1 - d0
        for i in range(delta.days + 1):
            yield (d0 + timedelta(days=i)).strftime('%Y-%m-%d')

    def getDaysWithDisciplinesLanes(self):
        dwd = {}
        for day in self.getDays():
            db_out = self.db_.execute('''SELECT DISTINCT discipline, lane FROM start s
                                         INNER JOIN competition_athlete ca
                                         ON s.competition_athlete_id == ca.id
                                         WHERE (ca.competition_id==? AND s.day==?)''',
                                      (self.id_, day))
            print(">>>", day)
            disciplines_on_day = list({d[0] for d in db_out})
            disciplines_w_lanes = {}
            for dis in disciplines_on_day:
                disciplines_w_lanes[dis] = [d[1] for d in db_out if d[0]==dis]
            dwd[day] = disciplines_w_lanes
        logging.debug(dwd)
        return dwd

    def getDisciplines(self):
        if self.disciplines is None:
            return []
        dwc = []
        # only aida has Overall and SpecialRanking
        if self.comp_type == "aida":
            dwc.append("Overall")
            # only add special_ranking result if we have at least one special_ranking
            for a in self.athletes_:
                if a.special_ranking:
                    dwc.append(self.special_ranking_name)
                    break
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
                for a in self.athletes_:
                    if a.special_ranking:
                        countries.append(self.special_ranking_name)
                        break
        else:
            countries += self.countries
        return countries

    def getStartList(self, day, discipline):
        if self.comp_file is None:
            return None
        db_out = self.db_.execute('''
            SELECT a.first_name, a.last_name, a.country, s.AP, s.OT, s.lane
            FROM start s
            INNER JOIN competition_athlete ca ON s.competition_athlete_id == ca.id
            INNER JOIN athlete a ON ca.athlete_id == a.id
            WHERE ca.competition_id==? AND s.discipline==? AND s.day==?''',
            (self.id_, discipline, day))
        # RPs are 'Meters or Min.1'
        start_list = [{'Name': r[0] + " " + r[1],
                       'Nationality': r[2],
                       'AP': r[3],
                       'Warmup': self.getWTfromOT(r[4]),
                       'OT': r[4],
                       'Lane': self.laneStyleConverter(r[5])}
                       for r in db_out]
        return start_list

    def getWTfromOT(self, ot):
        ota = ot.split(':')
        otf = int(ot[0])*60 + int(ot[1])
        wtf = otf-45 # does not work if ot is close to midnight, but seriously?
        wt = str(math.floor(wtf/60)) + ":" + str(wtf%60)
        return wt

    def getStartListPDF(self, day="all", discipline="all", in_memory=False):
        if day=="all" and discipline=="all":
            dwd = self.getDaysWithDisciplinesLanes()
            files = []
            for d in dwd:
                for dis in dwd[d].keys():
                    files.append(self.getStartListPDF(d, dis, True))
            pages = []
            for doc in files:
                for page in doc.pages:
                    pages.append(page)
            merged_pdf = files[0].copy(pages)
            fname = os.path.join(self.config.download_folder, self.name + "_start_lists.pdf")
            merged_pdf.write_pdf(fname)
            return fname
        start_df = pd.DataFrame(self.getStartList(day, discipline))
        html_string = start_df.to_html(index=False, justify="left", classes="df_table")
        day_obj = datetime.strptime(day, "%Y-%m-%d")
        human_day = day_obj.strftime("%d. %m. %Y")
        html_string = """
            <html>
            <head>
            <style>
            tr th:first-child {{
                padding-left:0px;
                text-align: left;
            }}
            tr td:first-child {{
                padding-left:0px;
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
            """.format(self.name, discipline, human_day, html_string, self.sponsor_img_data, self.sponsor_img_width, self.sponsor_img_height)
        html = wp.HTML(string=html_string, base_url="/")
        #fname = os.path.join(self.config.download_folder, "test.html")
        #with open(fname, "w") as f:
        #    f.write(html_string)
        if in_memory:
            return html.render()
        else:
            fname = os.path.join(self.config.download_folder, self.name + "_start_list_" + day + "_" + discipline + ".pdf")
            html.write_pdf(fname)
            return fname

    def getLaneList(self, day, discipline, lane):
        if self.comp_file is None:
            return None
        df = pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1)
        ap_lambda = lambda x, y, self: str(x)
        if discipline == "STA":
            ap_lambda = lambda x, y, self: self.formatSTA(x, y)
        # RPs are 'Meters or Min.1'
        lane_list = [{'Name': r['Diver Name'],
                       'AP': ap_lambda(r['Meters or Min'], r['Sec(STA only)'], self),
                       'OT': self.parseTime(r['OT']),
                       'NR': r['Diver Country']}
                       for i,r in df.iterrows() if r['Discipline'] == discipline and self.laneStyleConverter(str(r['Zone'])) == lane]
        return lane_list

    def getLaneListPDF(self, day="all", discipline="all", lane="all", in_memory=False):
        if day=="all" and discipline=="all":
            dwd = self.getDaysWithDisciplinesLanes()
            files = []
            for d in dwd:
                for dis in dwd[d].keys():
                    for l in dwd[d][dis]:
                        files.append(self.getLaneListPDF(d, dis, l, True))
            pages = []
            for doc in files:
                for page in doc.pages:
                    pages.append(page)
            merged_pdf = files[0].copy(pages)
            fname = os.path.join(self.config.download_folder, self.name + "_lane_lists.pdf")
            merged_pdf.write_pdf(fname)
            return fname
        lane_df = pd.DataFrame(self.getLaneList(day, discipline, lane))
        lane_df["RP"] = ""
        lane_df["Card"] = ""
        lane_df["Remarks"] = ""
        html_string = lane_df.to_html(index=False, justify="left", classes="df_table")
        day_obj = datetime.strptime(day, "%Y-%m-%d")
        human_day = day_obj.strftime("%d. %m. %Y")
        html_string = """
            <html>
            <head>
            <style>
            table {{
                width: 100%;
            }}
            tr th:first-child {{
                padding-left:0px;
                text-align: left;
            }}
            tr td:first-child {{
                padding-left:0px;
                text-align: left;
            }}
            th, td {{
                padding:10px 0px 10px 50px;
                text-align: center;
                border-bottom: 1px solid #ddd;
            }}
            table th:nth-child(1) {{
                width: 20%;
            }}
            table th:nth-child(2) {{
                width: 7%;
            }}
            table th:nth-child(3) {{
                width: 7%;
            }}
            table th:nth-child(4) {{
                width: 7%;
            }}
            table th:nth-child(5) {{
                width: 10%;
            }}
            table th:nth-child(6) {{
                width: 10%;
            }}
            table th:nth-child(7) {{
                width: 39%;
            }}
            @page {{
                margin: 4cm 1cm 1cm 1cm;
                size: A4 landscape;
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
                bottom: -1cm;
                height: 1cm;
                text-align: center;
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
            <footer></footer>
            </body>
            </html>
            """.format(self.name, discipline, lane, human_day, html_string, self.sponsor_img_data, self.sponsor_img_width, self.sponsor_img_height)
        html = wp.HTML(string=html_string, base_url="/")
        fname = os.path.join(self.config.download_folder, "test.html")
        with open(fname, "w") as f:
            f.write(html_string)
        if in_memory:
            return html.render()
        else:
            fname = os.path.join(self.config.download_folder, self.name + "_lane_list_" + day + "_" + discipline + "_" + lane + ".pdf")
            html.write_pdf(fname)
            return fname

    def getResult(self, discipline, gender, country):
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
            dfs = []
            for day in self.getDays():
                dfs.append(pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1))
            full_df = pd.concat(dfs)
            full_df = full_df[(full_df['Gender'] == gender)]
            if (country != 'International'):
                full_df = full_df[(full_df['Diver Country'] == country)]
            if discipline == self.special_ranking_name:
                special_ranking_ids = []
                for a in self.athletes_:
                    if a.special_ranking:
                        special_ranking_ids.append(a.aida_id)
                full_df = full_df[full_df['Diver Id'].astype('string').isin(special_ranking_ids)]
            reduction_dict = {'Points': 'sum', 'Diver Name': 'first', 'Diver Country': 'first'}
            for dis in self.disciplines:
                reduction_dict[dis] = 'first'
                if dis == "STA":
                    full_df[dis] = full_df.apply(lambda row: self.formatSTA(row['Meters or Min.1'], row['Sec(STA only).1']) + " (" + str(row['Points']) + ")" if row['Discipline'] == dis and not np.isnan(row['Meters or Min.1']) else np.nan, axis=1)
                else:
                    full_df[dis] = full_df.apply(lambda row: str(row['Meters or Min.1']) + " (" + str(row['Points']) + ")" if row['Discipline'] == dis and not np.isnan(row['Meters or Min.1']) else np.nan, axis=1)
            columns = self.disciplines + ["Diver Name", "Diver Id", "Diver Country", "Points"]
            if self.comp_type == "cmas":
                columns.append("Club")
            exp_df = full_df[columns]
            result_df = exp_df.groupby('Diver Id').agg(reduction_dict).reset_index()
            # remove everyone with 0 points overall
            mask = result_df['Points'] != 0.
            result_df = result_df[mask]
            result_df = result_df.sort_values(by=['Points'], ascending=[False])
            result_df.fillna("", inplace=True).infer_objects(copy=False)
            result_df['Rank'] = result_df['Points'].rank(ascending=False)
            columns = ['Rank', 'Diver Name', 'Diver Country'] + self.disciplines + ['Points'] # order is important for pdf output
            result_df = result_df[columns]
            result_df['Rank'] = result_df['Rank'].astype(int)
            result_df.rename(columns = {'Diver Name': 'Name', 'Diver Country': 'Country'}, inplace = True)
            result_keys += self.disciplines + ["Points"]
            return result_df.to_dict('records'), result_keys
        else:
            ap_lambda = lambda x, y, self: str(x)
            if discipline == "STA":
                ap_lambda = lambda x, y, self: self.formatSTA(x, y)
            dfs = []
            for day in self.getDays():
                dfs.append(pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1))
            full_df = pd.concat(dfs)
            result_df = full_df[(full_df['Discipline'] == discipline) & (full_df['Gender'] == gender)]
            if country != 'International' and country != self.special_ranking_name:
                result_df = result_df[(result_df['Diver Country'] == country)]
            if self.comp_type == "cmas" and country == self.special_ranking_name:
                result_df = result_df[(result_df['Diver Country'] == self.selected_country) | (result_df['Diver Country'] == self.selected_country + "*")]
                special_ranking_ids = []
                for a in self.athletes_:
                    if a.special_ranking:
                        special_ranking_ids.append(a.aida_id)
                result_df = result_df[result_df['Diver Id'].astype('string').isin(special_ranking_ids)]
            result_df = result_df.sort_values(by=['Points', 'Meters or Min', 'Sec(STA only)'], ascending=[False, False, False])
            # RPs are 'Meters or Min.1'
            result_df.fillna(0., inplace=True).infer_objects(copy=False)
            if self.comp_type == "aida":
                result = [{'Rank': i,
                           'Name': r['Diver Name'],
                           'Country': r['Diver Country'],
                           'AP': ap_lambda(r['Meters or Min'], r['Sec(STA only)'], self),
                           'RP': ap_lambda(r['Meters or Min.1'], r['Sec(STA only).1'], self),
                           'Penalty': float(r['Pen(UNDER AP)']) + float(r['Pen(other)']),
                           'Card': r['Card'],
                           'Remarks': r['Remarks'],
                           'Points': r['Points']}
                           for i,r in result_df.iterrows()]
                result_keys += ["AP", "RP", "Penalty", "Card", "Remarks", "Points"]
            else:
                result = [{'Rank': i,
                           'Name': r['Diver Name'],
                           'Country': r['Diver Country'],
                           'Club': r['Club'],
                           'RP': ap_lambda(r['Meters or Min.1'], r['Sec(STA only).1'], self),
                           'Card': r['Card'],
                           'Remarks': r['Remarks'],
                           'Points': r['Points']}
                           for i,r in result_df.iterrows()]
                result_keys += ["RP", "Card", "Remarks"]
            cur_points = 1000000
            cur_ap = ""
            for i in range(len(result)):
                if result[i]["Points"] == 0:
                    result[i]["Rank"] = ""
                elif result[i]["Points"] == cur_points and (self.comp_type == "cmas" or result[i]["AP"] == cur_ap):
                    result[i]["Rank"] = ""
                else:
                    cur_points = result[i]["Points"]
                    if self.comp_type == "aida":
                        cur_ap = result[i]["AP"]
                    result[i]["Rank"] = i+1
            return result, result_keys

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
        df = pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1)
        for a in self.athletes:
            df_a = df[df['Diver Id'].astype('string') == a.aida_id]
            n = len(df_a.index)
            for i in range(n-1):
                this_break = {"Name": a.first_name + " " + a.last_name}
                this_break["Dis1"] = df_a['Discipline'].iloc[i+0]
                this_break["Dis2"] = df_a['Discipline'].iloc[i+1]
                this_break["OT1"] = self.parseTime(df_a['OT'].iloc[i+0])
                this_break["OT2"] = self.parseTime(df_a['OT'].iloc[i+1])
                ot1 = this_break["OT1"].split(":")
                ot2 = this_break["OT2"].split(":")
                time = int(ot2[0])*60 + int(ot2[1]) - int(ot1[0])*60 - int(ot1[1])
                min_break = min(min_break, time)
                this_break["Break"] = str(int(time/60)).zfill(2) + ":" + str(time%60).zfill(2)
                breaks_list.append(this_break)
        min_break = str(int(min_break/60)).zfill(2) + ":" + str(min_break%60).zfill(2)
        breaks_list = sorted(breaks_list, key=lambda d: d["Break"])
        return {"min_break": min_break, "breaks_list": breaks_list}

    def setOTs(self, data):
        ots = []
        for day in self.getDays():
            df = pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1)
            ots_on_day = list({self.parseTime(r['OT']) for i,r in df.iterrows()})
            dayc = ":".join(day.split("-"))
            ots += [dayc + ":" + ot + ":00" for ot in ots_on_day]
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
        out = str(int(minutes)) + ":"
        if self.comp_type == "aida":
            out += str(int(seconds)).zfill(2)
        else:
            out += "%05.2f" % round(seconds, 2)
        return out
