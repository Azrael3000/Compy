"""Tests for start list editing (CompyData.updateStartList): the full
round-trip of fetching, editing and saving a start list, including breaks,
removing multiple starts at once (which used broken SQL before) and the
optional PB column, which a save used to turn into 0 or 99:99."""
import unittest

from compy_constants import DEPTH_DISCIPLINES

import compy_testing


class TestStartListUpdate(compy_testing.CompyDataTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comp_id = cls.createCompetitionWithExcel("Start List Test Open")

    def setUp(self):
        super().setUp()
        self.data = self.newData(self.comp_id)
        # the class shares one database: start every test from the state the
        # excel import leaves behind (no PBs), whatever an earlier test saved
        self.db.execute(
            '''UPDATE start SET PB=NULL WHERE competition_athlete_id IN
               (SELECT id FROM competition_athlete WHERE competition_id == ?)''',
            self.comp_id)
        blocks = self.data.getBlocks()
        self.day = sorted(blocks.keys())[0]
        self.block = sorted(blocks[self.day].keys())[0]

    def fetchStartList(self):
        return self.data.getStartList(self.day, self.block)

    def allBlocks(self):
        blocks = self.data.getBlocks()
        return [(day, block) for day in sorted(blocks) for block in sorted(blocks[day])]

    def storedPbs(self, day, block):
        rows = self.db.execute(
            '''SELECT s.PB FROM start s
               INNER JOIN competition_athlete ca ON ca.id == s.competition_athlete_id
               INNER JOIN block b ON b.id == s.block
               WHERE ca.competition_id == ? AND s.block == ? AND b.day == ?''',
            (self.comp_id, block, day.replace("-", "")))
        return [row[0] for row in rows] if rows is not None else []

    def saveStartList(self, start_list, to_remove = ()):
        return self.data.updateStartList(self.day, self.block, list(to_remove), start_list)

    def makeBreak(self, duration):
        return {"Name": "Break", "AP": duration, "PB": "", "Nationality": "",
                "Warmup": "", "OT": "", "Lane": "", "Discipline": "", "Id": -1,
                "Dive Time": ""}

    def testRoundTripWithoutChangesKeepsList(self):
        start_list = self.fetchStartList()

        self.assertEqual(self.saveStartList(start_list), 0)

        start_list_after = self.fetchStartList()
        self.assertEqual([entry["Name"] for entry in start_list_after],
                         [entry["Name"] for entry in start_list])
        self.assertEqual([entry["OT"] for entry in start_list_after],
                         [entry["OT"] for entry in start_list])

    def testRemoveMultipleStartsAtOnce(self):
        start_list = self.fetchStartList()
        removed_ids = [start_list[0]["Id"], start_list[1]["Id"]]
        kept_list = start_list[2:]

        self.assertEqual(self.saveStartList(kept_list, to_remove=removed_ids), 0)

        start_list_after = self.fetchStartList()
        self.assertEqual(len(start_list_after), len(start_list) - 2)
        ids_after = {entry["Id"] for entry in start_list_after}
        for removed_id in removed_ids:
            self.assertNotIn(removed_id, ids_after)

    def testAddAndRemoveBreak(self):
        start_list = self.fetchStartList()
        start_list.insert(1, self.makeBreak("0:10"))

        self.assertEqual(self.saveStartList(start_list), 0)

        start_list_with_break = self.fetchStartList()
        self.assertEqual(start_list_with_break[1]["Name"], "Break")
        self.assertEqual(start_list_with_break[1]["AP"], "0:10")

        del start_list_with_break[1]
        self.assertEqual(self.saveStartList(start_list_with_break), 0)
        breaks_after = [entry for entry in self.fetchStartList() if entry["Name"] == "Break"]
        self.assertEqual(breaks_after, [])

    def testChangeOfficialTop(self):
        start_list = self.fetchStartList()
        changed_id = start_list[-1]["Id"]
        start_list[-1]["OT"] = "23:45"

        self.assertEqual(self.saveStartList(start_list), 0)

        changed_entry = [entry for entry in self.fetchStartList()
                         if entry["Id"] == changed_id][0]
        self.assertEqual(changed_entry["OT"], "23:45")

    def testInvalidDayIsRejected(self):
        self.assertEqual(self.data.updateStartList("not-a-day", self.block, [], []), -1)

    # ---- PB handling: the excel import has no PB column, so after an
    # ---- import every PB is empty and a save must keep it that way

    def testExcelImportLeavesPbEmpty(self):
        # a fresh import: the aida excel has no PB column at all
        self.data.refresh()
        for day, block in self.allBlocks():
            self.assertTrue(all(pb is None for pb in self.storedPbs(day, block)),
                            "day %s block %s" % (day, block))
            for entry in self.data.getStartList(day, block):
                self.assertEqual(entry["PB"], "")

    def testSaveKeepsEmptyPbEmptyInEveryDiscipline(self):
        # the editor sends the whole list back, unchanged rows included:
        # saving one edit must not invent a PB for the other rows
        # (STA used to become 99:99 = 6039 s, every other discipline 0)
        for day, block in self.allBlocks():
            start_list = self.data.getStartList(day, block)
            start_list[0]["OT"] = "23:00"
            self.assertEqual(self.data.updateStartList(day, block, [], start_list), 0)

            self.assertTrue(all(pb is None for pb in self.storedPbs(day, block)),
                            "day %s block %s: %s" % (day, block, self.storedPbs(day, block)))
            for entry in self.data.getStartList(day, block):
                self.assertEqual(entry["PB"], "", entry["Discipline"])

    def testSaveKeepsFilledPbs(self):
        for day, block in self.allBlocks():
            start_list = self.data.getStartList(day, block)
            for entry in start_list:
                entry["PB"] = "4:35" if entry["Discipline"] == "STA" else "57"
            self.assertEqual(self.data.updateStartList(day, block, [], start_list), 0)

            for entry in self.data.getStartList(day, block):
                expected = "4:35" if entry["Discipline"] == "STA" else "57.0"
                self.assertEqual(entry["PB"], expected, entry["Discipline"])
            start_list_again = self.data.getStartList(day, block)
            self.assertEqual(self.data.updateStartList(day, block, [], start_list_again), 0)
            self.assertEqual([e["PB"] for e in self.data.getStartList(day, block)],
                             [e["PB"] for e in start_list_again])

    def testPbCanBeClearedAgain(self):
        start_list = self.fetchStartList()
        start_list[0]["PB"] = "4:35" if start_list[0]["Discipline"] == "STA" else "57"
        self.assertEqual(self.saveStartList(start_list), 0)
        self.assertNotEqual(self.fetchStartList()[0]["PB"], "")

        start_list = self.fetchStartList()
        start_list[0]["PB"] = ""
        self.assertEqual(self.saveStartList(start_list), 0)
        self.assertEqual(self.fetchStartList()[0]["PB"], "")

    def testUnparsablePbIsStoredAsEmpty(self):
        # garbage from the client must not end up as 99:99 / 6039 s either
        start_list = self.fetchStartList()
        sta = [e for e in start_list if e["Discipline"] == "STA"]
        if len(sta) == 0:
            self.skipTest("first block has no STA start")
        sta[0]["PB"] = "not a time"
        self.assertEqual(self.saveStartList(start_list), 0)
        changed = [e for e in self.fetchStartList() if e["Id"] == sta[0]["Id"]][0]
        self.assertEqual(changed["PB"], "")

    def testMissingPbKeyIsTreatedAsEmpty(self):
        # older clients may not send the key at all
        start_list = self.fetchStartList()
        for entry in start_list:
            entry.pop("PB", None)
        self.assertEqual(self.saveStartList(start_list), 0)
        self.assertTrue(all(pb is None for pb in self.storedPbs(self.day, self.block)))

    def testNewStartWithEmptyPb(self):
        athlete = self.db.execute(
            '''SELECT a.id, a.first_name, a.last_name, a.country FROM athlete a
               INNER JOIN competition_athlete ca ON ca.athlete_id == a.id
               WHERE ca.competition_id == ? AND a.id NOT IN (
                   SELECT ca2.athlete_id FROM start s
                   INNER JOIN competition_athlete ca2 ON ca2.id == s.competition_athlete_id
                   WHERE s.block == ?)''', (self.comp_id, self.block))[0]
        start_list = self.fetchStartList()
        discipline = start_list[0]["Discipline"]
        start_list.append({"Name": athlete[1] + " " + athlete[2], "Nationality": athlete[3],
                           "AP": "4:00" if discipline == "STA" else "50", "PB": "",
                           "Warmup": "", "OT": "23:30", "Lane": "1", "Id": -athlete[0],
                           "Discipline": discipline, "Dive Time": "0:00"})
        self.assertEqual(self.saveStartList(start_list), 0)
        added = [e for e in self.fetchStartList() if e["Name"] == athlete[1] + " " + athlete[2]]
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]["PB"], "")


if __name__ == '__main__':
    unittest.main()
