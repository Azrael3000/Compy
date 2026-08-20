"""Tests for the read-only AIDA International API integration.

Covers the API client (compy_aida_api.py) with a fake requests session and
the sync logic (CompyData.syncFromAida) with a fake client, so no test ever
talks to the real AIDA server. The sync tests verify the safety guarantees
the integration promises: atomic apply, upsert instead of duplicate, never
delete local data, never touch locally entered OTs, clubs or results.
"""
import unittest
import unittest.mock

import requests

import compy_aida_api
import compy_data
import compy_utilities as u
from compy_testing import CompyDataTestCase, CompyServerTestCase

EVENT_ID = 4885
API_KEY = "test-key-not-a-real-one"

ANNA = "11111111-1111-1111-1111-111111111111"
LUKAS = "22222222-2222-2222-2222-222222222222"
MARIE = "33333333-3333-3333-3333-333333333333"


def dayEntry(day_id, name, date, index, rest=False):
    return {"id": day_id, "name": name, "date": date, "dayIndex": index,
            "isRestDay": rest}


def prereg(athlete_id, first, last, gender, alpha3, nationality,
           approved=True, paid=True, medical=True):
    return {
        "id": 1, "athleteId": athlete_id, "firstName": first,
        "lastName": last, "diverGender": gender,
        "diverNationality": nationality,
        "diverNationalityAbrv": alpha3[:2],
        "diverNationalityAbrvAlpha3": alpha3,
        "selfRegistered": True, "eventRole": None,
        "status": {"id": 1, "code": "APP" if approved else "PEN",
                   "label": "Approved" if approved else "Pending"},
        "tags": None, "tshirtSize": "M",
        "documents": {"medicalCertificate": medical, "competitionForm": True,
                      "imageRights": True, "passport": True,
                      "liabilityRelease": True, "paymentReceipt": paid},
    }


def startEntry(start_id, first, last, gender, alpha3, heat, lane, dis, ap,
               measurement="meters"):
    return {"startId": start_id, "diverFirstName": first,
            "diverLastName": last, "diverGender": gender,
            "diverNationalityAbrv": alpha3[:2], "heat": heat, "lane": lane,
            "disciplineAbrv": dis, "announcedPerformance": ap,
            "reportedPerformance": None, "performanceMeasurement": measurement,
            "judgeStatus": None, "diveTime": None, "descendTime": None}


class FakeAidaClient:
    """Stands in for AidaApiClient; serves canned payloads."""

    def __init__(self, days, preregistrations, start_lists, profiles=None):
        self.days_ = days
        self.preregistrations_ = preregistrations
        self.start_lists_ = start_lists  # day_id -> list of start entries
        self.profiles_ = profiles or {}  # athlete_id -> personalBests list
        self.profile_calls = []

    def getAthleteProfile(self, event_id, athlete_id):
        self.profile_calls.append(athlete_id)
        return {"profile": {"personalBests":
                            self.profiles_.get(athlete_id, [])}}

    def getDays(self, event_id):
        return {"eventId": event_id, "eventName": "Fake Open",
                "days": self.days_}

    def getPreregistrations(self, event_id):
        return {"eventId": event_id, "eventName": "Fake Open",
                "count": len(self.preregistrations_),
                "preregistrations": self.preregistrations_}

    def getStartList(self, event_id, day_id):
        return {"name": "Day", "date": "", "published": True,
                "startList": self.start_lists_.get(day_id, [])}


class FailingAidaClient(FakeAidaClient):
    """Delivers days and registrations, then fails on the start list."""

    def getStartList(self, event_id, day_id):
        raise compy_aida_api.AidaApiError("simulated network loss")


def defaultFakeClient():
    days = [dayEntry(101, "Day 1", "2026-09-01", 1),
            dayEntry(102, "Day 2", "2026-09-02", 2)]
    preregistrations = [
        prereg(ANNA, "Anna", "Berger", "F", "AUT", "Austria"),
        prereg(LUKAS, "Lukas", "Steiner", "M", "AUT", "Austria",
               approved=False, paid=False, medical=False),
        # ISO alpha-3 DEU must become IOC GER
        prereg(MARIE, "Marie", "Schmidt", "F", "DEU", "Germany"),
    ]
    start_lists = {
        101: [startEntry(9001, "Anna", "Berger", "F", "AUT", 1, 1, "CWT", 52),
              startEntry(9002, "Lukas", "Steiner", "M", "AUT", 1, 2, "CWT", 61)],
        102: [startEntry(9003, "Anna", "Berger", "F", "AUT", 1, 1, "STA",
                         240, "seconds")],
    }
    return FakeAidaClient(days, preregistrations, start_lists)


