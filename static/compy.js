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

var _global_prev_name = "";
var _days_with_disciplines_lanes = null;
var _disciplines = null;
var _countries = null;
var _result_countries = null;
var _sl = null;
var _sl_edited = false;
var _ots = []; // date in YYYY:MM:DD:HH:MM:SS
// debug for ots
//fillOtsForDebuggin();
var _autoplay_enabled = false;
let _audioElement = new Audio('static/countdown_aida.wav'); // Set the path to your audio file
let _audioTimeout = null;

$(window).on('load', function() {
    $('#comp_name').val("undefined");
    $('#numeric_radio').prop('checked', true);
    $('#aida_radio').prop('checked', true);
    _days_with_disciplines_lanes = null;
    _disciplines = null;
    _countries = null;
    _result_countries = null;
    _sl = null;
    _sl_edited = false;
    $('#special_ranking_name').val("Newcomer");
    $('#country_chooser').hide();
    $('#overlay_blur').hide();
});

function generateStartList(startlist) {
    let max_lane = 1;
    let interval = 0;
    let sl = "";
    if (startlist) {
        sl += "<a href='#' class='sl_pdf_button' id='sl_pdf_" + day + "_" + discipline + "'>Print PDF</a>";
        sl += `
            <table>
                <tr>
                    <td>Start time</td>
                    <td><input type="time" id="sl_start_time"/></td>
                </tr>
                <tr>
                    <td>Interval</td>
                    <td><input type="time" id="sl_interval"/></td>
                </tr>
                <tr>
                    <td>Number of lanes</td>
                    <td><input type="number" step="1" id="sl_no_lanes"/></td>
                </tr>
                    <td><button id="sl_recalc">Recalculate</button></td>
                    <td><button id="sl_sort">Sort by AP</button></td>
                <tr>
                </tr>
            </table>
            <button>Save start list</button>`;
        sl += '<table id="startlist">';
        sl += `
            <tr>
                <td>Name</td>
                <td>AP</td>
                <td>Nationality</td>
                <td>Warmup</td>
                <td>OT</td>
                <td>Lane</td>
                <td></td>
                <td></td>
                <td></td>
                <td></td>
            </tr>`;
        let empty = "<td></td>";
        let down_btn = (i) => `<td><button id="sl_down_${i}" class="down" type="button">Down</button></td>`;
        let up_btn = (i) => `<td><button id="sl_up_${i}" class="up" type="button">Up</button></td>`;
        let break_btn = (i) => `<td><button id="sl_break_${i}" class="break" type="button">` +
                               (startlist[i].Name=="Break" ? "Remove" : "Add") + ` break</button></td>`;
        let interval_ot1 = 0;
        for (let i = 0; i < startlist.length; i++) {
            sl += `
                <tr>
                    <td>${startlist[i].Name}</td>
                    <td>${startlist[i].AP}</td>
                    <td>${startlist[i].Nationality}</td>
                    <td>${startlist[i].Warmup}</td>
                    <td>${startlist[i].OT}</td>
                    <td>${startlist[i].Lane}</td>
                    <td><button id="sl_edit_${i}" class="edit" type="button">Edit</button></td>`;
            if (i == 0)
                sl += empty + down_btn(i) + break_btn(i);
            else if (i == startlist.length-1)
                sl += up_btn(i) + empty + empty;
            else {
                if (i == 1 && startlist[i].Name == "Break")
                    sl += empty + down_btn(i) + break_btn(i);
                else if (i == startlist.length-2 && startlist[i].Name == "Break")
                    sl += up_btn(i) + empty + break_btn(i);
                else
                    sl += up_btn(i) + down_btn(i) + break_btn(i);
            }
            sl += `
                </tr>`;
            max_lane = Math.max(max_lane, startlist[i].Lane);
            if (interval_ot1 == 0 && startlist[i].Lane == 1 && interval == 0)
                interval_ot1 = timeToMinutes(startlist[i].OT);
            if (startlist[i].Name == "Break")
                interval_ot1 = 0;
            if (interval == 0 && startlist[i].Lane == 1 && interval_ot1 != 0)
                interval = Math.max(timeToMinutes(startlist[i].OT) - interval_ot1, 0);
        }
        sl += "</table>";
    }

    let sl_content = document.getElementById('sl_content');
    sl_content.innerHTML = sl;

    if (startlist) {
        $('#sl_no_lanes').val(max_lane);
        if (startlist.length > 1)
            $('#sl_start_time').val(startlist[0].OT.padStart(5, '0'));
        if (interval > 0)
            $('#sl_interval').val(minutesToStr(interval, true));
    }
}

function timeToMinutes(time) {
    let h = Number(time.split(':')[0]);
    let m = Number(time.split(':')[1]);
    return h*60 + m;
}

