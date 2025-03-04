/*
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

           ━━━━━━━━━━━━━
            ┏┓┏┓┳┳┓┏┓┓┏
            ┃ ┃┃┃┃┃┃┃┗┫
            ┗┛┗┛┛ ┗┣┛┗┛
           ━━━━━━━━━━━━━

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Competition organization tool
  for freediving competitions.

  Copyright 2023 - Arno Mayrhofer

  Licensed under the GNU AGPL

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Authors:

  - Arno Mayrhofer

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/

var dbg = false;

class Menu {
    contructor() {
        this.day = null;
        this.block = null;
        this.lane = null;
        this.s_id = null;
        this.edited = false;
    }
    unsetStartId() {
        this.s_id = null;
    }
    getDict() {
        return {'day': this.day, 'block': this.block, 'lane': this.lane, 's_id': this.s_id}
    }
}

var _judge_hash = null;
var _judge_id = null;
var _comp_id = null;
var _blocks = null;
var _menu = null;
var _lane_list = null;
var _result = null;
var _federation = null;

function getBaseDict() {
    return {judge_hash: _judge_hash, judge_id: _judge_id, comp_id: _comp_id};
}

function init(judge_hash, judge_id, comp_id, blocks, federation) {
    _judge_hash = judge_hash;
    _judge_id = judge_id;
    _comp_id = comp_id;
    _blocks = blocks;
    _federation = federation;
    _menu = new Menu();
    showDayMenu();
    if (dbg) {
        _menu.day = '2025-02-22';
        _menu.block = 12;
        _menu.lane = 'A';
        _lane_list = [
          {
            "AP": "0:01",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "10:23",
            "Name": "Andrej Ropret",
            "Nat": "SLO",
            "OT": "10:00",
            "PB": "10:23",
            "RP": "7:43",
            "Remarks": "OK",
            "id": 45,
            "s_id": 2069
          },
          {
            "AP": "0:01",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "7:59",
            "Name": "Nikola Kofentová",
            "Nat": "CZE",
            "OT": "10:14",
            "PB": "5:31",
            "RP": "5:36",
            "Remarks": "OK",
            "id": 31,
            "s_id": 2059
          },
          {
            "AP": "0:15",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "9:07",
            "Name": "Ludmilla Eimer",
            "Nat": "GER",
            "OT": "10:26",
            "PB": "5:30",
            "RP": "5:12",
            "Remarks": "OK",
            "id": 65,
            "s_id": 2066
          },
          {
            "AP": "0:35",
            "Card": "RED",
            "Dis": "STA",
            "NR": "8:30",
            "Name": "Atena Zalbeik-Dormayer",
            "Nat": "AUT",
            "OT": "10:38",
            "PB": "3:50",
            "RP": "3:55",
            "Remarks": "DQSP",
            "id": 59,
            "s_id": 2072
          },
          {
            "AP": "1:00",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "5:36",
            "Name": "Kitti Tárnok",
            "Nat": "HUN",
            "OT": "10:50",
            "PB": "4:00",
            "RP": "4:17",
            "Remarks": "OK",
            "id": 83,
            "s_id": 2076
          },
          {
            "AP": "2:00",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "9:04",
            "Name": "Markus Sorger",
            "Nat": "AUT",
            "OT": "11:20",
            "PB": "4:45",
            "RP": "4:48",
            "Remarks": "OK",
            "id": 81,
            "s_id": 2078
          },
          {
            "AP": "3:00",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "10:12",
            "Name": "Jan Pittner",
            "Nat": "SVK",
            "OT": "11:32",
            "PB": "6:00",
            "RP": "4:32",
            "Remarks": "OK",
            "id": 77,
            "s_id": 2082
          },
          {
            "AP": "3:00",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "7:16",
            "Name": "Mayer András",
            "Nat": "HUN",
            "OT": "11:44",
            "PB": "6:16",
            "RP": "6:13",
            "Remarks": "OK",
            "id": 17,
            "s_id": 2087
          },
          {
            "AP": "3:10",
            "Card": "RED",
            "Dis": "STA",
            "NR": "8:01",
            "Name": "Pia Imbar",
            "Nat": "FRA",
            "OT": "11:56",
            "PB": "5:08",
            "RP": "5:43",
            "Remarks": "DQSP",
            "id": 70,
            "s_id": 2089
          },
          {
            "AP": "3:40",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "8:58",
            "Name": "Klaus Kasten",
            "Nat": "GER",
            "OT": "12:08",
            "PB": "7:15",
            "RP": "0:00",
            "Remarks": "DNS",
            "id": 71,
            "s_id": 2055
          },
          {
            "AP": "4:15",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "9:04",
            "Name": "Franz Pehn",
            "Nat": "AUT",
            "OT": "12:20",
            "PB": "4:40",
            "RP": "5:05",
            "Remarks": "OK",
            "id": 75,
            "s_id": 2092
          },
          {
            "AP": "5:00",
            "Card": "WHITE",
            "Dis": "STA",
            "NR": "9:04",
            "Name": "Michael Nix",
            "Nat": "AUT",
            "OT": "12:32",
            "PB": "6:42",
            "RP": "6:46",
            "Remarks": "OK",
            "id": 41,
            "s_id": 2065
          }
        ];
        jQuery('<div>', {
        id: 'athlete_2069',
        class: 'athlete_menu',
        title: 'foo'
        }).appendTo('#content').ready(function() { $('#athlete_2069').trigger('click'); });
    }
}

$(document).ready(function() {

    $('#content').on("click", '.day_menu', function() {
        _menu.day = this.id.split('_')[1];
        showBlockMenu(_menu.day);
    });

    $('#content').on("click", '.block_menu', function() {
        _menu.block = this.id.split('_')[1];
        showLaneMenu(_menu.day, _menu.block);
    });

    $('#content').on("click", '.lane_menu', function() {
        _menu.lane = this.id.split('_')[1];
        // merge two dict objects
        params = Object.assign({}, _menu.getDict(), getBaseDict())
        $.ajax({
            type: "GET",
            url: "/judge/athletes?" + $.param(params),
            success: function(data) {
                console.log(data.status_msg);
                if ('lane_list' in data)
                    showAthleteMenu(data.lane_list);
                else
                    showLaneMenu(_menu.day, _menu.block);
            }
        });
    });

    $('#content').on("click", '.athlete_menu', function() {
        showAthlete(this.id.split('_')[1]);
    });

    $('#content').on("click", '#block_back', function() {
        showDayMenu(_menu.day);
    });
    $('#content').on("click", '#lane_back', function() {
        showBlockMenu(_menu.day, _menu.block);
    });
    $('#content').on("click", '#athlete_back', function() {
        showLaneMenu(_menu.day, _menu.block, _menu.lane);
    });
    $('#content').on("click", '#result_back', function() {
        saveContinue(function() { showAthleteMenu(_lane_list); });
    });
    $('#content').on('change', 'input', function() { _menu.edited = true; });
    $('#content').on("click", '#cancel', function() {
        if ($('#result_info').is(':visible')) {
            showAthlete(_menu.s_id);
            return;
        }
        $('#result_info').show();
        $('#result_entry').hide();
        if (_menu.edited) {
            $('#cancel').show();
            $('#save').show();
        } else {
            $('#cancel').hide();
            $('#save').hide();
        }
    });
    $('#content').on("click", '.nav', function() {
        let rp_on = $('#rp_entry').is(':visible');
        let card_on = $('#card_entry').is(':visible');
        let penalty_on = $('#penalty_entry').is(':visible');
        let remarks_on = $('#remarks_entry').is(':visible');
        let judge_remarks_on = $('#judge_remarks_entry').is(':visible');
        let is_next = this.id == "next";
        let is_prev = this.id == "prev";
        let is_ok = this.id == "ok";
        $('#result_entry').show();
        $('#result_info').hide();
        //$('#rp_entry').hide();
        //$('#card_entry').hide();
        //$('#penalty_entry').hide();
        //$('#remarks_entry').hide();
        //$('#judge_remarks_entry').hide();
        $('#next').show();
        $('#cancel').show();
        $('#prev').show();
        $('#save').hide();
        if (rp_on)
            saveRP();
        if (card_on)
            saveCard();
        if (penalty_on)
            savePenalty();
        if (remarks_on)
            saveRemarks();
        if (judge_remarks_on)
            saveJudgeRemarks();
        $('#result_input').empty();
        if ((is_prev && card_on) ||
            this.id == "edit_button" ||
            this.id == "info_RP") {
            showRP();
        }
        else if ((is_next && rp_on) ||
                 (is_prev && penalty_on) ||
                  this.id == "info_card") {
            showCard();
        }
        else if ((is_next && card_on) ||
                 (is_prev && remarks_on) ||
                  this.id=="info_penalty") {
            showPenalty();
        }
        else if ((is_next && penalty_on) ||
                 (is_prev && judge_remarks_on) ||
                  this.id == "info_remarks") {
            showRemarks();
        }
        else if ((is_next && remarks_on) ||
                 (is_prev && penalty_on) ||
                  this.id == "info_judge_remarks") {
            showJudgeRemarks();
        } else if (is_ok) {
            $('#result_info').show();
            $('#result_entry').hide();
            if (_menu.edited) {
                $('#cancel').show();
                $('#save').show();
            } else {
                $('#cancel').hide();
                $('#save').hide();
            }
        }
    });
    $('#content').on("click", "#save", function() {
        data = {id: _menu.s_id,
                rp: $('#info_RP').children('.info').html(),
                penalty: $('#info_penalty').children('.info').html(),
                card: $('#card_title').html(),
                remarks: $('#info_remarks').children('.info_piece').children('.info').html(),
                judge_remarks: $('#info_judge_remarks').children('.info_piece').children('.info').html()};
        $.ajax({
            type: "PUT",
            url: "/result",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                if ('Name' in data)
                    showResultEntryMask(data);
            }
        });
    });
    $('#content').on("click", ".card.selector", function() {
        $('.card.selector').removeClass("highlight");
        $(this).addClass('highlight');
        _menu.edited = true;
    });
    $('#content').on("click", ".remark.selector", function() {
        if ($(this).hasClass('highlight')) {
            $(this).removeClass('highlight');
        } else {
            $(this).addClass('highlight');
        }
        _menu.edited = true;
    });
});

function saveRP() {
    $('#info_RP').children('.info').html($('#rp_input').val());
}

function showRP() {
    $('#prev').hide();
    $('#result_input').html(`
        <div id="rp_entry" class="info_piece">
            <span class="info_head">Realized Performance</span><br>
            <input type="text" id="rp_input"/>
        </div>`);
    let dis = $('#info_dis').children('.info').html();
    let input = getPerformanceInput(dis, _federation);
    $('#rp_input').get(0).type = input['type'];
    $('#rp_input').get(0).step = input['step'];
    let old_rp = $('#info_RP').children('.info').html();
    if (dis == "STA")
        old_rp = old_rp.padStart(5, "0");
    $('#rp_input').val(old_rp);
}

function saveCard() {
    let hl = $('.card.selector.highlight');
    if (hl.length == 1) {
        let color = hl[0].id.split('_')[1];
        $('#card_title').removeClass("red").removeClass("yellow").removeClass("white").addClass(color).html(color.toUpperCase());
    }
}

function showCard() {
    $('#result_input').html(`
        <div id="card_entry" class="info_piece">
            <span class="info_head">Card</span><br>
            <span id="card_white" class="card white selector">WHITE</span>
            <span id="card_yellow" class="card yellow selector">YELLOW</span>
            <span id="card_red" class="card red selector">RED</span><br>
        </div>`);
    let card = $('#card_title').html();
    if (!isValidCard(card, _federation))
        return;
    $('.card.selector').removeClass("highlight");
    if (_federation == "aida") {
        if (getJudgePenaltyUnder() != null) {
            $('#card_white').hide();
            if (card == "WHITE")
                card = "YELLOW";
        } else
            $('#card_white').show();
    }
    $('#card_' + card.toLowerCase()).addClass('highlight');
}

function savePenalty() {
    let pen = Math.max(Number($('#penalty_input').val()) + getJudgePenaltyUnder(), 0);
    $('#info_penalty').children('.info').html(pen);
}

function showPenalty() {
    $('#result_input').html(`
        <div id="penalty_entry" class="info_piece">
            <span class="info_head">Penalty</span><br>
            <input type="number" id="penalty_input"/><span id="under_ap_penalty"></span>
        </div>`);
    let card = $('#card_title').html();
    let penalty = $('#info_penalty').children('.info').html();
    if (card != "YELLOW") {
        penalty = "";
        $('#penalty_input').prop('disabled', true);
        $('#penalty_input').val("");
    } else {
        let pen_under = getJudgePenaltyUnder();
        if (pen_under != null) {
            penalty -= pen_under;
            penalty = Math.max(penalty, 0);
            $('#under_ap_penalty').html(`+ ${pen_under} (under AP)`);
        }
        else
            $('#under_ap_penalty').empty();
        $('#penalty_input').prop('disabled', false);
        $('#penalty_input').val(penalty);
    }
}

function saveRemarks() {
    let hl = $('.remark.selector.highlight');
    let remarks = hl.map(function(i) { return hl[i].innerText; }).toArray().join(",");
    $('#info_remarks').children('.info_piece').children('.info').html(remarks);
}

function showRemarks() {
    $('#result_input').html(`
        <div id="remarks_entry" class="info_piece">
            <span class="info_head">Remarks</span><br>
            <div id="remarks_input"></div>
        </div>`);
    let card = $('#card_title').html();
    let old_remarks = getRemarksFromStr($('#info_remarks').children('.info_piece').children('.info').html(), _federation);
    if (!isValidCard(card, _federation))
        return;
    let remarks = getRemarksForCard(card, _federation);
    let div = $('#remarks_input');
    div.empty();
    for (let i = 0; i < remarks.length; i++) {
        let highlight = "";
        if (remarks.length == 1 ||
            old_remarks.includes(remarks[i]) ||
            (getJudgePenaltyUnder() != null && remarks[i] == "UNDER AP"))
            highlight = "highlight";
        div.append(`<span class='remark selector ${highlight}'>${remarks[i]}</span`);
    }
}

function saveJudgeRemarks() {
    $('#info_judge_remarks').children('.info_piece').children('.info').html($('#judge_remarks_input').val());
}

function showJudgeRemarks() {
    let jr = $('#info_judge_remarks').children('.info_piece').children('.info').html();
    $('#result_input').html(`
        <div id="judge_remarks_entry" class="info_piece">
            <span class="info_head">Judge Remarks</span><br>
            <input type="text" id="judge_remarks_input" value="${jr}"/>
        </div>`);
    $('#next').hide();
}

function getJudgePenaltyUnder() {
    let rp = $('#info_RP').children('.info').html();
    let ap = $('#info_AP').children('.info').html();
    let dis = $('#info_dis').children('.info').html();
    let card = $('#card_title').html();
    return penaltyUnderAP(rp, ap, card, _federation, dis);
}

function showAthlete(s_id) {
    _menu.s_id = s_id;
    params = Object.assign({}, _menu.getDict(), getBaseDict())
    $.ajax({
        type: "GET",
        url: "/judge/athlete/result?" + $.param(params),
        success: function(data) {
            console.log(data.status_msg);
            if ('Name' in data)
                showResultEntryMask(data);
        }
    });
}

function showDayMenu() {
    _menu.unsetStartId();
    let menu = "";
    keys = Object.keys(_blocks);
    for (let i = 0; i < keys.length; i++) {
        let day = keys[i];
        menu += `<button id="block_${day}" type="button" class="day_menu">${day}</button><br>`;
    }
    $('#content').html(menu);
}

function showBlockMenu(day) {
    _menu.unsetStartId();
    if (day in _blocks) {
        let menu = `<button id="block_back" type="button">Back</button><br>`;
        blocks = Object.keys(_blocks[day]);
        for (let i = 0; i < blocks.length; i++) {
            let block = _blocks[day][blocks[i]];
            menu += `<button id="menu_${blocks[i]}" type="button" class="block_menu">${block['dis_s']}</button><br>`;
        }
        $('#content').html(menu);
    }
    else
        showDayMenu();
}

function showLaneMenu(day, block) {
    _menu.unsetStartId();
    if (!day in _blocks)
    {
        showDayMenu();
        return;
    }
    if (!block in _blocks[day])
    {
        showBlockMenu(day);
        return;
    }
    let menu = `<button id="lane_back" type="button">Back</button><br>`;
    for (let i = 0; i < _blocks[day][block]['lanes'].length; i++) {
        let lane = _blocks[day][block]['lanes'][i];
        menu += `<button id="menu_${lane}" type="button" class="lane_menu">${lane}</button><br>`;
    }
    $('#content').html(menu);
}

function showAthleteMenu(lane_list) {
    _lane_list = lane_list;
    let menu = `<button id="athlete_back" type="button">Back</button><br>`;
    menu += "<table>";
    menu += `
        <tr>
            <th>OT</th>
            <th>Name</th>
            <th>AP</th>
            <th>Dis</th>
        </tr>`;
    for (let i = 0; i < lane_list.length; i++) {
        menu += `
            <tr id="athlete_${lane_list[i].s_id}" class="athlete_menu">
                <td>${lane_list[i].OT}</td>
                <td>${lane_list[i].Name}</td>
                <td>${lane_list[i].AP}</td>
                <td>${lane_list[i].Dis}</td>
            </tr>`;
    }
    menu += "</table>";
    $('#content').html(menu);
}

function saveContinue(next_action) {
    if (_menu.edited) {
        $('#content').hide();
        $('#continue').show();
        $('#continue').html(`
            <div id="continue_msg">You have unsaved changes.<br>
            Press 'Continue' if you want to discard them or 'Cancel' if you would like to get back.</div>
            <button id="continue_btn">Continue</button>
            <button onclick="switchBackToContent(null)">Cancel</button>
        `);
        $('#continue_btn').get(0).onclick = function() { switchBackToContent(next_action) };
    } else {
        $('#continue').hide();
        next_action();
    }
}

function switchBackToContent(next_action) {
    $('#continue').hide();
    $('#content').show();
    if (next_action != null)
        next_action();
}

function showResultEntryMask(data) {
    _menu.edited = false;
    let iCur = _lane_list.findIndex(function(a){ return a['s_id']==_menu.s_id; });
    if (iCur == -1) {
        console.log("Invalid athlete not found in lane_list");
        return;
    }
    let prev_athlete_btn = "";
    let next_athlete_btn = "";
    //TODO when showAthlete prev or next, then if (_menu.edited) { showSave(); }
    if (iCur > 0) {
        prev_athlete_btn = `<button onclick="showAthlete(${_lane_list[iCur-1]['s_id']})" type="button">Previous athlete</button><br>`;
    }
    if (iCur < _lane_list.length-1) {
        next_athlete_btn = `<button onclick="showAthlete(${_lane_list[iCur+1]['s_id']})" type="button">Next athlete</button>`;
    }
    let card = "";
    if ('Card' in data && isValidCard(data.Card, _federation))
        card = `<span id="card_title" class="card ${data.Card.toLowerCase()}">${data.Card}</span>`;
    let content = `
        <button id="result_back" type="button">Back</button><br>
        ${prev_athlete_btn}
        <div class="info_all">
            <div id="info_ot" class="info_piece">
                <span class="info_head">OT</span><br>
                <span class="info">${data.OT}</span>
            </div>
            <div id="info_name" class="info_piece">
                <span class="info_head">Name</span><br>
                <span class="info">${data.Name}</span>
            </div>
            <div id="info_nat" class="info_piece">
                <span class="info_head">Nat.</span><br>
                <span class="info">${data.Country}</span>
            </div>
        </div>
        <div class="info_all">
            <div id="info_AP" class="info_piece">
                <span class="info_head">AP</span><br>
                <span class="info">${data.AP}</span>
            </div>
            <div id="info_dis" class="info_piece">
                <span class="info_head">Dis.</span><br>
                <span class="info">${data.Dis}</span>
            </div>
            <div id="info_PB" class="info_piece">
                <span class="info_head">PB</span><br>
                <span class="info">${data.PB}</span>
            </div>
            <div id="info_NR" class="info_piece">
                <span class="info_head">NR</span><br>
                <span class="info">${data.NR}</span>
            </div>
        </div>
        <div id="result_info" style="display:__INFO_DISPLAY__">
            <div class="info_all">
                <div id="info_RP" class="info_piece nav">
                    <span class="info_head">RP</span><br>
                    <span class="info">${data.RP}</span>
                </div>
                <div id="info_card" class="info_piece nav">
                    <span class="info_head">Card</span><br>
                    <span class="info">${card}</span>
                </div>
                <div id="info_penalty" class="info_piece nav">
                    <span class="info_head">Penalty</span><br>
                    <span class="info">${data.Penalty}</span>
                </div>
            </div>
            <div id="info_remarks" class="info_all nav">
                <div class="info_piece">
                    <span class="info_head">Remarks</span><br>
                    <span class="info">${data.Remarks}</span>
                </div>
            </div>
            <div id="info_judge_remarks" class="info_all nav">
                <div class="info_piece">
                    <span class="info_head">Judge Remarks</span><br>
                    <span class="info">${data.JudgeRemarks}</span>
                </div>
            </div>
            <button id="edit_button" type="button" class="nav">Edit</button>
        </div>

        <div id="result_entry" style="display:__EDIT_DISPLAY__">
            <button id="prev" class="nav">Previous</button>
            <div class="info_all" id="result_input">
            </div>
            <button id="next" class="nav">Next</button>
            <button id="ok" class="nav">Ok</button>
        </div>

        <button id="cancel" style="display:none;">Cancel</button>
        <button id="save" style="display:none;">Save</button>
        ${next_athlete_btn}
        `;

    let showInfo = 'RP' in data && data.RP != "";
    if (showInfo)
        // show overview page
        content = content.replace('__INFO_DISPLAY__', 'block').replace('__EDIT_DISPLAY__', 'none');
    else
        // show edit form
        content = content.replace('__INFO_DISPLAY__', 'none').replace('__EDIT_DISPLAY__', 'block');

    $('#content').html(content);

    if (!showInfo)
        showRP();
}
