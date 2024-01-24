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
var _days_with_disciplines = null;

$(window).on('load', function() {
    let comp_name = document.getElementById('comp_name');
    comp_name.value = "undefined";
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
                initSubmenus(data);
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
            success: function(data) { console.log(data.status_msg); }
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
                initSubmenus(data);
                if (data.hasOwnProperty("comp_name")) {
                    let comp_name = document.getElementById('comp_name');
                    comp_name.value = data.comp_name;
                }
            }
        })
    });
    $("#sl_discipline_menu").on("click", "a", function() {
        let day = this.id.substr(3, 10); // button id is equal to "sl_" + day + "_" + discipline
        let discipline = this.id.substr(3 + 10 + 1);
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
        getStartList("all", "all");
    });
    $("#sl_content").on("click", ".sl_pdf_button", function() {
        day = this.id.substr(7, 10); // button id is equal to "sl_pdf_" + day + "_" + discipline
        discipline = this.id.substr(7 + 10 + 1);
        getStartList(day, discipline);
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
                console.log(data.status_msg);
            }
        });
    });
});

function getStartList(day, discipline)
{
    let data = {
        day: day,
        discipline: discipline
    };
    $.ajax({
        type: "GET",
        url: "/start_list_pdf?" + $.param(data),
        xhrFields: {
            responseType: 'blob'
        },
        success: function(data) {
            let link = document.createElement('a');
            link.href = window.URL.createObjectURL(data);
            let comp_name = document.getElementById("comp_name").value;
            if (day == "all" && discipline == "all") {
                link.download = comp_name + "_start_lists.pdf";
            } else {
                link.download = comp_name + "_start_list_" + day + "_" + discipline + ".pdf";
            }
            link.style.display = 'none';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            console.log("Served pdf");
        }
    })
}

function switchTo(id) {
    let tab_ids = ['settings', 'newcomer', 'start_lists']
    for (let i = 0; i < tab_ids.length; i++) {
        let element = document.getElementById(tab_ids[i]);
        if (tab_ids[i] === id) {
            element.style.display = "block";
        } else {
            element.style.display = "none";
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

function initSubmenus(data)
{
    if (data.hasOwnProperty("days_with_disciplines") && data.days_with_disciplines != null)
    {
        _days_with_disciplines = data.days_with_disciplines;
        // start_list submenu
        let sl_date_menu = document.getElementById('sl_date_menu');
        sl_date_menu.innerHTML = "";
        keys = Object.keys(_days_with_disciplines);
        for (let i = 0; i < keys.length; i++)
        {
            let day = keys[i];
            sl_date_menu.innerHTML += "<a href='#' onclick='selectStartListDay(\"" + day + "\")'>" + day + "</a>&nbsp;";
        }
    }
    else
        _days_with_disciplines = null;
}

function selectStartListDay(day)
{
    if (_days_with_disciplines != null && _days_with_disciplines.hasOwnProperty(day))
    {
        let sl_discipline_menu = document.getElementById('sl_discipline_menu');
        sl_discipline_menu.innerHTML = "";
        disciplines = _days_with_disciplines[day];
        for (let i = 0; i < disciplines.length; i++)
        {
            let dis = disciplines[i];
            sl_discipline_menu.innerHTML += "<a href='#' class='sl_discipline_button' id='sl_" + day + "_" + dis + "'>" + dis + "</a>&nbsp;";
            let sl_content = document.getElementById('sl_content');
            sl_content.innerHTML = "";
        }
    }
}
