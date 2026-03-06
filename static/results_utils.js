var REMARKS = {
    'aida': {
        'WHITE': 'OK',
        'YELLOW': {
            'Penalties': ["OTHER", "SHORT", "LATESTART", "GRAB", "LANYARD", "PULL", "TURN", "EARLYSTART", "START", "NO TAG", "UNDER AP"],
        },
        'RED': {
            'DQ': ["DQSP", "DQJUMP", "DQOTHER", "DQAIRWAYS", "DQTOUCH", "DQLATESTART", "DQCHECK-IN", "DQBO-UW", "DQBO-SURFACE", "DQPULL", "DQOTHER-LANE", "DNS"]
        }
    },
    'cmas': {
        'WHITE': '-',
        'YELLOW': {
            'Penalties': ['NO WALL TOUCH', 'DOLPHIN', 'BODY STRAY', 'ASSISTANT WARNED', 'POSTPONED']
        },
        'RED': {
            'DQSP': ['DQ SP NO OK', 'DQ SP OK DIR', 'DQ SP HELP', 'DQ SP HEAD', 'DQ SP CHIN', 'DQ SP OUT'],
            'DQ ASSIST': ['DQ ASSIST', 'DQ HELP DELEG', 'DQ TOUCH'],
            'DQ BO': ['DQ SURFACE BO', 'DQ UW BO'],
            'DQ START': ['DQ LATE START', 'DQ EARLY START'],
            'DQ OTHER': ['DQ HOLD WALL', 'DQ WALL TURN', 'DQ SURFACING', 'DQ INTERFERE', 'DQ WEIGHT', 'DQ O2', 'DQ EQUIPMENT', 'EARLY WARMUP', 'DNS']
        }
    }
};

function penaltyUnderAP(rp, ap, card, federation, discipline) {
    if (federation != "aida" || card != "YELLOW")
        return null;

    penalty_not_reached_ap = 0;
    if (discipline == "STA") {
        rp = timeToMinutes(rp);
        ap = timeToMinutes(ap);
    }
    if (ap > rp) {
        let delta = ap - rp;
        let factor = discipline == "STA" ? 0.2 : (discipline[0] == "D" ? 0.5 : 1.);
        penalty_not_reached_ap = delta*factor;
    }
    if (penalty_not_reached_ap > 0)
        return Math.round(penalty_not_reached_ap*100)/100.;
    return null;
}

function getAllFrom(federation, card) {
    return Array.from(Object.values(REMARKS[federation][card])).flat();
}

function getRemarksFromStr(str, federation) {
    let all_remarks = str.split(',')
                         .map(function(i){ return i.trim(); });
    let valid_remarks = [];
    for (let i = 0; i < str.length; i++) {
        if (REMARKS[federation]['WHITE'] == all_remarks[i] ||
            getAllFrom(federation, 'YELLOW').includes(all_remarks[i]) ||
            getAllFrom(federation, 'RED').includes(all_remarks[i])) {
            valid_remarks.push(all_remarks[i]);
        }
    }
    return valid_remarks;
}

function isValidCard(card, federation) {
    let all_cards = Object.keys(REMARKS[federation]);
    return all_cards.includes(card);
}

function getRemarksForCard(card, federation) {
    if (card == 'WHITE') {
        return REMARKS[federation]['WHITE'];
    }
    if (card == 'YELLOW') {
        return REMARKS[federation]['YELLOW'];
    }
    return Object.assign({}, REMARKS[federation]['YELLOW'], REMARKS[federation]['RED']);
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
