*** Settings ***
Resource    compy.resource
Resource    compy_athlete.resource
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
