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
 - Read-only sync of registrations and start lists from the AIDA International API
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
 - **Registration tab checkboxes**: "registered" (AIDA status approved),
   "paid" (payment receipt uploaded) and "medical checked" (medical
   certificate uploaded) are pre-filled from AIDA.
 - **Competition days**: the start and end date of the competition are set
   from AIDA's day list (rest days are skipped).
 - **Start lists**: one block per day and discipline with each start's
   lane and announced performance (STA converted to seconds). AIDA's start
   ids are stored so repeated syncs update the right entries.
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
 - Locally entered data is never overwritten: official tops (the API has no
   OT field, assign OTs in Compy as before), clubs, PBs and all results
   (RP, cards, penalties, remarks) stay as they are.
 - Invalid entries from AIDA (missing UUID, unknown discipline, start of an
   unregistered diver) are skipped with a warning instead of failing the
   sync. Note that AIDA start list entries carry no athlete UUID, so starts
   are matched to athletes by name and gender.

### Not covered by the API

 - Judges and clubs are not exposed by the API and are managed in Compy.
 - Results are still submitted to AIDA via the generated results excel file
   ("Store results"); there is no test environment on the AIDA side, so
   Compy does not write anything to the API.

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
 - node.js (v20 or newer, with npm) — to build the frontend

On Windows:
Install Weasyprint https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows (including the steps to install Msys and Pango)

## Installing the software

 - Navigate with a terminal (powershell on Windows) to the folder where you want to create the compy folder in
 - Execute `git clone https://github.com/Azrael3000/Compy.git`
 - Switch to the new folder: `cd Compy`
 - Set up the environmen: `cp .env_sample .env`
 - Enable the git hooks (auto-formats frontend code on commit): `git config core.hooksPath tools/git-hooks`
 - For deployments you MUST edit the .env file:
   - Provide a new secret (used to sign the admin session cookie). A new one can be generated e.g. by running
     `python3 -c "import secrets; print(secrets.token_hex())"`
   - Set your own admin password. Either change `FLASK_ADMIN_PASSWORD`, or (recommended) remove it and set
     `FLASK_ADMIN_PASSWORD_HASH` to a password hash generated by running
     `python3 -c "from werkzeug.security import generate_password_hash; import getpass; print(generate_password_hash(getpass.getpass()))"`
 - Start a virtual environment and install required packages:
   - Linux: `source venv/bin/activate && pip install -r requirements.txt`
 - Build the frontend: `npm --prefix frontend ci && npm --prefix frontend run build`
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

### Configuration precedence

`.env` supplies defaults; anything exported in the environment overrides it.
So a second instance can be run without touching the file:

```
FLASK_DATABASE=/tmp/scratch.sqlite python3 compy.py --init_db --port 5001
```

Note this is the opposite of how it behaved before: `.env` used to win over
the environment, which meant `FLASK_DATABASE=… python3 compy.py` silently did
nothing. If you have `FLASK_*` variables left over in a shell profile, they
now take effect where previously the file would have overridden them.

## Frontend development

The frontend is a React + TypeScript app (Vite, Tailwind CSS, shadcn/ui) in `frontend/`,
with one entry per screen (admin, judge, results, clock). Flask serves the built pages
from `frontend/dist` (see the `/app/` route in `compy_flask.py`), so a plain
`python3 compy.py` after `npm run build` is all a deployment needs.

For development with hot reload, a single command starts both servers:

 - `npm --prefix frontend run dev` (or `npm run dev` inside `frontend/`) — runs Flask on
   port 5000 and Vite on port 5173 (proxying API calls to 5000) together; Ctrl+C stops both.
   `npm run dev:vite` starts only Vite if Flask is already running elsewhere.
 - `COMPY_BACKEND_PORT=5001 npm --prefix frontend run dev` runs the pair against
   another port — the variable is passed to `compy.py --port` and used as the Vite
   proxy target, so a test instance can sit next to an already running server.

Then open e.g. `http://localhost:5173/app/admin.html`. The judge and clock pages take
their path parameters as query parameters in dev, e.g.
`/app/judge.html?comp_id=1&judge_id=2&hash=...` and
`/app/clock.html?comp_id=1&current=0&offset=0`.

## Code style

