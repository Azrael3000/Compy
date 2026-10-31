*** Settings ***
Resource    compy.resource
Resource    compy_seed.resource
Documentation   Venue clock display (frontend/src/pages/clock/ClockApp.tsx).
...
...             The clock runs unattended on a screen nobody is looking after,
...             so the cases that matter are the ones where it is wrong rather
...             than broken: showing another competition's starts because the
...             url was malformed, or showing an hour-old start list as if it
...             were current.
Suite Setup     Setup Clock Competition
Suite Teardown  Delete Seeded Competition   ${CLOCK_COMP_ID}

*** Variables ***
${CLOCK_COMP_ID}    ${NONE}
${CLOCK_COMP_NAME}  ${NONE}

*** Keywords ***
Setup Clock Competition
    Open Seed Session
    ${name} =   Unique Name     clock_suite
    ${comp_id} =    Seed Competition With Excel     ${name}
    Set Suite Variable  ${CLOCK_COMP_ID}    ${comp_id}
    Set Suite Variable  ${CLOCK_COMP_NAME}  ${name}

Open Clock
    [Arguments]     ${comp_id}  ${current}=0   ${offset}=0
    New Page    ${BASE_URL}/clock/${comp_id}/${current}/${offset}
    Wait For Elements State     id=clock_comp_name  visible     timeout=15s

*** Test Cases ***
Clock shows the competition it was asked for
    Open Clock  ${CLOCK_COMP_ID}
    Get Text    id=clock_comp_name  ==  ${CLOCK_COMP_NAME}

Clock shows the wall time
    Open Clock  ${CLOCK_COMP_ID}
    # toLocaleTimeString, e.g. "10:23:45 AM" or "10:23:45"
    Get Text    id=clock_time   matches     ^\\s*\\d{1,2}:\\d{2}:\\d{2}

Clock lists the starts of the block
    Open Clock  ${CLOCK_COMP_ID}
    Wait For Elements State     id=clock_starts     visible     timeout=15s
    Get Text    id=clock_starts_label   contains    starts:
    ${starts} =     Get Element Count   id=clock_starts >> div
    Should Be True  ${starts} > 0   clock shows no starts for a competition that has them

Malformed clock url is called out instead of guessed
    [Documentation]     A missing comp_id used to default to competition 1, so
    ...                 the venue screen confidently showed the wrong starts.
    New Page    ${BASE_URL}/app/clock.html
    Wait For Elements State     id=clock_invalid    visible     timeout=15s
    Get Text    id=clock_invalid    contains    Invalid clock URL
    Get Element Count   id=clock_comp_name  ==  0

Starts are marked stale when the backend goes quiet
    [Documentation]     The last good starts stay on screen (a venue display
    ...                 must not blank out on a blip) but are marked stale.
    ...                 Takes over 30s: the clock polls every 10s and needs
    ...                 three consecutive failures.
    [Tags]      slow
    Open Clock  ${CLOCK_COMP_ID}
    Wait For Elements State     id=clock_starts     visible     timeout=15s
    Set Offline     ${True}
    Wait For Elements State     id=clock_stale  visible     timeout=60s
    Get Text    id=clock_stale  contains    no connection
    # the starts are still there, just dimmed
    ${starts} =     Get Element Count   id=clock_starts >> div
    Should Be True  ${starts} > 0   stale clock dropped the starts instead of keeping them
    [Teardown]      Set Offline     ${False}
