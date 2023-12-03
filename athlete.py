
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

    def __init__(self, id, last_name, first_name, gender, country):
        self.id_ = id
        self.last_name_ = last_name
        self.first_name_ = first_name
        self.gender_ = gender
        self.country_ = country
        self.newcomer_ = False

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

    def setNewcomer(self, newcomer):
        self.newcomer_ = newcomer
