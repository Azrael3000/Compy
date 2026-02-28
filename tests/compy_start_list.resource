*** Settings ***
Library         Collections
Documentation   Athlete resources for compy

*** Variables ***
${START_LISTS_BUTTON}   id=start_lists_button >> a
${ADD_BLOCK_BUTTON}     id=sl_add_day
${OVERLAY_CANCEL_BUTTON}    id=overlay_cancel

*** Keywords ***
Goto Start List
    Click   ${START_LISTS_BUTTON}
    ${add_block_visible} =   Get Element States  ${ADD_BLOCK_BUTTON}    contains    visible
    Should Be True  ${add_block_visible}     Add block button is not visible

Create Block Today
    [Arguments]     ${discipline}
    Goto Start List
    Click   ${ADD_BLOCK_BUTTON}

Cancel Overlay
    Click   ${OVERLAY_CANCEL_BUTTON}
