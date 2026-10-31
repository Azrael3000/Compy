# Known issues

Open items after the React migration (branch `reactRefactor`). Most were
found by a post-migration code review; the critical and major
data-integrity findings from that review are already fixed — what remains
is listed here, roughly by impact. File references point at the current
code.

The Robustness, Behavior-drift, Correctness and Cleanup sections have
since been worked through, as have the three small items that were found
outside the migration review and the UI test coverage gap (there is now a
Robot suite per screen; see "UI tests" in the Readme). shadcn/ui has been
adopted on the admin screen. What is left are the larger follow-ups plus
the items the shadcn work deliberately left open.

## Larger follow-ups

- [ ] **The pre-commit hook only formats the TypeScript frontend.** The
  Python backend has no automated formatting/lint gate.
- [ ] **The Robot suites use their own server harness.**
  `tests/` needs a server whose admin password matches `${ADMIN_PASSWORD}`
  and whose database is disposable, and it currently gets one by building
  the app directly through `compy_testing.makeApp` rather than running
  `compy.py`. Now that exported `FLASK_*` variables override `.env`, that
  workaround is no longer forced — `FLASK_DATABASE=… FLASK_ADMIN_PASSWORD=…
  python3 compy.py` works — so the harness could be replaced by a
  documented command. Low priority; the harness is not wrong, just
  redundant.

## Response contract tests

Endpoints whose response the admin page applies as a reset
(`applyResponse(data, true)`) must carry all five submenu datasets, because
the reset clears them first and refills from the response alone. An endpoint
that omits one therefore empties that menu rather than leaving it alone.
`compy_testing.SUBMENU_KEYS` defines the contract in one place; the seven
reset-carrying responses each have a test: `start_list` (PUT), `block`
(POST/PATCH/DELETE), `load_comp`, `upload_file`,
`change_special_ranking_name` and `aida/sync`.

Endpoints whose response is merged rather than reset are deliberately not
covered — a dataset they omit is simply left as it was. Any of them that
later switches to a reset inherits the contract and needs a test.

**Why this is a test and not a type.** An OpenAPI spec with generated
TypeScript types was the original plan here. It was dropped after checking
the premise: every declared shape (`Athlete`, `Competition`, `Judge`,
`Blocks`, `StartEntry` and the endpoint envelopes) was compared against
live responses and none had drifted. More decisively, generated types would
not have caught either contract bug this project has actually had
(`updateStartList`, `modifyBlock`) — those fields are declared optional, so
a response omitting them type-checks identically to one carrying them. The
requirement is "present, because of what the caller does with the
response", which is a fact about the consumer and not expressible in the
field's type at all. Hand-maintaining `contracts.ts` remains a small cost,
but with one client, in this repo, type-checked in the same build, a schema
toolchain buys documentation rather than safety. Revisit if a second or
external API consumer ever appears.

## shadcn/ui: adopted on the admin screen, open elsewhere

`frontend/src/components/ui/` now holds `dialog`, `tabs` and `button`. The
admin overlay is a Radix Dialog (focus trap, Escape, focus restore,
accessible name), the tab bar is a real `tablist` with arrow-key
navigation, and the admin's buttons go through a `Button` whose cva
variants replaced the element-level CSS. See "Vendored shadcn components"
in the Readme for the import convention.

What that work deliberately did not do:

- [ ] **The judge, results and clock screens keep their native elements.**
  The clock has no interactive elements at all, the judge is a
  viewport-scaled phone wizard that deliberately hijacks `Tab`, and results
  is read-only — shadcn buys little on any of them and carries the most
  risk on the screen that records competition results.
- [ ] **~26 inputs have no associated `htmlFor` label.** A real
  accessibility gap, deferred because nothing drove it: no conformance
  requirement and no known assistive-technology user.
- [ ] **Vendored components carry stock styling this app never uses** —
  `tabs.tsx`'s `line` variant, vertical orientation and dark-mode block,
  for instance — which `admin.css` then partly overrides by id
  specificity. That is the normal cost of vendoring, but it means a style
  question now has two places to look.
- [ ] **The countdown remote's keydown gating has no executable test.**
  `AdminApp.tsx` makes the `'o'` key inert while a dialog is open; that is
  verified by reading the guard, not by a test, because no WebAudio
  harness exists to drive a countdown cycle.

## Decided, not bugs

Two "behavior drift vs. the old app" items were confirmed against the
pre-migration sources (`git show e3f37bd^:static/judge.js`) and
deliberately kept as they are:

- **Judge, `UNDER AP` auto-select with a RED card.** The old
  `showRemarks()` highlighted `UNDER AP` whenever `getJudgePenaltyUnder(false)`
  was non-null, and that helper hard-codes `card = 'YELLOW'`, so the old
  auto-select ignored the real card — and `getRemarksForCard('RED', …)`
  merges the YELLOW and RED sets, so it really did fire on RED cards. The
  port restricts it to YELLOW: a RED card is a disqualification, on which
  an under-AP *penalty* is meaningless. (`JudgeApp.tsx` `enterStep('remarks')`)
- **Judge, clicking the Penalty field on the overview.** Old
  `navAction('info_penalty')` called `showPenalty(false)`, which for a
  valid non-YELLOW card silently set the penalty to 0 and jumped back to
  the Remarks step. The port shows a disabled penalty input instead,
  which explains why the field cannot be edited rather than bouncing the
  judge somewhere they did not ask to go. (`JudgeApp.tsx` `navAction`)
