"""Tests for start list editing (CompyData.updateStartList): the full
round-trip of fetching, editing and saving a start list, including breaks
and removing multiple starts at once (which used broken SQL before)."""
import unittest

import compy_testing


class TestStartListUpdate(compy_testing.CompyDataTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comp_id = cls.createCompetitionWithExcel("Start List Test Open")

    def setUp(self):
        super().setUp()
        self.data = self.newData(self.comp_id)
        blocks = self.data.getBlocks()
        self.day = sorted(blocks.keys())[0]
        self.block = sorted(blocks[self.day].keys())[0]

    def fetchStartList(self):
        return self.data.getStartList(self.day, self.block)

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


if __name__ == '__main__':
    unittest.main()
