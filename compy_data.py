
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

import athlete
from compy_config import CompyConfig

class CompyData:

    def __init__(self, comp_file=''):
        self.config_ = CompyConfig()
        self.version_ = None
        self.lane_style_ = "numeric"
        self.comp_file_ = comp_file
        self.start_date_ = None
        self.end_date_ = None
        self.athletes_ = []
        self.countries_ = None

        self.NR = namedtuple("NR", ["country", "gender", "discipline"])

    @property
    def version(self):
        if self.version_ is None:
            with open('VERSION', 'r') as f:
                self.version_ = str(f.read().strip())
        return self.version_

    @property
    def config:
        return self.config_

    @property
    def lane_style(self):
        return self.lane_style_

    def laneStyleChange(self, lane_style):
        self.lane_style_ = lane_style

    @property
    def comp_file(self):
        return self.comp_file_

    @property
    def athletes(self):
        return self.athletes_

    @property
    def number_of_athletes(self):
        return len(self.athletes_)

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
            i += 1
        logging.debug("Start date: %s. End date: %s", self.start_date_, self.end_date_)

        # read second sheet (list of athletes)
        df = pd.read_excel(self.comp_file_, sheet_name="Athletes and Judges", skiprows=1)
        self.athletes_ = [athlete.Athlete(r['Id'], r['LastName'], r['FirstName'], r['Gender'], r['Country']) for i,r in df.iterrows()]
        [logging.debug("Athlete: %s %s %s %s %s", r['Id'], r['LastName'], r['FirstName'], r['Gender'], r['Country']) for i,r in df.iterrows()]
        logging.debug("Number of athletes: %d", len(self.athletes_))

        # count countries
        self.countries_ = Counter([a.country for a in self.athletes_])
        logging.debug("Country | Number of athletes:")
        for c in self.countries_:
            logging.debug("%s     | %s", c, self.countries_[c])
        logging.debug("-----------------------------")

        # Requires update of country_converter
        #self.nrs_ = self.getNationalRecords()

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
                found = True
                return 0
        if not found:
            logging.warning("Tried setting newcomer (" + str(newcomer) + ") to athlete with id '" + athlete_id + "' but this id could not be found")
        return 1
