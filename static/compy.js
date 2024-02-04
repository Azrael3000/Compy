/*
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

           ━━━━━━━━━━━━━
            ┏┓┏┓┳┳┓┏┓┓┏
            ┃ ┃┃┃┃┃┃┃┗┫
            ┗┛┗┛┛ ┗┣┛┗┛
           ━━━━━━━━━━━━━

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Competition organization tool
  for AIDA International
  competitions.

  Copyright 2023 - Arno Mayrhofer

  Licensed under the GNU AGPL

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Authors:

  - Arno Mayrhofer

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/

var _global_prev_name = "";
var _days_with_disciplines_lanes = null;
var _disciplines = null;
var _countries = null

$(window).on('load', function() {
    let comp_name = document.getElementById('comp_name');
    comp_name.value = "undefined";
    $('#numeric_radio').prop('checked', true);
    _days_with_disciplines_lanes = null;
    _disciplines = null;
    _countries = null;
});

$(document).ready(function() {
    $('#upload_file_button').click(function() {
        let form_data = new FormData($('#upload_file')[0]);
        $.ajax({
            type: 'POST',
            url: '/upload_file',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function(data) {
                let element = document.getElementById('file_upload_status');
                console.log(data.status_msg)
                // show status msg
                element.style.display = "block";
                element.innerHTML = data.status_msg;
                populateNewcomer(data);
                initSubmenus(data, true);
            },
        })
    });
    $('#upload_sponsor_img_button').click(function() {
        let form_data = new FormData($('#upload_sponsor_img')[0]);
        $.ajax({
            type: 'POST',
            url: '/upload_sponsor_img',
            data: form_data,
            contentType: false,
            cache: false,
            processData: false,
            success: function(data) {
                let element = document.getElementById('file_upload_status');
                console.log(data.status_msg)
                // show status msg
                element.style.display = "block";
                element.innerHTML = data.status_msg;
            },
        })
    });
    $('#comp_name').change(function() {
        let data = {comp_name: this.value, overwrite: false};
        $.ajax({
            type: "POST",
            url: "/change_comp_name",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                if (data.file_exists) {
                    let overwrite_div = document.getElementById("overwrite");
                    overwrite_div.style.display = "block";
                    _global_prev_name = data.prev_name;
                }
            }
        })
    });
    $('#overwrite_yes').click(function() {
        let comp_name = document.getElementById("comp_name").value;
        let data = {comp_name: comp_name, overwrite: true};
        $.ajax({
            type: "POST",
            url: "/change_comp_name",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                let overwrite_div = document.getElementById("overwrite");
                overwrite_div.style.display = "none";
            }
        })
    });
    $('#overwrite_no').click(function() {
        document.getElementById("comp_name").value = _global_prev_name;
        let overwrite_div = document.getElementById("overwrite");
        overwrite_div.style.display = "none";
    });
    $("#newcomer").delegate(".newcomer_checkbox", "change", function() {
        let athlete_id = this.id.substring(6); // checkbox id is equal to "nc_cb_" + athlete_id
        let data = {id: athlete_id, checked: this.checked};
        $.ajax({
            type: "POST",
            url: "/change_newcomer",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                initSubmenus(data);
            }
        })
    });
    $("#competition_list").delegate(".load_comp_button", "click", function() {
        let comp_name = this.id.substring(5); // button id is equal to "load_" + comp name
        let data = {comp_name: comp_name};
        $.ajax({
            type: "POST",
            url: "/load_comp",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data)
            {
                console.log(data.status_msg);
                populateNewcomer(data);
                initSubmenus(data, true);
                if (data.hasOwnProperty("comp_name")) {
                    let comp_name = document.getElementById('comp_name');
                    comp_name.value = data.comp_name;
                }
                if ("lane_style" in data && data.lane_style == "alphabetic") {
                    $('#alphabetic_radio').prop('checked', true);
                } else {
                    $('#numeric_radio').prop('checked', true);
                }
            }
        })
    });
    $("#sl_discipline_menu").on("click", "a", function() {
        let id_arr = this.id.split('_'); // button id is equal to "sl_" + day + "_" + discipline
        day = id_arr[1];
        discipline = id_arr[2];
        let data = {
            day: day,
            discipline: discipline
        };
        $.ajax({
            type: "GET",
            url: "/start_list?" + $.param(data),
            success: function(data) {
                console.log(data.status_msg);
                let sl = "";
                if (data.start_list) {
                    sl += "<a href='#' class='sl_pdf_button' id='sl_pdf_" + day + "_" + discipline + "'>Print PDF</a>";
                    sl += "<table>";
                    sl += `
                        <tr>
                            <td>Name</td>
                            <td>AP</td>
                            <td>Warmup</td>
                            <td>OT</td>
                            <td>Lane</td>
                        </tr>`;
                    for (let i = 0; i < data.start_list.length; i++) {
                        sl += `
                            <tr>
                                <td>${data.start_list[i].Name}</td>
                                <td>${data.start_list[i].AP}</td>
                                <td>${data.start_list[i].Warmup}</td>
                                <td>${data.start_list[i].OT}</td>
                                <td>${data.start_list[i].Lane}</td>
                            </tr>`;
                    }
                    sl += "</table>";
                }
                let sl_content = document.getElementById('sl_content');
                sl_content.innerHTML = sl;
            }
        })
    });
    $("#sl_all_pdf_button").click(function() {
        getPDF("start_list");
    });
    $("#sl_content").on("click", ".sl_pdf_button", function() {
        let id_arr = this.id.split('_'); // button id is equal to "sl_pdf_" + day + "_" + discipline
        day = id_arr[2];
        discipline = id_arr[3];
        let data = {
            day: day,
            discipline: discipline
        };
        getPDF("start_list", data);
    });
    $("#ll_lane_menu").on("click", "a", function() {
        let id_arr = this.id.split('_'); // button id is equal to "ll_" + day + "_" + discipline + "_" + lane
        day = id_arr[1];
        discipline = id_arr[2];
        lane = id_arr[3];
        let data = {
            day: day,
            discipline: discipline,
            lane: lane
        };
        $.ajax({
            type: "GET",
            url: "/lane_list?" + $.param(data),
            success: function(data) {
                console.log(data.status_msg);
                let ll = "";
                if (data.lane_list) {
                    ll += "<a href='#' class='ll_pdf_button' id='ll_pdf_" + day + "_" + discipline + "_" + lane + "'>Print PDF</a>";
                    ll += "<table>";
                    ll += `
                        <tr>
                            <td>OT</td>
                            <td>Name</td>
                            <td>AP</td>
                            <td>NR</td>
                            <td>RP</td>
                            <td>Card</td>
                            <td>Remarks</td>
                        </tr>`;
                    for (let i = 0; i < data.lane_list.length; i++) {
                        ll += `
                            <tr>
                                <td>${data.lane_list[i].OT}</td>
                                <td>${data.lane_list[i].Name}</td>
                                <td>${data.lane_list[i].AP}</td>
                                <td>${data.lane_list[i].NR}</td>
                                <td></td>
                                <td></td>
                                <td></td>
                            </tr>`;
                    }
                    ll += "</table>";
                }
                let ll_content = document.getElementById('ll_content');
                ll_content.innerHTML = ll;
            }
        })
    });
    $("#result_country_menu").on("click", "a", function() {
        let id_arr = this.id.split('_'); // button id is equal to "result_" + discipline + "_" + gender + "_" + country
        discipline = id_arr[1];
        gender = id_arr[2];
        country = id_arr[3];
        let data = {
            discipline: discipline,
            gender: gender,
            country: country
        };
        $.ajax({
            type: "GET",
            url: "/result?" + $.param(data),
            success: function(data) {
                console.log(data.status_msg);
                let res = "";
                if (data.result) {
                    res += "<a href='#' class='results_pdf_button' id='result_pdf_" + discipline + "_" + gender + "_" + country + "'>Print PDF</a>";
                    res += "<table>";
                    if (discipline == "Overall" || discipline == "Newcomer")
                    {
                        res += `
                            <tr>
                                <td>Rank</td>
                                <td>Name</td>
                                <td>Country</td>`;
                        for (let j = 0; j < _disciplines.length; j++)
                        {
                            if (_disciplines[j] == "Overall" || _disciplines[j] == "Newcomer")
                                continue;
                            res += `
                                <td>${_disciplines[j]}</td>`;
                        }
                        res += `
                                <td>Points</td>
                            </tr>`;
                        for (let i = 0; i < data.result.length; i++) {
                            res += `
                                <tr>
                                    <td>${data.result[i].Rank}</td>
                                    <td>${data.result[i].Name}</td>
                                    <td>${data.result[i].Country}</td>`;
                            for (let j = 0; j < _disciplines.length; j++)
                            {
                                if (_disciplines[j] == "Overall" || _disciplines[j] == "Newcomer")
                                    continue;
                                res += "<td>" + data.result[i][_disciplines[j]] + "</td>";
                            }
                            res += `
                                    <td>${data.result[i].Points}</td>
                                </tr>`;
                        }
                        res += "</table>";
                    }
                    else
                    {
                        res += `
                            <tr>
                                <td>Rank</td>
                                <td>Name</td>
                                <td>Country</td>
                                <td>AP</td>
                                <td>RP</td>
                                <td>Penalty</td>
                                <td>Card</td>
                                <td>Remarks</td>
                                <td>Points</td>
                            </tr>`;
                        for (let i = 0; i < data.result.length; i++) {
                            res += `
                                <tr>
                                    <td>${data.result[i].Rank}</td>
                                    <td>${data.result[i].Name}</td>
                                    <td>${data.result[i].Country}</td>
                                    <td>${data.result[i].AP}</td>
                                    <td>${data.result[i].RP}</td>
                                    <td>${data.result[i].Penalty}</td>
                                    <td>${data.result[i].Card}</td>
                                    <td>${data.result[i].Remarks}</td>
                                    <td>${data.result[i].Points}</td>
                                </tr>`;
                        }
                        res += "</table>";
                    }
                }
                let results_content = document.getElementById('results_content');
                results_content.innerHTML = res;
            }
        })
    });
    $("#ll_all_pdf_button").click(function() {
        getPDF("lane_list");
    });
    $("#ll_content").on("click", ".ll_pdf_button", function() {
        let id_arr = this.id.split('_'); // button id is equal to "ll_pdf_" + day + "_" + discipline + "_" + lane
        day = id_arr[2];
        discipline = id_arr[3];
        lane = id_arr[4];
        let data = {
            day: day,
            discipline: discipline,
            lane: lane
        };
        getPDF("lane_list", data);
    });
    $('input[name="lane_style"]').change(function() {
        let selectedOption = $("input[name='lane_style']:checked").val();
        let data = {
            lane_style: selectedOption
        };
        $.ajax({
            url: '/change_lane_style',
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            type: 'POST',
            success: function(data) {
                initSubmenus(data);
                console.log(data.status_msg);
            }
        });
    });
});

function getPDF(type, params = {type: "all"})
{
    $.ajax({
        type: "GET",
        url: "/" + type + "_pdf?" + $.param(params),
        xhrFields: {
            responseType: 'blob'
        },
        success: function(data) {
            let link = document.createElement('a');
            link.href = window.URL.createObjectURL(data);
            let comp_name = document.getElementById("comp_name").value;
            if ("type" in params && params.type == "all") {
                link.download = comp_name + "_" + type + "s.pdf";
            } else {
                if (type == "start_list") {
                    link.download = comp_name + "_" + type + "_" + params.day + "_" + params.discipline + ".pdf";
                } else if (type == "lane_list") {
                    link.download = comp_name + "_" + type + "_" + params.day + "_" + params.discipline + "_" + params.lane + ".pdf";
                } else /* if (type == "result") */ {
                    link.download = comp_name + "_" + type + "_" + params.discipline + "_" + params.country + "_" + params.gender + ".pdf";
                }
            }
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            console.log("Served pdf: " + link.download);
        }
    })
}