class AidaSyncTest(CompyDataTestCase):

    def newComp(self, name):
        data = self.newData()
        data.changeName(name, False)
        ret, content = data.setAidaSettings(EVENT_ID, API_KEY)
        self.assertEqual(ret, 0)
        return data

    def athleteRows(self, data):
        return data.db_.execute(
            '''SELECT a.aida_id, a.first_name, a.gender, a.country, a.club,
                      ca.registered, ca.paid, ca.medical_checked
               FROM athlete a INNER JOIN competition_athlete ca
               ON ca.athlete_id == a.id WHERE ca.competition_id == ?''',
            data.id_)

    def startRows(self, data):
        return data.db_.execute(
            '''SELECT s.aida_start_id, s.discipline, s.lane, s.AP, s.OT,
                      s.RP, b.day, s.PB
               FROM start s
               INNER JOIN competition_athlete ca
               ON ca.id == s.competition_athlete_id
               INNER JOIN block b ON b.id == s.block
               WHERE ca.competition_id == ? ORDER BY s.aida_start_id''',
            data.id_)

    def test_sync_requires_configuration(self):
        data = self.newData()
        data.changeName("Aida unconfigured", False)
        ret, content = data.syncFromAida(client=defaultFakeClient())
        self.assertEqual(ret, 1)
        self.assertIn("event id", content["error_msg"])

    def test_settings_survive_save_and_load(self):
        data = self.newComp("Aida settings comp")
        reloaded = self.newData(data.id_)
        self.assertEqual(reloaded.aida_event_id, EVENT_ID)
        self.assertTrue(reloaded.has_aida_api_key)
        # empty key keeps the stored key, new event id is applied
        ret, content = reloaded.setAidaSettings(9999, "")
        self.assertEqual(ret, 0)
        reloaded = self.newData(data.id_)
        self.assertEqual(reloaded.aida_event_id, 9999)
        self.assertTrue(reloaded.has_aida_api_key)

    def test_initial_sync_seeds_athletes_blocks_and_starts(self):
        data = self.newComp("Aida seed comp")
        ret, report = data.syncFromAida(client=defaultFakeClient())
        self.assertEqual(ret, 0)
        self.assertEqual(report["athletes_added"], 3)
        self.assertEqual(report["starts_added"], 3)
        self.assertEqual(report["days_synced"], 2)

        athletes = {a[0]: a for a in self.athleteRows(data)}
        self.assertEqual(len(athletes), 3)
        # registration flags from AIDA status/documents
        self.assertTrue(athletes[ANNA][5])   # registered (APP)
        self.assertTrue(athletes[ANNA][6])   # paid
        self.assertFalse(athletes[LUKAS][5]) # pending -> not registered
        self.assertFalse(athletes[LUKAS][6]) # no payment receipt
        # ISO alpha-3 converted to IOC
        self.assertEqual(athletes[MARIE][3], "GER")

        starts = self.startRows(data)
        self.assertEqual(len(starts), 3)
        sta = [s for s in starts if s[1] == "STA"][0]
        self.assertEqual(sta[3], 240)  # STA AP stays in seconds
        # dates from the day list
        self.assertEqual(data.start_date, "2026-09-01")
        self.assertEqual(data.end_date, "2026-09-02")

    def test_resync_upserts_instead_of_duplicating(self):
        data = self.newComp("Aida resync comp")
        client = defaultFakeClient()
        self.assertEqual(data.syncFromAida(client=client)[0], 0)

        # local edits that a re-sync must preserve
        data.db_.execute("UPDATE athlete SET club='Vienna Apnea' WHERE aida_id=?",
                         ANNA)
        data.db_.execute("UPDATE start SET OT=930, RP=50.0, card='WHITE' "
                         "WHERE aida_start_id=9001")

        # AIDA side changes: new AP for Anna, late registration with a start
        client.start_lists_[101][0]["announcedPerformance"] = 55
        client.preregistrations_.append(
            prereg("44444444-4444-4444-4444-444444444444", "Nina", "Novak",
                   "F", "CZE", "Czech Republic"))
        client.start_lists_[101].append(
            startEntry(9004, "Nina", "Novak", "F", "CZE", 1, 3, "CWT", 40))

        ret, report = data.syncFromAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["athletes_added"], 1)
        self.assertEqual(report["athletes_updated"], 3)
        self.assertEqual(report["starts_added"], 1)
        self.assertEqual(report["starts_updated"], 3)

        athletes = {a[0]: a for a in self.athleteRows(data)}
        self.assertEqual(len(athletes), 4)
        self.assertEqual(athletes[ANNA][4], "Vienna Apnea")  # club kept

        starts = {s[0]: s for s in self.startRows(data)}
        self.assertEqual(len(starts), 4)
        self.assertEqual(starts[9001][3], 55)         # AP updated from AIDA
        self.assertEqual(str(starts[9001][4]), "930") # OT kept
        self.assertEqual(starts[9001][5], 50.0)    # result kept

    def test_sync_fills_empty_pbs_from_profiles(self):
        client = defaultFakeClient()
        client.profiles_ = {
            ANNA: [{"disciplineAbrv": "CWT", "reportedPerformance": "55"},
                   {"disciplineAbrv": "STA", "reportedPerformance": "300"}],
        }
        data = self.newComp("Aida pb fill comp")
        ret, report = data.syncFromAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["pbs_filled"], 2)
        starts = {s[0]: s for s in self.startRows(data)}
        self.assertEqual(starts[9001][7], 55.0)   # Anna CWT
        self.assertEqual(starts[9003][7], 300.0)  # Anna STA, stays seconds
        self.assertIsNone(starts[9002][7])        # Lukas has no profile PB

    def test_resync_never_overwrites_local_pb(self):
        client = defaultFakeClient()
        client.profiles_ = {
            ANNA: [{"disciplineAbrv": "CWT", "reportedPerformance": "55"}]}
        data = self.newComp("Aida pb keep comp")
        self.assertEqual(data.syncFromAida(client=client)[0], 0)
        data.db_.execute("UPDATE start SET PB=60.0 WHERE aida_start_id=9001")
        ret, report = data.syncFromAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["pbs_filled"], 0)
        starts = {s[0]: s for s in self.startRows(data)}
        self.assertEqual(starts[9001][7], 60.0)  # local PB kept

    def test_repeat_sync_skips_profile_fetch_once_pbs_are_filled(self):
        client = defaultFakeClient()
        client.profiles_ = {
            ANNA: [{"disciplineAbrv": "CWT", "reportedPerformance": "55"},
                   {"disciplineAbrv": "STA", "reportedPerformance": "300"}],
            LUKAS: [{"disciplineAbrv": "CWT", "reportedPerformance": "61"}],
        }
        data = self.newComp("Aida pb skip comp")
        self.assertEqual(data.syncFromAida(client=client)[0], 0)
        # first sync: every athlete is new, so every profile is fetched
        self.assertEqual(set(client.profile_calls), {ANNA, LUKAS, MARIE})

        client.profile_calls = []
        self.assertEqual(data.syncFromAida(client=client)[0], 0)
        # all PBs are filled (Marie has no starts): nothing to fetch
        self.assertEqual(client.profile_calls, [])

    def test_profile_fetch_failure_warns_but_syncs(self):
        class NoProfileClient(FakeAidaClient):
            def getAthleteProfile(self, event_id, athlete_id):
                raise compy_aida_api.AidaApiError("profile unavailable")

        client = defaultFakeClient()
        failing = NoProfileClient(client.days_, client.preregistrations_,
                                  client.start_lists_)
        data = self.newComp("Aida pb failure comp")
        ret, report = data.syncFromAida(client=failing)
        self.assertEqual(ret, 0)
        self.assertEqual(report["athletes_added"], 3)
        self.assertEqual(report["starts_added"], 3)
        self.assertTrue(any("profile unavailable" in w
                            for w in report["warnings"]))

    def test_dead_profile_endpoint_stops_after_three_attempts(self):
        # live AIDA returned 404 for every profile (endpoint not deployed):
        # the sync must stop probing and emit one summary warning instead
        # of one warning and one request per athlete
        class NoProfileClient(FakeAidaClient):
            def getAthleteProfile(self, event_id, athlete_id):
                self.profile_calls.append(athlete_id)
                raise compy_aida_api.AidaApiError("HTTP 404")

        days = [dayEntry(101, "Day 1", "2026-09-01", 1)]
        preregistrations = [
            prereg(ANNA, "Anna", "Berger", "F", "AUT", "Austria"),
            prereg(LUKAS, "Lukas", "Steiner", "M", "AUT", "Austria"),
            prereg(MARIE, "Marie", "Schmidt", "F", "DEU", "Germany"),
            prereg("44444444-4444-4444-4444-444444444444", "Nina", "Novak",
                   "F", "CZE", "Czech Republic"),
            prereg("55555555-5555-5555-5555-555555555555", "Iva", "Horak",
                   "F", "CZE", "Czech Republic"),
        ]
        client = NoProfileClient(days, preregistrations, {101: []})
        data = self.newComp("Aida dead profiles comp")
        ret, report = data.syncFromAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["athletes_added"], 5)
        self.assertEqual(len(client.profile_calls), 3)
        profile_warnings = [w for w in report["warnings"] if "profile" in w]
        self.assertEqual(len(profile_warnings), 1)
        self.assertIn("HTTP 404", profile_warnings[0])

    def test_sync_never_deletes_local_athletes(self):
        data = self.newComp("Aida keep local comp")
        self.assertEqual(data.addAthlete("Walk", "In", "M", "SVK", "", "999"), 0)
        ret, report = data.syncFromAida(client=defaultFakeClient())
        self.assertEqual(ret, 0)
        self.assertEqual(report["only_local"], ["Walk In"])
        athletes = self.athleteRows(data)
        self.assertEqual(len(athletes), 4)  # 3 synced + walk-in kept

    def test_failed_fetch_changes_nothing(self):
        data = self.newComp("Aida atomic comp")
        client = defaultFakeClient()
        failing = FailingAidaClient(client.days_, client.preregistrations_,
                                    client.start_lists_)
        ret, content = data.syncFromAida(client=failing)
        self.assertEqual(ret, 1)
        self.assertIn("simulated network loss", content["error_msg"])
        self.assertIsNone(self.athleteRows(data))
        self.assertIsNone(self.startRows(data))

    def test_invalid_entries_are_skipped_with_warnings(self):
        days = [dayEntry(101, "Day 1", "2026-09-01", 1)]
        preregistrations = [
            prereg(ANNA, "Anna", "Berger", "F", "AUT", "Austria"),
            prereg("", "No", "Uuid", "F", "AUT", "Austria"),
            prereg("55555555-5555-5555-5555-555555555555", "Bad", "Gender",
                   "?", "AUT", "Austria"),
        ]
        start_lists = {101: [
            startEntry(9001, "Anna", "Berger", "F", "AUT", 1, 1, "CWT", 52),
            startEntry(9002, "Anna", "Berger", "F", "AUT", 1, 2, "XXX", 52),
            startEntry(9003, "Not", "Registered", "M", "AUT", 1, 3, "CWT", 52),
        ]}
        data = self.newComp("Aida skip comp")
        ret, report = data.syncFromAida(
            client=FakeAidaClient(days, preregistrations, start_lists))
        self.assertEqual(ret, 0)
        self.assertEqual(report["athletes_added"], 1)
        self.assertEqual(report["starts_added"], 1)
        self.assertEqual(len(report["warnings"]), 4)

    def test_rest_days_are_skipped(self):
        days = [dayEntry(101, "Day 1", "2026-09-01", 1),
                dayEntry(102, "Rest", "2026-09-02", 2, rest=True)]
        preregistrations = [prereg(ANNA, "Anna", "Berger", "F", "AUT",
                                   "Austria")]
        data = self.newComp("Aida rest day comp")
        ret, report = data.syncFromAida(
            client=FakeAidaClient(days, preregistrations, {101: []}))
        self.assertEqual(ret, 0)
        self.assertEqual(report["days_synced"], 1)


