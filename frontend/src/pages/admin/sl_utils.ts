/* Start-list time/lane helpers ported from static/compy.js. */
import { timeToMinutes } from '@/lib/results_utils'

export interface StartEntry {
  Name: string
  Discipline: string
  AP: string
  PB: string
  Nationality: string
  Warmup: string
  OT: string
  Lane: string | number
  Id: number
  'Dive Time': string
}

export function dateToStr(date: Date, hZeroPad = false): string {
  let hStr = date.getUTCHours().toString()
  if (hZeroPad) {
    hStr = hStr.padStart(2, '0')
  }
  return hStr + ':' + date.getMinutes().toString().padStart(2, '0')
}

export function strToDate(str: string): Date {
  const date = new Date()
  date.setUTCHours(Number(str.split(':')[0]))
  date.setMinutes(Number(str.split(':')[1]))
  return date
}

export function minutesToStr(mins: number, padH = false): string {
  const m = mins % 60
  let hStr = Math.round((mins - m) / 60).toString()
  if (padH) {
    hStr = hStr.padStart(2, '0')
  }
  return hStr + ':' + m.toString().padStart(2, '0')
}

export function convertNumericLaneToActual(ilane: number, numeric: boolean): string | number {
  return numeric ? ilane : String.fromCharCode(64 + ilane)
}

export function convertActualLaneToNumeric(alane: string | number, numeric: boolean): number {
  return numeric ? Number(alane) : String(alane).charCodeAt(0) - 64
}

export function makeBreakEntry(duration: string): StartEntry {
  return {
    Name: 'Break',
    AP: duration,
    Nationality: '',
    Warmup: '',
    OT: '',
    Lane: '',
    Id: -1,
    Discipline: '',
    PB: '',
    'Dive Time': '',
  }
}

export function setOT(sl: StartEntry[], i: number, ot: Date) {
  sl[i].OT = dateToStr(ot)
  const wt = new Date(ot)
  wt.setMinutes(wt.getMinutes() - 45)
  sl[i].Warmup = dateToStr(wt)
}

export function adjustOTbyDiff(sl: StartEntry[], j: number, diff: number) {
  if (sl[j].Name !== 'Break') {
    const otThis = strToDate(sl[j].OT)
    otThis.setMinutes(otThis.getMinutes() + diff)
    setOT(sl, j, otThis)
  }
}

export function swapStartList(sl: StartEntry[], i: number, j: number) {
  /* everything except OT/Warmup/Lane swaps (those belong to the slot) */
  ;[sl[i].Name, sl[j].Name] = [sl[j].Name, sl[i].Name]
  ;[sl[i].AP, sl[j].AP] = [sl[j].AP, sl[i].AP]
  ;[sl[i].PB, sl[j].PB] = [sl[j].PB, sl[i].PB]
  ;[sl[i].Nationality, sl[j].Nationality] = [sl[j].Nationality, sl[i].Nationality]
  ;[sl[i].Id, sl[j].Id] = [sl[j].Id, sl[i].Id]
  ;[sl[i].Discipline, sl[j].Discipline] = [sl[j].Discipline, sl[i].Discipline]
  ;[sl[i]['Dive Time'], sl[j]['Dive Time']] = [sl[j]['Dive Time'], sl[i]['Dive Time']]
}

export function addBreakAt(sl: StartEntry[], i: number, duration: string) {
  if (i >= 0 && i < sl.length - 1) {
    const breakDate = strToDate(duration)
    sl.splice(i + 1, 0, makeBreakEntry(duration))
    const otOld = timeToMinutes(sl[i + 2].OT)
    const otPrev = timeToMinutes(sl[i].OT)
    const otNew = otPrev + breakDate.getUTCHours() * 60 + breakDate.getMinutes()
    const diff = otNew - otOld
    for (let j = i + 2; j < sl.length; j++) {
      adjustOTbyDiff(sl, j, diff)
    }
  }
}

export function removeBreakAt(sl: StartEntry[], i: number, interval: string): string | undefined {
  if (i === 0 || i === sl.length - 1) {
    return
  }
  const duration = sl[i].AP
  sl.splice(i, 1)
  /* if interval is not set, remove the break but don't change anything */
  if (interval) {
    const intervalDate = strToDate(interval)
    const otOld = timeToMinutes(sl[i].OT)
    const otPrev = timeToMinutes(sl[i - 1].OT)
    const otNew = otPrev + intervalDate.getUTCHours() * 60 + intervalDate.getMinutes()
    const diff = otNew - otOld
    for (let j = i; j < sl.length; j++) {
      adjustOTbyDiff(sl, j, diff)
    }
  }
  return duration
}

function hms(hours: number, minutes: number, seconds: number): string {
  return (
    hours.toString().padStart(2, '0') +
    ':' +
    minutes.toString().padStart(2, '0') +
    ':' +
    seconds.toString().padStart(2, '0')
  )
}

/* wall-clock display for the admin header */
export function formatTime(date: Date): string {
  return hms(date.getHours(), date.getMinutes(), date.getSeconds())
}

/* countdown display for a distance in milliseconds; -1 means "no next OT" */
export function formatCountdown(distance: number): string {
  if (distance < 0) {
    return 'n/a'
  }
  /* +1 s so the 59->00 flip in the clock matches the 01->00 flip here */
  const tenths = Math.ceil((distance + 1000) / 100)
  const days = Math.floor(tenths / (10 * 60 * 60 * 24))
  const hours = Math.floor((tenths % (10 * 60 * 60 * 24)) / (10 * 60 * 60))
  const minutes = Math.floor((tenths % (10 * 60 * 60)) / (10 * 60))
  const seconds = Math.floor((tenths % (10 * 60)) / 10)
  const timeStr = hms(hours, minutes, seconds)
  return days > 0 ? days.toString().padStart(2, '0') + ' days ' + timeStr : timeStr
}