function switchTo(id) {
    let tab_ids = ['settings', 'newcomer', 'start_lists', 'lane_lists', 'results']
    for (let i = 0; i < tab_ids.length; i++) {
        let element = document.getElementById(tab_ids[i]);
        let button = document.getElementById(tab_ids[i] + "_button");
        if (tab_ids[i] === id) {
            element.style.display = "block";
            button.style.fontWeight = "bold";
        } else {
            element.style.display = "none";
            button.style.fontWeight = "normal";
        }
    }
}

function populateNewcomer(data) {
    // show newcomer header always
    let newcomer_table = document.getElementById('newcomer_table');
    newcomer_table.innerHTML = `
        <tr>
            <td>Last name</td>
            <td>First name</td>
            <td>Gender</td>
            <td>Country</td>
            <td>Newcomer</td>
        </tr>
    `;
    if (data.hasOwnProperty("athletes")) {
        athletes = data.athletes;
        for (let i = 0; i < athletes.length; i++) {
            let chkd_str = "";
            if (athletes[i].hasOwnProperty("newcomer") && athletes[i].newcomer)
                chkd_str = "checked";
            newcomer_table.innerHTML += `
                <tr>
                    <td>${athletes[i].last_name}</td>
                    <td>${athletes[i].first_name}</td>
                    <td>${athletes[i].gender}</td>
                    <td>${athletes[i].country}</td>
                    <td><input type="checkbox" id="nc_cb_${athletes[i].id}" name="${athletes[i].id}" value="true" class="newcomer_checkbox" ${chkd_str}/></td>
                </tr>
            `;
        }
    }
}

