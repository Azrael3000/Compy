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

import athlete
import compy_aida_api
import compy_data
import compy_utilities as u
from compy_constants import DISCIPLINES
from compy_testing import (CompyDataTestCase, CompyServerTestCase,
                           SubmenuPayloadAssertions)

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


def liveStartEntry(start_id, athlete_id, first, last, gender, alpha3, order,
                   lane, heat, ot, dis, ap, measurement, rp="", status="",
                   card="", penalty="0", points=""):
    """A start list row as the live API sends it (AIDA Hydro Dynamic 2026,
    October 2026): letter lanes, officialTop, the athlete UUID inside
    athleteProfileLink, STA values as mm:ss and the judged result."""
    return {"startId": start_id, "order": order, "lane": lane, "heat": heat,
            "officialTop": ot, "diverFirstName": first, "diverLastName": last,
            "diverGender": gender, "diverNationality": "", 
            "diverNationalityAbrv": alpha3[:2],
            "diverNationalityAbrvAlpha3": alpha3,
            "athleteProfileLink": "/apiv2/events/athletes/profile/"
                                  + str(EVENT_ID) + "/" + athlete_id,
            "recordsNationalityLink": "/apiv2/records/nationality/"
                                      + alpha3[:2] + "/" + dis + "/" + gender,
            "announcedPerformance": ap, "reportedPerformance": rp,
            "personalBest": "", "performanceMeasurement": measurement,
            "judgeStatus": status, "penaltyCard": card,
            "penaltyPoints": penalty, "points": points,
            "possibleRecord": False, "disciplineAbrv": dis, "diveTime": "",
            "descendTime": ""}


def livePrereg(athlete_id, first, last, gender, alpha3, nationality,
               code="Ok", role=None):
    """A registration as the live API sends it: status codes "Ok"
    (Complete registration) / "Exc" (For non registered), not "APP"."""
    entry = prereg(athlete_id, first, last, gender, alpha3, nationality)
    entry["status"] = {"id": 1, "code": code,
                       "label": "Complete registration" if code == "Ok"
                       else "For non registered"}
    entry["eventRole"] = role
    entry["athleteProfileLink"] = ("/apiv2/events/athletes/profile/"
                                   + str(EVENT_ID) + "/" + athlete_id)
    return entry


