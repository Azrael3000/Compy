*** Settings ***
Library         Collections
Documentation   Registration resources for compy

*** Variables ***
${REGISTRATION_TABLE}   id=registration_table

*** Keywords ***
Goto Registration
    Click   id=registration_button >> a
    Get Element States  ${REGISTRATION_TABLE}    contains    visible

Verify Athletes In Registration Table
    Goto Registration
    FOR     ${athlete_id}   IN RANGE    ${n_athletes}
        ${athlete} =    Get Athlete     ${athlete_id}
        ${tr} =     Get Element     ${REGISTRATION_TABLE} >> xpath=.//tr[.//td[text()='${athlete.ln}']]
        ${tds} =    Get Elements    ${tr} >> td
        ${fn} =     Get From List   ${tds}  1
        ${ln} =     Get From List   ${tds}  0
        ${gen} =    Get From List   ${tds}  2
        ${ctr} =    Get From List   ${tds}  3
        Get Text    ${fn}   ==  ${athlete.fn}
        Get Text    ${ln}   ==  ${athlete.ln}
        Get Text    ${gen}  ==  ${athlete.gen}
        Get Text    ${ctr}  ==  ${athlete.ctr}
    END
