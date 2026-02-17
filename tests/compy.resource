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
    Open Admin Page
    ${comp_id} =    Evaluate     str(uuid.uuid4())   uuid
    Fill Text   id=comp_name  ${comp_id}
    Press Keys  id=comp_name    Tab
    ${save_visible} =   Get Element States  id=save_comp    contains    visible
    Should Be True  ${save_visible}     Button with id save_comp is not visible
    Click   id=save_comp
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

Add Athlete
    [Arguments]     ${comp_id}
    Goto Athletes
    Fill Text   id=athlete_first_name  ${comp_id}_fn
    Fill Text   id=athlete_last_name  ${comp_id}_ln
    Fill Text   id=athlete_country  AUT
    Fill Text   id=athlete_club  ${comp_id}_cl
    Fill Text   id=athlete_aida_id  ${comp_id}_ai
    Click   id=add_athlete
    ${tr} =     Get Element     id=athletes_table >> xpath=.//tr[.//td[text()='${comp_id}_fn']]
    ${tds} =    Get Elements    ${tr} >> td
    ${fn} =     Get From List   ${tds}  0
    Get Text    ${fn}   ==  ${comp_id}_fn
    Get Text    id=total_athletes   ==  Total athletes: 1
