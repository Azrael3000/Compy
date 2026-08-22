/*
 * Response contracts of the admin endpoints in compy_flask.py.
 *
 * The server's convention is that mutation responses carry the refreshed
 * datasets back to the client; DataPayload lists every dataset an endpoint
 * may include, and applyResponse() in AdminApp merges whatever is present
 * into the admin state.
 */
import type { Envelope } from '@/lib/api'
import type { Athlete, Blocks, Competition, DaysWithDisciplinesLanes, Judge } from '@/lib/types'
import type { StartEntry } from './sl_utils'

export interface DataPayload extends Envelope {
  days_with_disciplines_lanes?: DaysWithDisciplinesLanes | null
  blocks?: Blocks | null
  disciplines?: string[] | null
  countries?: string[] | null
  result_countries?: string[] | null
  athletes?: Athlete[] | null
  judges?: Judge[] | null
  competitions?: Competition[] | null
  special_ranking_name?: string | null
  aida_event_id?: number | null
  aida_has_key?: boolean
  ots?: string[] | null
}

/* GET /admin_data */
export interface AdminDataResponse extends Envelope {
  version: string
  competitions: Competition[] | null
  comp_name: string
}

/* POST /load_comp */
export interface LoadCompResponse extends DataPayload {
  comp_name?: string
  selected_country?: string
  lane_style?: 'numeric' | 'alphabetic'
  comp_type?: 'aida' | 'cmas'
  publish_results?: boolean
}

/* POST /competition */
export interface SaveCompResponse extends DataPayload {
  comp_id?: number | null
  file_exists?: boolean
  prev_name?: string
}

/* GET /judge/qr_code */
export interface QrCodeResponse extends Envelope {
  judge_first_name: string
  judge_last_name: string
  judge_url: string
  judge_qr_code: string
}

/* GET|PUT /start_list */
export interface StartListResponse extends DataPayload {
  start_list?: StartEntry[]
}

/* GET /athletes */
export interface AthleteListResponse extends Envelope {
  athletes: Athlete[]
}

/* GET /disciplines/<federation> */
export interface DisciplinesResponse extends Envelope {
  disciplines: string[]
}

/* GET|PUT /result — the columns are server-defined via `keys` */
export type ResultRow = Record<string, string | number>

export interface AdminResultResponse extends Envelope {
  results?: ResultRow[] | null
  keys?: string[] | null
}

/* GET /lane_list */
export interface LaneRow {
  OT: string
  Dis: string
  Name: string
  AP: string
  PB: string
  Nat: string
  NR: string
  RP: string
  Card: string
  Remarks: string
}

export interface LaneListResponse extends Envelope {
  lane_list?: LaneRow[]
}

/* GET /breaks */
export interface BreakRow {
  Name: string
  Dis1: string
  OT1: string
  Dis2: string
  OT2: string
  Break: string
}

export interface BreaksResponse extends Envelope {
  min_break?: string
  breaks_list?: BreakRow[]
}
