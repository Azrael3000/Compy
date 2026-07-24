"""Integration test for concurrent multi-page use.

Simulates what previously broke the app: an admin tab, a clock display
(reloading every few seconds), judge pages and public result pages all
hitting the server at the same time, on two different competitions. The
flask app runs on an embedded threaded HTTP server with its own temporary
database, so the test is self-contained and repeatable.
"""
import threading
import unittest

import requests

import compy_testing

N_ROUNDS = 20


class TestConcurrentPages(compy_testing.CompyServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        session = requests.Session()

        # name the default competition and upload the excel file
        response = session.post(cls.base_url + "/competition",
                                json={"comp_name": "Comp One", "overwrite": False, "comp_id": 1})
        cls.comp_one_id = response.json()["comp_id"]
        with open(compy_testing.TEST_COMPETITION_XLSX, "rb") as excel_file:
            response = session.post(cls.base_url + "/upload_file",
                                    files={"file": ("test_competition.xlsx", excel_file)},
                                    data={"comp_id": str(cls.comp_one_id)})
        if len(response.json().get("athletes", [])) != 30:
            raise AssertionError("test competition upload failed")

        # a second, empty competition
        response = session.post(cls.base_url + "/competition",
                                json={"comp_name": "Comp Two", "overwrite": False, "comp_id": None})
        cls.comp_two_id = response.json()["comp_id"]

        # day and block of comp one for start list requests
        response = session.post(cls.base_url + "/load_comp", json={"comp_id": cls.comp_one_id})
        blocks = response.json()["blocks"]
        cls.first_day = sorted(blocks.keys())[0]
        cls.first_block = sorted(blocks[cls.first_day].keys())[0]

        # a judge with a valid QR hash for comp one
        response = session.post(cls.base_url + "/judge",
                                json={"first_name": "Judy", "last_name": "Judge",
                                      "comp_id": cls.comp_one_id})
        cls.judge_id = response.json()["judges"][0]["id"]
        response = session.get(cls.base_url + "/judge/qr_code",
                               params={"judge_id": cls.judge_id, "comp_id": cls.comp_one_id})
        cls.judge_hash = response.json()["judge_url"].split("hash=")[1]

        # publish comp one for the public results pages
        session.request("UPDATE", cls.base_url + "/publish_results",
                        json={"publish_results": True, "comp_id": cls.comp_one_id})

    # --- one round of requests per simulated page -------------------------

    def adminTabCompOne(self, session, round_index):
        # admin tab on comp 1: athletes list + start list must stay comp 1's
        response = session.get(self.base_url + "/athletes",
                               params={"comp_id": self.comp_one_id})
        assert response.status_code == 200, "athletes -> %d" % response.status_code
        athletes = response.json()["athletes"]
        assert len(athletes) == 30, "comp1 athlete count changed: %d" % len(athletes)
        response = session.get(self.base_url + "/start_list",
                               params={"comp_id": self.comp_one_id,
                                       "day": self.first_day, "block": self.first_block})
        assert response.status_code == 200, "start_list -> %d" % response.status_code
        assert len(response.json()["start_list"]) > 0, "comp1 start list empty"

    def adminTabCompTwo(self, session, round_index):
        # a second admin tab working on the (empty) comp 2 at the same time
        response = session.post(self.base_url + "/load_comp",
                                json={"comp_id": self.comp_two_id})
        assert response.status_code == 200, "load_comp comp2 -> %d" % response.status_code
        assert response.json()["comp_name"] == "Comp Two", \
            "comp2 name is %s" % response.json()["comp_name"]
        assert len(response.json().get("athletes", [])) == 0, "comp2 unexpectedly has athletes"
        response = session.get(self.base_url + "/athletes",
                               params={"comp_id": self.comp_two_id})
        assert len(response.json().get("athletes", [])) == 0, "comp2 athletes leaked from comp1"

    def clockDisplay(self, session, round_index):
        # the clock page reloads itself; it used to switch the global competition
        response = session.get(self.base_url + "/clock/%d/%d/0"
                               % (self.comp_one_id, round_index % 2))
        assert response.status_code == 200, "clock -> %d" % response.status_code
        assert "Comp One" in response.text, "clock does not show comp 1"

    def judgePhone(self, session, round_index):
        response = session.get(self.base_url + "/judge/athletes",
                               params={"comp_id": self.comp_one_id, "judge_id": self.judge_id,
                                       "judge_hash": self.judge_hash, "day": self.first_day,
                                       "block": self.first_block, "lane": "1"})
        assert response.status_code == 200, "judge athletes -> %d" % response.status_code

    def publicResultsPage(self, session, round_index):
        response = session.get(self.base_url + "/results",
                               params={"comp_id": self.comp_one_id})
        assert response.status_code == 200, "results -> %d" % response.status_code
        response = session.get(self.base_url + "/results_list",
                               params={"comp_id": self.comp_one_id, "discipline": 0,
                                       "gender": "Female", "country": 0})
        assert response.status_code == 200, "results_list -> %d" % response.status_code

    def registrationWrites(self, session, round_index):
        # concurrent writes on comp 1
        response = session.post(self.base_url + "/change_registration",
                                json={"comp_id": self.comp_one_id, "id": "1",
                                      "checked": round_index % 2 == 0, "type": "paid"})
        assert response.status_code == 200, "change_registration -> %d" % response.status_code

    # --- the tests --------------------------------------------------------

    def testConcurrentPagesDoNotInterfere(self):
        page_simulations = [
            ("admin1", self.adminTabCompOne),
            ("admin2", self.adminTabCompTwo),
            ("clock", self.clockDisplay),
            ("judge", self.judgePhone),
            ("results", self.publicResultsPage),
            ("registration", self.registrationWrites),
        ]
        failures = []
        stop_event = threading.Event()

        def run_page(page_name, request_round):
            page_session = requests.Session()
            for round_index in range(N_ROUNDS):
                if stop_event.is_set():
                    return
                try:
                    request_round(page_session, round_index)
                except Exception as error:
                    failures.append("%s round %d: %s" % (page_name, round_index, error))
                    stop_event.set()
                    return

        page_threads = [threading.Thread(target=run_page, args=simulation, name=simulation[0])
                        for simulation in page_simulations]
        for page_thread in page_threads:
            page_thread.start()
        for page_thread in page_threads:
            page_thread.join()

        self.assertEqual(failures, [])

        # after the storm: comp 1 must be fully intact
        session = requests.Session()
        response = session.post(self.base_url + "/load_comp", json={"comp_id": self.comp_one_id})
        self.assertEqual(response.json()["comp_name"], "Comp One")
        self.assertEqual(len(response.json()["athletes"]), 30)
        response = session.get(self.base_url + "/start_list",
                               params={"comp_id": self.comp_one_id,
                                       "day": self.first_day, "block": self.first_block})
        self.assertGreater(len(response.json()["start_list"]), 0)

        # deleting comp 2 must not touch comp 1
        response = session.delete(self.base_url + "/competition",
                                  json={"comp_id": self.comp_two_id})
        self.assertEqual(response.status_code, 200)
        response = session.get(self.base_url + "/athletes",
                               params={"comp_id": self.comp_one_id})
        self.assertEqual(len(response.json()["athletes"]), 30)

    def testForgedJudgeHashIsRejected(self):
        response = requests.get(self.base_url + "/judge/athletes",
                                params={"comp_id": self.comp_one_id, "judge_id": self.judge_id,
                                        "judge_hash": "deadbeef", "day": self.first_day,
                                        "block": self.first_block, "lane": "1"})
        self.assertEqual(response.status_code, 404)
        # ...and it must not have switched or broken anything
        response = requests.get(self.base_url + "/athletes",
                                params={"comp_id": self.comp_one_id})
        self.assertEqual(len(response.json()["athletes"]), 30)


if __name__ == '__main__':
    unittest.main()
