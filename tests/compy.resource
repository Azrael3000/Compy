*** Settings ***
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
    New Page    ${ADMIN_URL}
    Get Text    h1    contains    Compy

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
    ${comp_li} =    Get Element     id=competition_list >> li >> text=${comp_id}
    ${del_button} =     Get Element     ${comp_li} >> .delete_comp_button
    Click   ${del_button}
