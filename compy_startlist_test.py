"""Tests for start list editing: the full round-trip of fetching, editing
and saving a start list, including breaks and removing multiple starts at
once (which used broken SQL before), plus the payload the PUT /start_list
endpoint sends back to the admin page."""
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


class TestStartListEndpointPayload(compy_testing.SubmenuPayloadAssertions,
                                   compy_testing.CompyServerTestCase):
    """A successful PUT /start_list must carry the whole submenu dataset.

    The admin page treats a start list save as a reset: applyResponse()
    clears every submenu and repopulates it from the response alone. A
    partial payload therefore does not leave the old menus in place, it
    empties them - which is what used to happen to the Results tab, whose
    menus are built from 'disciplines' and 'result_countries'.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comp_id = cls.createCompetitionWithExcel("Start List Endpoint Open")
        cls.session = cls.adminSession()
        response = cls.session.post(cls.base_url + "/load_comp",
                                    json={"comp_id": cls.comp_id})
        blocks = response.json()["blocks"]
        cls.day = sorted(blocks.keys())[0]
        cls.block = sorted(blocks[cls.day].keys())[0]

    def testSaveReturnsEverySubmenuDataset(self):
        response = self.session.get(self.base_url + "/start_list",
                                    params={"comp_id": self.comp_id,
                                            "day": self.day, "block": self.block})
        start_list = response.json()["start_list"]

        response = self.session.put(self.base_url + "/start_list",
                                    json={"comp_id": self.comp_id,
                                          "day": self.day, "block": self.block,
                                          "to_remove": [], "startlist": start_list})

        self.assertEqual(response.status_code, 200)
        self.assertCarriesSubmenuData(response.json())


class TestBlockEndpointPayload(compy_testing.SubmenuPayloadAssertions,
                               compy_testing.CompyServerTestCase):
    """Adding, editing and removing a block must carry the whole submenu set.

    Same contract as PUT /start_list above, and the same reason: the admin
    page applies these three responses as a reset, so a payload that omits
    'disciplines' or 'result_countries' empties the Results menus rather
    than leaving them alone. It matters more here than for a start list
    save - adding a block with a new discipline is exactly when the
    discipline list changes.
    """

    NEW_DAY = "2031-04-05"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comp_id = cls.createCompetitionWithExcel("Block Endpoint Open")
        cls.session = cls.adminSession()
        cls.session.post(cls.base_url + "/load_comp", json={"comp_id": cls.comp_id})

    def setUp(self):
        super().setUp()
        # a block on a day of its own, so its id is unambiguous and removing
        # it cannot disturb the blocks the excel import created
        response = self.session.post(self.base_url + "/block",
                                     json={"comp_id": self.comp_id, "day": self.NEW_DAY,
                                           "dis": ["CWT"], "block": "-1"})
        self.assertEqual(response.status_code, 200)
        self.added = response.json()
        self.block = sorted(self.added["blocks"][self.NEW_DAY].keys())[0]

    def tearDown(self):
        self.session.delete(self.base_url + "/block",
                            json={"comp_id": self.comp_id, "block": self.block})
        super().tearDown()

    def testAddReturnsEverySubmenuDataset(self):
        self.assertCarriesSubmenuData(self.added)

    def testEditReturnsEverySubmenuDataset(self):
        response = self.session.patch(self.base_url + "/block",
                                      json={"comp_id": self.comp_id, "day": self.NEW_DAY,
                                            "dis": ["DYN"], "block": self.block})

        self.assertEqual(response.status_code, 200)
        self.assertCarriesSubmenuData(response.json())

    def testRemoveReturnsEverySubmenuDataset(self):
        response = self.session.delete(self.base_url + "/block",
                                       json={"comp_id": self.comp_id, "block": self.block})

        self.assertEqual(response.status_code, 200)
        self.assertCarriesSubmenuData(response.json())


if __name__ == '__main__':
    unittest.main()
