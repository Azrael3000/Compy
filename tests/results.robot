*** Settings ***
Resource    compy.resource
Resource    compy_seed.resource
Documentation   Public results page (frontend/src/pages/results/ResultsApp.tsx).
...
...             This is the only screen the public ever sees, and the thing it
...             must never do is show results that were not released yet. The
...             publish flag is therefore checked from the outside here, on the
...             page itself, not only in the backend unit tests.
Suite Setup     Setup Results Competitions
Suite Teardown  Teardown Results Competitions

*** Variables ***
${PUBLISHED_COMP_ID}    ${NONE}
${UNPUBLISHED_COMP_ID}  ${NONE}
${PUBLISHED_NAME}       ${NONE}
${UNPUBLISHED_NAME}     ${NONE}

*** Keywords ***
Setup Results Competitions
    Open Seed Session
    ${published_name} =     Unique Name     results_published
    ${published} =      Seed Competition With Excel      ${published_name}
    Publish Results     ${published}
    Set Suite Variable  ${PUBLISHED_COMP_ID}    ${published}
    Set Suite Variable  ${PUBLISHED_NAME}   ${published_name}
    ${unpublished_name} =   Unique Name     results_unpublished
    ${unpublished} =    Seed Competition With Excel      ${unpublished_name}
    Set Suite Variable  ${UNPUBLISHED_COMP_ID}  ${unpublished}
    Set Suite Variable  ${UNPUBLISHED_NAME}     ${unpublished_name}

Teardown Results Competitions
    Delete Seeded Competition   ${PUBLISHED_COMP_ID}
    Delete Seeded Competition   ${UNPUBLISHED_COMP_ID}

Open Results
    [Arguments]     ${query}=${EMPTY}
    New Page    ${BASE_URL}/results${query}
    Wait For Elements State     id=compy_title  visible     timeout=15s

Show Discipline
    [Documentation]     Picks a discipline by name rather than by menu index:
    ...                 the index of a discipline depends on how many rankings
    ...                 precede it, which is not what these tests are about.
    [Arguments]     ${name}
    Wait For Elements State     id=list_0   visible     timeout=15s
    Click   xpath=//button[contains(@class,'list_menu') and contains(@class,'discipline') and text()='${name}']
    Wait For Elements State     id=main_0   visible     timeout=15s

*** Test Cases ***
Published competition shows its discipline menu
    Open Results    ?comp_id=${PUBLISHED_COMP_ID}
    Get Text    id=title    ==  ${PUBLISHED_NAME}
    Wait For Elements State     id=list_0   visible     timeout=15s
    ${disciplines} =    Get Element Count   css=.list_menu.discipline
    Should Be True  ${disciplines} > 0  published competition offers no disciplines

Picking a discipline shows the ranking
    Open Results    ?comp_id=${PUBLISHED_COMP_ID}
    Wait For Elements State     id=list_0   visible     timeout=15s
    Click   id=list_0
    Wait For Elements State     id=main_0   visible     timeout=15s
    # header cells double as the menu buttons once a result is shown
    Get Element States  id=discipline   contains    visible
    Get Element States  id=gender   contains    visible
    Get Element States  id=country  contains    visible
    ${rows} =   Get Element Count   css=tr.toggle.first
    Should Be True  ${rows} > 0     ranking is empty for a discipline that has results

A discipline result expands to its card and penalty
    [Documentation]     A row for a single discipline expands into the
    ...                 Nat./Card/AP and Penalty/Remarks/Points pair of rows.
    Open Results    ?comp_id=${PUBLISHED_COMP_ID}
    Show Discipline     STA
    Get Element Count   id=sub1_0   ==  0
    Click   id=main_0
    Wait For Elements State     id=sub1_0   visible     timeout=15s
    Get Text    id=sub1_0   contains    Nat.
    Get Text    id=sub1_0   contains    Card
    Get Text    id=sub2_0   contains    Penalty
    Get Text    id=sub2_0   contains    Points

An aggregate ranking expands to its individual disciplines
    [Documentation]     The payload decides the sub-row layout, not the name:
    ...                 a ranking carrying individual_results expands into one
    ...                 row per discipline instead of the card/penalty pair.
    Open Results    ?comp_id=${PUBLISHED_COMP_ID}
    Show Discipline     Overall
    Click   id=main_0
    Wait For Elements State     id=sub0_0   visible     timeout=15s
    ${subs} =   Get Element Count   css=tr.sub_0
    Should Be True  ${subs} > 1     aggregate row did not expand into its disciplines
    Get Text    id=sub0_0   not contains    Nat.

Without a comp_id the published competitions are listed
    Open Results
    Wait For Elements State     id=comp_${PUBLISHED_COMP_ID}    visible     timeout=15s
    Get Text    id=comp_${PUBLISHED_COMP_ID}    ==  ${PUBLISHED_NAME}

An unpublished competition is not readable
    [Documentation]     Asking for an unpublished competition by id must fail
    ...                 rather than serve its results, and must say so instead
    ...                 of rendering an empty page.
    Open Results    ?comp_id=${UNPUBLISHED_COMP_ID}
    Wait For Elements State     id=results_error    visible     timeout=15s
    Get Text    id=results_error    contains    Failed to load results
    Get Element Count   id=list_0   ==  0

An unpublished competition is not offered in the list
    Open Results
    Wait For Elements State     id=comp_${PUBLISHED_COMP_ID}    visible     timeout=15s
    Get Element Count   id=comp_${UNPUBLISHED_COMP_ID}  ==  0