function initSubmenus(data, reset=false)
{
    if (reset) {
        _days_with_disciplines_lanes = null;
        _disciplines = null;
        _countries = null;
    }

    if (data.hasOwnProperty("days_with_disciplines_lanes") && data.days_with_disciplines_lanes != null)
        _days_with_disciplines_lanes = data.days_with_disciplines_lanes;

    if (_days_with_disciplines_lanes != null) {
        // start_list and lane_list submenu
        let sl_date_menu = document.getElementById('sl_date_menu');
        let ll_date_menu = document.getElementById('ll_date_menu');
        sl_date_menu.innerHTML = "";
        ll_date_menu.innerHTML = "";
        keys = Object.keys(_days_with_disciplines_lanes);
        for (let i = 0; i < keys.length; i++) {
            let day = keys[i];
            sl_date_menu.innerHTML += "<a href='#' onclick='selectListDay(\"start\", \"" + day + "\")'>" + day + "</a>&nbsp;";
            ll_date_menu.innerHTML += "<a href='#' onclick='selectListDay(\"lane\", \"" + day + "\")'>" + day + "</a>&nbsp;";
        }
    }

    // submenu for results
    if ("disciplines" in data && data.disciplines != null)
        _disciplines = data.disciplines;
    if ("countries" in data && data.countries != null)
        _countries = data.countries;

    if (_disciplines != null && _countries != null) {
        let result_dis_menu = document.getElementById('result_discipline_menu');
        result_dis_menu.innerHTML = "";
        for (let i = 0; i < _disciplines.length; i++) {
            let dis = _disciplines[i];
            result_dis_menu.innerHTML += "<a href='#' onclick='selectResultDiscipline(\"" + dis + "\")'>" + dis + "</a>&nbsp;";
        }
    }

    // lower tier menus
    document.getElementById('sl_discipline_menu').innerHTML = "";
    document.getElementById('ll_discipline_menu').innerHTML = "";
    document.getElementById('ll_lane_menu').innerHTML = "";
    document.getElementById('result_gender_menu').innerHTML = "";
    document.getElementById('result_country_menu').innerHTML = "";
}

