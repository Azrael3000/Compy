 ```
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

          ━━━━━━━━━━━━━
           ┏┓┏┓┳┳┓┏┓┓┏
           ┃ ┃┃┃┃┃┃┃┗┫
           ┗┛┗┛┛ ┗┣┛┗┛
          ━━━━━━━━━━━━━

 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Competition organization tool
 for freediving competitions.

 Copyright 2023 - Arno Mayrhofer

 Licensed under the GNU AGPL

 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Authors:

 - Arno Mayrhofer

 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ```

# Compy

Compy is a competition organization tool for freediving competition. Its current features are:

 - Parse AIDA International Style Excel files
 - Sync of registrations and start lists from the AIDA International API, and upload of the judged results
 - Switch between CMAS and AIDA competitions (different countdown, different result view without points for CMAS)
 - Uploading of sponsor image for output on PDFs
 - Output of results, lane lists and start lists via PDF
 - Possibility to select athletes for special ranking (e.g. newcommer)
 - List of breaks for each athlete on each day
 - Automated countdown

Future features can be seen in the TODO file.

## AIDA API sync (read only)

Instead of downloading the excel file from AIDA, a competition can be seeded
and refreshed directly from the [AIDA International API](https://www.aidainternational.org/api-docs):

 - Ask the event organizer for an API key: keys are managed on the "API
   settings" page of the event in AIDA's organizer portal. Keys carry a
   scope (`read` for GET requests is all Compy needs) and may be tied to a
   single event, so expect a different key for every competition.
 - On the Settings tab enter the AIDA event id and the API key and press
   "Save". The key is stored with the competition in the local database and
   is never sent back to the browser.
 - "Test connection" fetches the event name and days - do this days before
   the competition to verify key, scope and event binding.
 - "Sync from AIDA" pulls the event data described below. The sync is
   applied atomically: if any request fails nothing is changed. It can be
   repeated at any time (e.g. after late registrations); existing entries
   are updated instead of duplicated.

### What the sync populates

 - **Athlete list**: all registered divers with first/last name, gender and
   nationality (converted to the IOC three letter codes Compy uses),
   matched and updated by their AIDA athlete UUID.
 - **Registration tab checkboxes**: "registered" (AIDA status "Ok" =
   complete registration, or the documented "APP" = approved; "Exc" = for
   non registered is kept as an athlete but not registered), "paid"
   (payment receipt uploaded) and "medical checked" (medical certificate
   uploaded) are pre-filled from AIDA.
 - **Competition days**: the start and end date of the competition are set
   from AIDA's day list (rest days are skipped).
 - **Start lists**: one block per day and discipline with each start's
   lane (AIDA's letter lanes A, B, ... become 1, 2, ...), official top and
   announced performance (STA converted to seconds). AIDA's start ids are
   stored so repeated syncs update the right entries. A day whose start
   list is not published on AIDA yet is reported in the status message.
 - **Personal bests**: PBs that are still empty in Compy are pre-filled
   from the athletes' AIDA profiles (locally entered PBs are never
   overwritten). If a profile cannot be fetched the sync continues and
   reports a warning. Note: as of August 2026 the documented profile
   endpoint answers 404 for every athlete of an event that has no start
   lists yet (whether it is not deployed or requires start lists is not
   distinguishable from the outside); the sync detects this after three
   attempts and reports a single warning instead of one per athlete. The
   pre-fill starts working automatically as soon as the endpoint answers.

### What the sync deliberately leaves alone

 - It never deletes anything: athletes or starts that exist only in Compy
   are listed in the status message but kept.
 - Locally entered data is never overwritten: official tops set in Compy
   (AIDA's official top is only taken while the OT is still unset), clubs,
   PBs and all results (RP, cards, penalties, remarks) stay as they are -
   results that are already on AIDA are not imported either.
 - Invalid entries from AIDA (missing UUID, unknown discipline, start of an
   unregistered diver) are skipped with a warning instead of failing the
   sync. Starts are matched to athletes by the athlete UUID carried in the
   row's `athleteProfileLink`; rows without it fall back to first name,
   last name and gender, compared case-insensitively (the registration
   list and the start list spell some names differently).

### Results upload

"Upload results to AIDA" posts the judged result of every start to AIDA
(`POST /events/startlists`, the only write the app ever makes; the key
needs **write** scope). AIDA only accepts a result for a row of its own
start list, so the upload first matches each local start to the AIDA start
list of the same day - by the AIDA start id stored by an earlier sync, else
by name, gender and discipline (competitions seeded from the excel file have
no AIDA ids). Starts that are not on the AIDA start list are listed and
skipped; if AIDA has no start list for the event at all, nothing can be
uploaded until it is created there. "Preview results upload" does the
matching and shows what would be sent without sending anything.

What is sent per start: RP (meters, STA in seconds; empty for a DNS), the
penalty card, the total penalty points and the judge remarks as AIDA status
codes (`ok` alone for a white card; `UNDER AP` and `NO TAG` are left out
because the AIDA server appends them itself). AIDA computes the points.
Uploading again overwrites, so corrections can simply be re-uploaded. A
refused write (no write scope, key of another event, finalised event) stops
the upload; a single rejected result is reported and the others still go
through.

### Not covered by the API

 - Judges and clubs are not exposed by the API and are managed in Compy.
 - The results excel file ("Store results") remains available as the
   fallback for submitting results.

### Records

Refreshing the national records uses the AIDA API when the competition has
an API key configured: national, continental and world records are fetched
for exactly the countries and disciplines present in the competition, and
the result list flags a white-card performance that beats a record with the
highest applicable tier (**WR** over **CR** over **NR**). An API refresh
only replaces the records of the countries it queried, so competitions
sharing one Compy database do not disturb each other's records. Without an
API key the records page of the AIDA website is scraped as before, which
provides national records only.

The excel workflow remains fully supported and is the fallback if the API or
the internet connection is unavailable during a competition.

## Prerequisites

 - git
 - python3
   - openpyxl
   - pandas
   - country_converter
   - flask

On Windows:
Install Weasyprint https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows (including the steps to install Msys and Pango)

## Installing the software

 - Navigate with a terminal (powershell on Windows) to the folder where you want to create the compy folder in
 - Execute `git clone https://github.com/Azrael3000/Compy.git`
 - Switch to the new folder: `cd Compy`
 - Set up the environmen: `cp .env_sample .env`
 - For deployments you MUST edit the .env file:
   - Provide a new secret (used to sign the admin session cookie). A new one can be generated e.g. by running
     `python3 -c "import secrets; print(secrets.token_hex())"`
   - Set your own admin password. Either change `FLASK_ADMIN_PASSWORD`, or (recommended) remove it and set
     `FLASK_ADMIN_PASSWORD_HASH` to a password hash generated by running
     `python3 -c "from werkzeug.security import generate_password_hash; import getpass; print(generate_password_hash(getpass.getpass()))"`
 - Start a virtual environment and install required packages:
   - Linux: `source venv/bin/activate && pip install -r requirements.txt`
 - Set up the database and run the server: `python3 compy.py --init_db`

## Running the software

 - Download the repository
 - Navigate with a terminal to the folder containing `compy.py`
 - Start a virtual environment:
   - Linux: `source venv/bin/activate`
 - Execute `compy.py`
   - Linux: `python3 compy.py`
   - Windows: `python3.exe compy.py`
 - Navigate your browser to `localhost:5000`
 - The admin interface is at `localhost:5000/admin`. It asks for the admin password configured in
   `.env` (`FLASK_ADMIN_PASSWORD` or `FLASK_ADMIN_PASSWORD_HASH`); a login is valid for 12 hours
   or until you press "Logout"

## Test data

A generator for a realistic sample competition (30 athletes, 3 days: CWT, STA, DYN,
results and cards for past days, DNS entries, open results for today) lives in
`tools/generate_test_data.py`:

 - `python3 tools/generate_test_data.py test_competition.xlsx`
 - Start the server and open the admin page
 - Set a competition name, save, choose the generated file and press "Refresh data"

Alternatively a pre-seeded `compy.sqlite` with the competition "Compy Test Open 2026"
(including `test_competition.xlsx`) may already be present, in which case you can simply
load it from "Load competition" on the Settings tab.

## Want to help?

As is clearly visible, this tool is lacking a nice user interface. If you want to help making one, please write me at hydros@TLD. (`TLD=posteo.net`). Other help (writing the backend, documentation, testing) is also welcome.
