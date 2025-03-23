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
var _blocks = null;
var _disciplines = null;
var _countries = null;
var _result_countries = null;
var _cur_menu = {};
var _sl = null;
var _sl_remove = [];
var _sl_edited = false;
var _sl_athletes = null;
var _ots = []; // date in YYYY:MM:DD:HH:MM:SS
var _autoplay_enabled = false;
let _audioElement = new Audio('static/countdown_aida.wav'); // Set the path to your audio file
let _audioTimeout = null;

$(window).on('load', function() {
    $('#comp_name').val("undefined");
    $('#numeric_radio').prop('checked', true);
    $('#aida_radio').prop('checked', true);
    _days_with_disciplines_lanes = null;
    _blocks = null;
    _disciplines = null;
    _countries = null;
    _result_countries = null;
    _sl = null;
    _sl_remove = [];
    _cur_menu = {};
    _sl_edited = false;
    _sl_athletes = null;
    $('#special_ranking_name').val("Newcomer");
    $('#country_chooser').hide();
    $('#overlay_blur').hide();
    initSubmenus({}, true);
    loadCompetition(1);
});

function generateStartList(startlist) {
    let max_lane = 1;
    let interval = 0;
    let sl = "";
    if (startlist) {
        sl += `<button class='sl_edit_block' id='sl_edit_block_${day}_${block}'>Edit block</button><br>`;
        sl += "<a href='#' class='sl_pdf_button' id='sl_pdf_" + day + "_" + block + "'>Print PDF</a>";
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
                    <td><button id="sl_add">Add athlete</button></td>
                    <td></td>
                <tr>
                </tr>
            </table>
            <button id="sl_save">Save start list</button>`;
        sl += '<table id="startlist">';
        sl += `
            <tr>
                <td>Name</td>
                <td>Discipline</td>
                <td>AP</td>
                <td>PB</td>
                <td>Nationality</td>
                <td>Warmup</td>
                <td>OT</td>
                <td>Lane</td>
                <td></td>
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
        let rm_btn = (i) => startlist[i].Name != "Break" ? `<td><button id="sl_remove_${i}" class="remove" type="button">Remove</button></td>` : empty;
        let interval_ot1 = 0;
        for (let i = 0; i < startlist.length; i++) {
            sl += `
                <tr>
                    <td>${startlist[i].Name}</td>
                    <td>${startlist[i].Discipline}</td>
                    <td>${startlist[i].AP}</td>
                    <td>${startlist[i].PB}</td>
                    <td>${startlist[i].Nationality}</td>
                    <td>${startlist[i].Warmup}</td>
                    <td>${startlist[i].OT}</td>
                    <td>${startlist[i].Lane}</td>
                    <td><button id="sl_edit_${i}" class="edit" type="button">Edit</button></td>`;
            if (i == 0)
                sl += empty + down_btn(i) + break_btn(i) + rm_btn(i);
            else if (i == startlist.length-1)
                sl += up_btn(i) + empty + empty + rm_btn(i);
            else {
                if (i == 1 && startlist[i].Name == "Break")
                    sl += empty + down_btn(i) + break_btn(i) + empty;
                else if (i == startlist.length-2 && startlist[i].Name == "Break")
                    sl += up_btn(i) + empty + break_btn(i) + empty;
                else
                    sl += up_btn(i) + down_btn(i) + break_btn(i) + rm_btn(i);
            }
            sl += `
                </tr>`;
            if (interval_ot1 == 0 && startlist[i].Lane == convertNumericLaneToAcutal(1) && interval == 0)
                interval_ot1 = timeToMinutes(startlist[i].OT);
            if (startlist[i].Name == "Break")
                interval_ot1 = 0;
            else
                max_lane = Math.max(max_lane, convertActualLaneToNumeric(startlist[i].Lane));
            if (interval == 0 && startlist[i].Lane == convertNumericLaneToAcutal(1) && interval_ot1 != 0)
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
    $('body').addClass('stop-scrolling');
}

function hideOverlayBox() {
    $('#overlay_blur').hide();
    $('body').removeClass('stop-scrolling');
}

function getCountdownDuration() {
    let selectedOption = $("input[name='comp_type']:checked").val();
    if (selectedOption == "aida")
        return 2;
    else
        return 3;
}

function getDateNow(with_correction = true) {
    let now = new Date();
    //now.setDate(now.getDate() + 7);
    //now.setHours(now.getHours() + 1);
    //now.setMinutes(now.getMinutes() + 11);
    if (with_correction) {
        seconds_adjust = parseInt($("#seconds_adjust").val(), 10);
        deciseconds_adjust = parseInt($("#deciseconds_adjust").val(), 10);
        //console.log(seconds_adjust, deciseconds_adjust*100);
        now.setSeconds(now.getSeconds() + seconds_adjust);
        now.setMilliseconds(now.getMilliseconds() + deciseconds_adjust*100);
    }
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

    return nextPlayTime - getDateNow();
}

// Schedule the audio to play at the next play time
function schedulePlay() {
    let delay = getNextPlayTime();

    if (delay >= 0) {
        hour = Math.floor(delay/3600/1000);
        min = Math.floor((delay - hour*3600*1000)/60/1000);
        sec = (delay - (hour*3600 + min*60)*1000)/1000;
        console.log("Next play in:", hour, "h", min, "min", sec, "s");
        _audioTimeout = setTimeout(function() {
            //console.log("Starting play at", new Date().toISOString());
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

function testAutoPlay() {
    // Attempt to play the audio immediately
    if (!_autoplay_enabled)
    {
        // TODO This function does not work in chrome as on the second call it suceeds, even though it still cannot play
        //      Maybe try by spawning a worker thread
        //      Similarly the setTimeouts might not be called in an accurate manner if the tab is in the background
        //      which might kill the OT timing
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
                    $('#stop_countdown_div').html('<b>Audio autoplay is disabled. Countdown will not be played!</b><button onclick="testAutoPlay()">Try again</button>');
                } else {
                    // Handle other errors
                    console.error('An error occurred while attempting to play audio:', error);
                }
            });
        _audioElement.pause();
        _audioElement.currentTime =  0;
    }
}

$(document).ready(function() {

    // Start scheduling the plays
    schedulePlay();

    function updateTime() {
        $('#time').text(formatTime(getDateNow()), false);
        $('#countdown_ot').text(formatTime(getNextPlayTime(true), true));
        window.requestAnimationFrame(updateTime);
    };

    updateTime();

    testAutoPlay();

    // Function to stop the audio and reset the playhead
    function stopAudio() {
        $('#stop_countdown_btn').prop("disabled", true);
        _audioElement.pause();
        _audioElement.currentTime =  0;
        schedulePlay();
    }

    $('input[name=seconds_adjust]').change(function() { changeTime(); });
    $('input[name=deciseconds_adjust]').change(function() { changeTime(); });

    function showStatus(msg) {
        let element = document.getElementById('file_upload_status');
        element.style.display = "block";
        element.innerHTML = msg;
    }

    $('#refresh_nrs').click(function() {
        showStatus("Update of national records started.");
        $('#refresh_nrs').prop("disabled", true);
        $.ajax({
            type: 'GET',
            url: '/national_records',
            success: function(data) {
                showStatus("Update of national records completed.");
            },
            error: function(data) {
                showStatus("Update of national records failed.");
            },
            complete: function (data) {
                console.log(data.status_msg);
                $('#refresh_nrs').prop("disabled", false);
            }
        })
    });
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
                populateJudges(data);
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
    $("#registration").delegate(".registration_checkbox", "change", function() {
        let id = this.id.split('_'); // checkbox id is equal to type + "_cb_" + athlete_id
        let type = id[0];
        let athlete_id = id[2];
        let data = {id: athlete_id, checked: this.checked, type: type};
        $.ajax({
            type: "POST",
            url: "/change_registration",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                initSubmenus(data);
            }
        })
    });
    $('#judges_table').on("click", "#add_judge", function() {
        let data = {
            first_name: $('#judge_first_name')[0].value,
            last_name: $('#judge_last_name')[0].value,
        };
        $.ajax({
            url: '/judge',
            data: JSON.stringify(data),
            contentType: 'application/json',
            dataType: 'json',
            type: 'POST',
            success: function(data) {
                console.log(data.status_msg);
                populateJudges(data);
                $('#judge_first_name').val("");
                $('#judge_last_name').val("");
            },
            error: function(data) {
                console.log(data.status_msg);
                // TODO show to user
            }
        });
    });
    $('#judges_table').on("click", ".show", function() {
        let judge_id = this.id.split('_')[2]; // button id is equal to "show_judge_" + id
        let data = {judge_id: judge_id};
        $.ajax({
            type: "GET",
            url: "/judge/qr_code?" + $.param(data),
            success: function(data)
            {
                console.log(data.status_msg);
                content = `
                    QR Code for ${data.judge_first_name} ${data.judge_last_name}:<br>
                    <a href="${data.judge_url}" target="_blank"><img src="${data.judge_qr_code}" style="width:250px;"/></a><br>
                    <button id="overlay_cancel" type="button">Close</button>
                    `;
                showOverlayBox(400, 300, content);
            }
        });
    });
    $('#judges_table').on("click", ".delete", function() {
        let judge_id = this.id.split('_')[2]; // button id is equal to "del_judge_" + id
        let data = {judge_id: judge_id};
        $.ajax({
            type: "DELETE",
            url: "/judge",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data)
            {
                console.log(data.status_msg);
                populateJudges(data);
            }
        });
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
        loadCompetition(comp_id);
    });
    $("#sl_discipline_menu").on("click", "a", function() {
        let id_arr = this.id.split('_'); // button id is equal to "sl_" + day + "_" + block
        $('.sl_discipline_button').css('font-weight', 'normal');
        $(this).css('font-weight', 'bold');
        day = id_arr[1];
        block = id_arr[2];
        _cur_menu = {block: block, day: day};
        $.ajax({
            type: "GET",
            url: "/start_list?" + $.param(_cur_menu),
            success: function(data) {
                console.log(data.status_msg);
                if (data.start_list)
                    generateStartList(data.start_list);
                    _sl = data.start_list;
                    _sl_remove = [];
                    _sl_edited = false;
                    _sl_athletes = null;
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
    $("#sl_content").on("click", ".sl_edit_block", function() {
        let id_arr = this.id.split('_'); // button id is equal to "sl_edit_block_" + day + "_" + block
        let day = id_arr[3];
        let block = id_arr[4];
        let disciplines = _blocks[day][block]["dis_s"].split(", ");
        blockModify("edit", day, disciplines, block);
    });
    $("#sl_content").on("click", ".sl_pdf_button", function() {
        let id_arr = this.id.split('_'); // button id is equal to "sl_pdf_" + day + "_" + block
        let day = id_arr[2];
        let block = id_arr[3];
        let data = {
            day: day,
            block: block
        };
        getPDF("start_list", data);
    });
    $("#ll_lane_menu").on("click", "a", function() {
        let id_arr = this.id.split('_'); // button id is equal to "ll_" + day + "_" + block + "_" + lane
        let day = id_arr[1];
        let block = id_arr[2];
        let lane = id_arr[3];
        let data = {
            day: day,
            block: block,
            lane: lane
        };
        $.ajax({
            type: "GET",
            url: "/lane_list?" + $.param(data),
            success: function(data) {
                console.log(data.status_msg);
                let ll = "";
                if (data.lane_list) {
                    ll += "<a href='#' class='ll_pdf_button' id='ll_pdf_" + day + "_" + block + "_" + lane + "'>Print PDF</a>";
                    ll += "<table>";
                    ll += `
                        <tr>
                            <td>OT</td>
                            <td>Dis</td>
                            <td>Name</td>
                            <td>AP</td>
                            <td>PB</td>
                            <td>Nat.</td>
                            <td>NR</td>
                            <td>RP</td>
                            <td>Card</td>
                            <td>Remarks</td>
                        </tr>`;
                    for (let i = 0; i < data.lane_list.length; i++) {
                        ll += `
                            <tr>
                                <td>${data.lane_list[i].OT}</td>
                                <td>${data.lane_list[i].Dis}</td>
                                <td>${data.lane_list[i].Name}</td>
                                <td>${data.lane_list[i].AP}</td>
                                <td>${data.lane_list[i].PB}</td>
                                <td>${data.lane_list[i].Nat}</td>
                                <td>${data.lane_list[i].NR}</td>
                                <td>${data.lane_list[i].RP}</td>
                                <td>${data.lane_list[i].Card}</td>
                                <td>${data.lane_list[i].Remarks}</td>
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
    $("#ll_safety_all_pdf_button").click(function() {
        getPDF("lane_list", {"type": "safety"});
    });
    $("#ll_content").on("click", ".ll_pdf_button", function() {
        let id_arr = this.id.split('_'); // button id is equal to "ll_pdf_" + day + "_" + block + "_" + lane
        day = id_arr[2];
        block = id_arr[3];
        lane = id_arr[4];
        let data = {
            day: day,
            block: block,
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
            duration = removeBreak(i);
            addBreak(i, duration);
        }
        else if (_sl[i+1].Name == "Break") {
            if (i == 0) // don't allow break at 0
                return;
            duration = removeBreak(i+1);
            addBreak(i-1, duration);
        }
        else {
            [_sl[i].Name,        _sl[i+1].Name       ] = [_sl[i+1].Name,        _sl[i].Name       ];
            [_sl[i].AP,          _sl[i+1].AP         ] = [_sl[i+1].AP,          _sl[i].AP         ];
            [_sl[i].PB,          _sl[i+1].PB         ] = [_sl[i+1].PB,          _sl[i].PB         ];
            [_sl[i].Nationality, _sl[i+1].Nationality] = [_sl[i+1].Nationality, _sl[i].Nationality];
            [_sl[i].Id         , _sl[i+1].Id         ] = [_sl[i+1].Id         , _sl[i].Id         ];
            [_sl[i].Discipline , _sl[i+1].Discipline ] = [_sl[i+1].Discipline , _sl[i].Discipline ];
        }
        generateStartList(_sl);
        _sl_edited = true;
    });
    $('#sl_content').on('click', '.up', function() {
        let i = Number(this.id.split('_')[2]); // id is sl_up_${i}
        if (i < 1 || i >= _sl.length)
            return;
        if (_sl[i].Name == "Break") {
            duration = removeBreak(i);
            addBreak(i-2, duration);
        }
        else if (_sl[i-1].Name == "Break") {
            if (i == _sl.length-1)
                return; // don't allow break at end
            duration = removeBreak(i-1);
            addBreak(i-1, duration);
        }
        else {
            [_sl[i].Name,        _sl[i-1].Name       ] = [_sl[i-1].Name,        _sl[i].Name       ];
            [_sl[i].AP,          _sl[i-1].AP         ] = [_sl[i-1].AP,          _sl[i].AP         ];
            [_sl[i].PB,          _sl[i-1].PB         ] = [_sl[i-1].PB,          _sl[i].PB         ];
            [_sl[i].Nationality, _sl[i-1].Nationality] = [_sl[i-1].Nationality, _sl[i].Nationality];
            [_sl[i].Id         , _sl[i-1].Id         ] = [_sl[i-1].Id         , _sl[i].Id         ];
            [_sl[i].Discipline , _sl[i-1].Discipline ] = [_sl[i-1].Discipline , _sl[i].Discipline ];
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
                        <td><button id="overlay_cancel" type="button">Cancel</button></td>
                        <td><button id="sl_edit_save" type="button">Save</button></td>
                    </tr>
                </table>
                `;
        }
        else {
            let input = getPerformanceInput(_sl[i].Discipline, $("input[name='comp_type']:checked").val());
            let ap = _sl[i].AP;
            let pb = _sl[i].PB;
            if (_sl[i].Discipline == "STA") {
                ap = ap.padStart(5, "0");
                pb = pb.padStart(5, "0");
            }
            let ap_btn = `<input type="${input['type']}" step="${input['step']}" id="sl_edit_ap" value="${ap}"/>`;
            let pb_btn = `<input type="${input['type']}" step="${input['step']}" id="sl_edit_pb" value="${pb}"/>`;
            content = `
                Edit start of ${_sl[i].Name}<br>
                <input type="hidden" id="sl_edit_i" value="${i}"/>
                <table>
                    <tr>
                        <td>Discipline</td>
                        <td>${_sl[i].Discipline}</td>
                    </tr>
                    <tr>
                        <td>AP</td>
                        <td>${ap_btn}</td>
                    </tr>
                    <tr>
                        <td>PB</td>
                        <td>${pb_btn}</td>
                    </tr>
                    <tr>
                        <td>OT</td>
                        <td>
                            <input type="time" id="sl_edit_ot" value="${_sl[i].OT.padStart(5, '0')}"/>
                        </td>
                    </tr>
                    <tr>
                        <td><button id="overlay_cancel" type="button">Cancel</button></td>
                        <td><button id="sl_edit_save" type="button">Save</button></td>
                    </tr>
                </table>
                `;
        }
        showOverlayBox(400, 300, content);
    });
    $('#overlay_box').on('click', '#overlay_cancel', function() {
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
                _sl[i].AP = br_new;
            }
            else {
                if (_sl[i].Discipline == "STA") {
                    let ap = $('#sl_edit_ap')[0].valueAsDate;
                    _sl[i].AP = dateToStr(ap);
                    let pb = $('#sl_edit_pb')[0].valueAsDate;
                    _sl[i].PB = dateToStr(pb);
                } else {
                    _sl[i].AP = $('#sl_edit_ap').val();
                    _sl[i].PB = $('#sl_edit_pb').val();
                }
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
                            <td><button id="overlay_cancel" type="button">Cancel</button></td>
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
        function convertToInt(s) {
            if (s.Discipline == 'STA')
                return timeToMinutes(s.AP);
            else
                return Number(s.AP);
        }
        if (_sl.length == 0)
            return;
        let brs = [];
        for (let i = 0; i < _sl.length; i++) {
            if (_sl[i].Name == "Break")
                brs.push({i: i, time: _sl[i].AP});
        }
        for (let i = brs.length-1; i >= 0; i--)
            _sl.splice(brs[i].i, 1);
        _sl.sort((a,b) => Math.sign(convertToInt(a) - convertToInt(b)));
        for (let i = 0; i < brs.length; i++) {
            let break_entry = {Name: "Break", AP: brs[i].time, Nationality: "", Warmup: "", OT: "", Lane: "", Id: -1, Discipline: "", PB: ""};
            _sl.splice(brs[i].i, 0, break_entry);
        }
        calculateStartList();
    });
    $('#sl_content').on('click', '.remove', function() {
        let i = Number(this.id.split('_')[2]); // id is sl_remove_${i}
        if (i < 0 || i >= _sl.length || _sl[i].Name == "Break")
            return;
        if (_sl[i].Id >= 0)
            _sl_remove.push(_sl[i].Id);
        _sl.splice(i, 1);
        generateStartList(_sl);
        _sl_edited = true;
    });
    $('#sl_content').on('click', '#sl_add', function() {
        if (_cur_menu.block == "")
            return;
        $.ajax({
            type: "GET",
            url: "/athletes",
            success: function(data) {
                console.log(data.status_msg);
                let disciplines = _blocks[_cur_menu.day][_cur_menu.block]["dis_s"].split(', ');
                let ap_btn = `<input type="number" step="1" id="sl_add_ap" value="1"/>`;
                let pb_btn = `<input type="number" step="1" id="sl_add_pb" value="1"/>`;
                let cmas = $("input[name='comp_type']:checked").val() == "cmas";
                if (cmas && disciplines[0] in ["DNF", "DYN", "DYNB"]) { //TODO proper handling of multiple disciplines
                    ap_btn = `<input type="number" step="0.5" id="sl_add_ap" value="1"/>`;
                    pb_btn = `<input type="number" step="0.5" id="sl_add_pb" value="1"/>`;
                } else if (disciplines[0] == "STA") {
                    ap_btn = `<input type="time" id="sl_add_ap" value="00:01"/>`;
                    pb_btn = `<input type="time" id="sl_add_pb" value="00:01"/>`;
                }
                dis_chooser = "";
                for (let i = 0; i < disciplines.length; i++) {
                    let dis = disciplines[i];
                    let checked = i == 0 ? "checked" : "";
                    dis_chooser += `<input type="radio" name="sl_add_dis" value="${dis}" id="sl_add_dis_${dis}" ${checked}/>
                                    <label for="sl_add_dis_${dis}">${dis}</label><br>`;
                }
                content = `
                    Add athlete<br>
                    <table>
                        <tr>
                            <td>Athlete</td>
                            <td>
                                <select id="sl_add_athlete">
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td>Discipline</td>
                            <td>${dis_chooser}</td>
                        </tr>
                        <tr>
                            <td>AP</td>
                            <td>${ap_btn}</td>
                        </tr>
                        <tr>
                            <td>PB</td>
                            <td>${pb_btn}</td>
                        </tr>
                        <tr>
                            <td>OT</td>
                            <td><input type="time" id="sl_add_ot" value="00:00"/></td>
                        </tr>
                        <tr>
                            <td>Lane</td>
                            <td><input type="number" id="sl_add_lane" value="1"/></td>
                        </tr>
                        <tr>
                            <td><button id="overlay_cancel" type="button">Cancel</button></td>
                            <td><button id="sl_add_save" type="button">Save</button></td>
                        </tr>
                    </table>
                    `;
                showOverlayBox(400, 300, content);
                let sl_add_athlete = $('#sl_add_athlete');
                sl_add_athlete.empty();
                for (let i = 0; i < data.athletes.length; i++)
                    sl_add_athlete.append(new Option(data.athletes[i].first_name + " " + data.athletes[i].last_name, i));
                _sl_athletes = data.athletes;
            }
        });
    });
    $('#overlay_box').on('click', '#sl_add_save', function() {
        let i = Number($('#sl_add_athlete').find("option:selected").attr('value'));
        let dis = $("input[name='sl_add_dis']:checked").val();
        if (!$('#sl_add_ap') || isNaN(i) || i < 0 || i >= _sl_athletes.length)
            return;
        let new_entry = {Name: _sl_athletes[i].first_name + " " + _sl_athletes[i].last_name, AP: $('#sl_add_ap').val(), PB: $('#sl_add_pb').val(), Nationality: _sl_athletes[i].country, Warmup: "", OT: "", Lane: $('#sl_add_lane').val(), Id: -_sl_athletes[i].id, Discipline: dis};
        let ot = timeToMinutes($('#sl_add_ot').val());
        i = 0;
        for (; i < _sl.length; i++) {
            let ot_this = timeToMinutes(_sl[i].OT);
            if (ot < ot_this)
                break;
        }
        _sl.splice(i, 0, new_entry);
        setOT(i, $('#sl_add_ot')[0].valueAsDate);
        hideOverlayBox();
        generateStartList(_sl);
        _sl_edited = true;
        _sl_athletes = null;
    });
    $('#sl_content').on('click', '#sl_save', function() {
        let _sl_edited = false;
        let _sl_athletes = null;
        let data = {startlist: _sl, to_remove: _sl_remove, day: _cur_menu.day, block: _cur_menu.block};
        $.ajax({
            type: "PUT",
            url: "/start_list",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                generateStartList(data.start_list);
                _sl = data.start_list;
                _sl_remove = [];
                _sl_edited = false;
                _sl_athletes = null;
            }
        });
    });
    $('#results_content').on('click', '.result_add', function() {
        let id = Number(this.id.split('_')[1]); // id is result_${id}
        let name = $(`#result_Name_${id}`).html();
        let rp = 0;
        let content = generateResultContent("Add", name, rp, 0, "", "checked", "", "", "");
        _sl_athletes = id;
        showOverlayBox(400, 800, content);
    });
    $('#results_content').on('click', '.result_edit', function() {
        //TODO: card auto select and forbid
        //TODO: autoselect remarks
        let id = Number(this.id.split('_')[1]); // id is result_${id}
        let name = $(`#result_Name_${id}`).html();
        let rp = $(`#result_RP_${id}`).html();
        let ap = $(`#result_AP_${id}`).html();
        let card = $(`#result_Card_${id}`).html();
        let penalty = $(`#result_Penalty_${id}`).html();
        let remark = $(`#result_Remarks_${id}`).html();
        let judge_remark = $(`#result_JudgeRemarks_${id}`).html();
        let federation = $("input[name='comp_type']:checked").val();
        let penalty_not_reached_ap = penaltyUnderAP(rp, ap, card, federation, _cur_menu.discipline);
        let penalty_not_reached_ap_str = "";
        if (penalty_not_reached_ap != null) {
            penalty -= penalty_not_reached_ap;
            penalty_not_reached_ap_str = ` + ${penalty_not_reached_ap} (UNDER AP)`;
        }
        let rcw_checked = card == "WHITE" ? "checked" : "";
        let rcy_checked = card == "YELLOW" ? "checked" : "";
        let rcr_checked = card == "RED" ? "checked" : "";
        let content = generateResultContent("Edit", name, rp, penalty, penalty_not_reached_ap_str, rcw_checked, rcy_checked, rcr_checked, judge_remark);
        _sl_athletes = id;
        showOverlayBox(400, 800, content);
    });
    $('#overlay_box').on('click', '#result_save', function() {
        let rp = $('#result_rp').val();
        let penalty = $('#result_penalty').val();
        let card = $("input[name='result_card']:checked").val();
        let remarks = $.map($('input[name="result_remark"]:checked'), function (a) { return a.value; }).join();
        let judge_remarks = $('#result_judge_remarks').val();
        let id = _sl_athletes;
        _sl_athletes = null;
        let data = {id: id,
                    rp: rp,
                    penalty: penalty,
                    card: card,
                    remarks: remarks,
                    judge_remarks: judge_remarks,
                    discipline: _cur_menu.discipline, //TODO correct handling of new _cur_menu structure
                    gender: _cur_menu.gender,
                    country: _cur_menu.country};
        $.ajax({
            type: "PUT",
            url: "/result",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                hideOverlayBox();
                showResults(data.result, data.result_keys);
            }
        });
    });
    $('#sl_date_menu').on('click', '#sl_add_day', function() {
        blockModify("add");
    });
    $('#overlay_box').on('click', '#sl_modify_block_save', function() {
        let dis = $.map($('input[name="sl_modify_block_dis"]:checked'), function (a) { return a.value; });
        let day = $('#sl_modify_block_day').val();
        let type = $('#sl_modify_block_type').val();
        let block = $('#sl_modify_block_id').val();
        let data = {day: day, dis: dis, block: block};
        $.ajax({
            type: type == "add" ? "POST" : "UPDATE",
            url: "/block",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                hideOverlayBox();
                initSubmenus(data, true);
            }
        })
    });
    $('#overlay_box').on('click', '#sl_modify_block_remove', function() {
        let block = $('#sl_modify_block_id').val();
        let data = {block: block};
        $.ajax({
            type: "DELETE",
            url: "/block",
            data: JSON.stringify(data),
            contentType: "application/json",
            dataType: "json",
            success: function(data) {
                console.log(data.status_msg);
                hideOverlayBox();
                initSubmenus(data, true);
            }
        })
    });
});

function blockModify(type, day = "", disciplines = [], block = -1)
{
    let federation = $("input[name='comp_type']:checked").val();
    $.ajax({
        type: "GET",
        url: `disciplines/${federation}`,
        success: function(data) {
            let all_disciplines = data.disciplines;
            let dis_chooser = "";
            for (let i = 0; i < all_disciplines.length; i++)
            {
                let dis = all_disciplines[i];
                let checked = (disciplines.length > 0 && disciplines.includes(dis)) ? "checked" : "";
                dis_chooser += `<input type="checkbox" name="sl_modify_block_dis" value="${dis}" id="sl_modify_block_dis_${dis}" ${checked}/>
                                <label for="sl_modify_block_dis_${dis}">${dis}</label><br>`;
            }
            var typeU = type[0].toUpperCase() + type.slice(1);
            let day_value = day == "" ? "" : `value="${day}"`;
            let delete_btn = type == "edit" ? "&nbsp;<button id='sl_modify_block_remove' type='button'>Remove</button>" : "";
            content = `
                ${typeU} block<br>
                <input type="hidden" id="sl_modify_block_type" value="${type}"/>
                <input type="hidden" id="sl_modify_block_id" value="${block}"/>
                <table>
                    <tr>
                        <td>Day</td>
                        <td><input type="date" id="sl_modify_block_day" ${day_value}/></td>
                    </tr>
                    <tr>
                        <td>Disciplines</td>
                        <td>${dis_chooser}</td>
                    </tr>
                    <tr>
                        <td><button id="overlay_cancel" type="button">Cancel</button></td>
                        <td><button id="sl_modify_block_save" type="button">Save</button>${delete_btn}</td>
                    </tr>
                </table>
                `;
            showOverlayBox(400, 400, content);
        }
    });
}

function generateResultContent(type_str, name, rp, penalty, penalty_not_reached_ap, rcw_checked, rcy_checked, rcr_checked, judge_remarks) {
    let is_sta = _cur_menu.discipline == "STA";
    let rp_input_type = is_sta ? "time" : "number"; // TODO does not work for STA, change rp
    if (is_sta)
        rp = minutesToStr(rp, true);
    let federation = $("input[name='comp_type']:checked").val();
    let content = `
        ${type_str} result for ${name}<br>
        <table>
            <tr>
                <td>RP</td>
                <td><input type="${rp_input_type}" id="result_rp" value="${rp}"/></td>
            </tr>
            <tr>
                <td>Penalty</td>
                <td><input type="number" id="result_penalty" value="${penalty}"/>${penalty_not_reached_ap}</td>
            </tr>
            <tr>
                <td>Card</td>
                <td>
                    <div id="result_card_chooser">
                        <input type="radio" name="result_card" value="WHITE" id="result_card_white" ${rcw_checked}/>
                        <label for="result_card_white">WHITE</label>`;
     if (federation == "aida") {
        content +=     `<input type="radio" name="result_card" value="YELLOW" id="result_card_yellow" ${rcy_checked}/>
                        <label for="result_card_yellow">YELLOW</label>`;
     }
     content +=        `<input type="radio" name="result_card" value="RED" id="result_card_red" ${rcr_checked}/>
                        <label for="result_card_red">RED</label>
                    </div>
                </td>
            </tr>
            <tr>
                <td>Remark</td>
                <td>
                    <div id="result_remark_chooser">`;
     if (federation == "aida") {
        let aida_remarks = ["OK", "OTHER", "SHORT", "LATESTART", "GRAB", "LANYARD", "PULL", "TURN", "EARLYSTART", "START", "NO TAG", "UNDER AP", "DQSP", "DQJUMP", "DQOTHER", "DQAIRWAYS", "DQTOUCH", "DQLATESTART", "DQCHECK-IN", "DQBO-UW", "DQBO-SURFACE", "DQPULL", "DQOTHER-LANE", "DNS"];
        for (let i = 0; i < aida_remarks.length; i++) {
            let remark = aida_remarks[i];
            content += `<input type="checkbox" name="result_remark" value="${remark}" id="result_remark_${remark}"/>
                        <label for="result_remark_${remark}">${remark}</label><br>`;
        }
     }
     else {
        // TODO
     }
     content +=    `</div>
                </td>
            </tr>
            <tr>
                <td>Judge Remarks</td>
                <td><input type="text" id="result_judge_remarks" value="${judge_remarks}"/></td>
            </tr>
            <tr>
                <td><button id="overlay_cancel" type="button">Cancel</button></td>
                <td><button id="result_save" type="button">Save</button></td>
            </tr>
        </table>
        `;
    return content;
}

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
        _sl[i].Lane = convertNumericLaneToAcutal(lane);
        setOT(i, ot);
        lane = lane % no_lane + 1;
    }
    generateStartList(_sl);
    _sl_edited = true;
}

function addBreak(i, duration) {
    if (i >= 0 && i < _sl.length-1) {
        let break_str = null;
        let break_date = null;
        if (duration != null)
        {
            break_date = strToDate(duration);
            break_str = duration;
        } else {
            break_date = $('#sl_break_duration')[0].valueAsDate;
            break_str = dateToStr(break_date);
        }
        let break_entry = {Name: "Break", AP: break_str, Nationality: "", Warmup: "", OT: "", Lane: "", Id: -1, Discipline: "", PB: ""};
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
    duration = _sl[i].AP;
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
    return duration;
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
            } else if ("type" in params && params.type == "safety") {
                link.download = comp_name + "_" + type + "s_safety.pdf";
            } else if ("type" in params && params.type == "top3") {
                link.download = comp_name + "_" + type + "s_top3.pdf";
            } else {
                if (type == "start_list") {
                    let dis = params.block;
                    if (_blocks != null)
                        dis = _blocks[params.day][params.block]["dis_s"].replace(", ", "_");
                    link.download = comp_name + "_" + type + "_" + params.day + "_" + dis + ".pdf";
                } else if (type == "lane_list") {
                    let dis = params.block;
                    if (_blocks != null)
                        dis = _blocks[params.day][params.block]["dis_s"].replace(", ", "_");
                    link.download = comp_name + "_" + type + "_" + params.day + "_" + dis + "_" + params.lane + ".pdf";
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
    let tab_ids = ['settings', 'judges', 'athletes', 'registration', 'breaks', 'start_lists', 'lane_lists', 'results']
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

function populateJudges(data) {
    $('#judges_table').html(`
        <tr>
            <td>First name</td>
            <td>Last name</td>
            <td>Action</td>
        </tr>
        <tr>
            <td><input type="text" id="judge_first_name"/></td>
            <td><input type="text" id="judge_last_name"/></td>
            <td><button id="add_judge" type="button">Add</button></td>
        </tr>`);
    if (data.hasOwnProperty("judges")) {
        let judges = data.judges;
        for (let i = 0; i < judges.length; i++) {
            $('#judges_table').append(`
                <tr>
                    <td>${judges[i].first_name}</td>
                    <td>${judges[i].last_name}</td>
                    <td>
                        <button id="show_judge_${judges[i].id}" type="button" class="show">Show QR</button>
                        <button id="del_judge_${judges[i].id}" type="button" class="delete">Delete</button>
                    </td>
                </tr>
            `);
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
                    <td>${athletes[i].first_name}</td>
                    <td>${athletes[i].last_name}</td>
                    <td>${athletes[i].gender}</td>
                    <td>${athletes[i].country}</td>
                    <td>${athletes[i].club}</td>
                    <td>${athletes[i].aida_id}</td>
                    <td><button id="del_athlete_${athletes[i].id}" type="button" class="delete">Delete</button></td>
                </tr>
            `);
        }
        $('#total_athletes').html("<b>Total athletes: " + athletes.length + "</b>");
    }
}

function populateSpecialRanking(data) {
    // show special_ranking header always
    let special_ranking_name = $('#special_ranking_name').val();
    let registration_table = `
        <tr>
            <td>Last name</td>
            <td>First name</td>
            <td>Gender</td>
            <td>Country</td>
            <td>${special_ranking_name}</td>
            <td>Paid</td>
            <td>Medical</td>
            <td>Registered</td>
        </tr>
    `;
    if (data.hasOwnProperty("athletes")) {
        let athletes = data.athletes;
        for (let i = 0; i < athletes.length; i++) {
            let checked = ['special_ranking', 'paid', 'medical_checked', 'registered'];
            registration_table += `
                <tr>
                    <td>${athletes[i].last_name}</td>
                    <td>${athletes[i].first_name}</td>
                    <td>${athletes[i].gender}</td>
                    <td>${athletes[i].country}</td>`;
            for (let j = 0; j < checked.length; j++) {
                let c = "";
                if (athletes[i].hasOwnProperty(checked[j]) && athletes[i][checked[j]])
                    c = "checked";
                registration_table += `
                    <td><input type="checkbox" id="${checked[j].replace('_', '')}_cb_${athletes[i].id}" name="${athletes[i].id}" value="true" class="registration_checkbox" ${c}/></td>`;
            }
            registration_table += "</tr>";
        }
    }
    $('#registration_table').html(registration_table);
}

function setOTs(data)
{
    if ('ots' in data)
        _ots = data.ots
        // debug for ots
        //fillOtsForDebuggin();
        if (_audioTimeout)
            clearTimeout(_audioTimeout);
        schedulePlay();
}

function initSubmenus(data, reset=false)
{
    if (reset) {
        _days_with_disciplines_lanes = null;
        _blocks = null;
        _disciplines = null;
        _countries = null;
        _result_countries = null;
    }

    if (data.hasOwnProperty("days_with_disciplines_lanes") && data.days_with_disciplines_lanes != null)
        _days_with_disciplines_lanes = data.days_with_disciplines_lanes;

    if (data.hasOwnProperty("blocks") && data.blocks != null)
        _blocks = data.blocks;

    if (_days_with_disciplines_lanes != null) {
        // lane_list submenu
        let ll_date_menu = $('#ll_date_menu');
        let breaks_date_menu = $('#breaks_date_menu');
        ll_date_menu.empty();
        breaks_date_menu.empty();
        keys = Object.keys(_days_with_disciplines_lanes);
        for (let i = 0; i < keys.length; i++) {
            let day = keys[i];
            ll_date_menu.append("<a href='#' onclick='selectListDay(\"lane\", \"" + day + "\")'>" + day + "</a>&nbsp;");
            breaks_date_menu.append("<a href='#' id='breaks_" + day + "'>" + day + "</a>&nbsp;");
        }
    }

    // start_list submenu
    let sl_date_menu = $('#sl_date_menu');
    sl_date_menu.empty();
    if (_blocks != null) {
        keys = Object.keys(_blocks);
        for (let i = 0; i < keys.length; i++) {
            let day = keys[i];
            sl_date_menu.append("<a href='#' id='sl_day_" + day + "' class='sl_day' onclick='selectStartListDay(\"" + day + "\")'>" + day + "</a>&nbsp;");
        }
    }
    sl_date_menu.append("<button id='sl_add_day'>Add block</button>");

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
    $('#sl_discipline_menu').empty();
    $('#sl_content').empty();
    $('#ll_discipline_menu').empty();
    $('#ll_lane_menu').empty();
    $('#ll_content').empty();
    $('#result_gender_menu').empty();
    $('#result_country_menu').empty();
    $('#results_content').empty();
    $('#breaks_content').empty();
}

function selectListDay(type, day)
{
    if (_blocks != null && _blocks.hasOwnProperty(day)) {
        let l_discipline_menu = $('#ll_discipline_menu');
        l_discipline_menu.empty();
        blocks = Object.keys(_blocks[day]);
        for (let i = 0; i < blocks.length; i++)
        {
            let block = _blocks[day][blocks[i]];
            l_discipline_menu.append("<a href='#' onclick='selectLaneListDayDiscipline(\"" + day + "\", \"" + blocks[i] + "\")'>" + block['dis_s'] + "</a>&nbsp;");
        }
        $('#ll_lane_menu').empty();
        $('#ll_content').empty();
    }
}

function selectStartListDay(day)
{
    if (_blocks != null && _blocks.hasOwnProperty(day)) {
        $('.sl_day').css('font-weight', 'normal');
        $('.sl_discipline_button').css('font-weight', 'normal');
        $('#sl_day_' + day).css('font-weight', 'bold');
        let dis_menu = $('#sl_discipline_menu');
        dis_menu.empty();
        let blocks = Object.keys(_blocks[day]);
        for (let i = 0; i < blocks.length; i++) {
            let block = _blocks[day][blocks[i]];
            dis_menu.append("<a href='#' class='sl_discipline_button' id='sl_" + day + "_" + blocks[i] + "'>" + block['dis_s'] + "</a>&nbsp;");
        }
        $('#sl_content').empty();
    }
}

function selectLaneListDayDiscipline(day, block)
{
    if (_days_with_disciplines_lanes != null && _days_with_disciplines_lanes.hasOwnProperty(day)) {
        let l_lane_menu = $('#ll_lane_menu');
        l_lane_menu.empty();
        lanes = _blocks[day][block]['lanes'];
        for (let i = 0; i < lanes.length; i++)
        {
            let lane = lanes[i];
            l_lane_menu.append("<a href='#' class='ll_lane_button' id='ll_" + day + "_" + block + "_" + lane + "'>" + lane + "</a>&nbsp;");
        }
        $('#ll_content').empty();
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
    _cur_menu = {discipline: discipline, gender: gender, country: country};
    $.ajax({
        type: "GET",
        url: "/result?" + $.param(_cur_menu),
        success: function(data) {
            console.log(data.status_msg);
            showResults(data.result, data.result_keys);
        }
    });
}

function showResults(result, result_keys) {
    let res = "";
    if (result && result_keys) {
        res += "<a href='#' class='results_pdf_button' id='result_pdf_" + discipline + "_" + gender + "_" + country + "'>Print PDF</a>";
        res += "<table>";
        res += "<tr>"
        for (let j = 0; j < result_keys.length; j++)
        {
                res += `<td>${result_keys[j]}</td>`;
        }
        res += "<td/></tr>";
        let start_not_set_found = false;
        for (let i = 0; i < result.length; i++) {
            res += "<tr>"
            for (let j = 0; j < result_keys.length; j++)
            {
                    if (result[i]['Remarks'] == "" && !start_not_set_found) {
                        res += "</tr><td/><td style='padding-top:10px'><b>Athletes without result</b></td><tr>";
                        start_not_set_found = true;
                    }
                    res += `<td id='result_${result_keys[j]}_${result[i]["Id"]}'>${result[i][result_keys[j]]}</td>`;
            }
            if (discipline != "Overall" && discipline != $('#special_ranking_name').val()) {
                if (start_not_set_found)
                    res += `<td><button class='result_add' id='result_${result[i]["Id"]}'>Add result</button></td>`
                else
                    res += `<td><button class='result_edit' id='result_${result[i]["Id"]}'>Edit result</button></td>`
            }
            res += "</tr>";
        }
        res += "</table>";
    }
    let results_content = document.getElementById('results_content');
    results_content.innerHTML = res;
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
    let c1 = getDateNow(false);
    c1.setMinutes(c1.getMinutes() + 2);
    c1.setSeconds(c1.getSeconds() + 10);
    _ots.push(formatTime(c1, false, true));
    // countdown 2 = now + 4:50
    //let c2 = getDateNow(false);
    //c2.setMinutes(c2.getMinutes() + 4);
    //c2.setSeconds(c2.getSeconds() + 50);
    //_ots.push(formatTime(c2, false, true));
}

function loadCompetition(comp_id) {
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
            // Update clock link
            $('#clock_button').children()[0].href = "clock/" + comp_id + "/0";
            if ('special_ranking_name' in data)
            {
                $('#special_ranking_name').val(data.special_ranking_name);
            }
            populateSpecialRanking(data);
            populateAthletes(data);
            populateJudges(data);
            initSubmenus(data, true);
            if ('comp_name' in data) {
                $('#comp_name').val(data.comp_name);
            }
            if ("selected_country" in data) {
                if ($('#country_select option:contains(' + data.selected_country + ')').length) {
                    $('#country_select').val(data.selected_country);
                }
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
}

function convertNumericLaneToAcutal(ilane) {
    let lane_style = $("input[name='lane_style']:checked").val();
    return lane_style == "numeric" ? ilane : String.fromCharCode(64+ilane);
}

function convertActualLaneToNumeric(alane) {
    let lane_style = $("input[name='lane_style']:checked").val();
    return lane_style == "numeric" ? alane : alane.charCodeAt()-64;
}