class RecordsFakeClient:
    """Serves canned record payloads and remembers what was queried."""

    def __init__(self, records=None):
        self.records_ = records or {}  # (abrv, dis, gender) -> payload
        self.calls = []

    def getRecords(self, abrv, dis, gender):
        self.calls.append((abrv, dis, gender))
        return self.records_.get((abrv, dis, gender),
                                 {"nr": [], "cr": [], "wr": []})


def record(value, measurement="meters"):
    return {"reportedPerformance": str(value),
            "performanceMeasurement": measurement}


class AidaRecordsTest(CompyDataTestCase):
    """updateNationalRecords: API when a key is configured (all record
    tiers, scoped to the competition's countries and disciplines), the
    existing scraper otherwise."""

    def newComp(self, name):
        data = self.newData()
        data.changeName(name, False)
        self.assertEqual(data.setAidaSettings(EVENT_ID, API_KEY)[0], 0)
        self.assertEqual(data.syncFromAida(client=defaultFakeClient())[0], 0)
        return data

    def recordRows(self, data, country, gender, discipline):
        rows = data.db_.execute(
            '''SELECT tier, value FROM records WHERE federation='aida'
               AND country=? AND gender=? AND discipline=?''',
            (country, gender, discipline))
        return {} if rows is None else {r[0]: r[1] for r in rows}

    def test_api_records_store_all_tiers_scoped_to_competition(self):
        data = self.newComp("Aida records api comp")
        client = RecordsFakeClient({
            ("AT", "CWT", "F"): {"nr": [record(50)], "cr": [record(60)],
                                 "wr": [record(73)]},
            ("AT", "STA", "F"): {"nr": [record(272, "seconds")],
                                 "cr": [], "wr": []},
        })
        with unittest.mock.patch.object(
                compy_data.u, "getNationalRecordsAida",
                side_effect=AssertionError("scraper must not run")):
            ret, content = data.updateNationalRecords(client=client)
        self.assertEqual(ret, 0)
        # one query per competition country x discipline x gender
        self.assertEqual(set(client.calls),
                         {(a, d, g) for a in ("AT", "DE")
                          for d in ("CWT", "STA") for g in ("M", "F")})
        self.assertEqual(self.recordRows(data, "AUT", "F", "CWT"),
                         {"NR": 50.0, "CR": 60.0, "WR": 73.0})
        self.assertEqual(self.recordRows(data, "AUT", "F", "STA"),
                         {"NR": 272.0})
        # the NR lookup used by results keeps working
        self.assertEqual(data.getNr("AUT", "", "F", "CWT"), 50.0)

    def test_sta_records_in_minute_format_are_parsed(self):
        # the live API sends STA records as "10:12" with
        # performanceMeasurement "time" (not in seconds as documented)
        data = self.newComp("Aida sta records comp")
        client = RecordsFakeClient({
            ("AT", "STA", "M"): {"nr": [record("10:12", "time")],
                                 "cr": [], "wr": []},
        })
        self.assertEqual(data.updateNationalRecords(client=client)[0], 0)
        self.assertEqual(self.recordRows(data, "AUT", "M", "STA"),
                         {"NR": 612.0})

    def test_result_remarks_flag_highest_record_tier(self):
        data = self.newComp("Aida record flag comp")
        client = RecordsFakeClient({
            ("AT", "CWT", "F"): {"nr": [record(50)], "cr": [record(60)],
                                 "wr": [record(73)]}})
        self.assertEqual(data.updateNationalRecords(client=client)[0], 0)
        # several comps in this test db sync the same AIDA start ids, so
        # scope the lookup to this competition
        s_id = data.db_.execute(
            '''SELECT s.id FROM start s INNER JOIN competition_athlete ca
               ON ca.id == s.competition_athlete_id
               WHERE s.aida_start_id=9001 AND ca.competition_id=?''',
            data.id_)[0][0]

        def annaRemarks():
            ret, content = data.getResult("CWT", "F", "International")
            self.assertEqual(ret, 0)
            by_name = {r["Name"]: r for r in content["results"]}
            return by_name["Anna Berger"]["Remarks"]

        for rp, flag in ((55, "NR"), (65, "CR"), (74, "WR")):
            self.assertEqual(
                data.updateResult(s_id, rp, 0, "WHITE", "", "")[0], 0)
            remarks = annaRemarks()
            self.assertIn("<b>" + flag + "</b>", remarks)
            for other in {"NR", "CR", "WR"} - {flag}:
                self.assertNotIn("<b>" + other + "</b>", remarks)

        # equalling a record or a non-white card is not flagged
        for rp, card in ((50, "WHITE"), (74, "YELLOW")):
            self.assertEqual(
                data.updateResult(s_id, rp, 0, card, "", "")[0], 0)
            self.assertNotIn("<b>", annaRemarks())

    def test_api_refresh_keeps_other_countries_records(self):
        data = self.newComp("Aida records keep comp")
        stale = '''INSERT INTO records
                   (federation, country, class, gender, discipline, value, tier)
                   VALUES ('aida', ?, '', 'F', 'CWT', ?, 'NR')'''
        # a country not in this competition (from the scraper or another
        # competition's refresh) and a stale row for a competition country
        data.db_.execute(stale, ("FRA", 90.0))
        data.db_.execute(stale, ("AUT", 10.0))
        data.db_.execute(stale, ("GER", 20.0))
        client = RecordsFakeClient({
            ("AT", "CWT", "F"): {"nr": [record(50)], "cr": [], "wr": []}})
        self.assertEqual(data.updateNationalRecords(client=client)[0], 0)
        # FRA was not queried and survives untouched
        self.assertEqual(self.recordRows(data, "FRA", "F", "CWT"),
                         {"NR": 90.0})
        # AUT was queried: stale row replaced by the fetched record
        self.assertEqual(self.recordRows(data, "AUT", "F", "CWT"),
                         {"NR": 50.0})
        # GER was queried and has no records any more: stale row removed
        self.assertEqual(self.recordRows(data, "GER", "F", "CWT"), {})

    def test_records_are_scoped_to_the_federation(self):
        data = self.newComp("Aida federation comp")
        client = RecordsFakeClient({
            ("AT", "CWT", "F"): {"nr": [record(50)], "cr": [],
                                 "wr": [record(73)]}})
        self.assertEqual(data.updateNationalRecords(client=client)[0], 0)
        self.assertEqual(data.getNr("AUT", "", "F", "CWT"), 50.0)
        self.assertEqual(data.getRecord("AUT", "", "F", "CWT", "WR"), 73.0)
        # a cmas competition must not see aida records as its own
        self.assertEqual(data.changeCompType("cmas"), 0)
        self.assertEqual(data.getNr("AUT", "", "F", "CWT"), "")
        self.assertEqual(data.getRecord("AUT", "", "F", "CWT", "WR"), "")
        self.assertEqual(data.changeCompType("aida"), 0)
        self.assertEqual(data.getNr("AUT", "", "F", "CWT"), 50.0)

    def test_without_key_records_come_from_scraper(self):
        data = self.newData()
        data.changeName("Aida records scraper comp", False)
        scraped = {u.NR("aida", "AUT", "", "F", "CWT"): 48.0}
        with unittest.mock.patch.object(
                compy_data.u, "getNationalRecordsAida",
                return_value=scraped):
            ret, content = data.updateNationalRecords()
        self.assertEqual(ret, 0)
        self.assertEqual(self.recordRows(data, "AUT", "F", "CWT"),
                         {"NR": 48.0})
        self.assertEqual(data.getNr("AUT", "", "F", "CWT"), 48.0)


