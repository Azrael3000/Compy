*** Settings ***
Resource    compy.resource
Resource    compy_athlete.resource
Resource    compy_registration.resource
Resource    compy_start_list.resource

*** Test Cases ***
Title on admin page
    Open Admin Page

Create and remove competition
    ${comp_id} =    Create Competition
    Remove Competition  ${comp_id}

Load competition
    ${c1} =     Create Competition
    ${c2} =     Create Competition
    Load Competition    ${c1}
    Remove Competition  ${c2}
    Remove Competition  ${c1}

Create and remove athletes
    ${comp_id} =    Create Competition
    Add Athlete
    Remove Athlete  0
    Remove Competition  ${comp_id}

Start creating block and cancel
    ${comp_id} =    Create Competition
    Goto Start List
    Click Add Block And Cancel Overlay
    Remove Competition  ${comp_id}

Create block and remove
    ${comp_id} =    Create Competition
    @{sta} =    Create List     STA
    @{dnf} =    Create List     DNF
    @{dnf_dyn} =    Create List     DNF     DYN
    Create Block    @{sta}  day=2000-01-01
    Remove Block    @{sta}  day=2000-01-01
    Create Block    @{sta}  day=2000-01-01
    Create Block    @{dnf}  day=2000-01-01
    Create Block    @{dnf_dyn}  day=2000-01-01
    Remove Block    @{sta}  day=2000-01-01
    Remove Block    @{dnf_dyn}  day=2000-01-01
    Remove Block    @{dnf}  day=2000-01-01
    Remove Competition  ${comp_id}

Test registration
    ${comp_id} =    Create Competition
    Add Athlete
    Add Athlete
    Verify Athletes In Registration Table
    Remove Athlete  0
    Remove Athlete  1
    Remove Competition  ${comp_id}

Escape closes the overlay
    [Documentation]     The hand-rolled overlay ignored the keyboard, so a
    ...                 dialog opened by mistake could only be dismissed by
    ...                 finding the Cancel button.
    ${comp_id} =    Create Competition
    Goto Start List
    Click   ${ADD_BLOCK_BUTTON}
    Wait For Elements State     id=overlay_box  visible     timeout=10s
    Keyboard Key    press   Escape
    Wait For Elements State     id=overlay_box  detached    timeout=10s
    Remove Competition  ${comp_id}

Closing the overlay returns focus to the button that opened it
    [Documentation]     Focus fell back to the document body before, so a
    ...                 keyboard user lost their place every time a dialog
    ...                 closed.
    ${comp_id} =    Create Competition
    Goto Start List
    Click   ${ADD_BLOCK_BUTTON}
    Wait For Elements State     id=overlay_box  visible     timeout=10s
    Keyboard Key    press   Escape
    Wait For Elements State     id=overlay_box  detached    timeout=10s
    Wait For Elements State     ${ADD_BLOCK_BUTTON}     focused     timeout=10s
    Remove Competition  ${comp_id}

The overlay is announced as a dialog
    ${comp_id} =    Create Competition
    Goto Start List
    Click   ${ADD_BLOCK_BUTTON}
    Wait For Elements State     id=overlay_box  visible     timeout=10s
    ${role} =   Get Attribute   id=overlay_box  role
    Should Be Equal     ${role}     dialog
    Click   ${OVERLAY_CANCEL_BUTTON}
    Remove Competition  ${comp_id}

The tab bar is announced as a tablist
    Open Admin Page
    ${role} =   Get Attribute   id=main_nav     role
    Should Be Equal     ${role}     tablist
    ${selected} =   Get Attribute   id=settings_button  aria-selected
    Should Be Equal     ${selected}     true

Arrow keys move between tabs
    [Documentation]     The tab bar was a table of links, so a keyboard user
    ...                 had to tab through every one of them.
    Open Admin Page
    Click   id=settings_button
    Keyboard Key    press   ArrowRight
    Get Attribute   id=judges_button    aria-selected    ==    true
    Get Attribute   id=settings_button  aria-selected    ==    false

A tab keeps its state while another tab is shown
    [Documentation]     All panels stay mounted (forceMount), so a selected
    ...                 day survives a detour to another tab.
    ${comp_id} =    Create Competition
    @{sta} =    Create List     STA
    Create Block    @{sta}  day=2000-01-01
    Goto Start List
    Click   id=${DAY_PREFIX}2000-01-01
    Goto Athletes
    Goto Start List
    ${visible} =    Get Element States  xpath=//a[contains(@class,'${BLOCK_DISCIPLINE_CLASS}') and text()='STA']    contains    visible
    Should Be True  ${visible}  the start list tab lost its selected day
    Remove Block    @{sta}  day=2000-01-01
    Remove Competition  ${comp_id}

