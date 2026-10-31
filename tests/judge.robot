*** Settings ***
Resource    compy.resource
Resource    compy_seed.resource
Documentation   Judge wizard (frontend/src/pages/judge/JudgeApp.tsx).
...
...             The judge phone is where a swallowed failure costs most: a
...             tapped "Save" that quietly does nothing loses a result that
...             nobody will notice is missing until the ranking is wrong. The
...             happy path and the failed save are therefore both covered.
Suite Setup     Setup Judge Competition
Suite Teardown  Delete Seeded Competition   ${JUDGE_COMP_ID}

*** Variables ***
${JUDGE_COMP_ID}    ${NONE}
${JUDGE_COMP_NAME}  ${NONE}
${JUDGE_HASH}       ${NONE}
${JUDGE_ID}         ${NONE}

*** Keywords ***
Setup Judge Competition
    Open Seed Session
    ${name} =   Unique Name     judge_suite
    ${comp_id} =    Seed Competition With Excel     ${name}
    Set Suite Variable  ${JUDGE_COMP_ID}    ${comp_id}
    Set Suite Variable  ${JUDGE_COMP_NAME}  ${name}
    ${judge} =      Seed Judge  ${comp_id}
    Set Suite Variable  ${JUDGE_ID}     ${judge}[id]
    Set Suite Variable  ${JUDGE_HASH}   ${judge}[hash]

Open Judge Page
    [Arguments]     ${hash}=${JUDGE_HASH}   ${judge_id}=${JUDGE_ID}
    New Page    ${BASE_URL}/judge/${JUDGE_COMP_ID}/${judge_id}?hash=${hash}

Open A Lane
    [Documentation]     Walks day -> block -> lane by class rather than by id:
    ...                 the ids carry database keys the test cannot know.
    ...                 Uses the last day, which the fixture leaves open (no
    ...                 results entered), so a result can be set here.
    Open Judge Page
    Wait For Elements State     css=.day_menu >> nth=-1     visible     timeout=15s
    Click   css=.day_menu >> nth=-1
    Wait For Elements State     css=.block_menu >> nth=0    visible     timeout=15s
    Click   css=.block_menu >> nth=0
    Wait For Elements State     css=.lane_menu >> nth=0     visible     timeout=15s
    Click   css=.lane_menu >> nth=0
    Wait For Elements State     css=.athlete_menu >> nth=0  visible     timeout=15s

Open Athlete
    [Documentation]     An athlete with no result yet opens straight in the
    ...                 entry mask, not on the overview: the judge came here
    ...                 to enter a result, not to read one.
    [Arguments]     ${index}=0
    Open A Lane
    Click   css=.athlete_menu >> nth=${index}
    Wait For Elements State     id=result_entry     visible     timeout=15s

Accept White Card
    [Documentation]     Walks the entry mask from the pre-filled RP to a white
    ...                 card and back to the overview. The RP is left at the
    ...                 AP the mask pre-fills: anything lower counts as under
    ...                 AP, and AIDA then stops offering the white card.
    ...                 Picking the card is also what marks the result edited,
    ...                 which is what makes Save appear.
    Click   id=next
    Wait For Elements State     id=card_entry   visible     timeout=15s
    Click   id=card_white
    Click   id=ok
    Wait For Elements State     id=save     visible     timeout=15s

*** Test Cases ***
An invalid judge hash is refused
    [Documentation]     The judge endpoints answer with the json envelope, so
    ...                 the page has to render the 404 itself.
    Open Judge Page     hash=not-a-real-hash
    Wait For Elements State     id=judge_not_found  visible     timeout=15s
    Get Text    id=judge_not_found  contains    404
    Get Element Count   css=.day_menu   ==  0

A judge with a valid hash sees the competition
    Open Judge Page
    Wait For Elements State     id=competition  visible     timeout=15s
    Get Text    id=competition  contains    ${JUDGE_COMP_NAME}
    Get Text    id=judge_name   contains    Judy

A judge can walk down to the athletes of a lane
    Open A Lane
    ${athletes} =   Get Element Count   css=.athlete_menu
    Should Be True  ${athletes} > 0     lane shows no athletes

An athlete without a result opens in the entry mask
    [Documentation]     And the realized performance is pre-filled with the
    ...                 announced performance, which is the value a judge
    ...                 confirms most often.
    Open Athlete
    ${ap} =     Get Text    id=info_AP >> css=.info
    Get Text    id=info_name >> css=.info   !=  ${EMPTY}
    Get Property    id=rp_input     value   ==  ${ap}
    Get Element Count   id=result_info  ==  0

Cancelling the entry mask shows the overview
    Open Athlete
    Click   id=cancel
    Wait For Elements State     id=result_info  visible     timeout=15s
    Get Element States  id=info_ot  contains    visible
    Get Element States  id=info_dis     contains    visible
    Get Element States  id=info_card    contains    visible

A recorded white card result is stored
    [Documentation]     Saves a result and reopens the athlete, so a save that
    ...                 only updates the screen would still fail here: an
    ...                 athlete whose RP is set comes back on the overview
    ...                 rather than in the entry mask.
    Open Athlete
    ${ap} =     Get Text    id=info_AP >> css=.info
    Accept White Card
    Click   id=save
    Wait For Elements State     id=result_info  visible     timeout=15s
    Get Text    id=card_title   ==  WHITE
    Get Text    id=info_RP >> css=.info     ==  ${ap}
    # reopened from the server, not from the screen it was just saved on
    Open A Lane
    Click   css=.athlete_menu >> nth=0
    Wait For Elements State     id=result_info  visible     timeout=15s
    Get Text    id=card_title   ==  WHITE
    Get Text    id=info_RP >> css=.info     ==  ${ap}

A failed save is reported instead of swallowed
    [Documentation]     The old app ignored request failures here, so a judge
    ...                 on a flaky phone could tap Save and lose the result
    ...                 without any sign that anything went wrong. Uses a
    ...                 different athlete than the save test so the two do not
    ...                 depend on each other's order.
    Open Athlete    index=1
    Accept White Card
    Set Offline     ${True}
    Click   id=save
    Wait For Elements State     id=error_banner     visible     timeout=15s
    Get Text    id=error_banner     !=  ${EMPTY}
    # still on the overview with Save offered, so the judge can retry
    Get Element States  id=save     contains    visible
    [Teardown]      Set Offline     ${False}
