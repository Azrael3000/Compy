import { useState } from 'react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { DialogTitle } from '@/components/ui/dialog'
import type {
  AthleteListResponse,
  DataPayload,
  DisciplinesResponse,
  StartListResponse,
} from '../contracts'
import { DEPTH_DISCIPLINES, getPerformanceInput, timeToMinutes } from '@/lib/results_utils'
import { useAdmin } from '../AdminApp'
import {
  adjustOTbyDiff,
  addBreakAt,
  convertActualLaneToNumeric,
  convertNumericLaneToActual,
  dateToStr,
  makeBreakEntry,
  minutesToStr,
  removeBreakAt,
  setOT,
  strToDate,
  swapStartList,
  type StartEntry,
} from '../sl_utils'

export function StartListsTab() {
  const admin = useAdmin()
  const { state, applyResponse, withCompId, showOverlay, hideOverlay, getPDF, reportError } = admin
  const [curDay, setCurDay] = useState<string | null>(null)
  const [curBlock, setCurBlock] = useState<string | null>(null)
  const [sl, setSl] = useState<StartEntry[] | null>(null)
  const [slRemove, setSlRemove] = useState<number[]>([])
  /* the three recalc inputs (start time / interval / number of lanes) */
  const [startTime, setStartTime] = useState('')
  const [interval, setIntervalStr] = useState('')
  const [noLanes, setNoLanes] = useState(1)

  const numeric = state.laneStyle === 'numeric'

  /* derived defaults after (re)loading a list — port of generateStartList's
   * max_lane / interval detection */
  function deriveInputs(list: StartEntry[]) {
    let maxLane = 1
    let detected = 0
    let intervalOt1 = 0
    for (const entry of list) {
      if (
        intervalOt1 === 0 &&
        String(entry.Lane) === String(convertNumericLaneToActual(1, numeric)) &&
        detected === 0
      ) {
        intervalOt1 = timeToMinutes(entry.OT)
      }
      if (entry.Name === 'Break') {
        intervalOt1 = 0
      } else {
        maxLane = Math.max(maxLane, convertActualLaneToNumeric(entry.Lane, numeric))
      }
      if (
        detected === 0 &&
        String(entry.Lane) === String(convertNumericLaneToActual(1, numeric)) &&
        intervalOt1 !== 0
      ) {
        detected = Math.max(timeToMinutes(entry.OT) - intervalOt1, 0)
      }
    }
    setNoLanes(maxLane)
    if (list.length > 1) {
      setStartTime(list[0].OT.padStart(5, '0'))
    }
    if (detected > 0) {
      setIntervalStr(minutesToStr(detected, true))
    }
  }

  function loadBlock(day: string, block: string) {
    setCurDay(day)
    setCurBlock(block)
    api
      .get<StartListResponse>('/start_list', withCompId({ day, block }))
      .then((data) => {
        if (data.start_list) {
          const list = data.start_list
          setSl(list)
          setSlRemove([])
          deriveInputs(list)
        }
      })
      .catch(reportError)
  }

  function mutate(fn: (list: StartEntry[]) => void) {
    setSl((old) => {
      if (old === null) {
        return old
      }
      const copy = old.map((entry) => ({ ...entry }))
      fn(copy)
      return copy
    })
  }

  function moveDown(i: number) {
    mutate((list) => {
      if (i < 0 || i >= list.length - 1) {
        return
      }
      if (list[i].Name === 'Break') {
        const duration = removeBreakAt(list, i, interval)
        if (duration !== undefined) {
          addBreakAt(list, i, duration)
        }
      } else if (list[i + 1].Name === 'Break') {
        if (i === 0) {
          return
        }
        const duration = removeBreakAt(list, i + 1, interval)
        if (duration !== undefined) {
          addBreakAt(list, i - 1, duration)
        }
      } else {
        swapStartList(list, i, i + 1)
      }
    })
  }

  function moveUp(i: number) {
    mutate((list) => {
      if (i < 1 || i >= list.length) {
        return
      }
      if (list[i].Name === 'Break') {
        const duration = removeBreakAt(list, i, interval)
        if (duration !== undefined) {
          addBreakAt(list, i - 2, duration)
        }
      } else if (list[i - 1].Name === 'Break') {
        if (i === list.length - 1) {
          return
        }
        const duration = removeBreakAt(list, i - 1, interval)
        if (duration !== undefined) {
          addBreakAt(list, i - 1, duration)
        }
      } else {
        swapStartList(list, i, i - 1)
      }
    })
  }

  function removeEntry(i: number) {
    /* both updates are driven from the current sl rather than queueing the
     * to_remove push inside the setSl updater: StrictMode double-invokes
     * updaters, so the nested setSlRemove recorded the same id twice */
    if (sl === null || i < 0 || i >= sl.length || sl[i].Name === 'Break') {
      return
    }
    const removedId = sl[i].Id
    if (removedId >= 0) {
      setSlRemove((ids) => (ids.includes(removedId) ? ids : [...ids, removedId]))
    }
    setSl((old) => {
      if (old === null) {
        return old
      }
      const copy = old.map((entry) => ({ ...entry }))
      copy.splice(i, 1)
      return copy
    })
  }

  function recalc(list?: StartEntry[]) {
    const base = list ?? sl
    if (base === null) {
      return
    }
    const copy = base.map((entry) => ({ ...entry }))
    const intervalMin = interval ? timeToMinutes(interval) : 0
    if (!noLanes || !intervalMin || !startTime || noLanes < 1) {
      setSl(copy)
      return
    }
    const ot = strToDate(startTime)
    let lane = 1
    for (let i = 0; i < copy.length; i++) {
      if (copy[i].Name === 'Break') {
        lane = 1
        ot.setMinutes(ot.getMinutes() + timeToMinutes(copy[i].AP) - intervalMin)
        continue
      } else if (lane === 1 && i !== 0) {
        ot.setMinutes(ot.getMinutes() + intervalMin)
      }
      copy[i].Lane = convertNumericLaneToActual(lane, numeric)
      setOT(copy, i, ot)
      lane = (lane % noLanes) + 1
    }
    setSl(copy)
  }

  function sortBy(byAp: boolean) {
    if (sl === null || sl.length === 0) {
      return
    }
    const copy = sl.map((entry) => ({ ...entry }))
    const brs: { i: number; time: string }[] = []
    copy.forEach((entry, i) => {
      if (entry.Name === 'Break') {
        brs.push({ i, time: entry.AP })
      }
    })
    for (let i = brs.length - 1; i >= 0; i--) {
      copy.splice(brs[i].i, 1)
    }
    const toInt = (entry: StartEntry) =>
      entry.Discipline === 'STA'
        ? timeToMinutes(byAp ? entry.AP : entry.PB)
        : Number(byAp ? entry.AP : entry.PB)
    copy.sort((a, b) => Math.sign(toInt(a) - toInt(b)))
    brs.forEach((br) => copy.splice(br.i, 0, makeBreakEntry(br.time)))
    recalc(copy)
  }

  function save() {
    api
      .putJson<StartListResponse>(
        '/start_list',
        withCompId({ startlist: sl, to_remove: slRemove, day: curDay, block: curBlock }),
      )
      .then((data) => {
        if (data.start_list != null) {
          setSl(data.start_list)
          setSlRemove([])
          deriveInputs(data.start_list)
        }
        applyResponse(data, true)
      })
      .catch(reportError)
  }

  function editEntry(i: number) {
    if (sl === null) {
      return
    }
    const entry = sl[i]
    if (entry.Name === 'Break') {
      showOverlay(
        <BreakEditDialog
          initial={entry.AP.padStart(5, '0')}
          onCancel={hideOverlay}
          onSave={(newBr) => {
            mutate((list) => {
              const diff = timeToMinutes(newBr) - timeToMinutes(list[i].AP)
              for (let j = i + 1; j < list.length; j++) {
                adjustOTbyDiff(list, j, diff)
              }
              list[i].AP = newBr
            })
            hideOverlay()
          }}
        />,
      )
    } else {
      showOverlay(
        <EntryEditDialog
          entry={entry}
          federation={state.compType}
          onCancel={hideOverlay}
          onSave={(values) => {
            mutate((list) => {
              list[i].AP = values.ap
              list[i].PB = values.pb
              if (values.diveTime !== null) {
                list[i]['Dive Time'] = values.diveTime
              }
              setOT(list, i, strToDate(values.ot))
            })
            hideOverlay()
          }}
        />,
      )
    }
  }

  function addBreakDialog(i: number) {
    if (sl === null) {
      return
    }
    if (sl[i].Name === 'Break') {
      mutate((list) => removeBreakAt(list, i, interval))
      return
    }
    showOverlay(
      <BreakEditDialog
        initial="00:00"
        title="Add break"
        onCancel={hideOverlay}
        onSave={(duration) => {
          mutate((list) => addBreakAt(list, i, duration))
          hideOverlay()
        }}
      />,
    )
  }

  function addAthleteDialog() {
    if (curDay === null || curBlock === null || state.blocks === null) {
      return
    }
    const disciplines = state.blocks[curDay][curBlock].dis_s.split(', ')
    api
      .get<AthleteListResponse>('/athletes', withCompId())
      .then((data) =>
        showOverlay(
          <AddAthleteDialog
            athletes={data.athletes}
            disciplines={disciplines}
            federation={state.compType}
            numeric={numeric}
            onCancel={hideOverlay}
            onSave={(entry, otStr) => {
              mutate((list) => {
                const ot = timeToMinutes(otStr)
                let i = 0
                for (; i < list.length; i++) {
                  if (ot < timeToMinutes(list[i].OT)) {
                    break
                  }
                }
                list.splice(i, 0, entry)
                setOT(list, i, strToDate(otStr))
              })
              hideOverlay()
            }}
          />,
        ),
      )
      .catch(reportError)
  }

  function blockModify(type: 'add' | 'edit', day = '', disciplines: string[] = [], block = '-1') {
    api
      .get<DisciplinesResponse>(`/disciplines/${state.compType}`)
      .then((data) =>
        showOverlay(
          <BlockModifyDialog
            type={type}
            day={day}
            block={block}
            allDisciplines={data.disciplines}
            checked={disciplines}
            onCancel={hideOverlay}
            onSave={(newDay, dis) => {
              const request =
                type === 'add'
                  ? api.postJson<DataPayload>('/block', withCompId({ day: newDay, dis, block }))
                  : api.patchJson<DataPayload>('/block', withCompId({ day: newDay, dis, block }))
              request
                .then((response) => {
                  hideOverlay()
                  applyResponse(response, true)
                  setSl(null)
                })
                .catch(reportError)
            }}
            onRemove={
              type === 'edit'
                ? () =>
                    api
                      .deleteJson<DataPayload>('/block', withCompId({ block }))
                      .then((response) => {
                        hideOverlay()
                        applyResponse(response, true)
                        setSl(null)
                      })
                      .catch(reportError)
                : undefined
            }
          />,
        ),
      )
      .catch(reportError)
  }

  const days = Object.keys(state.blocks ?? {})
  const blockEntries =
    curDay !== null && state.blocks != null ? Object.entries(state.blocks[curDay] ?? {}) : []
  const curBlockDis =
    curDay !== null && curBlock !== null
      ? (state.blocks?.[curDay]?.[curBlock]?.dis_s ?? null)
      : null
  const isDepth =
    curBlockDis !== null && curBlockDis.split(', ').some((dis) => DEPTH_DISCIPLINES.includes(dis))

  return (
    <>
      <div id="sl_date_menu">
        {days.map((day) => (
          <a
            key={day}
            href="#"
            id={`sl_day_${day}`}
            className="sl_day"
            style={{ fontWeight: curDay === day ? 'bold' : 'normal' }}
            onClick={(event) => {
              event.preventDefault()
              setCurDay(day)
              setCurBlock(null)
              setSl(null)
            }}
          >
            {day}
          </a>
        ))}
        <Button id="sl_add_day" onClick={() => blockModify('add')}>
          Add block
        </Button>
      </div>
      <div id="sl_discipline_menu">
        {blockEntries.map(([key, block]) => (
          <a
            key={key}
            href="#"
            className="sl_discipline_button"
            id={`sl_${curDay}_${key}`}
            style={{ fontWeight: curBlock === key ? 'bold' : 'normal' }}
            onClick={(event) => {
              event.preventDefault()
              loadBlock(curDay!, key)
            }}
          >
            {block.dis_s}
          </a>
        ))}
      </div>
      <a
        href="#"
        id="sl_all_pdf_button"
        onClick={(event) => {
          event.preventDefault()
          getPDF('start_list')
        }}
      >
        Print all
      </a>
      <div id="sl_content">
        {sl !== null && curDay !== null && curBlock !== null && curBlockDis !== null && (
          <>
            <Button
              className="sl_edit_block"
              id={`sl_edit_block_${curDay}_${curBlock}`}
              onClick={() => blockModify('edit', curDay, curBlockDis.split(', '), curBlock)}
            >
              Edit block
            </Button>
            <br />
            <a
              href="#"
              className="sl_pdf_button"
              id={`sl_pdf_${curDay}_${curBlock}`}
              onClick={(event) => {
                event.preventDefault()
                getPDF('start_list', { day: curDay, block: curBlock })
              }}
            >
              Print PDF
            </a>
            <table>
              <tbody>
                <tr>
                  <td>Start time</td>
                  <td>
                    <input
                      type="time"
                      id="sl_start_time"
                      value={startTime}
                      onChange={(event) => setStartTime(event.target.value)}
                    />
                  </td>
                </tr>
                <tr>
                  <td>Interval</td>
                  <td>
                    <input
                      type="time"
                      id="sl_interval"
                      value={interval}
                      onChange={(event) => setIntervalStr(event.target.value)}
                    />
                  </td>
                </tr>
                <tr>
                  <td>Number of lanes</td>
                  <td>
                    <input
                      type="number"
                      step={1}
                      id="sl_no_lanes"
                      value={noLanes}
                      onChange={(event) => setNoLanes(Number(event.target.value))}
                    />
                  </td>
                </tr>
                <tr>
                  <td>
                    <Button id="sl_recalc" onClick={() => recalc()}>
                      Recalculate
                    </Button>
                  </td>
                  <td>
                    <Button
                      id="sl_sort_ap"
                      className="sl_sort"
                      variant="outline"
                      onClick={() => sortBy(true)}
                    >
                      Sort by AP
                    </Button>
                  </td>
                  <td>
                    <Button
                      id="sl_sort_pb"
                      className="sl_sort"
                      variant="outline"
                      onClick={() => sortBy(false)}
                    >
                      Sort by PB
                    </Button>
                  </td>
                </tr>
                <tr>
                  <td>
                    <Button id="sl_add" onClick={addAthleteDialog}>
                      Add athlete
                    </Button>
                  </td>
                  <td></td>
                </tr>
              </tbody>
            </table>
            <Button id="sl_save" onClick={save}>
              Save start list
            </Button>
            <table id="startlist">
              <tbody>
                <tr>
                  <td>Name</td>
                  <td>Discipline</td>
                  <td>AP</td>
                  {isDepth && <td>Dive time</td>}
                  <td>PB</td>
                  <td>Nationality</td>
                  <td>Warmup</td>
                  <td>OT</td>
                  <td>Lane</td>
                  <td colSpan={5}></td>
                </tr>
                {sl.map((entry, i) => {
                  const isBreak = entry.Name === 'Break'
                  const first = i === 0
                  const last = i === sl.length - 1
                  return (
                    <tr key={i}>
                      <td>{entry.Name}</td>
                      <td>{entry.Discipline}</td>
                      <td>{entry.AP}</td>
                      {isDepth && <td>{entry['Dive Time']}</td>}
                      <td>{entry.PB}</td>
                      <td>{entry.Nationality}</td>
                      <td>{entry.Warmup}</td>
                      <td>{entry.OT}</td>
                      <td>{entry.Lane}</td>
                      <td>
                        <Button
                          id={`sl_edit_${i}`}
                          className="edit"
                          variant="outline"
                          type="button"
                          onClick={() => editEntry(i)}
                        >
                          Edit
                        </Button>
                      </td>
                      {/* a break directly after the first or before the last
                       * entry cannot move further (the re-insert would be a
                       * no-op and the break would vanish), so those buttons
                       * are hidden like in the old renderer */}
                      <td>
                        {!first && !(isBreak && i === 1) && (
                          <Button
                            id={`sl_up_${i}`}
                            className="up"
                            variant="outline"
                            type="button"
                            onClick={() => moveUp(i)}
                          >
                            Up
                          </Button>
                        )}
                      </td>
                      <td>
                        {!last && !(isBreak && i === sl.length - 2) && (
                          <Button
                            id={`sl_down_${i}`}
                            className="down"
                            variant="outline"
                            type="button"
                            onClick={() => moveDown(i)}
                          >
                            Down
                          </Button>
                        )}
                      </td>
                      <td>
                        {!last && (
                          <Button
                            id={`sl_break_${i}`}
                            className={`break${isBreak ? ' danger' : ''}`}
                            variant={isBreak ? 'destructive' : 'outline'}
                            type="button"
                            onClick={() => addBreakDialog(i)}
                          >
                            {isBreak ? 'Remove' : 'Add'} break
                          </Button>
                        )}
                      </td>
                      <td>
                        {!isBreak && (
                          <Button
                            id={`sl_remove_${i}`}
                            className="remove"
                            variant="destructive"
                            type="button"
                            onClick={() => removeEntry(i)}
                          >
                            Remove
                          </Button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </>
        )}
      </div>
    </>
  )
}

function BreakEditDialog({
  initial,
  title = 'Edit break',
  onCancel,
  onSave,
}: {
  initial: string
  title?: string
  onCancel: () => void
  onSave: (value: string) => void
}) {
  const [value, setValue] = useState(initial)
  return (
    <div>
      <DialogTitle>{title}</DialogTitle>
      <table>
        <tbody>
          <tr>
            <td>{title === 'Add break' ? 'Duration' : 'Break'}</td>
            <td>
              <input
                type="time"
                id={title === 'Add break' ? 'sl_break_duration' : 'sl_edit_new_br'}
                value={value}
                onChange={(event) => setValue(event.target.value)}
              />
            </td>
          </tr>
          <tr>
            <td>
              <Button id="overlay_cancel" type="button" onClick={onCancel}>
                Cancel
              </Button>
            </td>
            <td>
              <Button
                id={title === 'Add break' ? 'sl_break_save' : 'sl_edit_save'}
                type="button"
                onClick={() => onSave(value)}
              >
                Save
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

function EntryEditDialog({
  entry,
  federation,
  onCancel,
  onSave,
}: {
  entry: StartEntry
  federation: 'aida' | 'cmas'
  onCancel: () => void
  onSave: (values: { ap: string; pb: string; diveTime: string | null; ot: string }) => void
}) {
  const isSta = entry.Discipline === 'STA'
  const isDepth = DEPTH_DISCIPLINES.includes(entry.Discipline)
  const input = getPerformanceInput(entry.Discipline, federation)
  const [ap, setAp] = useState(isSta ? entry.AP.padStart(5, '0') : entry.AP)
  const [pb, setPb] = useState(isSta ? entry.PB.padStart(5, '0') : entry.PB)
  const [diveTime, setDiveTime] = useState(entry['Dive Time']?.padStart(5, '0') ?? '')
  const [ot, setOtValue] = useState(entry.OT.padStart(5, '0'))
  /* STA values come back from the time input as HH:MM; dateToStr(valueAsDate)
   * in the original produced H:MM, so strip a leading zero from the hours */
  const normalize = (value: string) => (isSta ? dateToStr(strToDate(value)) : value)
  return (
    <div>
      <DialogTitle>Edit start of {entry.Name}</DialogTitle>
      <table>
        <tbody>
          <tr>
            <td>Discipline</td>
            <td>{entry.Discipline}</td>
          </tr>
          <tr>
            <td>AP</td>
            <td>
              <input
                type={input.type}
                step={input.step}
                id="sl_edit_ap"
                value={ap}
                onChange={(event) => setAp(event.target.value)}
              />
            </td>
          </tr>
          {isDepth && (
            <tr>
              <td>Dive time</td>
              <td>
                <input
                  type="time"
                  id="sl_edit_dive_time"
                  value={diveTime}
                  onChange={(event) => setDiveTime(event.target.value)}
                />
              </td>
            </tr>
          )}
          <tr>
            <td>PB</td>
            <td>
              <input
                type={input.type}
                step={input.step}
                id="sl_edit_pb"
                value={pb}
                onChange={(event) => setPb(event.target.value)}
              />
            </td>
          </tr>
          <tr>
            <td>OT</td>
            <td>
              <input
                type="time"
                id="sl_edit_ot"
                value={ot}
                onChange={(event) => setOtValue(event.target.value)}
              />
            </td>
          </tr>
          <tr>
            <td>
              <Button id="overlay_cancel" type="button" onClick={onCancel}>
                Cancel
              </Button>
            </td>
            <td>
              <Button
                id="sl_edit_save"
                type="button"
                onClick={() =>
                  onSave({
                    ap: normalize(ap),
                    pb: normalize(pb),
                    diveTime: isDepth ? diveTime : null,
                    ot,
                  })
                }
              >
                Save
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

function AddAthleteDialog({
  athletes,
  disciplines,
  federation,
  numeric,
  onCancel,
  onSave,
}: {
  athletes: { id: number; first_name: string; last_name: string; country: string }[]
  disciplines: string[]
  federation: 'aida' | 'cmas'
  numeric: boolean
  onCancel: () => void
  onSave: (entry: StartEntry, ot: string) => void
}) {
  const [athleteIdx, setAthleteIdx] = useState(0)
  const [dis, setDis] = useState(disciplines[0])
  const isSta = disciplines[0] === 'STA'
  const cmasPool = federation === 'cmas' && ['DNF', 'DYN', 'DYNB'].includes(disciplines[0])
  const [ap, setAp] = useState(isSta ? '00:01' : '1')
  const [pb, setPb] = useState(isSta ? '00:01' : '1')
  const [diveTime, setDiveTime] = useState('00:00')
  const [ot, setOtValue] = useState('00:00')
  const [lane, setLane] = useState(numeric ? '1' : 'A')
  const isDepth = disciplines.some((d) => DEPTH_DISCIPLINES.includes(d))
  const step = cmasPool ? 0.5 : 1

  function save() {
    const laneNumeric = convertActualLaneToNumeric(lane, numeric)
    if (
      Number.isNaN(athleteIdx) ||
      athleteIdx < 0 ||
      athleteIdx >= athletes.length ||
      laneNumeric <= 0 ||
      laneNumeric > 12
    ) {
      return
    }
    const athlete = athletes[athleteIdx]
    onSave(
      {
        Name: athlete.first_name + ' ' + athlete.last_name,
        AP: ap,
        PB: pb,
        Nationality: athlete.country,
        Warmup: '',
        OT: '',
        Lane: lane,
        Id: -athlete.id,
        Discipline: dis,
        'Dive Time': diveTime,
      },
      ot,
    )
  }

  return (
    <div>
      <DialogTitle>Add athlete</DialogTitle>
      <table>
        <tbody>
          <tr>
            <td>Athlete</td>
            <td>
              <select
                id="sl_add_athlete"
                value={athleteIdx}
                onChange={(event) => setAthleteIdx(Number(event.target.value))}
              >
                {athletes.map((athlete, index) => (
                  <option key={athlete.id} value={index}>
                    {athlete.first_name} {athlete.last_name}
                  </option>
                ))}
              </select>
            </td>
          </tr>
          <tr>
            <td>Discipline</td>
            <td>
              {disciplines.map((d) => (
                <span key={d}>
                  <input
                    type="radio"
                    name="sl_add_dis"
                    value={d}
                    id={`sl_add_dis_${d}`}
                    checked={dis === d}
                    onChange={() => setDis(d)}
                  />
                  <label htmlFor={`sl_add_dis_${d}`}>{d}</label>
                  <br />
                </span>
              ))}
            </td>
          </tr>
          <tr>
            <td>AP</td>
            <td>
              <input
                type={isSta ? 'time' : 'number'}
                step={step}
                id="sl_add_ap"
                value={ap}
                onChange={(event) => setAp(event.target.value)}
              />
            </td>
          </tr>
          {isDepth && (
            <tr>
              <td>Dive time</td>
              <td>
                <input
                  type="time"
                  id="sl_add_dive_time"
                  value={diveTime}
                  onChange={(event) => setDiveTime(event.target.value)}
                />
              </td>
            </tr>
          )}
          <tr>
            <td>PB</td>
            <td>
              <input
                type={isSta ? 'time' : 'number'}
                step={step}
                id="sl_add_pb"
                value={pb}
                onChange={(event) => setPb(event.target.value)}
              />
            </td>
          </tr>
          <tr>
            <td>OT</td>
            <td>
              <input
                type="time"
                id="sl_add_ot"
                value={ot}
                onChange={(event) => setOtValue(event.target.value)}
              />
            </td>
          </tr>
          <tr>
            <td>Lane</td>
            <td>
              <input
                type={numeric ? 'number' : 'text'}
                id="sl_add_lane"
                value={lane}
                onChange={(event) => setLane(event.target.value)}
              />
            </td>
          </tr>
          <tr>
            <td>
              <Button id="overlay_cancel" type="button" onClick={onCancel}>
                Cancel
              </Button>
            </td>
            <td>
              <Button id="sl_add_save" type="button" onClick={save}>
                Save
              </Button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

function BlockModifyDialog({
  type,
  day,
  allDisciplines,
  checked,
  onCancel,
  onSave,
  onRemove,
}: {
  type: 'add' | 'edit'
  day: string
  block: string
  allDisciplines: string[]
  checked: string[]
  onCancel: () => void
  onSave: (day: string, dis: string[]) => void
  onRemove?: () => void
}) {
  const [dayValue, setDayValue] = useState(day)
  const [selected, setSelected] = useState<string[]>(checked)
  return (
    <div>
      <DialogTitle>{type[0].toUpperCase() + type.slice(1)} block</DialogTitle>
      <table>
        <tbody>
          <tr>
            <td>Day</td>
            <td>
              <input
                type="date"
                id="sl_modify_block_day"
                value={dayValue}
                onChange={(event) => setDayValue(event.target.value)}
              />
            </td>
          </tr>
          <tr>
            <td>Disciplines</td>
            <td>
              {allDisciplines.map((dis) => (
                <span key={dis}>
                  <input
                    type="checkbox"
                    name="sl_modify_block_dis"
                    value={dis}
                    id={`sl_modify_block_dis_${dis}`}
                    checked={selected.includes(dis)}
                    onChange={(event) =>
                      setSelected((old) =>
                        event.target.checked ? [...old, dis] : old.filter((d) => d !== dis),
                      )
                    }
                  />
                  <label htmlFor={`sl_modify_block_dis_${dis}`}>{dis}</label>
                  <br />
                </span>
              ))}
            </td>
          </tr>
          <tr>
            <td>
              <Button id="overlay_cancel" type="button" onClick={onCancel}>
                Cancel
              </Button>
            </td>
            <td>
              <Button
                id="sl_modify_block_save"
                type="button"
                onClick={() => onSave(dayValue, selected)}
              >
                Save
              </Button>
              {onRemove !== undefined && (
                <>
                  &nbsp;
                  <Button id="sl_modify_block_remove" type="button" onClick={onRemove}>
                    Remove
                  </Button>
                </>
              )}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}
