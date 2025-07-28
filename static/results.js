class ResultMenu {
    constructor() {
        this.comp_id = null;
        this.comp_name = null;
        this.discipline = null;
        this.gender = null;
        this.country = null;
    }
    getDict() {
        return {comp_id: this.comp_id, discipline: this.discipline, gender: this.gender, country: this.country};
    }
}

var _comp_list = null;
var _menu = null;
var _disciplines = null;
var _countries = null;

function init(data) {
    _comp_list = null;
    _menu = new ResultMenu();
    _disciplines = null;
    _countries = null;
    if ('comp_list' in data) {
        _comp_list = data.comp_list;
        showCompMenu();
    } else {
        _menu.comp_id = data.comp_id;
        _menu.comp_name = data.comp_name;
        _disciplines = data.disciplines;
        _countries = data.countries;
        showDisciplineMenu(_disciplines, "discipline");
    }
}

function showCompMenu() {
    $('#header').empty();
    $('#content').empty();
    if (_comp_list == null)
        return;
    let content = "";
    for (let i = 0; i < _comp_list.length; i++) {
        content += `<button id="comp_${_comp_list[i].id}" type="button" class="comp_menu" onclick="location.href='?comp_id=${_comp_list[i].id}';">${_comp_list[i].name}</button>`;
    }
    $('#content').html(content);
}

function getTitleDiv() {
    return `<div id="title">${_menu.comp_name}</div>`;
}

function showDisciplineMenu(list, list_name) {
    $('#content').empty();
    if (list == null)
        return;
    let content = "";
    for (let i = 0; i < list.length; i++) {
        content += `<button id="list_${i}" type="button" class="list_menu ${list_name}">${list[i]}</button>`;
    }
    $('#content').html(content);
    $('#header').html(getTitleDiv());
}

function showResult() {
    $('#content').empty();
    if (_menu.gender == null) {
        _menu.gender = "Female";
    }
    if (_menu.country == null) {
        _menu.country = 0;
        for (let i = 0; i < _countries.length; i++) {
            if (_countries[i] == 'International') {
                _menu.country = i;
            }
        }
    }
    let discipline = _disciplines[_menu.discipline];
    let country = _countries[_menu.country];
    let gender = _menu.gender;
    $('#header').html(
      `${getTitleDiv()}
       <div>
         <div id="discipline">${discipline}</div>
         <div id="gender">${gender}</div>
         <div id="country">${country}</div>
       </div>`
     );

     $.ajax({
        type: 'GET',
        url:"/results_list?" + $.param(_menu.getDict()),
        success: function(data) {
            if (!'results' in data) {
                showError("Invalid response.");
                return;
            }

            let table = "<table>";
            let len = data.results.length;
            for (let i = 0; i < len; i++) {
                card_class = "";
                if (data.results[i].card != null && data.results[i].card != "WHITE") {
                    card_class = data.results[i].card;
                }
                table += `
                    <tr>
                        <td>${data.results[i].rank}</td>
                        <td>${data.results[i].name}</td>
                        <td class="${card_class}">${data.results[i].value}</td>
                    </tr>`;
            }
            table += "</table>";
            $('#content').html(table);
        },
        error: function(xhr) {
            showError("Failed to get result data.");
        }
     });
}

function showError(error_msg) {
    $('#content').html(`<div class="error">${error_msg}</div>`);
}

$(document).ready(function() {
    $('#content').on('click', '.list_menu', function () {
        let list_id = this.id.split('_')[1];
        if (this.classList[1] == 'discipline') {
            _menu.discipline = list_id;
        } else if (this.classList[1] == 'country') {
            _menu.country = list_id;
        }
        showResult();
    });
    $('#header').on('click', '#title', function () {
        location.assign('results');
    });
    $('#header').on('click', '#discipline', function () {
        showDisciplineMenu(_disciplines, "discipline");
    });
    $('#header').on('click', '#gender', function () {
        _menu.gender = _menu.gender == "Female" ? "Male" : "Female";
        showResult();
    });
    $('#header').on('click', '#country', function () {
        showDisciplineMenu(_countries, "country");
    });
});