def liveFakeClient():
    """Two days like event 4885; names in the registration list differ in
    case from the start list (as they really do), one DQ, one DNS."""
    days = [dayEntry(8497, "STA-DYN", "2026-10-17", 1),
            dayEntry(8498, "DYNB-DNF", "2026-10-18", 2)]
    preregistrations = [
        livePrereg(ANNA, "anna", "BERGER", "F", "AUT", "Austria"),
        livePrereg(LUKAS, "Lukas", "Steiner", "M", "AUT", "Austria", code="Exc"),
        livePrereg(MARIE, "Marie", "Schmidt", "F", "DEU", "Germany"),
    ]
    start_lists = {
        8497: {"dayInfo": {"published": True, "isRestDay": False,
                           "name": "STA-DYN", "date": "17-10-2026",
                           "dayIndex": 1, "startListAvailable": True},
               "startList": [
                   liveStartEntry(122221, ANNA, "Anna", "Berger", "F", "AUT",
                                  1, "A", 1, "10:00", "STA", "04:30", "time",
                                  rp="05:39", status="OK", card="White",
                                  points="67.8"),
                   liveStartEntry(122222, LUKAS, "Lukas", "Steiner", "M", "AUT",
                                  2, "C", 1, "10:00", "STA", "00:01", "time",
                                  rp="05:05", status="DQSP", card="Red",
                                  points="0"),
                   liveStartEntry(122223, ANNA, "Anna", "Berger", "F", "AUT",
                                  3, "B", 2, "14:12", "DYN", "80", "meters",
                                  rp="", status="DNS")]},
        8498: {"dayInfo": {"published": False, "isRestDay": False,
                           "name": "DYNB-DNF", "date": "18-10-2026",
                           "dayIndex": 2, "startListAvailable": False},
               "startList": []},
    }
    client = FakeAidaClient(days, preregistrations, {})
    client.live_start_lists_ = start_lists
    client.getStartList = lambda event_id, day_id: start_lists[day_id]
    return client


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

    def postResult(self, event_id, day_id, start_id, penalty_points,
                   rp=None, judge_status=None, card=None):
        if not hasattr(self, "posted"):
            self.posted = []
        self.posted.append({"event_id": event_id, "day_id": day_id,
                            "start_id": start_id, "rp": rp,
                            "judge_status": judge_status, "card": card,
                            "penalty_points": penalty_points})
        return {"startId": start_id, "points": "42"}


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

    def test_sync_repairs_zero_pbs_left_by_old_start_list_save(self):
        # before the fix, saving a start list wrote PB=0 for every empty PB;
        # 0 is never a real PB, so the sync treats it as empty and fills it
        client = defaultFakeClient()
        client.profiles_ = {
            ANNA: [{"disciplineAbrv": "CWT", "reportedPerformance": "55"}]}
        data = self.newComp("Aida zero pb comp")
        self.assertEqual(data.syncFromAida(client=client)[0], 0)
        data.db_.execute("UPDATE start SET PB=0 WHERE aida_start_id=9001")
        client.profile_calls = []
        ret, report = data.syncFromAida(client=client)
        self.assertEqual(ret, 0)
        self.assertIn(ANNA, client.profile_calls)
        self.assertEqual(report["pbs_filled"], 1)
        starts = {s[0]: s for s in self.startRows(data)}
        self.assertEqual(starts[9001][7], 55.0)

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

    # ---- the live payload of October 2026 (see tools/aida_dump_*.json) ----

    def test_live_start_list_lanes_ot_and_uuid_match(self):
        client = liveFakeClient()
        data = self.newComp("Aida live shape comp")
        ret, report = data.syncFromAida(client=client)
        self.assertEqual(ret, 0)
        # names differ in case between registrations and start list: the
        # UUID in athleteProfileLink still matches every start
        self.assertEqual(report["starts_added"], 3)
        self.assertEqual([w for w in report["warnings"]
                          if "registration list" in w], [])
        starts = {s[0]: s for s in self.startRows(data)}
        # letter lanes become numbers, officialTop becomes the OT
        self.assertEqual(starts[122221][2], 1)       # lane A
        self.assertEqual(starts[122222][2], 3)       # lane C
        self.assertEqual(starts[122221][4], "1000")  # OT 10:00
        self.assertEqual(starts[122223][4], "1412")  # OT 14:12
        # STA announced as mm:ss -> seconds, meters stay meters
        self.assertEqual(starts[122221][3], 270.0)
        self.assertEqual(starts[122223][3], 80.0)
        # results on AIDA are never imported into the local results
        self.assertIsNone(starts[122221][5])
        self.assertIsNone(starts[122222][5])

    def test_live_registration_status_ok_means_registered(self):
        client = liveFakeClient()
        data = self.newComp("Aida live status comp")
        self.assertEqual(data.syncFromAida(client=client)[0], 0)
        flags = {row[0]: row[5] for row in self.athleteRows(data)}
        self.assertTrue(flags[ANNA])     # "Ok" = complete registration
        self.assertFalse(flags[LUKAS])   # "Exc" = for non registered
        # "Exc" athletes still take part (one did in Hydro 2026): kept
        self.assertEqual(len(flags), 3)

    def test_day_without_published_start_list_is_reported(self):
        client = liveFakeClient()
        data = self.newComp("Aida live empty day comp")
        ret, report = data.syncFromAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["days_synced"], 2)
        self.assertEqual([w for w in report["warnings"] if "DYNB-DNF" in w],
                         ["No start list on AIDA for DYNB-DNF 2026-10-18 "
                          "(not published on AIDA yet)"])

    def test_resync_keeps_locally_changed_ot_but_fills_unset_one(self):
        client = liveFakeClient()
        data = self.newComp("Aida live ot comp")
        self.assertEqual(data.syncFromAida(client=client)[0], 0)
        data.db_.execute("UPDATE start SET OT='1030' WHERE aida_start_id=122221")
        data.db_.execute("UPDATE start SET OT='9999' WHERE aida_start_id=122222")
        self.assertEqual(data.syncFromAida(client=client)[0], 0)
        starts = {s[0]: s for s in self.startRows(data)}
        self.assertEqual(starts[122221][4], "1030")  # local edit kept
        self.assertEqual(starts[122222][4], "1000")  # unset -> from AIDA

    def test_lane_and_uuid_helpers(self):
        data = self.newComp("Aida helpers comp")
        # the inverse lane conversion takes letters and numbers whatever
        # the competition's lane style, since AIDA always sends letters
        for lane_style in ("numeric", "alphabetic"):
            data.lane_style_ = lane_style
            self.assertEqual(data.laneStyleConverter("A", True), 1)
            self.assertEqual(data.laneStyleConverter("d", True), 4)
            self.assertEqual(data.laneStyleConverter(3, True), 3)
            self.assertEqual(data.laneStyleConverter(" 3 ", True), 3)
            for garbage in ("", "AB", "x1"):
                with self.assertRaises(ValueError):
                    data.laneStyleConverter(garbage, True)
        data.lane_style_ = "numeric"
        self.assertEqual(data.laneStyleConverter(2), "2")
        data.lane_style_ = "alphabetic"
        self.assertEqual(data.laneStyleConverter(2), "B")
        self.assertEqual(data.aidaAthleteUuid(
            {"athleteProfileLink": "/apiv2/events/athletes/profile/4885/"
                                   "36F96F28-29a0-4f56-8d0e-4b9315a51f3a"}),
            "36f96f28-29a0-4f56-8d0e-4b9315a51f3a")
        self.assertIsNone(data.aidaAthleteUuid({"athleteProfileLink": ""}))
        self.assertIsNone(data.aidaAthleteUuid({}))
        self.assertIsNone(data.aidaAthleteUuid(
            {"athleteProfileLink": "/apiv2/events/athletes/profile/4885/x"}))

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


