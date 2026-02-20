*** Settings ***
Resource    compy.resource

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
    #Remove Competition  ${comp_id}