function dateToStr(date, hZeroPad) {
    let h_str = date.getUTCHours().toString();
    if (hZeroPad)
        h_str = h_str.padStart(2, "0");
    return h_str + ":" + date.getMinutes().toString().padStart(2, "0");
}

function strToDate(str) {
    let date = new Date();
    let h = Number(str.split(':')[0]);
    let m = Number(str.split(':')[1]);
    date.setUTCHours(h);
    date.setMinutes(m);
    return date;
}

function minutesToStr(mins, padH = false) {
    let m = mins % 60;
    let h = Math.round((mins - m)/60);
    let h_str = h.toString();
    if (padH)
        h_str = h_str.padStart(2, "0");
    return h_str + ":"  + m.toString().padStart(2, "0");
}

function showOverlayBox(width, height, content) {
    $('#overlay_blur').show();
    $('#overlay_box').width(width);
    $('#overlay_box').height(height);
    $('#overlay_box').html(content);
}

function hideOverlayBox() {
    $('#overlay_blur').hide();
}

function getCountdownDuration() {
    let selectedOption = $("input[name='comp_type']:checked").val();
    if (selectedOption == "aida")
        return 2;
    else
        return 3;
}

function getDateNow() {
    let now = new Date();
    //now.setDate(now.getDate() + 6);
    //now.setHours(now.getHours() + 1);
    //now.setMinutes(now.getMinutes() + 42);
    seconds_adjust = parseInt($("#seconds_adjust").val(), 10);
    deciseconds_adjust = parseInt($("#deciseconds_adjust").val(), 10);
    //console.log(seconds_adjust, deciseconds_adjust*100);
    now.setSeconds(now.getSeconds() + seconds_adjust);
    now.setMilliseconds(now.getMilliseconds() + deciseconds_adjust*100);
    return now;
}

// Function to calculate the time until the next play
function getNextPlayTime(ot = false) {
    let now = getDateNow();
    let nextPlayTime = null;

    _ots.forEach(function(timeStr) {
        let timeParts = timeStr.split(':');
        // -1 for month as 0 = Jan
        let playTime = new Date(parseInt(timeParts[0]), parseInt(timeParts[1]-1), parseInt(timeParts[2]), parseInt(timeParts[3]), parseInt(timeParts[4]), parseInt(timeParts[5]));
        // subtract getCountdownDuration() mins as play time starts that many mins before ot
        if (!ot)
            playTime.setMinutes(playTime.getMinutes() - getCountdownDuration());

        if (!nextPlayTime || (playTime >= now && (playTime < nextPlayTime || nextPlayTime < now))) {
            nextPlayTime = playTime;
        }
    });

    if (nextPlayTime <= now) {
        return -1;
    }

    return nextPlayTime - now;
}

// Schedule the audio to play at the next play time
function schedulePlay() {
    let delay = getNextPlayTime();

    if (delay >= 0) {
        //TODO: must be more accurate
        hour = Math.floor(delay/3600/1000);
        min = Math.floor((delay - hour*3600*1000)/60/1000);
        sec = (delay - (hour*3600 + min*60)*1000)/1000;
        console.log("Next play in:", hour, "h", min, "min", sec, "s");
        _audioTimeout = setTimeout(function() {
            _audioElement.play();
            setTimeout(function() { $('#stop_countdown_btn').prop("disabled", false); }, getCountdownDuration()*60*1000);
            setTimeout(function() { $('#stop_countdown_btn').prop("disabled", true); }, (getCountdownDuration()*60 + 30)*1000);
            // Reschedule the next play after the current one finishes
            _audioElement.addEventListener('ended', schedulePlay, { once: true });
        }, delay);
    }
}

function testCountdown() {
    if (_audioTimeout)
        clearTimeout(_audioTimeout);
    _audioElement.currentTime = (getCountdownDuration()-1)*60 + 55;
    _audioElement.play();
    setTimeout(function() {
        _audioElement.pause();
        _audioElement.currentTime = 0;
        schedulePlay();
    }, 6000);
}

function changeTime() {
    if (_audioTimeout)
        clearTimeout(_audioTimeout);
    schedulePlay();
}