class AidaUploadTest(CompyDataTestCase):
    """Results upload: matching local starts to the AIDA start list, the
    result -> AIDA field mapping, dry run, and the abort/continue policy."""

    def newComp(self, name):
        data = self.newData()
        data.changeName(name, False)
        self.assertEqual(data.setAidaSettings(EVENT_ID, API_KEY)[0], 0)
        return data

    def syncedComp(self, name):
        """A competition seeded by the sync: every start has an AIDA id."""
        client = defaultFakeClient()
        data = self.newComp(name)
        self.assertEqual(data.syncFromAida(client=client)[0], 0)
        return data, client

    def startIds(self, data):
        """{aida_start_id: local start id}"""
        rows = data.db_.execute(
            '''SELECT s.aida_start_id, s.id FROM start s
               INNER JOIN competition_athlete ca
               ON ca.id == s.competition_athlete_id
               WHERE ca.competition_id == ?''', data.id_)
        return {row[0]: row[1] for row in rows}

    def test_results_are_posted_with_aida_fields(self):
        data, client = self.syncedComp("Upload fields comp")
        ids = self.startIds(data)
        # Anna CWT 52 announced: white card, clean dive
        self.assertEqual(data.updateResult(ids[9001], "52", 0, "WHITE", "OK", "")[0], 0)
        # Lukas CWT 61 announced, 55 done: yellow, no tag + under ap
        # (compy stores the total penalty: 1 other + 6 under ap)
        self.assertEqual(data.updateResult(ids[9002], "55", 1, "YELLOW", "NO TAG,UNDER AP", "")[0], 0)
        # Anna STA: red card with two dq codes, 4:10
        self.assertEqual(data.updateResult(ids[9003], "4:10", 0, "RED", "DQSP,DQAIRWAYS", "")[0], 0)

        ret, report = data.uploadResultsToAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["uploaded"], 3)
        self.assertEqual(report["failed"], [])
        self.assertEqual(report["unmatched"], [])
        self.assertEqual(report["no_result"], 0)
        posted = {p["start_id"]: p for p in client.posted}
        self.assertEqual(posted[9001], {"event_id": EVENT_ID, "day_id": 101,
                                        "start_id": 9001, "rp": 52.0,
                                        "judge_status": "ok", "card": "WHITE",
                                        "penalty_points": 0.0})
        # server appends no tag / under ap itself; total penalty is sent
        self.assertEqual(posted[9002]["judge_status"], "")
        self.assertEqual(posted[9002]["card"], "YELLOW")
        self.assertEqual(posted[9002]["rp"], 55.0)
        self.assertEqual(posted[9002]["penalty_points"], 7.0)
        self.assertEqual(posted[9002]["day_id"], 101)
        # STA in seconds, dq codes lower case
        self.assertEqual(posted[9003]["rp"], 250.0)
        self.assertEqual(posted[9003]["judge_status"], "dqsp,dqairways")
        self.assertEqual(posted[9003]["card"], "RED")
        self.assertEqual(posted[9003]["day_id"], 102)
        self.assertEqual(report["results"][0]["points"], "42")

    def test_dns_is_posted_without_rp(self):
        data, client = self.syncedComp("Upload dns comp")
        ids = self.startIds(data)
        self.assertEqual(data.updateResult(ids[9001], "0", 0, "RED", "DNS", "")[0], 0)
        ret, report = data.uploadResultsToAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["uploaded"], 1)
        self.assertEqual(client.posted[0]["rp"], None)
        self.assertEqual(client.posted[0]["judge_status"], "dns")
        self.assertEqual(client.posted[0]["card"], None)
        self.assertEqual(client.posted[0]["penalty_points"], 0)

    def test_starts_without_result_are_skipped(self):
        data, client = self.syncedComp("Upload partial comp")
        ids = self.startIds(data)
        self.assertEqual(data.updateResult(ids[9001], "52", 0, "WHITE", "OK", "")[0], 0)
        ret, report = data.uploadResultsToAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["uploaded"], 1)
        self.assertEqual(report["no_result"], 2)
        self.assertEqual([p["start_id"] for p in client.posted], [9001])

    def test_excel_seeded_starts_are_matched_by_name_and_remembered(self):
        # no AIDA ids at all (competition run from the excel file); names on
        # AIDA may differ in case and spacing from the local ones
        client = defaultFakeClient()
        data = self.newComp("Upload excel comp")
        anna = athlete.Athlete.fromArgs(ANNA, "anna", "BERGER ", "F", "AUT", "", data.db_)
        anna.associateWithComp(data.id_)
        block = data.db_.insert(
            '''INSERT INTO block (competition_id, day, disciplines)
               VALUES (?, ?, ?)''', (data.id_, "20260901", 1 << DISCIPLINES.index("CWT")))
        start_id = data.db_.insert(
            '''INSERT INTO start (competition_athlete_id, discipline, lane, block,
                                  OT, AP, RP, card, penalty, remarks)
               VALUES (?, "CWT", 1, ?, "10:00", 52, 50, "YELLOW", 2, "UNDER AP")''',
            (anna.comp_athlete_id_, block))

        ret, report = data.uploadResultsToAida(client=client, dry_run=True)
        self.assertEqual(ret, 0)
        self.assertEqual(len(report["results"]), 1)
        self.assertEqual(report["results"][0]["aida_start_id"], 9001)
        # a dry run changes nothing
        self.assertFalse(hasattr(client, "posted"))
        self.assertIsNone(data.db_.execute(
            "SELECT aida_start_id FROM start WHERE id=?", start_id)[0][0])

        ret, report = data.uploadResultsToAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["uploaded"], 1)
        self.assertEqual(client.posted[0]["start_id"], 9001)
        self.assertEqual(client.posted[0]["penalty_points"], 2.0)
        # the match is stored for the next upload / sync
        self.assertEqual(data.db_.execute(
            "SELECT aida_start_id FROM start WHERE id=?", start_id)[0][0], 9001)

    def test_live_shape_upload_matches_by_uuid_and_sends_dns_status(self):
        # excel-seeded competition (no AIDA start ids), athlete stored
        # with the registration spelling; the start list spells her
        # differently but carries her UUID
        client = liveFakeClient()
        data = self.newComp("Upload live shape comp")
        anna = athlete.Athlete.fromArgs(ANNA, "anna", "BERGER", "F", "AUT", "", data.db_)
        anna.associateWithComp(data.id_)
        for dis, day, rp, card, remarks, penalty in (
                ("STA", "20261017", 339, "WHITE", "OK", 0),
                ("DYN", "20261017", 0, "nan", "DNS", "nan")):
            block = data.db_.insert(
                '''INSERT INTO block (competition_id, day, disciplines)
                   VALUES (?, ?, ?)''', (data.id_, day, 1 << DISCIPLINES.index(dis)))
            data.db_.insert(
                '''INSERT INTO start (competition_athlete_id, discipline, lane,
                                      block, OT, AP, RP, card, penalty, remarks)
                   VALUES (?, ?, 1, ?, "1000", 1, ?, ?, ?, ?)''',
                (anna.comp_athlete_id_, dis, block, rp, card, penalty, remarks))
        ret, report = data.uploadResultsToAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["unmatched"], [])
        self.assertEqual(report["uploaded"], 2)
        posted = {p["start_id"]: p for p in client.posted}
        self.assertEqual(posted[122221]["rp"], 339.0)
        self.assertEqual(posted[122221]["judge_status"], "ok")
        self.assertEqual(posted[122221]["card"], "WHITE")
        self.assertEqual(posted[122221]["day_id"], 8497)
        self.assertEqual(posted[122223], {"event_id": EVENT_ID, "day_id": 8497,
                                          "start_id": 122223, "rp": None,
                                          "judge_status": "dns", "card": None,
                                          "penalty_points": 0})

    def test_start_missing_on_aida_is_reported_not_sent(self):
        data, client = self.syncedComp("Upload unmatched comp")
        ids = self.startIds(data)
        self.assertEqual(data.updateResult(ids[9001], "52", 0, "WHITE", "OK", "")[0], 0)
        self.assertEqual(data.updateResult(ids[9002], "61", 0, "WHITE", "OK", "")[0], 0)
        # Lukas disappears from the AIDA start list (and his id with him)
        client.start_lists_[101] = [e for e in client.start_lists_[101]
                                    if e["startId"] != 9002]
        ret, report = data.uploadResultsToAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["uploaded"], 1)
        self.assertEqual(len(report["unmatched"]), 1)
        self.assertIn("Lukas Steiner CWT (2026-09-01)", report["unmatched"][0])

    def test_empty_aida_start_list_is_an_error(self):
        data, client = self.syncedComp("Upload empty comp")
        ids = self.startIds(data)
        self.assertEqual(data.updateResult(ids[9001], "52", 0, "WHITE", "OK", "")[0], 0)
        client.start_lists_ = {101: [], 102: []}
        ret, content = data.uploadResultsToAida(client=client)
        self.assertEqual(ret, 1)
        self.assertIn("no start list", content["error_msg"])

    def test_unconfigured_competition_is_rejected(self):
        data = self.newData()
        data.changeName("Upload unconfigured comp", False)
        ret, content = data.uploadResultsToAida(client=defaultFakeClient())
        self.assertEqual(ret, 1)
        self.assertIn("event id", content["error_msg"])

    def test_write_refusal_aborts_single_rejection_continues(self):
        class RejectingClient(FakeAidaClient):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.errors = {}
            def postResult(self, event_id, day_id, start_id, *args, **kwargs):
                if start_id in self.errors:
                    raise compy_aida_api.AidaApiError(self.errors[start_id])
                return super().postResult(event_id, day_id, start_id, *args, **kwargs)

        base = defaultFakeClient()
        client = RejectingClient(base.days_, base.preregistrations_, base.start_lists_)
        data = self.newComp("Upload reject comp")
        self.assertEqual(data.syncFromAida(client=client)[0], 0)
        ids = self.startIds(data)
        for aida_id in (9001, 9002, 9003):
            self.assertEqual(data.updateResult(ids[aida_id], "50", 0, "WHITE", "OK", "")[0], 0)

        # one rejected result: reported, the others still go through
        client.errors = {9001: "AIDA rejected the request (HTTP 400): bad"}
        ret, report = data.uploadResultsToAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["uploaded"], 2)
        self.assertEqual(len(report["failed"]), 1)
        self.assertIn("Anna Berger CWT", report["failed"][0])
        self.assertIsNone(report["aborted"])

        # a refused write (no write scope / finalised event) stops at once
        client.posted = []
        client.errors = {9001: "AIDA refused the write (HTTP 403). no scope"}
        ret, report = data.uploadResultsToAida(client=client)
        self.assertEqual(ret, 0)
        self.assertEqual(report["uploaded"], 0)
        self.assertEqual(client.posted, [])
        self.assertIn("HTTP 403", report["aborted"])

    def test_judge_status_mapping(self):
        data = self.newComp("Upload mapping comp")
        self.assertEqual(data.aidaJudgeStatus("WHITE", "OK"), "ok")
        self.assertEqual(data.aidaJudgeStatus("WHITE", "-"), "ok")
        self.assertEqual(data.aidaJudgeStatus("YELLOW", "UNDER AP"), "")
        self.assertEqual(data.aidaJudgeStatus("YELLOW", "LATESTART,UNDER AP"), "latestart")
        self.assertEqual(data.aidaJudgeStatus("YELLOW", "NO TAG, SHORT"), "short")
        self.assertEqual(data.aidaJudgeStatus("RED", "DQSP,DQTOUCH,DQBO-SURFACE"),
                         "dqsp,dqtouch,dqbo-surface")
        self.assertEqual(data.aidaJudgeStatus("RED", "DQCHECK-IN,DNS"), "dqcheck-in")
        self.assertIsNone(data.aidaResultPayload({"discipline": "DYN", "RP": None,
                                                  "card": None, "penalty": None,
                                                  "remarks": None}))
        self.assertIsNone(data.aidaResultPayload({"discipline": "DYN", "RP": None,
                                                  "card": "nan", "penalty": "nan",
                                                  "remarks": "-"}))
        dns = data.aidaResultPayload({"discipline": "DYN", "RP": None, "card": "nan",
                                      "penalty": "nan", "remarks": "UNDER AP,DNS"})
        self.assertEqual(dns["rp"], None)
        nan_pen = data.aidaResultPayload({"discipline": "DYN", "RP": 100.0,
                                          "card": "WHITE", "penalty": "nan",
                                          "remarks": "OK"})
        self.assertEqual(nan_pen["penalty_points"], 0.)


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

        # the flag is plain text (", NR" etc.); the react frontend escapes
        # any markup, so the server no longer embeds html in the data
        for rp, flag in ((55, "NR"), (65, "CR"), (74, "WR")):
            self.assertEqual(
                data.updateResult(s_id, rp, 0, "WHITE", "", "")[0], 0)
            remarks = annaRemarks()
            self.assertIn(", " + flag, remarks)
            for other in {"NR", "CR", "WR"} - {flag}:
                self.assertNotIn(other, remarks)

        # equalling a record counts as a record (upstream 7b6955c: <=)
        self.assertEqual(data.updateResult(s_id, 50, 0, "WHITE", "", "")[0], 0)
        self.assertIn(", NR", annaRemarks())
        # a non-white card or a performance below every record is not flagged
        for rp, card in ((74, "YELLOW"), (49, "WHITE")):
            self.assertEqual(
                data.updateResult(s_id, rp, 0, card, "", "")[0], 0)
            for flag in ("NR", "CR", "WR"):
                self.assertNotIn(flag, annaRemarks())

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


