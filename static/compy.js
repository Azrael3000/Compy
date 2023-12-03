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
                        newcomer_table.innerHTML += `
                            <tr>
                                <td>${athletes[i].last_name}</td>
                                <td>${athletes[i].first_name}</td>
                                <td>${athletes[i].gender}</td>
                                <td>${athletes[i].country}</td>
                                <td><input type="checkbox" id="nc_cb_${athletes[i].id}" name="${athletes[i].id}" value="true" class="newcomer_checkbox"/></td>
                            </tr>
                        `;
                    }
                }
            },
        })
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
});

function switchTo(id) {
    let tab_ids = ['settings', 'newcomer']
    for (let i = 0; i < tab_ids.length; i++) {
        let element = document.getElementById(tab_ids[i]);
        if (tab_ids[i] === id) {
            element.style.display = "block";
        } else {
            element.style.display = "none";
        }
    }
}