function selectListDay(type, day)
{
    if (_days_with_disciplines_lanes != null && _days_with_disciplines_lanes.hasOwnProperty(day)) {
        let type_char = "";
        if (type == "start") {
            type_char = "s";
        } else if (type == "lane") {
            type_char = "l";
        } else {
            return;
        }
        let l_discipline_menu = document.getElementById(type_char + 'l_discipline_menu');
        l_discipline_menu.innerHTML = "";
        disciplines = Object.keys(_days_with_disciplines_lanes[day]);
        for (let i = 0; i < disciplines.length; i++)
        {
            let dis = disciplines[i];
            if (type == "start") {
                l_discipline_menu.innerHTML += "<a href='#' class='sl_discipline_button' id='sl_" + day + "_" + dis + "'>" + dis + "</a>&nbsp;";
            } else {
                l_discipline_menu.innerHTML += "<a href='#' onclick='selectLaneListDayDiscipline(\"" + day + "\", \"" + dis + "\")'>" + dis + "</a>&nbsp;";
            }
            let l_content = document.getElementById(type_char + 'l_content');
            l_content.innerHTML = "";
        }
    }
}

function selectLaneListDayDiscipline(day, discipline)
{
    if (_days_with_disciplines_lanes != null && _days_with_disciplines_lanes.hasOwnProperty(day)) {
        let l_lane_menu = document.getElementById('ll_lane_menu');
        l_lane_menu.innerHTML = "";
        lanes = _days_with_disciplines_lanes[day][discipline];
        for (let i = 0; i < lanes.length; i++)
        {
            let lane = lanes[i];
            l_lane_menu.innerHTML += "<a href='#' class='ll_lane_button' id='sl_" + day + "_" + discipline + "_" + lane + "'>" + lane + "</a>&nbsp;";
            let l_content = document.getElementById('ll_content');
            l_content.innerHTML = "";
        }
    }
}

function selectResultDiscipline(discipline)
{
    if (_disciplines != null && _countries != null) {
        let result_gender_menu = document.getElementById('result_gender_menu');
        result_gender_menu.innerHTML = "";
        result_gender_menu.innerHTML += "<a href='#' onclick='selectResultDisciplineGender(\"" + discipline + "\", \"F\")'>Female</a>&nbsp;";
        result_gender_menu.innerHTML += "<a href='#' onclick='selectResultDisciplineGender(\"" + discipline + "\", \"M\")'>Male</a>&nbsp;";
    }
    document.getElementById('result_country_menu').innerHTML = "";
    document.getElementById('results_content').innerHTML = "";
}

function selectResultDisciplineGender(discipline, gender)
{
    if (_disciplines != null && _countries != null) {
        let result_country_menu = document.getElementById('result_country_menu');
        result_country_menu.innerHTML = "";
        for (let i = 0; i < _countries.length; i++)
            result_country_menu.innerHTML += "<a href='#' class='result_button' id='result_" + discipline + "_" + gender + "_" + _countries[i] + "'>" + _countries[i] + "</a>&nbsp;";
    }
    document.getElementById('results_content').innerHTML = "";
}