class AidaEndpointTest(SubmenuPayloadAssertions, CompyServerTestCase):
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
        for path in ("/aida/settings", "/aida/test", "/aida/sync",
                     "/aida/upload_results"):
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

    def test_sync_returns_every_submenu_dataset(self):
        """A sync replaces athletes, days and start lists wholesale, and the
        admin page applies its response as a reset - so it has to carry the
        whole submenu dataset back or the menus it omits are emptied."""
        comp_id = self.newKeyedComp("Aida sync payload comp")

        with unittest.mock.patch.object(compy_data.CompyData, "aidaClient",
                                        return_value=defaultFakeClient()):
            reply = self.adminSession().post(self.base_url + "/aida/sync",
                                             json={"comp_id": comp_id})

        self.assertEqual(reply.status_code, 200)
        self.assertCarriesSubmenuData(reply.json())

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


class AidaUploadEndpointTest(CompyServerTestCase):
    """/aida/upload_results: the report rendered for the admin box."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.app.app_context():
            data = compy_data.CompyData(cls.db, cls.app)
            data.changeName("Aida upload endpoint comp", False)
            data.setAidaSettings(EVENT_ID, API_KEY)
            cls.client = defaultFakeClient()
            data.syncFromAida(client=cls.client)
            start = data.db_.execute(
                "SELECT id FROM start WHERE aida_start_id=9003")[0][0]
            data.updateResult(start, "4:10", 0, "WHITE", "OK", "")
            cls.comp_id = data.id_

    def test_preview_and_upload_reports(self):
        session = self.adminSession()
        with unittest.mock.patch.object(compy_data.CompyData, "aidaClient",
                                        return_value=self.client):
            reply = session.post(self.base_url + "/aida/upload_results",
                                 json={"comp_id": self.comp_id, "dry_run": True})
            self.assertEqual(reply.status_code, 200)
            data = reply.json()
            self.assertEqual(data["status"], "success")
            self.assertIn("Preview (nothing was sent): 1 result(s)", data["status_msg"])
            self.assertIn("2 without result yet", data["status_msg"])
            # the table itself is rendered by the frontend from the rows
            self.assertNotIn("<", data["status_msg"])
            self.assertEqual(len(data["results"]), 1)
            self.assertEqual(data["results"][0]["rp_display"], "4:10")
            self.assertEqual(data["results"][0]["card"], "WHITE")
            self.assertFalse(hasattr(self.client, "posted"))

            reply = session.post(self.base_url + "/aida/upload_results",
                                 json={"comp_id": self.comp_id})
            data = reply.json()
            self.assertEqual(data["status"], "success")
            self.assertIn("1 result(s) uploaded", data["status_msg"])
            self.assertEqual(data["results"][0]["points"], "42")
            self.assertEqual(len(self.client.posted), 1)

    def test_unconfigured_competition_reports_error(self):
        with self.app.app_context():
            data = compy_data.CompyData(self.db, self.app)
            data.changeName("Aida upload unconfigured comp", False)
            comp_id = data.id_
        session = self.adminSession()
        reply = session.post(self.base_url + "/aida/upload_results",
                             json={"comp_id": comp_id})
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(reply.json()["status"], "error")


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
            self.last_method = None
            self.last_data = None

        def request(self, method, url, headers=None, data=None, timeout=None):
            self.last_method = method
            self.last_url = url
            self.last_headers = headers
            self.last_data = data
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

    # ---- write endpoints ----

    def resultReply(self):
        return self.FakeReply(200, {"isError": False, "errorMessage": "",
                                    "response": {"startId": 347,
                                                 "reportedPerformance": "50",
                                                 "judgeStatus": "DQJUMP",
                                                 "penaltyCard": "Yellow",
                                                 "penaltyPoints": "3",
                                                 "points": "95"}})

    def test_post_result_sends_form_fields(self):
        client, session = self.client(self.resultReply())
        reply = client.postResult(5005, 7601, 347, 3, rp=50,
                                  judge_status="dqjump", card="YELLOW")
        self.assertEqual(session.last_method, "POST")
        self.assertTrue(session.last_url.endswith("/events/startlists"))
        self.assertEqual(session.last_headers["Authorization"],
                         "Bearer " + API_KEY)
        self.assertEqual(session.last_data,
                         {"EventId": "5005", "EventDayId": "7601",
                          "EventStartListId": "347", "PenaltyPoints": "3",
                          "RP": "50", "judgeStatus": "dqjump",
                          "PenaltyCard": "2"})
        self.assertEqual(reply["points"], "95")

    def test_post_result_dns_sends_no_rp_status_or_card(self):
        client, session = self.client(self.resultReply())
        client.postResult(5005, 7601, 347, 0)
        self.assertEqual(session.last_data,
                         {"EventId": "5005", "EventDayId": "7601",
                          "EventStartListId": "347", "PenaltyPoints": "0"})

    def test_post_result_number_formatting(self):
        client, session = self.client(self.resultReply())
        client.postResult(1, 2, 3, 4.5, rp=275.0, judge_status="ok",
                          card="white")
        self.assertEqual(session.last_data["RP"], "275")
        self.assertEqual(session.last_data["PenaltyPoints"], "4.5")
        self.assertEqual(session.last_data["PenaltyCard"], "1")
        client.postResult(1, 2, 3, 0, rp=150.5, card="RED")
        self.assertEqual(session.last_data["RP"], "150.5")
        self.assertEqual(session.last_data["PenaltyCard"], "3")

    def test_post_result_rejects_unknown_card_before_sending(self):
        client, session = self.client(self.resultReply())
        with self.assertRaises(compy_aida_api.AidaApiError):
            client.postResult(1, 2, 3, 0, rp=50, card="BLUE")
        self.assertIsNone(session.last_url)

    def test_write_refusal_explains_scope_and_finalised_event(self):
        for code in (401, 403):
            client, _ = self.client(self.FakeReply(code, None))
            with self.assertRaises(compy_aida_api.AidaApiError) as ctx:
                client.postResult(1, 2, 3, 0, rp=50, card="WHITE")
            self.assertIn("write scope", str(ctx.exception))
            self.assertIn("finalised", str(ctx.exception))

    def test_rejected_write_reports_server_message(self):
        reply = self.FakeReply(400, {"isError": True,
                                     "errorMessage": "White only valid with ok",
                                     "response": None})
        client, _ = self.client(reply)
        with self.assertRaises(compy_aida_api.AidaApiError) as ctx:
            client.postResult(1, 2, 3, 0, rp=50, judge_status="dqsp",
                              card="WHITE")
        self.assertIn("White only valid with ok", str(ctx.exception))

    def test_malformed_write_reply_is_rejected(self):
        reply = self.FakeReply(200, {"isError": False, "errorMessage": "",
                                     "response": {"something": "else"}})
        client, _ = self.client(reply)
        with self.assertRaises(compy_aida_api.AidaApiError):
            client.postResult(1, 2, 3, 0, rp=50, card="WHITE")

    def test_delete_result(self):
        reply = self.FakeReply(200, {"isError": False, "errorMessage": "",
                                     "response": {"startId": 347,
                                                  "points": ""}})
        client, session = self.client(reply)
        client.deleteResult(347)
        self.assertEqual(session.last_method, "DELETE")
        self.assertTrue(session.last_url.endswith("/events/startlists/347/result"))


if __name__ == "__main__":
    unittest.main()
