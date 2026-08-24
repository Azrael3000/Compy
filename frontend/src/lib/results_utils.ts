/*
 * Port of static/results_utils.js — framework-free freediving domain logic
 * shared by the results, judge, and admin screens. Function names and
 * behavior are kept identical to the original.
 */

export type Federation = 'aida' | 'cmas'
export type Card = 'WHITE' | 'YELLOW' | 'RED'

type RemarkGroups = Record<string, { General: string[]; Pool: string[]; Depth: string[] }>

export const REMARKS: Record<
  Federation,
  { WHITE: string; YELLOW: RemarkGroups; RED: RemarkGroups }
> = {
  aida: {
    WHITE: 'OK',
    YELLOW: {
      Penalties: {
        General: ['OTHER', 'SHORT', 'EARLYSTART', 'UNDER AP'],
        Pool: ['LATESTART', 'PULL', 'TURN', 'START'],
        Depth: ['GRAB', 'LANYARD', 'NO TAG'],
      },
    },
    RED: {
      DQ: {
        General: [
          'DQSP',
          'DQJUMP',
          'DQOTHER',
          'DQAIRWAYS',
          'DQTOUCH',
          'DQLATESTART',
          'DQCHECK-IN',
          'DQBO-UW',
          'DQBO-SURFACE',
          'DNS',
        ],
        Pool: ['DQOTHER-LANE'],
        Depth: ['DQPULL'],
      },
    },
  },
  cmas: {
    WHITE: '-',
    YELLOW: {
      Penalties: {
        General: ['DOLPHIN', 'ASSISTANT WARNED', 'POSTPONED'],
        Pool: ['NO WALL TOUCH', 'BODY STRAY'],
        Depth: [],
      },
    },
    RED: {
      DQSP: {
        General: ['DQ SP NO OK', 'DQ SP OK DIR', 'DQ SP HELP', 'DQ SP HEAD', 'DQ SP CHIN'],
        Pool: ['DQ SP OUT'],
        Depth: [],
      },
      'DQ ASSIST': {
        General: ['DQ ASSIST', 'DQ HELP DELEG', 'DQ TOUCH'],
        Pool: [],
        Depth: [],
      },
      'DQ BO': {
        General: ['DQ SURFACE BO', 'DQ UW BO'],
        Pool: [],
        Depth: [],
      },
      'DQ START': {
        General: ['DQ LATE START', 'DQ EARLY START'],
        Pool: [],
        Depth: [],
      },
      'DQ OTHER': {
        General: [
          'DQ SURFACING',
          'DQ INTERFERE',
          'DQ WEIGHT',
          'DQ O2',
          'DQ EQUIPMENT',
          'EARLY WARMUP',
          'DNS',
        ],
        Pool: ['DQ HOLD WALL', 'DQ WALL TURN'],
        Depth: [],
      },
    },
  },
}

export const POOL_DISCIPLINES = ['STA', 'DYN', 'DYNB', 'DNF']
export const DEPTH_DISCIPLINES = ['CNF', 'CWT', 'CWTB', 'FIM']
export const DISCIPLINES = POOL_DISCIPLINES.concat(DEPTH_DISCIPLINES)

export function isMainDiscipline(discipline: string): boolean {
  return DISCIPLINES.indexOf(discipline) > -1
}

export function timeToMinutes(time: string): number {
  const h = Number(time.split(':')[0])
  const m = Number(time.split(':')[1])
  return h * 60 + m
}

export function penaltyUnderAP(
  rp: string | number,
  ap: string | number,
  card: string,
  federation: string,
  discipline: string,
): number | null {
  if (federation !== 'aida' || card !== 'YELLOW') {
    return null
  }

  let penaltyNotReachedAp = 0
  if (discipline === 'STA') {
    rp = timeToMinutes(String(rp))
    ap = timeToMinutes(String(ap))
  }
  const rpNum = Number(rp)
  const apNum = Number(ap)
  if (apNum > rpNum) {
    const delta = apNum - rpNum
    let factor = 1.0
    if (discipline === 'STA') {
      factor = 0.2
    } else if (discipline[0] === 'D') {
      factor = 0.5
    }
    penaltyNotReachedAp = delta * factor
  }
  if (penaltyNotReachedAp > 0) {
    return Math.round(penaltyNotReachedAp * 100) / 100
  }
  return null
}

export function getRemarksFromDiscipline(
  federation: Federation,
  card: 'YELLOW' | 'RED',
  discipline: string,
): Record<string, string[]> | null {
  let disType = ''
  if (POOL_DISCIPLINES.indexOf(discipline) > -1) {
    disType = 'Pool'
  } else if (DEPTH_DISCIPLINES.indexOf(discipline) > -1) {
    disType = 'Depth'
  }
  if (disType !== '') {
    const remarks: Record<string, string[]> = {}
    const all = REMARKS[federation][card]
    for (const type in all) {
      remarks[type] = all[type].General.concat(all[type][disType as 'Pool' | 'Depth'])
    }
    return remarks
  }
  return null
}

export function getAllFrom(
  federation: Federation,
  card: 'YELLOW' | 'RED',
  discipline: string,
): string[] {
  return Array.from(
    Object.values(getRemarksFromDiscipline(federation, card, discipline) ?? {}),
  ).flat()
}

export function getRemarksFromStr(
  str: string,
  federation: Federation,
  discipline: string,
): string[] {
  const allRemarks = str.split(',').map((i) => i.trim())
  const validRemarks: string[] = []
  for (const remark of allRemarks) {
    if (
      REMARKS[federation].WHITE === remark ||
      getAllFrom(federation, 'YELLOW', discipline).includes(remark) ||
      getAllFrom(federation, 'RED', discipline).includes(remark)
    ) {
      validRemarks.push(remark)
    }
  }
  return validRemarks
}

export function isValidCard(card: string, federation: Federation): boolean {
  return Object.keys(REMARKS[federation]).includes(card)
}

export function getRemarksForCard(
  card: Card,
  federation: Federation,
  discipline: string,
): string | Record<string, string[]> {
  if (card === 'WHITE') {
    return REMARKS[federation].WHITE
  }
  if (card === 'YELLOW') {
    return getRemarksFromDiscipline(federation, 'YELLOW', discipline) ?? {}
  }
  return Object.assign(
    {},
    getRemarksFromDiscipline(federation, 'YELLOW', discipline),
    getRemarksFromDiscipline(federation, 'RED', discipline),
  )
}

export function getPerformanceInput(
  discipline: string,
  federation: Federation,
): { type: 'time' | 'number'; step: number | '' } {
  if (discipline === 'STA') {
    return { type: 'time', step: '' }
  } else if (federation === 'cmas' && discipline[0] === 'D') {
    return { type: 'number', step: 0.5 }
  } else {
    return { type: 'number', step: 1 }
  }
}

export function getDefaultRemark(card: Card, federation: Federation): string {
  if (card === 'WHITE') {
    return REMARKS[federation].WHITE
  } else {
    return ''
  }
}