$(document).ready(function() {

    // Start scheduling the plays
    schedulePlay();

    setInterval(function() {
        $('#time').text(formatTime(getDateNow()), false);
        $('#countdown_ot').text(formatTime(getNextPlayTime(true), true));
        testAutoPlay();
    },  100);

    function testAutoPlay() {
        // Attempt to play the audio immediately
        if (!_autoplay_enabled)
        {
            _audioElement.play().then(function() {
                    _autoplay_enabled = true;
                    // Add a button to stop the audio
                    $('#stop_countdown_div').html('<button id="stop_countdown_btn">Stop Countdown</button>');
                    $('#test_countdown_div').html('<button id="test_countdown_btn">Test Countdown</button>');
                    $('#stop_countdown_btn').prop("disabled", true);
                    $('#stop_countdown_btn').click(function() {
                        stopAudio();
                    });
                    $('#test_countdown_btn').click(function() {
                        testCountdown();
                    });
                }).catch(function(error) {
                    _autoplay_enabled = false;
                    // If playback fails because of autoplay restrictions, show a prompt to the user
                    if (error.name === 'NotAllowedError') {
                        // Prompt the user to enable audio
                        $('#stop_countdown_div').html('<b>Audio autoplay is disabled. Countdown will not be played!</b>');
                    } else {
                        // Handle other errors
                        console.error('An error occurred while attempting to play audio:', error);
                    }
                });
            _audioElement.pause();
            _audioElement.currentTime =  0;
        }
    }

    // Function to stop the audio and reset the playhead
    function stopAudio() {
        $('#stop_countdown_btn').prop("disabled", true);
        _audioElement.pause();
        _audioElement.currentTime =  0;
        schedulePlay();
    }

    $('input[name=seconds_adjust]').change(function() { changeTime(); });
    $('input[name=deciseconds_adjust]').change(function() { changeTime(); });

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
                populateSpecialRanking(data);
                populateAthletes(data);
                setOTs(data);
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
    $('#special_ranking_name').change(function() {
        let name = this.value;
        let data = {special_ranking_name: name};
        $.ajax({
            type: "POST",
            url: "/change_special_ranking_name",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                $('#special_ranking_button').children().text(name);
                initSubmenus(data, true);
            }
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
                    $('#overwrite').show();
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
                $('#overwrite').hide();
            }
        })
    });
    $('#overwrite_no').click(function() {
        document.getElementById("comp_name").value = _global_prev_name;
        let overwrite_div = document.getElementById("overwrite");
        overwrite_div.style.display = "none";
    });
    $("#special_ranking").delegate(".special_ranking_checkbox", "change", function() {
        let athlete_id = this.id.substring(6); // checkbox id is equal to "nc_cb_" + athlete_id
        let data = {id: athlete_id, checked: this.checked};
        $.ajax({
            type: "POST",
            url: "/change_special_ranking",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                initSubmenus(data);
            }
        })
    });
    $('#athletes_table').on("click", "#add_athlete", function() {
        let data = {
            first_name: $('#athlete_first_name')[0].value,
            last_name: $('#athlete_last_name')[0].value,
            gender: $('#athlete_gender').find("option:selected").attr('value'),
            country: $('#athlete_country')[0].value,
            club: $('#athlete_club')[0].value,
            aida_id: $('#athlete_aida_id')[0].value
        };
        $.ajax({
            url: '/athlete',
            data: JSON.stringify(data),
            contentType: 'application/json',
            dataType: 'json',
            type: 'POST',
            success: function(data) {
                console.log(data.status_msg);
                populateSpecialRanking(data);
                populateAthletes(data);
                $('#athlete_first_name').val("");
                $('#athlete_last_name').val("");
                $('#athlete_gender').val("F");
                $('#athlete_country').val("");
                $('#athlete_club').val("");
                $('#athlete_aida_id').val("");
            },
            error: function(data) {
                console.log(data.status_msg);
                // TODO show to user
            }
        });
    });
    $('#athletes_table').on("click", ".delete", function() {
        let athlete_id = this.id.split('_')[2]; // button id is equal to "del_athlete_" + id
        let data = {athlete_id: athlete_id};
        $.ajax({
            type: "DELETE",
            url: "/athlete",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data)
            {
                console.log(data.status_msg);
                populateSpecialRanking(data);
                populateAthletes(data);
                initSubmenus(data);
                setOTs(data);
            }
        });
    });
    $("#competition_list").delegate(".load_comp_button", "click", function() {
        let comp_id = this.id.substring(5); // button id is equal to "load_" + comp id
        let data = {comp_id: comp_id};
        $.ajax({
            type: "POST",
            url: "/load_comp",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data)
            {
                console.log(data.status_msg);
                populateSpecialRanking(data);
                populateAthletes(data);
                initSubmenus(data, true);
                if ('comp_name' in data) {
                    $('#comp_name').val(data.comp_name);
                }
                if ("selected_country" in data) {
                    if ($('#country_select option:contains(' + data.selected_country + ')').length) {
                        $('#country_select').val(data.selected_country);
                    }
                }
                if ('special_ranking_name' in data)
                {
                    $('#special_ranking_name').val(data.special_ranking_name);
                    $('#special_ranking_button').children().text(data.special_ranking_name);
                }
                if ("lane_style" in data && data.lane_style == "alphabetic") {
                    $('#alphabetic_radio').prop('checked', true);
                } else {
                    $('#numeric_radio').prop('checked', true);
                }
                if ("comp_type" in data) {
                    _audioElement.remove();
                    if (data.comp_type == "aida") {
                        $('#aida_radio').prop('checked', true);
                        _audioElement = new Audio('static/countdown_aida.wav');
                    } else {
                        $('#cmas_radio').prop('checked', true);
                        _audioElement = new Audio('static/countdown_cmas.wav');
                    }
                }
                setOTs(data);
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
                if (data.start_list)
                    generateStartList(data.start_list);
                    _sl = data.start_list;
            }
        })
    });
    $("#breaks_date_menu").on("click", "a", function() {
        let id_arr = this.id.split('_'); // button id is equal to "breaks_" + day
        day = id_arr[1];
        let data = {
            day: day
        };
        $.ajax({
            type: "GET",
            url: "/breaks?" + $.param(data),
            success: function(data) {
                console.log(data.status_msg);
                let out = "";
                if (data.min_break) {
                    out += `Minimal break: ${data.min_break}<br>\n`;
                }
                if (data.breaks_list) {
                    out += "<table>";
                    out += `
                        <tr>
                            <td>Name</td>
                            <td>1st Discipline (OT)</td>
                            <td>2nd Discipline (OT)</td>
                            <td>Break</td>
                        </tr>`;
                    for (let i = 0; i < data.breaks_list.length; i++) {
                        out += `
                            <tr>
                                <td>${data.breaks_list[i].Name}</td>
                                <td>${data.breaks_list[i].Dis1} (${data.breaks_list[i].OT1})</td>
                                <td>${data.breaks_list[i].Dis2} (${data.breaks_list[i].OT2})</td>
                                <td>${data.breaks_list[i].Break}</td>
                            </tr>`;
                    }
                    out += "</table>";
                }
                $('#breaks_content').html(out);
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
        getResult(discipline, gender, country);
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
    $("#result_all_pdf_button").click(function() {
        getPDF("result");
    });
    $("#result_all_top3_pdf_button").click(function() {
        getPDF("result", {"type": "top3"});
    });
    $("#results_content").on("click", ".results_pdf_button", function() {
        let id_arr = this.id.split('_'); // button id is equal to "result_pdf_" + discipline + "_" + gender + "_" + country
        discipline = id_arr[2];
        gender = id_arr[3];
        country = id_arr[4];
        let data = {
            discipline: discipline,
            gender: gender,
            country: country
        };
        getPDF("result", data);
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
    $('input[name="comp_type"]').change(function() {
        let selectedOption = $("input[name='comp_type']:checked").val();
        let data = {
            comp_type: selectedOption
        };
        $.ajax({
            url: '/change_comp_type',
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            type: 'POST',
            success: function(data) {
                initSubmenus(data);
                _audioElement.remove();
                if (selectedOption == "aida")
                    _audioElement = new Audio('static/countdown_aida.wav');
                else
                    _audioElement = new Audio('static/countdown_cmas.wav');
                console.log(data.status_msg);
            }
        });
    });
    $('#country_select').change(function() {
        selected_country = $(this).find("option:selected").attr('value');
        let data = {
            selected_country: selected_country
        };
        $.ajax({
            url: '/change_selected_country',
            data: JSON.stringify(data),
            contentType: 'application/json',
            dataType: 'json',
            type: 'POST',
            success: function(data) {
                initSubmenus(data);
                console.log(data.status_msg);
            }
        });
    });
    $('#sl_content').on('click', '.down', function() {
        let i = Number(this.id.split('_')[2]); // id is sl_down_${i}
        if (i < 0 || i >= _sl.length-1)
            return;
        if (_sl[i].Name == "Break") {
            removeBreak(i);
            addBreak(i);
        }
        else if (_sl[i+1].Name == "Break") {
            if (i == 0) // don't allow break at 0
                return;
            removeBreak(i+1);
            addBreak(i-1);
        }
        else {
            [_sl[i].Name,        _sl[i+1].Name       ] = [_sl[i+1].Name,        _sl[i].Name       ];
            [_sl[i].AP,          _sl[i+1].AP         ] = [_sl[i+1].AP,          _sl[i].AP         ];
            [_sl[i].Nationality, _sl[i+1].Nationality] = [_sl[i+1].Nationality, _sl[i].Nationality];
        }
        generateStartList(_sl);
        _sl_edited = true;
    });
    $('#sl_content').on('click', '.up', function() {
        let i = Number(this.id.split('_')[2]); // id is sl_up_${i}
        if (i < 1 || i >= _sl.length)
            return;
        if (_sl[i].Name == "Break") {
            removeBreak(i);
            addBreak(i-2);
        }
        else if (_sl[i-1].Name == "Break") {
            if (i == _sl.length-1)
                return; // don't allow break at end
            removeBreak(i-1);
            addBreak(i-1);
        }
        else {
            [_sl[i].Name,        _sl[i-1].Name       ] = [_sl[i-1].Name,        _sl[i].Name       ];
            [_sl[i].AP,          _sl[i-1].AP         ] = [_sl[i-1].AP,          _sl[i].AP         ];
            [_sl[i].Nationality, _sl[i-1].Nationality] = [_sl[i-1].Nationality, _sl[i].Nationality];
        }
        generateStartList(_sl);
        _sl_edited = true;
    });
    $('#sl_content').on('click', '.edit', function() {
        let i = Number(this.id.split('_')[2]); // id is sl_edit_${i}
        if (i < 0 || i >= _sl.length)
            return;
        let content = "";
        if (_sl[i].Name == "Break") {
            content = `
                Edit break<br>
                <input type="hidden" id="sl_edit_i" value="${i}"/>
                <input type="hidden" id="sl_edit_prev_br" value="${_sl[i].AP}"/>
                <table>
                    <tr>
                        <td>Break</td>
                        <td>
                            <input type="time" id="sl_edit_new_br" value="${_sl[i].AP.padStart(5, '0')}"/>
                        </td>
                    </tr>
                    <tr>
                        <td><button id="sl_overlay_cancel" type="button">Cancel</button></td>
                        <td><button id="sl_edit_save" type="button">Save</button></td>
                    </tr>
                </table>
                `;
        }
        else {
            let ap_btn = `<input type="number" step="1" id="sl_edit_ap" value="${_sl[i].AP}"/>`;
            let cmas = $("input[name='comp_type']:checked").val() == "cmas";
            if (cmas && _sl[i].Discipline in ["DNF", "DYN", "DYNB"])
                ap_btn = `<input type="number" step="0.5" id="sl_edit_ap" value="${_sl[i].AP}"/>`;
            else if (_sl[i].Discipline == "STA") {
                let ap = _sl[i].AP.padStart(5, "0");
                ap_btn = `<input type="time" id="sl_edit_ap" value="${ap}"/>`;
            }
            content = `
                Edit start of ${_sl[i].Name}<br>
                <input type="hidden" id="sl_edit_i" value="${i}"/>
                <table>
                    <tr>
                        <td>AP</td>
                        <td>${ap_btn}</td>
                    </tr>
                    <tr>
                        <td>OT</td>
                        <td>
                            <input type="time" id="sl_edit_ot" value="${_sl[i].OT.padStart(5, '0')}"/>
                        </td>
                    </tr>
                    <tr>
                        <td><button id="sl_overlay_cancel" type="button">Cancel</button></td>
                        <td><button id="sl_edit_save" type="button">Save</button></td>
                    </tr>
                </table>
                `;
        }
        showOverlayBox(400, 300, content);
    });
    $('#overlay_box').on('click', '#sl_overlay_cancel', function() {
        hideOverlayBox();
    });
    $('#overlay_box').on('click', '#sl_edit_save', function() {
        let i = Number($('#sl_edit_i').val());
        if (i >= 0 && i < _sl.length) {
            if (_sl[i].Name == "Break") {
                let br_prev = $('#sl_edit_prev_br').val();
                let br_new = $('#sl_edit_new_br').val();
                let diff = timeToMinutes(br_new) - timeToMinutes(br_prev);
                for (let j = i+1; j < _sl.length; j++)
                    adjustOTbyDiff(j, diff);
            }
            else {
                if (_sl[i].Discipline == "STA") {
                    let ap = $('#sl_edit_ap')[0].valueAsDate;
                    _sl[i].AP = dateToStr(ap);
                }
                else
                    _sl[i].AP = $('#sl_edit_ap').val();
                let ot = $('#sl_edit_ot')[0].valueAsDate;
                setOT(i, ot);
            }
        }
        hideOverlayBox();
        generateStartList(_sl);
        _sl_edited = true;
    });
    $('#sl_content').on('click', '.break', function() {
        let i = Number(this.id.split('_')[2]); // id is sl_break_${i}
        if (i >= 0 && i < _sl.length-1) {
            let content = "";
            if (_sl[i].Name == "Break") { // this is for removing breaks
                removeBreak(i);
                generateStartList(_sl);
                _sl_edited = true;
            }
            else {
                content = `
                    Add break<br>
                    <input type="hidden" id="sl_break_i" value="${i}"/>
                    <table>
                        <tr>
                            <td>Duration</td>
                            <td><input type="time" id="sl_break_duration" value="00:00"/></td>
                        </tr>
                        <tr>
                            <td><button id="sl_overlay_cancel" type="button">Cancel</button></td>
                            <td><button id="sl_break_save" type="button">Save</button></td>
                        </tr>
                    </table>
                    `;
                showOverlayBox(400, 200, content);
            }
        }
    });
    $('#overlay_box').on('click', '#sl_break_save', function() {
        let i = Number($('#sl_break_i')[0].value);
        addBreak(i);
        hideOverlayBox();
        generateStartList(_sl);
        _sl_edited = true;
    });
    $('#sl_content').on('click', '#sl_recalc', function() {
        calculateStartList();
    });
    $('#sl_content').on('click', '#sl_sort', function() {
        if (_sl.length == 0)
            return;
        let brs = [];
        for (let i = 0; i < _sl.length; i++) {
            if (_sl[i].Name == "Break")
                brs.push({i: i, time: _sl[i].AP});
        }
        for (let i = brs.length-1; i >= 0; i--)
            _sl.splice(brs[i].i, 1);
        if (_sl[0].Discipline == "STA") // assumes all starts are STA
            _sl.sort((a,b) => Math.sign(timeToMinutes(a.AP)-timeToMinutes(b.AP)));
        else
            _sl.sort((a,b) => Math.sign(Number(a.AP)-Number(b.AP)));
        for (let i = 0; i < brs.length; i++) {
            let break_entry = {Name: "Break", AP: brs[i].time, Nationality: "", Warmup: "", OT: "", Lane: ""};
            _sl.splice(brs[i].i, 0, break_entry);
        }
        calculateStartList();
    });
});

function calculateStartList() {
    let no_lane = $('#sl_no_lanes').val();
    let interval = timeToMinutes($('#sl_interval').val());
    let ot = $('#sl_start_time')[0].valueAsDate;
    if (!no_lane || !interval || !ot || no_lane < 1)
        return;
    let lane = 1;
    for (let i = 0; i < _sl.length; i++) {
        if (_sl[i].Name == "Break") {
            lane = 1;
            let br = timeToMinutes(_sl[i].AP) - interval;
            ot.setMinutes(ot.getMinutes() + br);
            continue;
        }
        else if (lane == 1 && i != 0)
            ot.setMinutes(ot.getMinutes() + interval);
        _sl[i].Lane = lane;
        setOT(i, ot);
        lane = lane % no_lane + 1;
    }
    generateStartList(_sl);
    _sl_edited = true;
}

function addBreak(i) {
    if (i >= 0 && i < _sl.length-1) {
        let break_date = $('#sl_break_duration')[0].valueAsDate;
        break_str = dateToStr(break_date);
        let break_entry = {Name: "Break", AP: break_str, Nationality: "", Warmup: "", OT: "", Lane: ""};
        _sl.splice(i+1, 0, break_entry);
        let ot_old = timeToMinutes(_sl[i+2].OT);
        let ot_prev = timeToMinutes(_sl[i].OT);
        let ot_new = ot_prev + break_date.getUTCHours()*60 + break_date.getMinutes();
        let diff = ot_new - ot_old;
        for (let j=i+2; j < _sl.length; j++)
            adjustOTbyDiff(j, diff);
    }
}

function removeBreak(i) {
    if (i == 0 || i == _sl.length-1)
        return; // should not happen
    _sl.splice(i, 1);
    let interval = $('#sl_interval').val();
    // if interval is not set, remove the break but don't change anything
    if (interval) {
        let interval_date = strToDate(interval);
        let ot_old = timeToMinutes(_sl[i].OT);
        let ot_prev = timeToMinutes(_sl[i-1].OT);
        let ot_new = ot_prev + interval_date.getUTCHours()*60 + interval_date.getMinutes();
        let diff = ot_new - ot_old;
        for (let j = i; j < _sl.length; j++)
            adjustOTbyDiff(j, diff);
    }
}

function adjustOTbyDiff(j, diff) {
    if (_sl[j].Name != "Break") {
        let ot_this = strToDate(_sl[j].OT);
        ot_this.setMinutes(ot_this.getMinutes() + diff);
        setOT(j, ot_this);
    }
}

function setOT(i, ot) {
    _sl[i].OT = dateToStr(ot);
    let wt = new Date(ot);
    wt.setMinutes(wt.getMinutes() - 45);
    _sl[i].Warmup = dateToStr(wt);
}

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
            } else if ("type" in params && params.type == "top3") {
                link.download = comp_name + "_" + type + "s_top3.pdf";
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
    let tab_ids = ['settings', 'athletes', 'special_ranking', 'breaks', 'start_lists', 'lane_lists', 'results']
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

function populateAthletes(data) {
    $('#athletes_table').html(`
        <tr>
            <td>First name</td>
            <td>Last name</td>
            <td>Gender</td>
            <td>Country</td>
            <td>Club</td>
            <td>AIDA Id</td>
            <td></td>
        </tr>
        <tr>
            <td><input type="text" id="athlete_first_name"/></td>
            <td><input type="text" id="athlete_last_name"/></td>
            <td>
                <select name="athlete_gender" id="athlete_gender">
                    <option value="F">F</option>
                    <option value="M">M</option>
                </select>
            </td>
            <td><input type="text" id="athlete_country"/></td>
            <td><input type="text" id="athlete_club"/></td>
            <td><input type="text" id="athlete_aida_id"/></td>
            <td><button id="add_athlete" type="button">Add</button></td>
        </tr>
    `);
    if (data.hasOwnProperty("athletes")) {
        let athletes = data.athletes;
        for (let i = 0; i < athletes.length; i++) {
            $('#athletes_table').append(`
                <tr>
                    <td>${athletes[i].last_name}</td>
                    <td>${athletes[i].first_name}</td>
                    <td>${athletes[i].gender}</td>
                    <td>${athletes[i].country}</td>
                    <td>${athletes[i].club}</td>
                    <td>${athletes[i].aida_id}</td>
                    <td><button id="del_athlete_${athletes[i].id}" type="button" class="delete">Delete</button></td>
                </tr>
            `);
        }
    }
}

function populateSpecialRanking(data) {
    // show special_ranking header always
    let special_ranking_table = document.getElementById('special_ranking_table');
    special_ranking_table.innerHTML = `
        <tr>
            <td>Last name</td>
            <td>First name</td>
            <td>Gender</td>
            <td>Country</td>
            <td>Active</td>
        </tr>
    `;
    if (data.hasOwnProperty("athletes")) {
        let athletes = data.athletes;
        for (let i = 0; i < athletes.length; i++) {
            let chkd_str = "";
            if (athletes[i].hasOwnProperty("special_ranking") && athletes[i].special_ranking)
                chkd_str = "checked";
            special_ranking_table.innerHTML += `
                <tr>
                    <td>${athletes[i].last_name}</td>
                    <td>${athletes[i].first_name}</td>
                    <td>${athletes[i].gender}</td>
                    <td>${athletes[i].country}</td>
                    <td><input type="checkbox" id="nc_cb_${athletes[i].id}" name="${athletes[i].id}" value="true" class="special_ranking_checkbox" ${chkd_str}/></td>
                </tr>
            `;
        }
    }
}

function setOTs(data)
{
    if ('ots' in data)
        _ots = data.ots
        if (_audioTimeout)
            clearTimeout(_audioTimeout);
        schedulePlay();
        console.log(_ots)
}

function initSubmenus(data, reset=false)
{
    if (reset) {
        _days_with_disciplines_lanes = null;
        _disciplines = null;
        _countries = null;
        _result_countries = null;
    }

    if (data.hasOwnProperty("days_with_disciplines_lanes") && data.days_with_disciplines_lanes != null)
        _days_with_disciplines_lanes = data.days_with_disciplines_lanes;

    if (_days_with_disciplines_lanes != null) {
        // start_list and lane_list submenu
        let sl_date_menu = document.getElementById('sl_date_menu');
        let ll_date_menu = document.getElementById('ll_date_menu');
        let breaks_date_menu = $('#breaks_date_menu');
        sl_date_menu.innerHTML = "";
        ll_date_menu.innerHTML = "";
        breaks_date_menu.empty();
        keys = Object.keys(_days_with_disciplines_lanes);
        for (let i = 0; i < keys.length; i++) {
            let day = keys[i];
            sl_date_menu.innerHTML += "<a href='#' onclick='selectListDay(\"start\", \"" + day + "\")'>" + day + "</a>&nbsp;";
            ll_date_menu.innerHTML += "<a href='#' onclick='selectListDay(\"lane\", \"" + day + "\")'>" + day + "</a>&nbsp;";
            breaks_date_menu.append("<a href='#' id='breaks_" + day + "'>" + day + "</a>&nbsp;");
        }
    }

    // submenu for results
    if ("disciplines" in data && data.disciplines != null)
        _disciplines = data.disciplines;
    if ("countries" in data && data.countries != null)
    {
        _countries = data.countries;
        let country_select = $('#country_select');
        country_select.empty();
        $('#country_select').append(new Option('None', 'none'));
        for (let i = 0; i < _countries.length; i++)
        {
            if (_countries[i] == "International" || (i == 0 && _countries[i] != "International"))
                continue;
            country_select.append(new Option(_countries[i], _countries[i]));
        }
        if (_countries[0] != "International" && $('#country_select option:contains(' + _countries[0] + ')').length) {
            $('#country_select').val(_countries[0]);
        }
        $('#country_chooser').show();
    }
    else
        $('#country_chooser').hide();

    if ("result_countries" in data && data.result_countries != null)
        _result_countries = data.result_countries;
    if (_disciplines != null && _result_countries != null) {
        let result_dis_menu = document.getElementById('result_discipline_menu');
        result_dis_menu.innerHTML = "";
        for (let i = 0; i < _disciplines.length; i++) {
            let dis = _disciplines[i];
            result_dis_menu.innerHTML += "<a href='#' onclick='selectResultDiscipline(\"" + dis + "\")'>" + dis + "</a>&nbsp;";
        }
    }

    // lower tier menus
    document.getElementById('sl_discipline_menu').innerHTML = "";
    document.getElementById('sl_content').innerHTML = "";
    document.getElementById('ll_discipline_menu').innerHTML = "";
    document.getElementById('ll_lane_menu').innerHTML = "";
    document.getElementById('ll_content').innerHTML = "";
    document.getElementById('result_gender_menu').innerHTML = "";
    document.getElementById('result_country_menu').innerHTML = "";
    document.getElementById('results_content').innerHTML = "";
    $('#breaks_content').empty();
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
        }
        if (type == "lane")
            $('#ll_lane_menu').empty();
        let l_content = document.getElementById(type_char + 'l_content');
        l_content.innerHTML = "";
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
        }
        $('#ll_content').html("");
    }
}

function selectResultDiscipline(discipline)
{
    if (_disciplines != null && _result_countries != null) {
        let result_gender_menu = document.getElementById('result_gender_menu');
        result_gender_menu.innerHTML = "";
        result_gender_menu.innerHTML += "<a href='#' onclick='selectResultDisciplineGender(\"" + discipline + "\", \"F\")'>Female</a>&nbsp;";
        result_gender_menu.innerHTML += "<a href='#' onclick='selectResultDisciplineGender(\"" + discipline + "\", \"M\")'>Male</a>&nbsp;";
    }
    $('#result_country_menu').empty();
    $('#results_content').empty();
}

function selectResultDisciplineGender(discipline, gender)
{
    let i = -1;
    if (_disciplines != null && _result_countries != null) {
        let result_country_menu = document.getElementById('result_country_menu');
        result_country_menu.innerHTML = "";
        i = 0;
        for (; i < _result_countries.length; i++)
            result_country_menu.innerHTML += "<a href='#' class='result_button' id='result_" + discipline + "_" + gender + "_" + _result_countries[i] + "'>" + _result_countries[i] + "</a>&nbsp;";
    }
    if (i == 0)
        getResult(discipline, gender, "International"); // if only international, show right away
    else
        $('#results_content').empty();
}

function getResult(discipline, gender, country)
{
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
            if (data.result && data.result_keys) {
                res += "<a href='#' class='results_pdf_button' id='result_pdf_" + discipline + "_" + gender + "_" + country + "'>Print PDF</a>";
                res += "<table>";
                res += "<tr>"
                for (let j = 0; j < data.result_keys.length; j++)
                {
                        res += `<td>${data.result_keys[j]}</td>`;
                }
                res += "</tr>";
                for (let i = 0; i < data.result.length; i++) {
                    res += "<tr>"
                    for (let j = 0; j < data.result_keys.length; j++)
                    {
                            res += "<td>" + data.result[i][data.result_keys[j]] + "</td>";
                    }
                    res += "</tr>";
                }
                res += "</table>";
            }
            let results_content = document.getElementById('results_content');
            results_content.innerHTML = res;
        }
    });
}

