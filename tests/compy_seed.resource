*** Settings ***
Library         Browser
Library         Collections
Documentation   Fixture seeding over HTTP for the judge, results and clock suites.
...
...             admin.robot builds its fixtures by clicking through the admin
...             UI, which is right there: the admin UI is what it tests. The
...             other three screens are not the admin, so building their
...             fixtures by clicking would make a judge test fail whenever the
...             start list editor changes. These keywords talk to the same
...             endpoints the admin page uses instead.
...
...             Browser's `Http` keyword sends the request with the current
...             page's fetch, so the admin session cookie set by `Open Admin
...             Page` is reused and no extra http library is needed. Call
...             `Open Seed Session` before any Seed keyword.
...
...             Unlike `Create Competition` in compy.resource, `Seed
...             Competition` returns the numeric comp_id - the judge, results
...             and clock urls all need it, and the competition *name* the
...             admin suite works with is not enough.

*** Variables ***
${TEST_XLSX}    ${CURDIR}/../test_competition.xlsx
${FILE_INPUT}   id=file
${UPLOAD_BUTTON}    id=upload_file_button
${UPLOAD_STATUS}    id=file_upload_status

*** Keywords ***
Open Seed Session
    [Documentation]     Log in as admin so the Seed keywords have a session.
    Open Admin Page

Seed Request
    [Documentation]     One json request; fails loudly instead of returning a
    ...                 broken fixture that makes the real test fail later.
    [Arguments]     ${method}   ${url}  &{payload}
    ${body} =   Evaluate    json.dumps($payload)    json
    ${res} =    Http    ${url}  ${method}   ${body}
    Should Be True  ${res}[ok]  Seeding ${method} ${url} failed (${res}[status]): ${res}[body]
    RETURN  ${res}[body]

Unique Name
    [Documentation]     A competition name no other run can collide with.
    ...                 A suite that dies between creating a competition and
    ...                 storing its id leaks that competition; reusing a fixed
    ...                 name would then hit the "already exists" branch, which
    ...                 answers 200 without a comp_id and poisons every
    ...                 following request with a null competition.
    [Arguments]     ${prefix}
    RETURN  ${prefix}_${{str(__import__('uuid').uuid4())[:8]}}

Seed Competition
    [Documentation]     A new empty competition. Returns its numeric id.
    [Arguments]     ${name}
    ${body} =   Seed Request    POST    /competition    comp_name=${name}   overwrite=${False}  comp_id=${None}
    ${comp_id} =    Get From Dictionary     ${body}     comp_id  default=${None}
    Should Not Be Equal     ${comp_id}  ${None}
    ...     Competition '${name}' was not created (already exists?): ${body}
    RETURN  ${comp_id}

Seed Competition With Excel
    [Documentation]     A competition populated from test_competition.xlsx:
    ...                 30 athletes over 3 days, with results and cards on the
    ...                 days that are already over. Returns its numeric id.
    ...
    ...                 The upload is done through the admin form because
    ...                 /upload_file takes multipart, which `Http` cannot build.
    ...                 That form uploads into whatever competition the admin
    ...                 page currently has loaded, so the page is reopened and
    ...                 pointed at the new competition first - otherwise the
    ...                 athletes land in whichever competition was loaded
    ...                 before, and the fixture comes back empty.
    [Arguments]     ${name}
    ${comp_id} =    Seed Competition    ${name}
    Open Admin Page
    Load Competition    ${name}
    Upload File By Selector     ${FILE_INPUT}   ${TEST_XLSX}
    Click   ${UPLOAD_BUTTON}
    Wait For Elements State     ${UPLOAD_STATUS}    visible     timeout=30s
    RETURN  ${comp_id}

Seed Athlete
    [Arguments]     ${comp_id}  ${first_name}   ${last_name}    ${gender}=F     ${country}=AUT
    Seed Request    POST    /athlete    comp_id=${comp_id}  first_name=${first_name}
    ...             last_name=${last_name}  gender=${gender}    country=${country}
    ...             club=${first_name}_club     aida_id=${first_name}_aida

Seed Block
    [Documentation]     Adds a block of one or more disciplines on ${day}.
    [Arguments]     ${comp_id}  ${day}  @{disciplines}
    Seed Request    POST    /block  comp_id=${comp_id}  day=${day}  dis=${disciplines}  block=-1

Seed Judge
    [Documentation]     Adds a judge and returns the hash from its qr code url,
    ...                 which is what the judge page authenticates with.
    [Arguments]     ${comp_id}  ${first_name}=Judy  ${last_name}=Judge
    ${body} =   Seed Request    POST    /judge  comp_id=${comp_id}  first_name=${first_name}  last_name=${last_name}
    ${judge_id} =   Set Variable    ${body}[judges][0][id]
    # the query string is built first: a literal token containing '=' would be
    # read as robot's named-argument syntax, not as part of the url
    ${qr_url} =     Set Variable    /judge/qr_code?judge_id=${judge_id}&comp_id=${comp_id}
    ${qr} =     Seed Request    GET     ${qr_url}
    ${hash} =   Set Variable    ${{ $qr['judge_url'].split('hash=')[1] }}
    ${judge} =  Create Dictionary   id=${judge_id}  hash=${hash}
    RETURN  ${judge}

Publish Results
    [Arguments]     ${comp_id}
    ${res} =    Http    /publish_results     PATCH
    ...         ${{ __import__('json').dumps({'comp_id': $comp_id, 'publish_results': True}) }}
    Should Be True  ${res}[ok]  Publishing results failed (${res}[status]): ${res}[body]

Delete Seeded Competition
    [Documentation]     Teardown counterpart of Seed Competition. Never fails
    ...                 the test it cleans up after.
    [Arguments]     ${comp_id}
    Run Keyword And Ignore Error    Seed Request    DELETE  /competition   comp_id=${comp_id}
