*** Settings ***
Library     Browser
Resource    compy.resource

*** Test Cases ***
Title on admin page
    Open Admin Page

Create and remove competition
    ${comp_id} =    Create Competition
    Remove Competition  ${comp_id}
