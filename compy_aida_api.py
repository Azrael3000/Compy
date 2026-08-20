
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#           ━━━━━━━━━━━━━
#            ┏┓┏┓┳┳┓┏┓┓┏
#            ┃ ┃┃┃┃┃┃┃┗┫
#            ┗┛┗┛┛ ┗┣┛┗┛
#           ━━━━━━━━━━━━━
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Competition organization tool
#  for freediving competitions.
#
#  Copyright 2023 - Arno Mayrhofer
#
#  Licensed under the GNU AGPL
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Authors:
#
#  - Arno Mayrhofer
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""Read-only client for the AIDA International API v2.

Documentation: https://www.aidainternational.org/api-docs

Every request sends the per-event API key as a Bearer token together with
the mandatory "AIDA-Client" User-Agent. Responses come wrapped in an
envelope {isError, errorMessage, response}; this module unwraps it and
turns every failure mode (network, HTTP status, envelope error, malformed
payload) into an AidaApiError whose message is safe to show in the admin
interface. The API key is never logged.

Only read endpoints are implemented on purpose: the sync may never be able
to modify anything on the AIDA side.
"""

import logging
import re

try:
    import requests
except ImportError:
    print("Could not find requests. Install with 'pip3 install requests'")
    exit(-1)

AIDA_API_BASE_URL = "https://www.aidainternational.org/apiv2"
AIDA_REQUEST_TIMEOUT = 15  # seconds


class AidaApiError(RuntimeError):
    """A failed AIDA API call. str(error) is safe to show to the admin."""


class AidaApiClient:
    """Thin wrapper around the AIDA API v2 read endpoints.

    The requests session can be injected for testing; production code uses
    a plain requests.Session created here.
    """

    def __init__(self, api_key, base_url=AIDA_API_BASE_URL, session=None):
        if not api_key:
            raise AidaApiError("No AIDA API key configured for this competition")
        self.api_key_ = api_key
        self.base_url_ = base_url.rstrip("/")
        self.session_ = session if session is not None else requests.Session()

    def get(self, path):
        """GET one API path and return the unwrapped response payload."""
        url = self.base_url_ + path
        # never log headers: the Authorization header contains the key
        logging.debug("AIDA API request: GET %s", path)
        headers = {
            "Authorization": "Bearer " + self.api_key_,
            "User-Agent": "AIDA-Client",
            "Accept": "application/json",
        }
        try:
            reply = self.session_.get(url, headers=headers,
                                      timeout=AIDA_REQUEST_TIMEOUT)
        except requests.RequestException as e:
            logging.warning("AIDA API not reachable: %s", type(e).__name__)
            raise AidaApiError("Could not reach the AIDA server. Check the "
                               "internet connection (or use the excel file "
                               "workflow instead)")
        if reply.status_code in (401, 403):
            raise AidaApiError("AIDA rejected the API key (HTTP "
                               + str(reply.status_code) + "). Check that the "
                               "key is correct, has read scope and belongs "
                               "to this event")
        if reply.status_code == 404:
            raise AidaApiError("AIDA could not find the requested data "
                               "(HTTP 404). Check the event id")
        if reply.status_code == 429:
            raise AidaApiError("AIDA rate limit reached (HTTP 429). Wait a "
                               "moment and try again")
        if reply.status_code != 200:
            raise AidaApiError("AIDA server error (HTTP "
                               + str(reply.status_code) + "). Try again later")
        try:
            envelope = reply.json()
        except ValueError:
            raise AidaApiError("AIDA returned an unreadable response")
        if not isinstance(envelope, dict):
            raise AidaApiError("AIDA returned an unexpected response format")
        if envelope.get("isError"):
            msg = envelope.get("errorMessage") or "unknown error"
            raise AidaApiError("AIDA reported an error: " + str(msg))
        if "response" not in envelope:
            raise AidaApiError("AIDA returned an unexpected response format")
        return envelope["response"]

    def getDays(self, event_id):
        """List the competition days of an event.

        Returns the raw payload with at least eventName and a days list;
        every day is guaranteed to have an id and a date.
        """
        payload = self.get("/events/days/" + str(int(event_id)))
        days = self.requireList(payload, "days")
        for day in days:
            if not isinstance(day, dict) or day.get("id") is None \
               or not day.get("date"):
                raise AidaApiError("AIDA returned a malformed day entry")
        return payload

    def getPreregistrations(self, event_id):
        """List the (pre)registered divers of an event."""
        payload = self.get("/events/preregistrations/" + str(int(event_id)))
        self.requireList(payload, "preregistrations")
        return payload

    def getAthleteProfile(self, event_id, athlete_id):
        """Get the profile of one athlete in the context of an event.

        athlete_id is the AIDA athlete UUID. It is validated before being
        used in the URL, so a malformed id never reaches the server.
        """
        athlete_id = str(athlete_id or "").strip()
        if not re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                            r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", athlete_id):
            raise AidaApiError("Invalid AIDA athlete id: " + athlete_id[:40])
        payload = self.get("/events/athletes/profile/" + str(int(event_id))
                           + "/" + athlete_id)
        if not isinstance(payload, dict) \
           or not isinstance(payload.get("profile"), dict):
            raise AidaApiError("AIDA response is missing the athlete profile")
        self.requireList(payload["profile"], "personalBests")
        return payload

    def getStartList(self, event_id, day_id):
        """Get the start list of one competition day."""
        payload = self.get("/events/startlists/" + str(int(event_id))
                           + "/" + str(int(day_id)))
        self.requireList(payload, "startList")
        return payload

    def getRecords(self, nationality_abrv, discipline, gender):
        """Current NR/CR/WR records for one country, discipline and gender.

        nationality_abrv is the 2-letter code AIDA uses in start list rows
        (diverNationalityAbrv), not an IOC code.
        """
        abrv = str(nationality_abrv or "").strip().upper()
        dis = str(discipline or "").strip().upper()
        gender = str(gender or "").strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", abrv) \
           or not re.fullmatch(r"[A-Z]{2,6}", dis) or gender not in ("M", "F"):
            raise AidaApiError("Invalid record query: " + abrv + "/" + dis
                               + "/" + gender)
        payload = self.get("/records/nationality/" + abrv + "/" + dis
                           + "/" + gender)
        for tier in ("nr", "cr", "wr"):
            self.requireList(payload, tier)
        return payload

    def requireList(self, payload, key):
        if not isinstance(payload, dict) or not isinstance(payload.get(key), list):
            raise AidaApiError("AIDA response is missing the '" + key + "' list")
        return payload[key]
