"""Tests for result ranking (CompyData.getResult): ordering by points,
ties, red cards, DNS handling and the Overall ranking. Uses a small
hand-built competition so every expected value is known exactly."""
import unittest

import athlete
import compy_testing
import compy_utilities as u


class TestSingleDisciplineRanking(compy_testing.CompyDataTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.app.app_context():
            data = cls.newCompetition()
            cls.comp_id = data.id_
            block_id = cls.db.insert(
                "INSERT INTO block (competition_id, day, disciplines) VALUES (?, ?, ?)",
                (cls.comp_id, 20260101, data.disciplineListToInt(["CWT"])))

            # name, AP, RP, card, penalty, remarks
            cls.addStart(block_id, "Bea", 52, 55, "WHITE", 0., "")
            cls.addStart(block_id, "Ann", 50, 50, "WHITE", 0., "")
            cls.addStart(block_id, "Eve", 50, 50, "WHITE", 0., "")   # tie with Ann
            cls.addStart(block_id, "Cat", 60, 60, "RED", 0., "")
            cls.addStart(block_id, "Dot", 40, None, None, None, "DNS")
            cls.addStart(block_id, "Yol", 45, 43, "YELLOW", 2., "")

    @classmethod
    def newCompetition(cls):
        import compy_data
        data = compy_data.CompyData(cls.db, cls.app)
        data.changeName("Ranking Test Open", False)
        return data

    lane_counter = 0

    @classmethod
    def addStart(cls, block_id, first_name, ap, rp, card, penalty, remarks):
        new_athlete = athlete.Athlete.fromArgs(
            "id-" + first_name, first_name, "Diver", "F", "AUT", "", cls.db)
        new_athlete.associateWithComp(cls.comp_id)
        cls.lane_counter += 1
        cls.db.insert(
            '''INSERT INTO start
               (competition_athlete_id, discipline, lane, OT, AP, rp, card, penalty, remarks, block)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (new_athlete.comp_athlete_id_, "CWT", cls.lane_counter,
             u.convTime("10:00"), ap, rp, card, penalty, remarks, block_id))

    def setUp(self):
        super().setUp()
        self.data = self.newData(self.comp_id)
        ret, content = self.data.getResult("CWT", "F", "International")
        self.assertEqual(ret, 0)
        self.results = content['results']
        self.by_name = {result['Name']: result for result in self.results}

    def testOrderedByPointsDescending(self):
        names_in_order = [result['Name'] for result in self.results]
        self.assertEqual(names_in_order[:4],
                         ["Bea Diver", "Ann Diver", "Eve Diver", "Yol Diver"])

    def testPointsComputedFromRpAndPenalty(self):
        self.assertEqual(self.by_name["Bea Diver"]["Points"], "55.00")
        self.assertEqual(self.by_name["Yol Diver"]["Points"], "41.00")

    def testWinnerHasRankOne(self):
        self.assertEqual(self.by_name["Bea Diver"]["Rank"], 1)

    def testTieWithSameApSharesRank(self):
        self.assertEqual(self.by_name["Ann Diver"]["Rank"], 2)
        self.assertEqual(self.by_name["Eve Diver"]["Rank"], "")

    def testRedCardScoresZeroAndGetsNoRank(self):
        self.assertEqual(self.by_name["Cat Diver"]["Points"], "0.00")
        self.assertEqual(self.by_name["Cat Diver"]["Rank"], "")

    def testDnsScoresZeroAndKeepsDnsRemark(self):
        self.assertEqual(self.by_name["Dot Diver"]["Points"], "0.00")
        self.assertEqual(self.by_name["Dot Diver"]["Rank"], "")
        self.assertEqual(self.by_name["Dot Diver"]["Remarks"], "DNS")

    def testNoResultsForOtherGender(self):
        ret, content = self.data.getResult("CWT", "M", "International")
        self.assertEqual(ret, 0)
        self.assertEqual(content['results'], [])

    def testOverallExcludesZeroPointAthletes(self):
        ret, content = self.data.getResult("Overall", "F", "International")
        self.assertEqual(ret, 0)
        overall_names = [result['Name'] for result in content['results']]
        self.assertEqual(overall_names,
                         ["Bea Diver", "Ann Diver", "Eve Diver", "Yol Diver"])
        self.assertEqual(content['results'][0]['Rank'], 1)


if __name__ == '__main__':
    unittest.main()
