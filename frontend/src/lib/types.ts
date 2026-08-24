/*
 * Shared entity types for the Compy API. Shapes follow what the Flask
 * endpoints actually return (see compy_flask.py / compy_data.py).
 */

export interface Competition {
  comp_id: number
  name: string
  save_date: string
}

export interface Athlete {
  id: number
  first_name: string
  last_name: string
  gender: string
  country: string
  club: string
  aida_id: string
  eligible_national?: number
  special_ranking?: number
  paid?: number
  medical_checked?: number
  registered?: number
}

export interface Judge {
  id: number
  first_name: string
  last_name: string
}

/* blocks: {day: {block_key: {dis_s, lanes}}} (CompyData.getBlocks) */
export type Blocks = Record<string, Record<string, { dis_s: string; lanes: (string | number)[] }>>

/* {day: {discipline: lanes}} (CompyData.getDaysWithDisciplinesLanes) */
export type DaysWithDisciplinesLanes = Record<string, Record<string, (string | number)[]>>

/* One entry on the venue clock display (compy_data.py getClockData). */
export interface ClockStart {
  name: string
  country: string
  OT: string
  lane: string
  dns: boolean
}
