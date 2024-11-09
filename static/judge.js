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
        this.discipline = null;
        this.lane = null;
        this.athlete = null;
    }
    setAthlete(athlete) {
        this.athlete = athlete;
    }
    unsetAthlete() {
        this.athlete = null;
    }
    getDict() {
        return {'day': this.day, 'discipline': this.discipline, 'lane': this.lane, 'athlete': this.athlete}
    }
}

var _judge_hash = null;
var _judge_id = null;
var _comp_id = null;
var _days_with_disciplines_lanes = null;
var _menu = null;
var _lane_list = null;

function getBaseDict() {
    return {judge_hash: _judge_hash, judge_id: _judge_id, comp_id: _comp_id};
}

function init(judge_hash, judge_id, comp_id, days_with_disciplines_lanes) {
    _judge_hash = judge_hash
    _judge_id = judge_id
    _comp_id = comp_id
    _days_with_disciplines_lanes = days_with_disciplines_lanes
    _menu = new Menu();
    showDayMenu();
}

$(document).ready(function() {
    $('#content').on("click", '.day_menu', function() {
        _menu.day = this.id.split('_')[1];
        showDisciplineMenu(_menu.day);
    });

    $('#content').on("click", '.discipline_menu', function() {
        _menu.discipline = this.id.split('_')[1];
        showLaneMenu(_menu.day, _menu.discipline);
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
                    showLaneMenu(_menu.day, _menu.discipline);
            }
        });
    });

    $('#content').on("click", '.athlete_menu', function() {
        _menu.athlete = this.id.split('_')[1];
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

    $('#content').on("click", '#discipline_back', function() {
        showDayMenu(_menu.day);
    });
    $('#content').on("click", '#lane_back', function() {
        showDisciplineMenu(_menu.day, _menu.discipline);
    });
    $('#content').on("click", '#athlete_back', function() {
        showLaneMenu(_menu.day, _menu.discipline, _menu.lane);
    });
    $('#content').on("click", '#result_back', function() {
        showAthleteMenu(_lane_list);
    });
});

function showDayMenu() {
    _menu.unsetAthlete();
    let menu = "";
    keys = Object.keys(_days_with_disciplines_lanes);
    for (let i = 0; i < keys.length; i++) {
        let day = keys[i];
        menu += `<button id="day_${day}" type="button" class="day_menu">${day}</button><br>`;
    }
    $('#content').html(menu);
}

function showDisciplineMenu(day) {
    _menu.unsetAthlete();
    if (day in _days_with_disciplines_lanes) {
        let menu = `<button id="discipline_back" type="button">Back</button><br>`;
        keys = Object.keys(_days_with_disciplines_lanes[day]);
        for (let i = 0; i < keys.length; i++) {
            let discipline = keys[i];
            menu += `<button id="menu_${discipline}" type="button" class="discipline_menu">${discipline}</button><br>`;
        }
        $('#content').html(menu);
    }
    else
        showDayMenu();
}

function showLaneMenu(day, discipline) {
    _menu.unsetAthlete();
    if (!day in _days_with_disciplines_lanes)
    {
        showDayMenu();
        return;
    }
    if (!discipline in _days_with_disciplines_lanes[day])
    {
        showDisciplineMenu(day);
        return;
    }
    let menu = `<button id="lane_back" type="button">Back</button><br>`;
    for (let i = 0; i < _days_with_disciplines_lanes[day][discipline].length; i++) {
        let lane = _days_with_disciplines_lanes[day][discipline][i];
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
        </tr>`;
    for (let i = 0; i < lane_list.length; i++) {
        menu += `
            <tr id="athlete_${lane_list[i].id}" class="athlete_menu">
                <td>${lane_list[i].OT}</td>
                <td>${lane_list[i].Name} (${lane_list[i].Nat})</td>
                <td>${lane_list[i].AP}</td>
            </tr>`;
    }
    menu += "</table>";
    $('#content').html(menu);
}

function showResultEntryMask(data) {
    let content = `
        <button id="result_back" type="button">Back</button><br>
        <div>
            ${_menu.day} | ${_menu.discipline} | ${_menu.lane}<br>
            ${data.Name} (OT: ${data.OT} | AP: ${data.AP})
        </div>
        <div id="rp_div">
            RP: <span id="rp_title">${data.RP}</span><br>
            <div id="rp_entry" style="display:__RP_DISPLAY__">
                <input type="text" id="rp_input"/><br>
                <button>Cancel</button>
                <button>Next</button>
            </div>
            Card: <span id="card_title" class="card ${data.Card.toLowerCase()}">${data.Card}</span><br>
            <div id="card_entry" style="display:none;">
                <span id="card_white" class="card white">WHITE</span>
                <span id="card_yellow" class="card yellow">YELLOW</span>
                <span id="card_red" class="card red">RED</span><br>
                <button>Previous</button>
                <button>Cancel</button>
                <button>Next</button>
            </div>
            Penalty: <span id="penalty_title">${data.Penalty}</span><br>
            <div id="penalty_entry" style="display:none;">
                <input type="text" id="penalty_input"/><br>
                <button>Previous</button>
                <button>Cancel</button>
                <button>Next</button>
            </div>
            Remarks: <span id="penalty_title">${data.Remarks}</span><br>
            <div id="remarks_entry" style="display:none;">
                <input type="text" id="remarks_input"/><br>
                <button>Previous</button>
                <button>Cancel</button>
                <button>Next</button>
            </div>
            <div id="final_buttons" style="display:none">
                <button>Revert</button>
                <button>Save</button>
            </div>
        </div>
        `;

    if ('RP' in data && data.RP != "") {
        // show overview page
        content = content.replace('__RP_DISPLAY__', 'none');
    }
    else {
        // show edit form
        content = content.replace('__RP_DISPLAY__', 'block');
    }

    $('#content').html(content);
}
