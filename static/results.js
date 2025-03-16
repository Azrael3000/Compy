var REMARKS = {
    'aida': {
        'WHITE': ['OK'],
        'YELLOW': ["OTHER", "SHORT", "LATESTART", "GRAB", "LANYARD", "PULL", "TURN", "EARLYSTART", "START", "NO TAG", "UNDER AP"],
        'RED': ["DQSP", "DQJUMP", "DQOTHER", "DQAIRWAYS", "DQTOUCH", "DQLATESTART", "DQCHECK-IN", "DQBO-UW", "DQBO-SURFACE", "DQPULL", "DQOTHER-LANE", "DNS"]
    },
    'cmas': {
        'WHITE': ['-'],
        'YELLOW': ['-'],
        'RED': ['DQ early start', 'DQOTHER', 'DQ SP', 'DQ SP out', 'DQ surface BO', 'DQ underwater BO']
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

function getRemarksFromStr(str, federation) {
    let all_remarks = str.split(',')
                         .map(function(i){ return i.trim(); });
    let valid_remarks = [];
    for (let i = 0; i < str.length; i++) {
        if (REMARKS[federation]['WHITE'].includes(all_remarks[i]) ||
            REMARKS[federation]['YELLOW'].includes(all_remarks[i]) ||
            REMARKS[federation]['RED'].includes(all_remarks[i])) {
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
    if (card != 'RED') {
        return REMARKS[federation][card];
    }
    return REMARKS[federation]['YELLOW'].concat(REMARKS[federation]['RED']);
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
