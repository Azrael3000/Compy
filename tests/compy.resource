*** Settings ***
# Debug enable
#Library         Browser  auto_closing_level=KEEP
Library         Browser
Library         Collections
Documentation   Main compy resources

*** Variables ***
${URL}      localhost
${PORT}     5000
${PATH}     .
${BASE_URL}     http://${URL}:${PORT}/${PATH}
${ADMIN_KEY}    156a7f#
${ADMIN_URL}    ${BASE_URL}/admin?auth=${ADMIN_KEY}

*** Keywords ***
Open Admin Page
# Debug enable
#    Open Browser
    New Page    ${ADMIN_URL}
    Get Text    h1    contains    Compy

Goto Settings
    Click   id=settings_button >> a
    ${settings_visible} =   Get Element States  id=settings    contains    visible
    Should Be True  ${settings_visible}     Settings page not visible

Goto Athletes
    Click   id=athletes_button >> a
    ${table_visible} =   Get Element States  id=athletes_table    contains    visible
    Should Be True  ${table_visible}     Athletes table not visible

Create Competition
    Set Test Variable   ${n_athletes}   0
    Open Admin Page
    ${comp_id} =    Evaluate     str(uuid.uuid4())   uuid
    Fill Text   id=comp_name  ${comp_id}
    Press Keys  id=comp_name    Tab
    ${save_visible} =   Get Element States  id=save_comp    contains    visible
    Should Be True  ${save_visible}     Button with id save_comp is not visible
    Click   id=save_comp
    Set Test Variable   ${comp_id}
    RETURN  ${comp_id}

Remove Competition
    [Arguments]     ${comp_id}
    Goto Settings
    ${comp_li} =    Get Element     id=competition_list >> li >> text=${comp_id}
    ${del_button} =     Get Element     ${comp_li} >> .delete_comp_button
    Click   ${del_button}

Load Competition
    [Arguments]     ${comp_id}
    Goto Settings
    ${comp_li} =    Get Element     id=competition_list >> li >> text=${comp_id}
    ${load_button} =     Get Element     ${comp_li} >> .load_comp_button
    Click   ${load_button}
    Get Text    id=comp_name    ==  ${comp_id}

Get Athlete Country
    [Arguments]     ${athlete_id}
    ${is_aut} =     Evaluate    (${n_athletes} // 2) % 2 == 0
    IF  ${is_aut}
        RETURN  AUT
    ELSE
        RETURN  GER
    END

Get Athlete Gender
    [Arguments]     ${athlete_id}
    ${is_female} =     Evaluate    ${n_athletes} % 2 == 0
    IF  ${is_female}
        RETURN  F
    ELSE
        RETURN  M
    END

Get Athlete
    [Arguments]     ${athlete_id}
    ${fn} =  Set Variable   ${comp_id}_${athlete_id}_fn
    ${ln} =  Set Variable   ${comp_id}_${athlete_id}_ln
    ${gen} =  Get Athlete Gender  ${athlete_id}
    ${ctr} =  Get Athlete Country    ${athlete_id}
    ${clb} =  Set Variable  ${comp_id}_${athlete_id}_cl
    ${aid} =  Set Variable  ${comp_id}_${athlete_id}_ai
    ${athlete} =    Create Dictionary   fn=${fn}  ln=${ln}  gen=${gen}  ctr=${ctr}  clb=${clb}  aid=${aid}
    RETURN  ${athlete}

Add Athlete
    Goto Athletes
    ${athlete} =    Get Athlete     0
    Fill Text   id=athlete_first_name  ${athlete.fn}
    Fill Text   id=athlete_last_name  ${athlete.ln}
    Select Options By   id=athlete_gender   text    ${athlete.gen}
    Fill Text   id=athlete_country  ${athlete.ctr}
    Fill Text   id=athlete_club  ${athlete.clb}
    Fill Text   id=athlete_aida_id  ${athlete.aid}
    Click   id=add_athlete
    ${tr} =     Get Element     id=athletes_table >> xpath=.//tr[.//td[text()='${athlete.fn}']]
    ${tds} =    Get Elements    ${tr} >> td
    ${fn} =     Get From List   ${tds}  0
    ${ln} =     Get From List   ${tds}  1
    ${gen} =    Get From List   ${tds}  2
    ${ctr} =    Get From List   ${tds}  3
    ${clb} =    Get From List   ${tds}  4
    ${aid} =    Get From List   ${tds}  5
    Get Text    ${fn}   ==  ${athlete.fn}
    Get Text    ${ln}   ==  ${athlete.ln}
    Get Text    ${gen}  ==  ${athlete.gen}
    Get Text    ${ctr}  ==  ${athlete.ctr}
    Get Text    ${clb}  ==  ${athlete.clb}
    Get Text    ${aid}  ==  ${athlete.aid}
    Set Test Variable   ${n_athletes}   ${${n_athletes} + 1}
    Get Text    id=total_athletes   ==  Total athletes: ${n_athletes}

Remove Athlete
    [Arguments]     ${athlete_id}
    Goto Athletes
    ${athlete} =    Get Athlete     ${athlete_id}
    ${tr} =     Get Element     id=athletes_table >> xpath=.//tr[.//td[text()='${athlete.fn}']]
    ${btn} =    Get Element     ${tr} >> .delete
    Click   ${btn}
    Set Test Variable   ${n_athletes}   ${${n_athletes} - 1}
    Get Text    id=total_athletes   ==  Total athletes: ${n_athletes}
