*** Settings ***
# Debug switch
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
# Elements
${SETTINGS_BUTTON}  id=settings_button >> a
${COMP_NAME_FIELD}  id=comp_name
${SAVE_COMP_BUTTON}     id=save_comp
${COMPETITION_LIST}     id=competition_list >> li

*** Keywords ***
Open Admin Page
# Debug enable
#    Open Browser
    New Page    ${ADMIN_URL}
    Get Text    h1    contains    Compy

Goto Settings
    Click   ${SETTINGS_BUTTON}
    ${settings_visible} =   Get Element States  id=settings    contains    visible
    Should Be True  ${settings_visible}     Settings page not visible

Create Competition
    Set Test Variable   ${n_athletes}   0
    Open Admin Page
    ${comp_id} =    Evaluate     str(uuid.uuid4())   uuid
    Fill Text   ${COMP_NAME_FIELD}  ${comp_id}
    Press Keys  ${COMP_NAME_FIELD}    Tab
    ${save_visible} =   Get Element States  ${SAVE_COMP_BUTTON}    contains    visible
    Should Be True  ${save_visible}     Save competition button is not visible
    Click   ${SAVE_COMP_BUTTON}
    Set Test Variable   ${comp_id}
    RETURN  ${comp_id}

Remove Competition
    [Arguments]     ${comp_id}
    Goto Settings
    ${comp_li} =    Get Element     ${COMPETITION_LIST} >> text=${comp_id}
    ${del_button} =     Get Element     ${comp_li} >> .delete_comp_button
    Click   ${del_button}

Load Competition
    [Arguments]     ${comp_id}
    Goto Settings
    ${comp_li} =    Get Element     ${COMPETITION_LIST} >> text=${comp_id}
    ${load_button} =     Get Element     ${comp_li} >> .load_comp_button
    Click   ${load_button}
    Get Text    ${COMP_NAME_FIELD}    ==  ${comp_id}
