
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

import pandas as pd
import logging
from collections import Counter, namedtuple
import requests
import re
import country_converter
import os
import json
import glob
from datetime import datetime, timedelta
import weasyprint as wp
import base64
from PIL import Image
from io import BytesIO
import numpy as np

import athlete
from compy_config import CompyConfig

class CompyData:

    def __init__(self, comp_file=''):
        self.name_ = "undefined"
        self.config_ = CompyConfig()
        self.version_ = None
        self.lane_style_ = "numeric"
        self.comp_file_ = comp_file
        self.start_date_ = None
        self.end_date_ = None
        self.athletes_ = []
        self.countries_ = None
        self.nrs_ = None
        self.sponsor_img_ = None
        self.disciplines_ = None

        self.NR = namedtuple("NR", ["country", "gender", "discipline"])

        for i in range(512):
            if not os.path.exists(self.file_path):
                break
            self.name_ = "undefined" + str(i)

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
    def file_path(self):
        return os.path.join(self.config.storage_folder, self.name_ + ".cpy")

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

    def laneStyleConverter(self, lane):
        if self.lane_style_ == "alphabetic":
            return chr(lane + 64)
        else: # numeric
            return lane

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
        return self.disciplines_

    @property
    def sponsor_img_data(self):
        if self.sponsor_img_ is None:
            return ""
        else:
            return self.sponsor_img_["data"]

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
                self.disciplines_ = df[df.keys()[1]][i].split(",")
            i += 1
        logging.debug("Start date: %s. End date: %s", self.start_date_, self.end_date_)

        # read second sheet (list of athletes)
        df = pd.read_excel(self.comp_file_, sheet_name="Athletes and Judges", skiprows=1)
        self.athletes_ = [athlete.Athlete.fromArgs(r['Id'], r['FirstName'], r['LastName'], r['Gender'], r['Country']) for i,r in df.iterrows()]
        [logging.debug("Athlete: %s %s %s %s %s", r['Id'], r['FirstName'], r['LastName'], r['Gender'], r['Country']) for i,r in df.iterrows()]
        logging.debug("Number of athletes: %d", len(self.athletes_))

        # count countries
        self.countries_ = Counter([a.country for a in self.athletes_])
        logging.debug("Country | Number of athletes:")
        for c in self.countries_:
            logging.debug("%s     | %s", c, self.countries_[c])
        logging.debug("-----------------------------")

        # Do check if country converter is >= 1.2
        # only update if new nationalities are available (or forced)
        #self.nrs_ = self.getNationalRecords()

        self.save()

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
        print(country_value_map)
        for c in self.countries_:
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
        logging.debug("Country | Gender | Diszipline | Result | Points")
        for key, val in nrs.items():
            logging.debug("%s | %s | %s | %s | %d", key.country, key.gender, key.diszipline, val[0], val[1])
        logging.debug("-----------------")
        return nrs

    def setNewcomer(self, athlete_id, newcomer):
        found = False
        if len(self.athletes_) == 0:
            logging.warning("Data not initialized yet in setNewcomer")
            return 1
        for a in self.athletes_:
            if a.id == athlete_id:
                a.setNewcomer(newcomer)
                self.save()
                found = True
                return 0
        if not found:
            logging.warning("Tried setting newcomer (" + str(newcomer) + ") to athlete with id '" + athlete_id + "' but this id could not be found")
        return 1

    def getSavedCompetitions(self):
        os.chdir(self.config.storage_folder)
        saved_comp_files = glob.glob("*.cpy")
        logging.debug(saved_comp_files)
        if len(saved_comp_files) == 0:
            return None
        saved_comp_info = []
        for f in saved_comp_files:
            with open(f, "r") as comp_file_data:
                comp_data = json.load(comp_file_data)
                saved_comp_info.append({"name": comp_data["name"], "save_date": comp_data["save_date"]})
        return sorted(saved_comp_info, key=lambda ci: ci["save_date"], reverse=True)

    def changeName(self, new_name, overwrite):
        prev_name = self.name_
        prev_path = self.file_path
        self.name_ = new_name
        if os.path.exists(self.file_path) and not overwrite:
            self.name_ = prev_name
            return [1, self.name_]
        else:
            if os.path.exists(self.file_path):
                os.remove(prev_path)
            self.save()
            return [0, self.name_]

    def save(self):
        data = {}
        data["name"] = self.name_
        data["save_date"] = datetime.now().isoformat()
        data["version"] = self.version
        data["lane_style"] = self.lane_style
        data["comp_file"] = self.comp_file
        data["start_date"] = self.start_date_
        data["end_date"] = self.end_date_
        data["disciplines"] = self.disciplines_
        data["countries"] = self.countries_
        data["athletes"] = [a.saveData() for a in self.athletes]
        data["sponsor_img"] = self.sponsor_img_
        with open(self.file_path, "w") as write_file:
            json.dump(data, write_file)
        logging.debug("Saved to file: " + self.file_path)

    def load(self, name):
        prev_name = self.name
        self.name_ = name
        if not os.path.exists(self.file_path):
            logging.error("Could not find save file with name '" + name + "'")
            self.name_ = prev_name
            return 1
        else:
            with open(self.file_path, "r") as read_file:
                data = json.load(read_file)
            if not "name" in data:
                logging.error("Invalid file, no 'name' found")
                return 1
            if data["name"] != self.name:
                logging.error("Invalid file, 'name' does not match (" + self.name + " != " + data["name"] + ")")
                return 1
            read_keys = ["save_date", "version", "lane_style", "comp_file", "start_date", "end_date", "athletes"]
            for key in read_keys:
                if not key in data:
                    logging.error("Invalid file, no '" + key + "' found")
                    return 1
            self.version_ = data["version"]
            self.lane_style_ = data["lane_style"]
            self.comp_file_ = data["comp_file"]
            self.start_date_ = data["start_date"]
            self.end_date_ = data["end_date"]
            self.disciplines_ = data["disciplines"]
            self.countries_ = data["countries"]
            self.athletes_ = [athlete.Athlete.fromDict(a) for a in data["athletes"]]
            self.sponsor_img_ = data["sponsor_img"]
            self.getResultPDF('Overall', 'M', 'International')

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
            df = pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1)
            disciplines_on_day = list({r['Discipline'] for i,r in df.iterrows()})
            disciplines_w_lanes = {}
            for dis in disciplines_on_day:
                disciplines_w_lanes[dis] = list({self.laneStyleConverter(r['Zone']) for i,r in df.iterrows() if r['Discipline'] == dis})
            dwd[day] = disciplines_w_lanes
        logging.debug(dwd)
        return dwd

    def getDisciplines(self):
        if self.disciplines is None:
            return []
        dwc = ["Overall"]
        # only add newcomer result if we have at least one newcomer
        for a in self.athletes_:
            if a.newcomer:
                dwc.append("Newcomer")
                break
        dwc += self.disciplines
        return dwc

    def getCountries(self):
        countries = ["International"]
        for c in self.countries_:
            countries.append(c) # in the future this should be only the countries that are requested
        return countries

    def getStartList(self, day, discipline):
        if self.comp_file is None:
            return None
        df = pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1)
        ap_lambda = lambda x, y: str(x)
        if discipline == "STA":
            ap_lambda = lambda x, y: str(int(x)) + ":" + str(int(y)).zfill(2)
        # RPs are 'Meters or Min.1'
        start_list = [{'Name': r['Diver Name'],
                       'AP': ap_lambda(r['Meters or Min'], r['Sec(STA only)']),
                       'Warmup': r['WT'],
                       'OT': r['OT'],
                       'Lane': self.laneStyleConverter(r['Zone'])}
                       for i,r in df.iterrows() if r['Discipline'] == discipline]
        return start_list

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
                padding:10px 0px 10px 50px;
                text-align: center;
                border-bottom: 1px solid #ddd;
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
        ap_lambda = lambda x, y: str(x)
        if discipline == "STA":
            ap_lambda = lambda x, y: str(int(x)) + ":" + str(int(y)).zfill(2)
        # RPs are 'Meters or Min.1'
        lane_list = [{'Name': r['Diver Name'],
                       'AP': ap_lambda(r['Meters or Min'], r['Sec(STA only)']),
                       'OT': r['OT'],
                       'NR': r['Diver Country']}
                       for i,r in df.iterrows() if r['Discipline'] == discipline and self.laneStyleConverter(r['Zone']) == lane]
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
                margin: 4cm 1cm 6cm 1cm;
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
                <h2>Lane list {} - lane {} - {}</h2>
            </header>
            {}
            <footer><img src="{}" style="width:{}cm; height:{}cm;"></footer>
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
            return None
        result = []
        if discipline == "Overall" or discipline == "Newcomer":
            dfs = []
            for day in self.getDays():
                dfs.append(pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1))
            full_df = pd.concat(dfs)
            full_df = full_df[(full_df['Gender'] == gender)]
            if (country != 'International'):
                full_df = full_df[(full_df['Diver Country'] == country)]
            if discipline == "Newcomer":
                newcomer_ids = []
                for a in self.athletes_:
                    if a.newcomer:
                        newcomer_ids.append(a.id)
                full_df = full_df[full_df['Diver Id'].isin(newcomer_ids)]
            reduction_dict = {'Points': 'sum', 'Diver Name': 'first', 'Diver Country': 'first'}
            for dis in self.disciplines:
                reduction_dict[dis] = 'first'
                if dis == "STA":
                    full_df[dis] = full_df.apply(lambda row: str(int(row['Meters or Min.1'])) + ":" + str(int(row['Sec(STA only).1'])).zfill(2) + " (" + str(row['Points']) + ")" if row['Discipline'] == dis and not np.isnan(row['Meters or Min.1']) else np.nan, axis=1)
                else:
                    full_df[dis] = full_df.apply(lambda row: str(row['Meters or Min.1']) + " (" + str(row['Points']) + ")" if row['Discipline'] == dis and not np.isnan(row['Meters or Min.1']) else np.nan, axis=1)
            columns = self.disciplines + ["Diver Name", "Diver Id", "Diver Country", "Points"]
            exp_df = full_df[columns]
            result_df = exp_df.groupby('Diver Id').agg(reduction_dict).reset_index()
            # remove everyone with 0 points overall
            mask = result_df['Points'] != 0.
            result_df = result_df[mask]
            result_df = result_df.sort_values(by=['Points'], ascending=[False])
            result_df.fillna("", inplace=True)
            result_df['Rank'] = result_df['Points'].rank(ascending=False)
            columns = ['Rank', 'Diver Name', 'Diver Country'] + self.disciplines + ['Points'] # order is important for pdf output
            result_df = result_df[columns]
            result_df['Rank'] = result_df['Rank'].astype(int)
            result_df.rename(columns = {'Diver Name': 'Name', 'Diver Country': 'Country'}, inplace = True)
            return result_df.to_dict('records')
        else:
            ap_lambda = lambda x, y: str(x)
            if discipline == "STA":
                ap_lambda = lambda x, y: str(int(x)) + ":" + str(int(y)).zfill(2)
            dfs = []
            for day in self.getDays():
                dfs.append(pd.read_excel(self.comp_file_, sheet_name=day, skiprows=1))
            full_df = pd.concat(dfs)
            result_df = full_df[(full_df['Discipline'] == discipline) & (full_df['Gender'] == gender)]
            if (country != 'International'):
                result_df = result_df[(result_df['Diver Country'] == country)]
            result_df = result_df.sort_values(by=['Points', 'Meters or Min', 'Sec(STA only)'], ascending=[False, False, False])
            # RPs are 'Meters or Min.1'
            result_df.fillna(0., inplace=True)
            result = [{'Rank': i,
                       'Name': r['Diver Name'],
                       'Country': r['Diver Country'],
                       'AP': ap_lambda(r['Meters or Min'], r['Sec(STA only)']),
                       'RP': ap_lambda(r['Meters or Min.1'], r['Sec(STA only).1']),
                       'Penalty': float(r['Pen(UNDER AP)']) + float(r['Pen(other)']),
                       'Card': r['Card'],
                       'Remarks': r['Remarks'],
                       'Points': r['Points']}
                       for i,r in result_df.iterrows()]
            cur_points = 1000000
            cur_ap = ""
            for i in range(len(result)):
                if result[i]["Points"] == 0:
                    result[i]["Rank"] = ""
                elif result[i]["Points"] == cur_points and result[i]["AP"] == cur_ap:
                    result[i]["Rank"] = ""
                else:
                    cur_points = result[i]["Points"]
                    cur_ap = result[i]["AP"]
                    result[i]["Rank"] = i+1
            return result

    def getResultPDF(self, discipline="all", gender="all", country="all", in_memory=False):
        if discipline=="all" and gender=="all":
            dwd = self.getDaysWithDisciplinesLanes()
            files = []
            for d in self.disciplines + ["Overall", "Newcomer"]:
                for g in ["F", "M"]:
                    for c in self.getCountries():
                        pdf = self.getResultPDF(d, g, c, True)
                        if pdf is not None:
                            files.append(pdf)
            pages = []
            for doc in files:
                for page in doc.pages:
                    pages.append(page)
            merged_pdf = files[0].copy(pages)
            fname = os.path.join(self.config.download_folder, self.name + "_results.pdf")
            merged_pdf.write_pdf(fname)
            return fname
        result_df = pd.DataFrame(self.getResult(discipline, gender, country))
        if len(result_df.index) == 0:
            return None
        gender_str = "Female" if gender == "F" else "Male"
        html_string = result_df.to_html(index=False, justify="left", classes="df_table")
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
            /*
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
            */
            @page {{
                margin: 4cm 1cm 6cm 1cm;
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
                <h2>Result {} - {} - {}</h2>
            </header>
            {}
            <footer><img src="{}" style="width:{}cm; height:{}cm;"></footer>
            </body>
            </html>
            """.format(self.name, discipline, country, gender_str, html_string, self.sponsor_img_data, self.sponsor_img_width, self.sponsor_img_height)
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
