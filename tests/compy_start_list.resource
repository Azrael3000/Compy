*** Settings ***
Library         Collections
Documentation   Athlete resources for compy

*** Variables ***
${START_LISTS_BUTTON}   id=start_lists_button >> a
${ADD_BLOCK_BUTTON}     id=sl_add_day
${ADD_BLOCK_DAY_FIELD}  id=sl_modify_block_day
${ADD_BLOCK_DISCIPLINE_PREFIX}  sl_modify_block_dis_
${OVERLAY_CANCEL_BUTTON}    id=overlay_cancel
${OVERLAY_BLOCK_SAVE_BUTTON}  id=sl_modify_block_save
${OVERLAY_BLOCK_REMOVE_BUTTON}  id=sl_modify_block_remove
${DAY_PREFIX}   sl_day_
${BLOCK_DISCIPLINE_CLASS}   sl_discipline_button
${EDIT_BLOCK_BUTTON_CLASS}  sl_edit_block

*** Keywords ***
Goto Start List
    Click   ${START_LISTS_BUTTON}
    Get Element States  ${ADD_BLOCK_BUTTON}    contains    visible

Create Block
    [Arguments]     @{disciplines}   ${day}
    Goto Start List
    Click   ${ADD_BLOCK_BUTTON}
    Fill Text   ${ADD_BLOCK_DAY_FIELD}  2000-01-01
    FOR     ${discipline}   IN  @{disciplines}
        Check Checkbox      id=${ADD_BLOCK_DISCIPLINE_PREFIX}${discipline}
    END
    Click   ${OVERLAY_BLOCK_SAVE_BUTTON}
    Get Element States  id=${DAY_PREFIX}${day}  contains    visible
    Click   id=${DAY_PREFIX}${day}
    ${disciplinesString} =  Catenate    SEPARATOR=,${SPACE}   @{disciplines}
    Get Element States  xpath=//a[@class='${BLOCK_DISCIPLINE_CLASS}' and text()='${disciplinesString}']     contains    visible

Remove Block
    [Arguments]     @{disciplines}   ${day}
    Goto Start List
    Click   id=${DAY_PREFIX}${day}
    ${disciplinesString} =  Catenate    SEPARATOR=,${SPACE}   @{disciplines}
    Click   xpath=//a[@class='${BLOCK_DISCIPLINE_CLASS}' and text()='${disciplinesString}']
    Click   xpath=//button[@class='${EDIT_BLOCK_BUTTON_CLASS}' and text()='Edit block']
    ${promise} =    Promise To  Wait For Response   matcher=**/block    timeout=10s
    Click   ${OVERLAY_BLOCK_REMOVE_BUTTON}
    Wait For    ${promise}
    ${day_count} =    Get Element Count     id=${DAY_PREFIX}${day}
    IF  ${day_count} > 0
        Click   id=${DAY_PREFIX}${day}
        Get Element Count  xpath=//a[@class='${BLOCK_DISCIPLINE_CLASS}' and text()='${disciplinesString}']     ==  0
    END

Click Add Block And Cancel Overlay
    Click   ${ADD_BLOCK_BUTTON}
    Click   ${OVERLAY_CANCEL_BUTTON}