Frontend code (`frontend/src`) is auto-formatted by a pre-commit hook
(`tools/git-hooks/pre-commit`, enabled via `git config core.hooksPath tools/git-hooks`).
It runs ESLint and Prettier on the staged files:

 - every `if`/`else`/loop body gets braces on their own lines — `if (x) return;`
   is rewritten automatically to the braced multi-line form
 - nested ternary operators (a ternary inside a ternary) are rejected; a single
   ternary is fine. These cannot be fixed automatically — the commit is blocked
   and the reported lines have to be rewritten by hand (if/else or a lookup)

`npm --prefix frontend run lint` checks everything, `npm --prefix frontend run format`
applies the same fixes to the whole tree outside a commit.

### Vendored shadcn components

`frontend/src/components/ui/` holds components added with
`npx shadcn@latest add <name>`. `package.json` declares the unified
`radix-ui` package rather than the scoped `@radix-ui/react-*` packages, so
vendored components must import from `radix-ui`
(`import { Dialog as DialogPrimitive } from 'radix-ui'`), never from
`@radix-ui/react-*` — the scoped packages are present in `node_modules`
only as transitive dependencies of `radix-ui`, and importing them directly
resolves today purely because npm hoists a flat `node_modules`. After every
`add`, verify with:

    grep -rn "@radix-ui/" frontend/src/

which must return nothing.

`frontend/tsconfig.json` (the project-references root, which otherwise
compiles nothing — `files: []`) carries its own `compilerOptions.paths` for
`@/*`. That's not redundant with the identical mapping in
`tsconfig.app.json`: the shadcn CLI resolves the `@/components/ui` alias
via `tsconfig-paths`, which reads the root `tsconfig.json` directly and
does not follow `references` to find `paths` in a child config. Without
the duplicate mapping here, the CLI can't resolve the alias and writes
components to a literal `frontend/@/` directory instead of
`frontend/src/components/ui/`. Keep both in sync if the alias ever changes.

## Backend tests

Plain `unittest`, no extra dependencies, no server or database setup — each
test class builds its own sqlite database in a temporary directory:

 - `python3 -m unittest discover -p "*_test.py"` (the whole suite)
 - `python3 -m unittest compy_startlist_test` (one file)
 - `python3 -m unittest compy_startlist_test.TestBlockEndpointPayload` (one class)

Tests that need the full HTTP layer derive from `compy_testing.CompyServerTestCase`,
which runs the flask app on an embedded server. Nothing ever talks to the real
AIDA API; `compy_aida_test.py` uses a fake client.

Some of these are *response contract* tests. The admin page applies certain
responses as a reset — it clears every submenu and refills it from the response
alone — so an endpoint that omits one of the five datasets empties that menu
rather than leaving it alone. The frontend types cannot express that (the fields
are optional there), so `compy_testing.SUBMENU_KEYS` defines the contract and the
reset-carrying endpoints each assert it. If you add an endpoint whose response
the admin page resets from, add it there too.

## UI tests

The Robot Framework suites in `tests/` drive the real UI with the Browser (Playwright)
library. They need a **built** frontend and a running server whose admin password
matches `${ADMIN_PASSWORD}` in `tests/compy.resource`:

 - `pip install robotframework robotframework-browser && rfbrowser init`
 - `npm --prefix frontend run build`
 - start a server for the suite to drive, e.g. against a throwaway database:

   ```
   FLASK_DATABASE=/tmp/robot.sqlite FLASK_ADMIN_PASSWORD=compy-admin \
     python3 compy.py --init_db
   ```

 - `python3 -m robot tests/` (or a single suite, e.g. `tests/judge.robot`)

Point it at a throwaway database rather than your working `compy.sqlite`: the
suites create and delete competitions as they go.

One suite per screen: `admin.robot`, `judge.robot`, `results.robot`, `clock.robot`.
Every suite creates the competitions it needs and deletes them again, so the
suites can run against a development database.

`admin.robot` builds its fixtures by clicking through the admin UI, because the
admin UI is what it tests. The other three seed over HTTP instead
(`compy_seed.resource`) — hitting the same endpoints the admin page uses, via
Browser's `Http` keyword so the admin session cookie is reused. That keeps a
judge test from failing because the start list editor changed, and it returns
the numeric `comp_id` that the judge, results and clock urls all need.

`clock.robot` has one test tagged `slow`: the staleness banner needs three
failed polls at 10 s each, so it takes over half a minute. Skip it with
`--exclude slow`.

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