class AidaEndpointTest(CompyServerTestCase):
    """The new admin endpoints: guarded by the admin session, settings
    round-trip, and readable errors on an unconfigured competition. No test
    talks to the real AIDA server."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.app.app_context():
            data = compy_data.CompyData(cls.db, cls.app)
            data.changeName("Aida endpoint comp", False)
            cls.comp_id = data.id_

    def test_endpoints_require_admin(self):
        for path in ("/aida/settings", "/aida/test", "/aida/sync"):
            reply = requests.post(self.base_url + path,
                                  json={"comp_id": self.comp_id})
            self.assertEqual(reply.status_code, 401)

    def test_settings_roundtrip_and_key_masking(self):
        session = self.adminSession()
        reply = session.post(self.base_url + "/aida/settings",
                             json={"comp_id": self.comp_id,
                                   "aida_event_id": EVENT_ID,
                                   "aida_api_key": API_KEY})
        self.assertEqual(reply.status_code, 200)
        data = reply.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["aida_event_id"], EVENT_ID)
        self.assertTrue(data["aida_has_key"])
        # the key itself must never be sent back to the browser
        self.assertNotIn(API_KEY, reply.text)
        # load_comp reports the aida status for the settings tab
        reply = session.post(self.base_url + "/load_comp",
                             json={"comp_id": self.comp_id})
        data = reply.json()
        self.assertEqual(data["aida_event_id"], EVENT_ID)
        self.assertTrue(data["aida_has_key"])
        self.assertNotIn(API_KEY, reply.text)

    def newKeyedComp(self, name):
        with self.app.app_context():
            data = compy_data.CompyData(self.db, self.app)
            data.changeName(name, False)
            self.assertEqual(data.setAidaSettings(EVENT_ID, API_KEY)[0], 0)
            self.assertEqual(
                data.syncFromAida(client=defaultFakeClient())[0], 0)
            return data.id_

    def test_national_records_route_uses_api_for_keyed_comp(self):
        comp_id = self.newKeyedComp("Aida records endpoint comp")
        fake = RecordsFakeClient({
            ("AT", "CWT", "F"): {"nr": [record(50)], "cr": [],
                                 "wr": [record(73)]}})
        with unittest.mock.patch.object(compy_data.CompyData, "aidaClient",
                                        return_value=fake), \
             unittest.mock.patch.object(
                 compy_data.u, "getNationalRecordsAida",
                 side_effect=AssertionError("scraper must not run")):
            reply = self.adminSession().get(
                self.base_url + "/national_records",
                params={"comp_id": comp_id})
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(reply.json()["status"], "success")
        with self.app.app_context():
            rows = self.db.execute(
                '''SELECT tier FROM records WHERE federation='aida'
                   AND country='AUT' AND discipline='CWT' AND gender='F' ''')
        # the WR tier proves the API path ran end to end through the route
        self.assertIn("WR", {r[0] for r in rows})

    def test_national_records_route_reports_admin_safe_error(self):
        comp_id = self.newKeyedComp("Aida records error comp")

        class FailingRecordsClient:
            def getRecords(self, abrv, dis, gender):
                raise compy_aida_api.AidaApiError(
                    "AIDA rate limit reached (HTTP 429). Wait a moment "
                    "and try again")

        with unittest.mock.patch.object(compy_data.CompyData, "aidaClient",
                                        return_value=FailingRecordsClient()):
            reply = self.adminSession().get(
                self.base_url + "/national_records",
                params={"comp_id": comp_id})
        self.assertEqual(reply.status_code, 200)
        data = reply.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("rate limit", data["status_msg"])

    def test_sync_on_unconfigured_comp_reports_error(self):
        with self.app.app_context():
            data = compy_data.CompyData(self.db, self.app)
            data.changeName("Aida endpoint unconfigured", False)
            comp_id = data.id_
        session = self.adminSession()
        reply = session.post(self.base_url + "/aida/sync",
                             json={"comp_id": comp_id})
        self.assertEqual(reply.status_code, 200)
        data = reply.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("event id", data["status_msg"])


class AidaApiClientTest(unittest.TestCase):
    """Unit tests of the HTTP client against a fake requests session."""

    class FakeReply:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self.payload_ = payload

        def json(self):
            if self.payload_ is None:
                raise ValueError("no json")
            return self.payload_

    class FakeSession:
        def __init__(self, reply=None, exception=None):
            self.reply_ = reply
            self.exception_ = exception
            self.last_url = None
            self.last_headers = None

        def get(self, url, headers=None, timeout=None):
            self.last_url = url
            self.last_headers = headers
            if self.exception_ is not None:
                raise self.exception_
            return self.reply_

    def client(self, reply=None, exception=None):
        session = self.FakeSession(reply, exception)
        return compy_aida_api.AidaApiClient(API_KEY, session=session), session

    def test_sends_bearer_token_and_user_agent(self):
        reply = self.FakeReply(200, {"isError": False, "errorMessage": None,
                                     "response": {"days": []}})
        client, session = self.client(reply)
        client.get("/events/days/1")
        self.assertEqual(session.last_headers["Authorization"],
                         "Bearer " + API_KEY)
        self.assertEqual(session.last_headers["User-Agent"], "AIDA-Client")
        self.assertTrue(session.last_url.endswith("/events/days/1"))

    def test_missing_key_is_rejected(self):
        with self.assertRaises(compy_aida_api.AidaApiError):
            compy_aida_api.AidaApiClient("")

    def test_http_error_codes_give_readable_messages(self):
        for code, fragment in ((401, "API key"), (403, "API key"),
                               (404, "event id"), (429, "rate limit"),
                               (500, "server error")):
            client, _ = self.client(self.FakeReply(code, None))
            with self.assertRaises(compy_aida_api.AidaApiError) as ctx:
                client.get("/events/days/1")
            self.assertIn(fragment, str(ctx.exception))

    def test_envelope_error_is_reported(self):
        reply = self.FakeReply(200, {"isError": True,
                                     "errorMessage": "wrong event",
                                     "response": None})
        client, _ = self.client(reply)
        with self.assertRaises(compy_aida_api.AidaApiError) as ctx:
            client.get("/events/days/1")
        self.assertIn("wrong event", str(ctx.exception))

    def test_network_error_is_reported(self):
        import requests
        client, _ = self.client(exception=requests.ConnectionError("down"))
        with self.assertRaises(compy_aida_api.AidaApiError) as ctx:
            client.get("/events/days/1")
        self.assertIn("Could not reach", str(ctx.exception))

    def test_malformed_day_entries_are_rejected(self):
        reply = self.FakeReply(200, {"isError": False, "errorMessage": None,
                                     "response": {"days": [{"name": "x"}]}})
        client, _ = self.client(reply)
        with self.assertRaises(compy_aida_api.AidaApiError):
            client.getDays(1)

    def test_athlete_profile_is_fetched(self):
        profile = {"diverFirstName": "Anna", "personalBests": [
            {"disciplineAbrv": "CWT", "reportedPerformance": "73"}]}
        reply = self.FakeReply(200, {"isError": False, "errorMessage": None,
                                     "response": {"profile": profile}})
        client, session = self.client(reply)
        payload = client.getAthleteProfile(EVENT_ID, ANNA)
        self.assertTrue(session.last_url.endswith(
            "/events/athletes/profile/" + str(EVENT_ID) + "/" + ANNA))
        self.assertEqual(payload["profile"]["personalBests"][0]
                         ["disciplineAbrv"], "CWT")

    def test_athlete_profile_requires_personal_bests_list(self):
        reply = self.FakeReply(200, {"isError": False, "errorMessage": None,
                                     "response": {"profile": {}}})
        client, _ = self.client(reply)
        with self.assertRaises(compy_aida_api.AidaApiError):
            client.getAthleteProfile(EVENT_ID, ANNA)

    def test_athlete_profile_rejects_malformed_uuid(self):
        client, session = self.client()
        for bad in ("", "../../etc", "abc?x=1", "id with spaces"):
            with self.assertRaises(compy_aida_api.AidaApiError):
                client.getAthleteProfile(EVENT_ID, bad)
        # the malformed id must be rejected before any request is made
        self.assertIsNone(session.last_url)

    def test_records_are_fetched(self):
        reply = self.FakeReply(200, {"isError": False, "errorMessage": None,
                                     "response": {"nr": [
                                         {"reportedPerformance": "73"}],
                                         "cr": [], "wr": []}})
        client, session = self.client(reply)
        payload = client.getRecords("FR", "CWT", "F")
        self.assertTrue(session.last_url.endswith(
            "/records/nationality/FR/CWT/F"))
        self.assertEqual(payload["nr"][0]["reportedPerformance"], "73")

    def test_records_require_all_tier_lists(self):
        reply = self.FakeReply(200, {"isError": False, "errorMessage": None,
                                     "response": {"nr": [], "cr": []}})
        client, _ = self.client(reply)
        with self.assertRaises(compy_aida_api.AidaApiError):
            client.getRecords("FR", "CWT", "F")

    def test_records_reject_malformed_parameters(self):
        client, session = self.client()
        for abrv, dis, gender in (("F/R", "CWT", "F"), ("FR", "../x", "F"),
                                  ("FR", "CWT", "X"), ("", "CWT", "F")):
            with self.assertRaises(compy_aida_api.AidaApiError):
                client.getRecords(abrv, dis, gender)
        self.assertIsNone(session.last_url)


if __name__ == "__main__":
    unittest.main()
