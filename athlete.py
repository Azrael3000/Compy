
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

    def __init__(self, aida_id, first_name, last_name, gender, country, club, db, a_id = None):
        self.id_ = a_id
        self.comp_athlete_id_ = None
        self.aida_id_ = str(aida_id)
        self.first_name_ = first_name
        self.last_name_ = last_name
        self.gender_ = gender
        self.country_ = country
        self.club_ = club
        self.db_ = db
        self.createOrUpdate()

    @classmethod
    def fromDb(cls, a_id, db):
        load_data = db.execute('''SELECT aida_id, first_name, last_name, gender, country, club
                                  FROM athlete WHERE id=?''',
                               a_id)
        a_data = load_data[0]
        return cls(a_data[0], a_data[1], a_data[2], a_data[3], a_data[4], a_data[5], db, a_id)

    @classmethod
    def fromArgs(cls, id, first_name, last_name, gender, country, club, db):
        return cls(id, first_name, last_name, gender, country, club, db)

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
                                (first_name, last_name, aida_id, gender, country, club)
                                VALUES(?, ?, ?, ?, ?, ?)''',
                             (self.first_name, self.last_name, self.aida_id, self.gender, self.country, self.club))
            self.id_ = self.db_.last_index
        else:
            self.db_.execute('''UPDATE athlete
                                SET first_name=?, last_name=?, aida_id=?, gender=?, country=?,
                                club=? WHERE id=?''',
                             (self.first_name, self.last_name, self.aida_id, self.gender, self.country,
                              self.club, self.id_))

    def associateWithComp(self, comp_id, special_ranking = False):
        if self.comp_athlete_id_ is None:
            if self.id_ is None:
                logging.error("Cannot assign athlete to competition that has not db id")
                return
            db_id = self.db_.execute('''SELECT id FROM competition_athlete
                                        WHERE competition_id=? AND athlete_id=?''',
                                     (comp_id, self.id))
            if db_id is not None:
                self.comp_athlete_id_ = db_id[0][0]

        # if the comp_athlete_id is set, we don't need to do anything
        if self.comp_athlete_id_ is None:
            self.db_.execute(
                '''INSERT INTO competition_athlete
                   (competition_id, athlete_id, special_ranking) VALUES(?, ?, ?)''',
                (comp_id, self.id_, special_ranking))
            self.comp_athlete_id_ = self.db_.last_index

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
        has_sr = self.db_.execute("SELECT special_ranking FROM competition_athlete WHERE id==?",
                                  self.comp_athlete_id_)
        return has_sr is not None and has_sr[0][0]

    @property
    def club(self):
        return self.club_

    def saveData(self):
        self.createOrUpdate()
        data = {}
        data["id"] = self.id
        data["aida_id"] = self.aida_id
        data["first_name"] = self.first_name
        data["last_name"] = self.last_name
        data["gender"] = self.gender
        data["country"] = self.country
        data["club"] = self.club
        return data
