
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

class Athlete:

    def __init__(self, aida_id, first_name, last_name, gender, country, special_ranking, club, db):
        self.id_ = None
        self.aida_id_ = str(aida_id)
        self.first_name_ = first_name
        self.last_name_ = last_name
        self.gender_ = gender
        self.country_ = country
        self.special_ranking_ = special_ranking
        self.club_ = club
        self.db_ = db
        self.createOrUpdate()

    @classmethod
    def fromDict(cls, athlete_dict, db):
        read_keys = ["id", "first_name", "last_name", "gender", "country", "special_ranking", "club"]
        for key in read_keys:
            if not key in athlete_dict:
                logging.error("Invalid file, no '" + key + "' found");
                return None
        return cls(athlete_dict["id"], athlete_dict["first_name"], athlete_dict["last_name"], athlete_dict["gender"], athlete_dict["country"], athlete_dict["special_ranking"], athlete_dict["club"], db)

    @classmethod
    def fromArgs(cls, id, first_name, last_name, gender, country, club, db):
        return cls(id, first_name, last_name, gender, country, False, club, db)

    def createOrUpdate(self):
        # attempt to find athlete in database, first by aida_id, then by name, if id does not exist
        if self.id_ is None:
            db_id = None
            if len(self.aida_id) == 36:
                db_id = self.db_.execute('''SELECT id FROM athlete WHERE aida_id=?''',
                                         self.aida_id)
            else:
                db_id = self.db_.execute('''SELECT id FROM athlete
                                            WHERE first_name=? AND last_name=? AND gender=?''',
                                         (self.first_name, self.last_name, self.gender))
            if db_id is not None:
                self.id_ = db_id[0][0]
        if self.id_ is None:
            self.db_.execute('''INSERT INTO athlete
                                (first_name, last_name, aida_id, gender, country, special_ranking, club)
                                VALUES(?, ?, ?, ?, ?, ?, ?)''',
                             (self.first_name, self.last_name, self.aida_id, self.gender, self.country,
                              self.special_ranking, self.club))
            self.id_ = self.db_.last_index
        else:
            self.db_.execute('''UPDATE athlete
                                SET first_name=?, last_name=?, aida_id=?, gender=?, country=?,
                                special_ranking=?, club=? WHERE id=?''',
                             (self.first_name, self.last_name, self.aida_id, self.gender, self.country,
                              self.special_ranking, self.club, self.id_))

    @property
    def id(self):
        return self.id_

    @property
    def aida_id(self):
        return self.aida_id_

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
    def special_ranking(self):
        return self.special_ranking_

    @property
    def club(self):
        return self.club_

    def setSpecialRanking(self, special_ranking):
        self.special_ranking_ = special_ranking

    def saveData(self):
        self.createOrUpdate()
        data = {}
        data["id"] = self.id
        data["aida_id"] = self.aida_id
        data["first_name"] = self.first_name
        data["last_name"] = self.last_name
        data["gender"] = self.gender
        data["country"] = self.country
        data["special_ranking"] = self.special_ranking
        data["club"] = self.club
        return data
