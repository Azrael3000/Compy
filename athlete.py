
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

class Athlete:

    def __init__(self, id, first_name, last_name, gender, country, newcomer, club):
        self.id_ = str(id)
        self.first_name_ = first_name
        self.last_name_ = last_name
        self.gender_ = gender
        self.country_ = country
        self.newcomer_ = newcomer
        self.club_ = club


    @classmethod
    def fromDict(cls, athlete_dict):
        read_keys = ["id", "first_name", "last_name", "gender", "country", "newcomer", "club"]
        for key in read_keys:
            if not key in athlete_dict:
                logging.error("Invalid file, no '" + key + "' found");
                return None
        return cls(athlete_dict["id"], athlete_dict["first_name"], athlete_dict["last_name"], athlete_dict["gender"], athlete_dict["country"], athlete_dict["newcomer"], athlete_dict["club"])

    @classmethod
    def fromArgs(cls, id, first_name, last_name, gender, country, club=""):
        return cls(id, first_name, last_name, gender, country, False, club)

    @property
    def id(self):
        return self.id_

    @property
    def first_name(self):
        return self.first_name_

    @property
    def last_name(self):
        return self.last_name_

    @property
    def gender(self):
        return self.gender_

    @property
    def country(self):
        return self.country_

    @property
    def newcomer(self):
        return self.newcomer_

    @property
    def club(self):
        return self.club_

    def setNewcomer(self, newcomer):
        self.newcomer_ = newcomer

    def saveData(self):
        data = {}
        data["id"] = self.id
        data["first_name"] = self.first_name
        data["last_name"] = self.last_name
        data["gender"] = self.gender
        data["country"] = self.country
        data["newcomer"] = self.newcomer
        data["club"] = self.club
        return data