function formatTime(date, countdown=false, full_date=false) {
    let days = 0;
    let hours = 0;
    let minutes = 0;
    let seconds = 0;
    let tenth = 0;
    if (countdown) {
        if (date < 0)
            return "n/a";
        // in this case date = distance in ms
        // add 1 second so that the flip from 59->00 in time is equivalent to the switch from 01->00 in the countdown
        // using ceil here so that we align with the time output that is using getSeconds, which essentially is floor, but we use target - time, so we need ceil for the countdown;
        date = Math.ceil((date + 1000) / 100);
        days = Math.floor(date / (10 * 60 *  60 * 24));
        hours = Math.floor((date % (10 * 60 *  60 * 24)) / (10 * 60 * 60));
        minutes = Math.floor((date % (10 * 60 * 60)) / (10 * 60));
        seconds = Math.floor(date % (10 * 60) / 10);
        tenth = Math.round(date % 10);
    }
    else
    {
        days = date.getDate();
        hours = date.getHours();
        minutes = date.getMinutes();
        seconds = date.getSeconds();
        tenth = Math.floor(date.getMilliseconds()/100);
    }
    days = days.toString().padStart(2, '0');
    hours = hours.toString().padStart(2, '0');
    minutes = minutes.toString().padStart(2, '0');
    seconds = seconds.toString().padStart(2, '0');
    tenth = tenth.toString();
    let time_str = hours + ':' + minutes + ':' + seconds; // + '.' + tenth;
    if (full_date && !countdown)
    {
        let year = (date.getFullYear()).toString().padStart(4, '0');
        let month = (date.getMonth() + 1).toString().padStart(2, '0');
        time_str = year + ':' + month + ':' + days + ":" + time_str;
    }
    else if (days != "00" && countdown)
        time_str =  days + " days " + time_str;
    return time_str;
}

function fillOtsForDebuggin() {
    // countdown 1 = now + 2:10
    let c1 = getDateNow();
    c1.setMinutes(c1.getMinutes() + 2);
    c1.setSeconds(c1.getSeconds() + 10);
    // countdown 2 = now + 4:50
    let c2 = getDateNow();
    c2.setMinutes(c2.getMinutes() + 4);
    c2.setSeconds(c2.getSeconds() + 50);
    _ots.push(formatTime(c1, false, true));
    _ots.push(formatTime(c2, false, true));
}
