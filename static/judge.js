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

class Menu {
    contructor() {
        this.day = null;
        this.block = null;
        this.lane = null;
        this.s_id = null;
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

function getBaseDict() {
    return {judge_hash: _judge_hash, judge_id: _judge_id, comp_id: _comp_id};
}

function init(judge_hash, judge_id, comp_id, blocks) {
    _judge_hash = judge_hash
    _judge_id = judge_id
    _comp_id = comp_id
    _blocks = blocks
    _menu = new Menu();
    showDayMenu();
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
        _menu.s_id = this.id.split('_')[1];
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
        showAthleteMenu(_lane_list);
    });
    $('#content').on("click", '.cancel', function() {
        $('#edit_div').show();
        $('#rp_entry').hide();
        $('#penalty_entry').hide();
        $('#card_entry').hide();
        $('#remarks_entry').hide();
        $('#judgeremarks_entry').hide();
    });
    $('#content').on("click", '.nav', function() {
        $('#rp_entry').hide();
        $('#card_entry').hide();
        $('#penalty_entry').hide();
        $('#remarks_entry').hide();
        $('#judgeremarks_entry').hide();
        $('#edit_div').hide();
        if (this.id=="card_previous" || this.id=="rp_title_div" || this.id=="edit_button")
            $('#rp_entry').show();
        else if (this.id == "rp_next" || this.id=="penalty_previous" || this.id=="card_title_div")
            $('#card_entry').show();
        else if (this.id == "card_next" || this.id == "remarks_previous" || this.id=="penalty_title_div")
            $('#penalty_entry').show();
        else if (this.id == "penalty_next" || this.id == "judgeremarks_previous" || this.id=="remarks_title_div")
            $('#remarks_entry').show();
        else if (this.id == "remarks_next" || this.id=="judgeremarks_title_div")
            $('#judgeremarks_entry').show();
        else if (this.id == "judgeremarks_next")
            $('#final_div').show();
        let type = this.id.split('_')[0];
        if (this.tagName != "DIV" && this.id != "edit_button") {
            if (type != "card" && $('#' + type + '_input').val() != "")
                $('#' + type + '_title').html($('#' + type + '_input').val());
            else if (type == "card") {
                let hl = $('.card.selector.highlight');
                if (hl.length == 1) {
                    let color = "white";
                    if (hl.hasClass("red"))
                        color = "red";
                    else if (hl.hasClass("yellow"))
                        color = "yellow";
                    $('#card_title').removeClass("red").removeClass("yellow").removeClass("white").addClass(color).html(color.toUpperCase());
                }
            }
        }
    });
    $('#content').on("click", "#save_button", function() {
        data = {id: _menu.s_id,
                rp: $('#rp_title').html(),
                penalty: $('#penalty_title').html(),
                card: $('#card_title').html(),
                remarks: $('#remarks_title').html(),
                judge_remarks: $('#judgeremarks_title').html()};
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
    });
});

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
            <td>OT</td>
            <td>Name (Nat.)</td>
            <td>AP</td>
            <td>Dis</td>
        </tr>`;
    for (let i = 0; i < lane_list.length; i++) {
        menu += `
            <tr id="athlete_${lane_list[i].s_id}" class="athlete_menu">
                <td>${lane_list[i].OT}</td>
                <td>${lane_list[i].Name} (${lane_list[i].Nat})</td>
                <td>${lane_list[i].AP}</td>
                <td>${lane_list[i].Dis}</td>
            </tr>`;
    }
    menu += "</table>";
    $('#content').html(menu);
}

function showResultEntryMask(data) {
    let content = `
        <button id="result_back" type="button">Back</button><br>
        <div>
            ${_menu.day} | ${_menu.block} | ${_menu.lane}<br>
            ${data.Name} (OT: ${data.OT} | AP: ${data.AP})
        </div>
        <div id="rp_div">
            <div id="rp_title_div" class="nav">
                RP: <span id="rp_title">${data.RP}</span>
            </div>
            <div id="rp_entry" style="display:__RP_DISPLAY__">
                <input type="text" id="rp_input"/><br>
                <button class="cancel">Cancel</button>
                <button id="rp_next" class="nav">Next</button>
            </div>
        </div>
        <div id="card_div">
            <div id="card_title_div" class="nav">
                Card: <span id="card_title" class="card ${data.Card.toLowerCase()}">${data.Card}</span>
            </div>
            <div id="card_entry" style="display:none;">
                <span id="card_white" class="card white selector">WHITE</span>
                <span id="card_yellow" class="card yellow selector">YELLOW</span>
                <span id="card_red" class="card red selector">RED</span><br>
                <button id="card_previous" class="nav">Previous</button>
                <button class="cancel">Cancel</button>
                <button id="card_next" class="nav">Next</button>
            </div>
        </div>
        <div id="penalty_div">
            <div id="penalty_title_div" class="nav">
                Penalty: <span id="penalty_title">${data.Penalty}</span>
            </div>
            <div id="penalty_entry" style="display:none;">
                <input type="text" id="penalty_input"/><br>
                <button id="penalty_previous" class="nav">Previous</button>
                <button class="cancel">Cancel</button>
                <button id="penalty_next" class="nav">Next</button>
            </div>
        </div>
        <div id="remarks_div">
            <div id="remarks_title_div" class="nav">
                Remarks: <span id="remarks_title">${data.Remarks}</span>
            </div>
            <div id="remarks_entry" style="display:none;">
                <input type="text" id="remarks_input"/><br>
                <button id="remarks_previous" class="nav">Previous</button>
                <button class="cancel">Cancel</button>
                <button id="remarks_next" class="nav">Next</button>
            </div>
        </div>
        <div id="judgeremarks_div">
            <div id="judgeremarks_title_div" class="nav">
                Judge remarks: <span id="judgeremarks_title">${data.JudgeRemarks}</span>
            </div>
            <div id="judgeremarks_entry" style="display:none;">
                <input type="text" id="judgeremarks_input"/><br>
                <button id="judgeremarks_previous" class="nav">Previous</button>
                <button class="cancel">Cancel</button>
                <button id="judgeremarks_next" class="nav">Next</button>
            </div>
        </div>
        <div id="final_div" style="display:none">
            <button id="save_button">Save</button>
        </div>
        <div id="edit_div" style="display:__EDIT_DISPLAY__">
            <button id="edit_button" type="button" class="nav">Edit</button>
        </div>
        `;

    if ('RP' in data && data.RP != "") {
        // show overview page
        content = content.replace('__RP_DISPLAY__', 'none').replace('__EDIT_DISPLAY__', 'block');
    }
    else {
        // show edit form
        content = content.replace('__RP_DISPLAY__', 'block').replace('__EDIT_DISPLAY__', 'none');
    }

    $('#content').html(content);
}
/* TODOS:
 * RP input, only allow correct format
 * Card input:
 *  if rp < ap, don't allow white
 *  if status is != OK don't allow white
 *  if status is one of reds: only allow red
 * penalties input:
 *  only allow if card is yellow
 *  list of penalties sum, ap < rp, possibility to add from dropdown, possibility to add number
 * remarks input:
 *  if card is white: ok
 *  Available Remarks (check!)
        OK -> w
        OTHER -> y / r
        SHORT -> y / r
        LATESTART -> y / r
        GRAB -> y / r
        LANYARD -> y / r
        PULL -> y / r
        TURN -> y / r
        EARLYSTART -> r
        START -> y / r
        NO TAG -> y / r
        UNDER AP -> y / r
        DQSP -> r
        DQJUMP -> r
        DQOTHER -> r
        DQAIRWAYS -> r
        DQTOUCH -> r
        DQLATESTART -> r
        DQCHECK-IN -> r
        DQBO-UW -> r
        DQBO-SURFACE -> r
        DQPULL -> r
        DQOTHER-LANE -> r
        DQPULLX2 -> r
        DNS -> r
 * saving result
 */
