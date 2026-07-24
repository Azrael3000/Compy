"""Tests for the excel import (CompyData.refresh): athletes, days, blocks
and starts must all be created from the AIDA-style competition file, and a
re-import must not lose data or registration flags."""
import unittest

import compy_testing
import compy_utilities as u


class TestExcelImport(compy_testing.CompyDataTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comp_id = cls.createCompetitionWithExcel("Import Test Open")

    def setUp(self):
        super().setUp()
        self.data = self.newData(self.comp_id)

    def countStarts(self):
        rows = self.db.execute(
            '''SELECT COUNT(*) FROM start s
               INNER JOIN competition_athlete ca ON s.competition_athlete_id == ca.id
               WHERE ca.competition_id == ?''',
            self.comp_id)
        return rows[0][0]

    def testAllAthletesImported(self):
        self.assertEqual(self.data.number_of_athletes, 30)

    def testCompetitionDatesParsed(self):
        self.assertIsNotNone(self.data.start_date)
        self.assertIsNotNone(self.data.end_date)

    def testThreeCompetitionDays(self):
        days = list(self.data.getDays())
        self.assertEqual(len(days), 3)

    def testEveryDayHasABlockWithDisciplines(self):
        blocks = self.data.getBlocks()
        self.assertEqual(len(blocks), 3)
        for day, day_blocks in blocks.items():
            self.assertGreater(len(day_blocks), 0)
            for block_id, block in day_blocks.items():
                self.assertNotEqual(block['dis_s'], "")

    def testDisciplinesFromFile(self):
        disciplines = self.data.getDisciplines()
        # aida competitions additionally offer the Overall ranking
        self.assertIn("Overall", disciplines)
        for expected_discipline in ["STA", "DYN", "DYNB", "DNF", "CWT"]:
            self.assertIn(expected_discipline, disciplines)

    def testStartsImported(self):
        self.assertGreater(self.countStarts(), 0)

    def testDnsEntriesImported(self):
        dns_rows = self.db.execute(
            '''SELECT COUNT(*) FROM start s
               INNER JOIN competition_athlete ca ON s.competition_athlete_id == ca.id
               WHERE ca.competition_id == ? AND s.remarks == "DNS"''',
            self.comp_id)
        self.assertGreater(dns_rows[0][0], 0)

    def testReimportKeepsDataAndRegistrationFlags(self):
        athlete_rows = self.db.execute(
            '''SELECT athlete_id FROM competition_athlete
               WHERE competition_id == ? ORDER BY athlete_id''',
            self.comp_id)
        athlete_id = athlete_rows[0][0]
        self.assertEqual(self.data.setRegistration(athlete_id, True, "specialranking"), 0)
        starts_before = self.countStarts()

        self.data.refresh()

        self.assertEqual(self.data.number_of_athletes, 30)
        self.assertEqual(self.countStarts(), starts_before)
        special_ranking = self.db.execute(
            '''SELECT special_ranking FROM competition_athlete
               WHERE competition_id == ? AND athlete_id == ?''',
            (self.comp_id, athlete_id))
        self.assertTrue(special_ranking[0][0])

    def testMissingFileDoesNotWipeData(self):
        self.data.comp_file_ = "/nonexistent/path.xlsx"
        starts_before = self.countStarts()

        self.data.refresh()

        self.assertEqual(self.data.number_of_athletes, 30)
        self.assertEqual(self.countStarts(), starts_before)


if __name__ == '__main__':
    unittest.main()
