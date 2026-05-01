var REMARKS = {
    'aida': {
        'WHITE': 'OK',
        'YELLOW': {
            'Penalties': {
                'General': ["OTHER", "SHORT", "EARLYSTART", "UNDER AP"],
                'Pool': ["LATESTART", "PULL", "TURN", "START"],
                'Depth': ["GRAB", "LANYARD", "NO TAG"]
            },
        },
        'RED': {
            'DQ': {
                'General': ["DQSP", "DQJUMP", "DQOTHER", "DQAIRWAYS", "DQTOUCH", "DQLATESTART", "DQCHECK-IN", "DQBO-UW", "DQBO-SURFACE", "DNS"],
                'Pool': ["DQOTHER-LANE"],
                'Depth': ["DQPULL"]
            }
        }
    },
    'cmas': {
        'WHITE': '-',
        'YELLOW': {
            'Penalties': {
                'General': ['DOLPHIN', 'ASSISTANT WARNED', 'POSTPONED'],
                'Pool': ['NO WALL TOUCH', 'BODY STRAY'],
                'Depth': []
            }
        },
        'RED': {
            'DQSP': {
                'General': ['DQ SP NO OK', 'DQ SP OK DIR', 'DQ SP HELP', 'DQ SP HEAD', 'DQ SP CHIN'],
                'Pool': ['DQ SP OUT'],
                'Depth': []
            },
            'DQ ASSIST': {
                'General': ['DQ ASSIST', 'DQ HELP DELEG', 'DQ TOUCH'],
                'Pool': [],
                'Depth': []
            },
            'DQ BO': {
                'General': ['DQ SURFACE BO', 'DQ UW BO'],
                'Pool': [],
                'Depth': []
            },
            'DQ START': {
                'General': ['DQ LATE START', 'DQ EARLY START'],
                'Pool': [],
                'Depth': []
            },
            'DQ OTHER': {
                'General': ['DQ SURFACING', 'DQ INTERFERE', 'DQ WEIGHT', 'DQ O2', 'DQ EQUIPMENT', 'EARLY WARMUP', 'DNS'],
                'Pool': ['DQ HOLD WALL', 'DQ WALL TURN'],
                'Depth': []
            }
        }
    }
};

var POOL_DISCIPLINES = ['STA', 'DYN', 'DYNB', 'DNF'];
var DEPTH_DISCIPLINES = ['CNF', 'CWT', 'CWTB', 'FIM'];
var DISCIPLINES = POOL_DISCIPLINES.concat(DEPTH_DISCIPLINES);

function isMainDiscipline(discipline) {
    return DISCIPLINES.indexOf(discipline) > -1;
}

function penaltyUnderAP(rp, ap, card, federation, discipline) {
    if (federation != "aida" || card != "YELLOW")
        return null;

    penalty_not_reached_ap = 0;
    if (discipline == "STA") {
        rp = timeToMinutes(rp);
        ap = timeToMinutes(ap);
    }
    rp = Number(rp)
    ap = Number(ap)
    if (ap > rp) {
        let delta = ap - rp;
        let factor = discipline == "STA" ? 0.2 : (discipline[0] == "D" ? 0.5 : 1.);
        penalty_not_reached_ap = delta*factor;
    }
    if (penalty_not_reached_ap > 0)
        return Math.round(penalty_not_reached_ap*100)/100.;
    return null;
}

function getRemarksFromDiscipline(federation, card, discipline) {
    let disType = POOL_DISCIPLINES.indexOf(discipline) > -1 ?
                  "Pool" :
                  (DEPTH_DISCIPLINES.indexOf(discipline) > -1 ? "Depth" : "");
    if (disType != "") {
        let remarks = {};
        let all = REMARKS[federation][card];
        for (let type in all) {
            remarks[type] = all[type]['General'].concat(all[type][disType]);
        }
        return remarks;
    }
    return null;
}

function getAllFrom(federation, card, discipline) {
    return Array.from(Object.values(getRemarksFromDiscipline(federation, card, discipline))).flat();
}

function getRemarksFromStr(str, federation, discipline) {
    let all_remarks = str.split(',')
                         .map(function(i){ return i.trim(); });
    let valid_remarks = [];
    for (let i = 0; i < str.length; i++) {
        if (REMARKS[federation]['WHITE'] == all_remarks[i] ||
            getAllFrom(federation, 'YELLOW', discipline).includes(all_remarks[i]) ||
            getAllFrom(federation, 'RED', discipline).includes(all_remarks[i])) {
            valid_remarks.push(all_remarks[i]);
        }
    }
    return valid_remarks;
}

function isValidCard(card, federation) {
    let all_cards = Object.keys(REMARKS[federation]);
    return all_cards.includes(card);
}

function getRemarksForCard(card, federation, discipline) {
    if (card == 'WHITE') {
        return REMARKS[federation]['WHITE'];
    }
    if (card == 'YELLOW') {
        return getRemarksFromDiscipline(federation, 'YELLOW', discipline);
    }
    return Object.assign({},
        getRemarksFromDiscipline(federation, 'YELLOW', discipline),
        getRemarksFromDiscipline(federation, 'RED', discipline));
}

function getPerformanceInput(discipline, federation) {
    if (discipline == "STA")
        return { 'type': 'time', 'step': "" };
    else if (federation == "cmas" && discipline[0] == 'D')
        return { 'type': 'number', 'step': 0.5 };
    else
        return { 'type': 'number', 'step': 1 };
}

function timeToMinutes(time) {
    let h = Number(time.split(':')[0]);
    let m = Number(time.split(':')[1]);
    return h*60 + m;
}

function getDefaultRemark(card, federation) {
    if (card == 'WHITE')
        return REMARKS[federation][card];
    else
        return "";
}
