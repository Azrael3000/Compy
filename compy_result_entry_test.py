"""Tests for entering results through the judging interface.

Covers the full path a result takes from the judge (or the admin page)
into the database: white cards, yellow cards with manual and automatic
under-AP penalties, red cards with DQ remarks, DNS, and rejection of
invalid input. The data-layer tests check CompyData.updateResult and the
exact values that end up in the start table; the HTTP tests drive the
same flow through the flask endpoints a judge phone uses.
"""
import unittest

import requests

import athlete
import compy_testing
import compy_utilities as u


class ResultEntryCompetition:
    """Mixin that builds a small hand-made competition for result entry.

    One CWT block and one STA block, each athlete has an AP but no result
    yet, so every test can enter a result for its own athlete without
    interfering with the other tests.
    """

    CWT_ATHLETES = {"Wht": 50, "Yel": 50, "Uap": 50, "Wbp": 50, "Red": 60,
                    "Dns": 40, "Inv": 50, "Pen": 50, "Ovr": 50, "Neg": 50,
                    "Ada": 50, "Bel": 50, "Cyd": 55, "Dee": 50, "Eva": 50}
    STA_ATHLETES = {"Sta": 120}

    @classmethod
    def buildCompetition(cls, comp_name):
        import compy_data
        with cls.app.app_context():
            data = compy_data.CompyData(cls.db, cls.app)
            data.changeName(comp_name, False)
            cls.comp_id = data.id_
            cls.cwt_block = cls.db.insert(
                "INSERT INTO block (competition_id, day, disciplines) VALUES (?, ?, ?)",
                (cls.comp_id, 20260101, data.disciplineListToInt(["CWT"])))
            cls.sta_block = cls.db.insert(
                "INSERT INTO block (competition_id, day, disciplines) VALUES (?, ?, ?)",
                (cls.comp_id, 20260102, data.disciplineListToInt(["STA"])))
            cls.start_ids = {}
            ot = 1000
            for first_name, ap in cls.CWT_ATHLETES.items():
                cls.addStart(first_name, "CWT", cls.cwt_block, ap, ot)
                ot += 5
            for first_name, ap in cls.STA_ATHLETES.items():
                cls.addStart(first_name, "STA", cls.sta_block, ap, ot)
                ot += 5

    @classmethod
    def addStart(cls, first_name, discipline, block_id, ap, ot):
        new_athlete = athlete.Athlete.fromArgs(
            "id-" + first_name, first_name, "Diver", "F", "AUT", "", cls.db)
        new_athlete.associateWithComp(cls.comp_id)
        cls.start_ids[first_name] = cls.db.insert(
            '''INSERT INTO start
               (competition_athlete_id, discipline, lane, OT, AP, block)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (new_athlete.comp_athlete_id_, discipline, 1, ot, ap, block_id))


class TestResultEntry(ResultEntryCompetition, compy_testing.CompyDataTestCase):
    """CompyData.updateResult: what exactly lands in the start table."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.buildCompetition("Result Entry Test Open")

    def setUp(self):
        super().setUp()
        self.data = self.newData(self.comp_id)

    def fetchStart(self, first_name):
        row = self.db.execute(
            "SELECT rp, penalty, card, remarks, judge_remarks FROM start WHERE id == ?",
            self.start_ids[first_name])
        self.assertIsNotNone(row)
        return {"rp": row[0][0], "penalty": row[0][1], "card": row[0][2],
                "remarks": row[0][3], "judge_remarks": row[0][4]}

    def testWhiteCardResultIsStored(self):
        ret, _ = self.data.updateResult(
            self.start_ids["Wht"], "52", 0, "WHITE", "OK", "clean dive")
        self.assertEqual(ret, 0)
        start = self.fetchStart("Wht")
        self.assertEqual(float(start["rp"]), 52.)
        self.assertEqual(start["penalty"], 0.)
        self.assertEqual(start["card"], "WHITE")
        self.assertEqual(start["remarks"], "OK")
        self.assertEqual(start["judge_remarks"], "clean dive")

    def testYellowCardManualPenaltyIsStored(self):
        # AP reached, so only the manual penalty (e.g. early start) counts
        ret, _ = self.data.updateResult(
            self.start_ids["Yel"], "50", "2", "YELLOW", "EARLYSTART", "")
        self.assertEqual(ret, 0)
        start = self.fetchStart("Yel")
        self.assertEqual(start["card"], "YELLOW")
        self.assertEqual(start["penalty"], 2.)

    def testYellowCardUnderApPenaltyIsAddedAutomatically(self):
        # AP 50, RP 45: 5 penalty points for the missing meters on top of
        # the manual penalty of 1
        ret, _ = self.data.updateResult(
            self.start_ids["Uap"], "45", 1., "YELLOW", "UNDER AP", "")
        self.assertEqual(ret, 0)
        self.assertEqual(self.fetchStart("Uap")["penalty"], 6.)

    def testWhiteCardGetsNoUnderApPenalty(self):
        ret, _ = self.data.updateResult(
            self.start_ids["Wbp"], "45", 0, "WHITE", "OK", "")
        self.assertEqual(ret, 0)
        self.assertEqual(self.fetchStart("Wbp")["penalty"], 0.)

    def testRedCardDqIsStoredAndScoresZero(self):
        ret, _ = self.data.updateResult(
            self.start_ids["Red"], "60", 0, "RED", "DQBO-SURFACE", "BO at surface")
        self.assertEqual(ret, 0)
        start = self.fetchStart("Red")
        self.assertEqual(start["card"], "RED")
        self.assertEqual(start["remarks"], "DQBO-SURFACE")
        # a disqualified athlete scores zero points and gets no rank
        ret, content = self.data.getResult("CWT", "F", "International")
        self.assertEqual(ret, 0)
        red = [r for r in content["results"] if r["Name"] == "Red Diver"][0]
        self.assertEqual(red["Points"], "0.00")
        self.assertEqual(red["Rank"], "")

    def testDnsIsStored(self):
        ret, _ = self.data.updateResult(
            self.start_ids["Dns"], "", 0, "RED", "DNS", "")
        self.assertEqual(ret, 0)
        start = self.fetchStart("Dns")
        self.assertEqual(start["remarks"], "DNS")
        ret, content = self.data.getResult("CWT", "F", "International")
        dns = [r for r in content["results"] if r["Name"] == "Dns Diver"][0]
        self.assertEqual(dns["Points"], "0.00")
        self.assertEqual(dns["Remarks"], "DNS")
        self.assertEqual(dns["Rank"], "")

    def testInvalidCardIsRejectedWithoutStoring(self):
        ret, _ = self.data.updateResult(
            self.start_ids["Inv"], "50", 0, "PURPLE", "", "")
        self.assertEqual(ret, 1)
        self.assertIsNone(self.fetchStart("Inv")["rp"])
        self.assertIsNone(self.fetchStart("Inv")["card"])

    def testMissingCardIsRejected(self):
        ret, _ = self.data.updateResult(
            self.start_ids["Inv"], "50", 0, None, "", "")
        self.assertEqual(ret, 1)

    def testNonNumericPenaltyBecomesZero(self):
        ret, _ = self.data.updateResult(
            self.start_ids["Pen"], "50", "abc", "WHITE", "OK", "")
        self.assertEqual(ret, 0)
        self.assertEqual(self.fetchStart("Pen")["penalty"], 0.)

    def testNegativeRpBecomesZero(self):
        ret, _ = self.data.updateResult(
            self.start_ids["Neg"], "-5", 0, "WHITE", "OK", "")
        self.assertEqual(ret, 0)
        self.assertEqual(float(self.fetchStart("Neg")["rp"]), 0.)

    def testStaPerformanceIsStoredInSeconds(self):
        ret, _ = self.data.updateResult(
            self.start_ids["Sta"], "2:05", 0, "WHITE", "OK", "")
        self.assertEqual(ret, 0)
        self.assertEqual(float(self.fetchStart("Sta")["rp"]), 125.)
        # ...and is converted back to a time for display
        ret, content = self.data.getAthleteResult(self.start_ids["Sta"])
        self.assertEqual(ret, 0)
        self.assertEqual(content["RP"], "2:05")

    def testUnknownStartIdIsRejected(self):
        ret, _ = self.data.updateResult(999999, "50", 0, "WHITE", "", "")
        self.assertEqual(ret, 1)

    def testResultCanBeCorrected(self):
        # the judge first enters a white card, then corrects it to a red
        self.data.updateResult(
            self.start_ids["Ovr"], "52", 0, "WHITE", "OK", "")
        ret, _ = self.data.updateResult(
            self.start_ids["Ovr"], "52", 0, "RED", "DQLATESTART", "late start")
        self.assertEqual(ret, 0)
        start = self.fetchStart("Ovr")
        self.assertEqual(start["card"], "RED")
        self.assertEqual(start["remarks"], "DQLATESTART")
        self.assertEqual(start["judge_remarks"], "late start")


class TestJudgeEntryHttp(ResultEntryCompetition, compy_testing.CompyServerTestCase):
    """The endpoints a judge phone uses to look up athletes and save results."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.buildCompetition("Judge Entry Open")
        with cls.app.app_context():
            import compy_data
            data = compy_data.CompyData(cls.db, cls.app, cls.comp_id)
            data.addJudge("Judy", "Judge")
            judges = {}
            data.getJudgeData(judges)
            cls.judge_id = judges["judges"][0]["id"]
            qr_data = data.getJudgeQrCode(cls.judge_id, cls.base_url + "/")
            cls.judge_hash = qr_data[3].split("hash=")[1]
        cls.judge_params = {"comp_id": cls.comp_id, "judge_id": cls.judge_id,
                            "judge_hash": cls.judge_hash}

    def putResult(self, first_name, rp, penalty, card, remarks,
                  judge_remarks="", auth=None, extra=None):
        body = {"id": self.start_ids[first_name], "rp": rp, "penalty": penalty,
                "card": card, "remarks": remarks, "judge_remarks": judge_remarks}
        body |= self.judge_params if auth is None else auth
        body |= extra or {}
        return requests.put(self.base_url + "/result", json=body)

    def getAthleteResult(self, first_name):
        response = requests.get(self.base_url + "/judge/athlete/result",
                                params=self.judge_params |
                                       {"s_id": self.start_ids[first_name]})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def testJudgeSeesLaneList(self):
        response = requests.get(self.base_url + "/judge/athletes",
                                params=self.judge_params |
                                       {"day": "2026-01-01",
                                        "block": self.cwt_block, "lane": "1"})
        self.assertEqual(response.status_code, 200)
        lane_list = response.json()["lane_list"]
        self.assertEqual(len(lane_list), len(self.CWT_ATHLETES))
        # sorted by official top time, every entry has a start id to save to
        self.assertEqual(lane_list[0]["Name"], "Wht Diver")
        self.assertTrue(all("s_id" in entry for entry in lane_list))

    def testJudgeEntersWhiteResult(self):
        response = self.putResult("Ada", "52", 0, "WHITE", "OK", "good dive")
        self.assertEqual(response.status_code, 200)
        # without discipline/gender/country the athlete's result is returned
        self.assertEqual(response.json()["Card"], "WHITE")
        stored = self.getAthleteResult("Ada")
        self.assertEqual(stored["RP"], "52.0")
        self.assertEqual(stored["Card"], "WHITE")
        self.assertEqual(stored["Remarks"], "OK")
        self.assertEqual(stored["JudgeRemarks"], "good dive")

    def testJudgeEntersYellowWithUnderApPenalty(self):
        # AP 50, RP 45, manual penalty 1 -> 6 penalty points in total
        response = self.putResult("Bel", "45", 1, "YELLOW", "UNDER AP")
        self.assertEqual(response.status_code, 200)
        stored = self.getAthleteResult("Bel")
        self.assertEqual(stored["Card"], "YELLOW")
        self.assertEqual(float(stored["Penalty"]), 6.)

    def testJudgeEntersRedCardDq(self):
        response = self.putResult("Cyd", "0", 0, "RED", "DQBO-SURFACE", "BO")
        self.assertEqual(response.status_code, 200)
        stored = self.getAthleteResult("Cyd")
        self.assertEqual(stored["Card"], "RED")
        self.assertEqual(stored["Remarks"], "DQBO-SURFACE")

    def testInvalidCardIsRejectedOverHttp(self):
        response = self.putResult("Dee", "50", 0, "GREEN", "OK")
        self.assertEqual(response.status_code, 400)
        # nothing was stored for this athlete
        self.assertIsNone(self.getAthleteResult("Dee")["Card"])

    def testResultEntryWithoutCredentialsIsRejected(self):
        response = self.putResult("Ada", "10", 0, "WHITE", "OK",
                                  auth={"comp_id": self.comp_id})
        self.assertEqual(response.status_code, 401)

    def testJudgePageRendersWithValidHash(self):
        response = requests.get(
            self.base_url + "/judge/%d/%d" % (self.comp_id, self.judge_id),
            params={"hash": self.judge_hash})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Judge Entry Open", response.text)
        self.assertIn("Judy Judge", response.text)

    def testJudgePageWithForgedHashIs404(self):
        response = requests.get(
            self.base_url + "/judge/%d/%d" % (self.comp_id, self.judge_id),
            params={"hash": "deadbeef"})
        self.assertEqual(response.status_code, 404)

    def testAdminEntersResultAndReceivesUpdatedRanking(self):
        session = self.adminSession()
        body = {"comp_id": self.comp_id, "id": self.start_ids["Eva"],
                "rp": "48", "penalty": 0, "card": "WHITE", "remarks": "OK",
                "judge_remarks": "", "discipline": "CWT", "gender": "F",
                "country": "International"}
        response = session.put(self.base_url + "/result", json=body)
        self.assertEqual(response.status_code, 200)
        # with discipline/gender/country the whole ranking comes back
        eva = [r for r in response.json()["results"] if r["Name"] == "Eva Diver"]
        self.assertEqual(len(eva), 1)
        self.assertEqual(eva[0]["Points"], "48.00")


if __name__ == '__main__':
    unittest.main()
