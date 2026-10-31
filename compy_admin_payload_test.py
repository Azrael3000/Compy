"""Response contract of the admin endpoints the page applies as a reset.

The admin page treats some responses as authoritative: applyResponse(data,
reset = True) clears every submenu first and refills it from the response
alone. An endpoint that answers such a request with only part of the submenu
dataset therefore empties the menus it left out, until the competition is
reloaded. That has happened twice - updateStartList and modifyBlock both
hand-rolled two of the five datasets - and neither was catchable by the
frontend types, where every one of those fields is optional.

The start list and block endpoints are covered in compy_startlist_test.py
and the AIDA sync in compy_aida_test.py, next to the other tests of those
areas. This file covers the rest.
"""
import unittest

import compy_testing


class TestResetPayloads(compy_testing.SubmenuPayloadAssertions,
                        compy_testing.CompyServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comp_id = cls.createCompetitionWithExcel("Reset Payload Open")
        cls.session = cls.adminSession()

    def testLoadCompReturnsEverySubmenuDataset(self):
        response = self.session.post(self.base_url + "/load_comp",
                                     json={"comp_id": self.comp_id})

        self.assertEqual(response.status_code, 200)
        self.assertCarriesSubmenuData(response.json())

    def testChangeSpecialRankingNameReturnsEverySubmenuDataset(self):
        response = self.session.post(self.base_url + "/change_special_ranking_name",
                                     json={"comp_id": self.comp_id,
                                           "special_ranking_name": "Rookie"})

        self.assertEqual(response.status_code, 200)
        self.assertCarriesSubmenuData(response.json())

    def testUploadFileReturnsEverySubmenuDataset(self):
        """The excel import replaces the whole competition, so its response is
        the one the page most needs to be complete."""
        with open(compy_testing.TEST_COMPETITION_XLSX, "rb") as excel_file:
            response = self.session.post(
                self.base_url + "/upload_file",
                files={"file": ("test_competition.xlsx", excel_file)},
                data={"comp_id": str(self.comp_id)})

        self.assertEqual(response.status_code, 200)
        self.assertCarriesSubmenuData(response.json())


if __name__ == '__main__':
    unittest.main()