An inactive tab is not shown
    [Documentation]     forceMount keeps every panel mounted so a tab's local
    ...                 state survives a switch, but a mounted panel must still
    ...                 be hidden when it is not the active one. Radix ties its
    ...                 own hidden attribute to presence, not selection, so the
    ...                 hidden prop is passed explicitly.
    Open Admin Page
    Goto Settings
    Wait For Elements State     id=settings     visible     timeout=10s
    Wait For Elements State     id=athletes     hidden      timeout=10s
    Goto Athletes
    Wait For Elements State     id=athletes     visible     timeout=10s
    Wait For Elements State     id=settings     hidden      timeout=10s

The nav card holds the links without making them tabs
    [Documentation]     Clock and Logout share the nav card with the tabs, so
    ...                 the tempting tidy-up is to move them into the tablist.
    ...                 A tablist's children have to be tabs, and a screen
    ...                 reader would then announce Logout as one - which is why
    ...                 the card chrome is on the row and not on the tablist.
    Open Admin Page
    ${children} =   Get Element Count   css=#main_nav > *
    ${tabs} =       Get Element Count   css=#main_nav > [role="tab"]
    Should Be Equal As Integers     ${children}     ${tabs}
    ...     the tablist holds a child that is not a tab
    Get Element Count   css=#main_nav #clock_button     ==      ${0}
    Get Element Count   css=#main_nav #logout_button    ==      ${0}
    # they are still in the same card, which is the point of the layout
    Get Element Count   css=#main_nav_row #clock_button     ==      ${1}
    Get Element Count   css=#main_nav_row #logout_button    ==      ${1}

The judge QR code has a text alternative
    [Documentation]     The code is wrapped in a link to the judge page, so
    ...                 without alt text that link has no accessible name at
    ...                 all - a screen reader announces the destination as the
    ...                 raw data url.
    ${comp_id} =    Create Competition
    Click   id=judges_button
    Wait For Elements State     id=judges   visible     timeout=10s
    Fill Text   id=judge_first_name     Ada
    Fill Text   id=judge_last_name      Lovelace
    Click   id=add_judge
    Click   css=#judges_table [id^="show_judge_"]
    Wait For Elements State     id=overlay_box  visible     timeout=10s
    Get Attribute   css=#overlay_box img    alt     ==      QR code for Ada Lovelace
    Click   ${OVERLAY_CANCEL_BUTTON}
    Remove Competition  ${comp_id}

Opening the overlay leaves the page underneath it alone
    [Documentation]     Radix locks scrolling by moving the body's computed
    ...                 margins onto its padding, which assumes the body is a
    ...                 full-width scroll container. When the body itself
    ...                 carried the page's max-width the conversion resized the
    ...                 content instead of just offsetting it, so every dialog
    ...                 made the page jump.
    ${comp_id} =    Create Competition
    Goto Start List
    ${before} =     Get BoundingBox     h1  ALL
    Click   ${ADD_BLOCK_BUTTON}
    Wait For Elements State     id=overlay_box  visible     timeout=10s
    # the lock attribute is set in an effect, so the geometry is only settled
    # once it is on the body - measuring before that would pass either way
    Wait For Elements State     css=body[data-scroll-locked]    attached     timeout=10s
    ${after} =      Get BoundingBox     h1  ALL
    Should Be Equal     ${before}[x]        ${after}[x]         the page moved sideways when the overlay opened
    Should Be Equal     ${before}[width]    ${after}[width]     the page was resized when the overlay opened
    Click   ${OVERLAY_CANCEL_BUTTON}
    Remove Competition  ${comp_id}

The overlay has an accessible name
    [Documentation]     Radix names a dialog by pointing aria-labelledby at its
    ...                 DialogTitle. Without one the dialog is announced only as
    ...                 "dialog", which is why every overlay's heading is a real
    ...                 title rather than loose text.
    ${comp_id} =    Create Competition
    Goto Start List
    Click   ${ADD_BLOCK_BUTTON}
    Wait For Elements State     id=overlay_box  visible     timeout=10s
    ${labelledby} =     Get Attribute   id=overlay_box  aria-labelledby
    Should Not Be Empty     ${labelledby}   the dialog has no accessible name
    Get Text    id=${labelledby}   ==  Add block
    Click   ${OVERLAY_CANCEL_BUTTON}
    Remove Competition  ${comp_id}
