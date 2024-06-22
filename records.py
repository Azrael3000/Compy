from enum import Enum

class Federation(Enum):
    AIDA=0
    CMAS=1

class Gender(Enum):
    FEMALE=0
    MALE=1

class CmasClass(Enum):
    SENIOR=0
    MASTER=1

class Records:
    def __init__(self):
        self.cwt_ = 0
        self.cwtb_ = 0
        self.cnf_ = 0
        self.dyn_ = 0
        self.dynb_ = 0
        self.dnf_ = 0
        self.fim_ = 0
        self.sta_ = 0

    def save(self, data):
        data["cwt"] = self.cwt_
        data["cwtb"] = self.cwtb_
        data["cnf"] = self.cnf_
        data["dyn"] = self.dyn_
        data["dynb"] = self.dynb_
        data["dnf"] = self.dnf_
        data["fim"] = self.fim_
        data["sta"] = self.sta_

    def load(self, data):
        self.cwt_ = data["cwt"]
        self.cwtb_ = data["cwtb"]
        self.cnf_ = data["cnf"]
        self.dyn_ = data["dyn"]
        self.dynb_ = data["dynb"]
        self.dnf_ = data["dnf"]
        self.fim_ = data["fim"]
        self.sta_ = data["sta"]

class RecordsDB:
    def __init__(self):
        self.records_ = {}

    def records_aida(self, country=None, gender=Gender.FEMALE):
        if country is None:
            return self.records_[Federation.AIDA]
        elif country in self.records_[Federation.AIDA]:
            return self.records_[Federation.AIDA][country][gender]
        else:
            return None

    def records_cmas(self, country=None, class=CmasClass.SENIOR, gender=Gender.FEMALE):
        if country is None:
            return self.records_[Federation.CMAS]
        elif country in self.records_[Federation.CMAS]:
            return self.records_[Federation.CMAS][country][class][gender]
        else:
            return None

    def set_record(self, fed=Federation.AIDA, country=None, class=None, gender=None, value=0):
        # list of all countries (pandas series)
        all_countries = country_converter.CountryConverter().data["IOC"].dropna()
        return None

    def save(self):
        data = {"aida": {}, "cmas_masters": {}, "cmas_seniors": {}}
        for country in self.records_aida.keys():
            data["aida"][country] = {"female": {}, "male": {}}
            self.records_aida(country, Gender.FEMALE).save(data["aida"][country]["female"])
            self.records_aida(country, Gender.MALE).save(data["aida"][country]["male"])
        for country in self.records_cmas.keys():
            data["cmas"][country] = {"senior": {}, "master": {}}
            data["cmas"][country]["senior"] = {"female": {}, "male": {}}
            self.records_cmas(country, CmasClass.SENIOR, Gender.FEMALE).save(data["cmas"][country]["senior"]["female"])
            self.records_cmas(country, CmasClass.SENIOR, Gender.MALE).save(data["cmas"][country]["senior"]["male"])
            data["cmas"][country]["master"] = {"female": {}, "male": {}}
            self.records_cmas(country, CmasClass.MASTER, Gender.FEMALE).save(data["cmas"][country]["master"]["female"])
            self.records_cmas(country, CmasClass.MASTER, Gender.MALE).save(data["cmas"][country]["master"]["male"])
