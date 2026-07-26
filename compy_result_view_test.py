"""Tests for the public result view (the pages spectators open).

Results must only be visible after the organizer publishes them, and the
published ranking must faithfully reflect what the judges entered: rank
order, points with penalties, red cards shown with zero points and no
rank, DNS shown as DNS. Also checks that the admin-only result JSON stays
behind the login.
"""
import unittest

import requests

import athlete
import compy_testing


class TestPublicResultView(compy_testing.CompyServerTestCase):

    # name -> (AP, RP, penalty, card, remarks)
    RESULTS = {"Bea": (52, "55", 0, "WHITE", "OK"),
               "Ann": (50, "50", 0, "WHITE", "OK"),
               "Yol": (45, "43", 0, "YELLOW", "UNDER AP"),  # +2 under-AP penalty
               "Cat": (60, "60", 0, "RED", "DQBO-SURFACE"),
               "Dot": (40, "", 0, "RED", "DNS")}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.app.app_context():
            import compy_data
            data = compy_data.CompyData(cls.db, cls.app)
            data.changeName("Result View Open", False)
            cls.comp_id = data.id_
            block_id = cls.db.insert(
                "INSERT INTO block (competition_id, day, disciplines) VALUES (?, ?, ?)",
                (cls.comp_id, 20260101, data.disciplineListToInt(["CWT"])))
            ot = 1000
            for first_name, (ap, rp, penalty, card, remarks) in cls.RESULTS.items():
                new_athlete = athlete.Athlete.fromArgs(
                    "id-" + first_name, first_name, "Diver", "F", "AUT", "", cls.db)
                new_athlete.associateWithComp(cls.comp_id)
                s_id = cls.db.insert(
                    '''INSERT INTO start
                       (competition_athlete_id, discipline, lane, OT, AP, block)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (new_athlete.comp_athlete_id_, "CWT", 1, ot, ap, block_id))
                ot += 5
                # enter the results the way the judging interface does
                loaded = compy_data.CompyData(cls.db, cls.app, cls.comp_id)
                ret, _ = loaded.updateResult(s_id, rp, penalty, card, remarks, "")
                if ret != 0:
                    raise AssertionError("result entry failed in test setup")

    def publish(self, published):
        response = self.adminSession().request(
            "UPDATE", self.base_url + "/publish_results",
            json={"publish_results": published, "comp_id": self.comp_id})
        self.assertEqual(response.status_code, 200)

    def resultsList(self, discipline, expect_status=200):
        # discipline 0 is "Overall", 1 is CWT; country 0 is "International"
        response = requests.get(self.base_url + "/results_list",
                                params={"comp_id": self.comp_id,
                                        "discipline": discipline,
                                        "gender": "Female", "country": 0})
        self.assertEqual(response.status_code, expect_status)
        return response

    def testResultsPageRequiresPublishing(self):
        self.publish(False)
        response = requests.get(self.base_url + "/results",
                                params={"comp_id": self.comp_id})
        self.assertEqual(response.status_code, 400)
        self.resultsList(1, expect_status=400)

    def testResultsPageShowsPublishedCompetition(self):
        self.publish(True)
        response = requests.get(self.base_url + "/results",
                                params={"comp_id": self.comp_id})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Result View Open", response.text)

    def testCompetitionListShowsOnlyPublished(self):
        # spectators without a link get a list of published competitions
        self.publish(True)
        response = requests.get(self.base_url + "/results")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Result View Open", response.text)
        self.publish(False)
        response = requests.get(self.base_url + "/results")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Result View Open", response.text)

    def testPublishedRankingMatchesEnteredResults(self):
        self.publish(True)
        results = self.resultsList(1).json()["results"]
        by_name = {r["name"]: r for r in results}

        # ranked athletes come first, in points order
        names_in_order = [r["name"] for r in results]
        self.assertEqual(names_in_order[:3], ["Bea Diver", "Ann Diver", "Yol Diver"])
        self.assertEqual(by_name["Bea Diver"]["rank"], 1)
        self.assertEqual(by_name["Ann Diver"]["rank"], 2)
        self.assertEqual(by_name["Yol Diver"]["rank"], 3)

        # points include the yellow card's under-AP penalty (43 - 2 = 41)
        self.assertEqual(by_name["Bea Diver"]["points"], "55.00")
        self.assertEqual(by_name["Yol Diver"]["points"], "41.00")
        self.assertEqual(float(by_name["Yol Diver"]["penalty"]), 2.)

        # a red card is shown with zero points and no rank
        self.assertEqual(by_name["Cat Diver"]["card"], "RED")
        self.assertEqual(by_name["Cat Diver"]["points"], "0.00")
        self.assertEqual(by_name["Cat Diver"]["rank"], "")
        self.assertEqual(by_name["Cat Diver"]["remarks"], "DQBO-SURFACE")

        # DNS is shown as DNS, not as a performance
        self.assertEqual(by_name["Dot Diver"]["value"], "DNS")
        self.assertEqual(by_name["Dot Diver"]["rank"], "")

    def testOverallRankingExcludesRedCardAndDns(self):
        self.publish(True)
        results = self.resultsList(0).json()["results"]
        names = [r["name"] for r in results]
        self.assertEqual(names, ["Bea Diver", "Ann Diver", "Yol Diver"])
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[0]["value"], "55.00")
        # the overall ranking lists the individual discipline results
        self.assertEqual(results[0]["individual_results"][0]["dis"], "CWT")

    def testResultsListRejectsBadParameters(self):
        self.publish(True)
        response = requests.get(self.base_url + "/results_list",
                                params={"comp_id": self.comp_id, "discipline": 1,
                                        "gender": "X", "country": 0})
        self.assertEqual(response.status_code, 400)
        self.resultsList(99, expect_status=400)

    def testUnpublishingHidesResults(self):
        self.publish(True)
        self.resultsList(1, expect_status=200)
        self.publish(False)
        self.resultsList(1, expect_status=400)

    def testAdminResultJsonRequiresLogin(self):
        # the detailed result view (with judge remarks) is admin only
        params = {"comp_id": self.comp_id, "discipline": "CWT",
                  "gender": "F", "country": "International"}
        response = requests.get(self.base_url + "/result", params=params)
        self.assertEqual(response.status_code, 401)

        response = self.adminSession().get(self.base_url + "/result", params=params)
        self.assertEqual(response.status_code, 200)
        by_name = {r["Name"]: r for r in response.json()["results"]}
        self.assertEqual(by_name["Bea Diver"]["Points"], "55.00")
        self.assertEqual(by_name["Cat Diver"]["Card"], "RED")


if __name__ == '__main__':
    unittest.main()
