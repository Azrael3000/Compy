import { useCallback, useEffect, useRef, useState } from 'react'
import { api, type Envelope } from '@/lib/api'
import { judgeParams } from '@/lib/params'
import { errorMessage } from '@/lib/utils'
import { ErrorBanner } from '@/components/ErrorBanner'
import {
  getAllFrom,
  getDefaultRemark,
  getPerformanceInput,
  getRemarksForCard,
  getRemarksFromStr,
  isValidCard,
  penaltyUnderAP,
  type Card,
  type Federation,
} from '@/lib/results_utils'

/* blocks: {day: {block_key: {dis_s, lanes: [...]}}} (CompyData.getBlocks) */
type Blocks = Record<string, Record<string, { dis_s: string; lanes: string[] }>>

interface JudgeBootstrap extends Envelope {
  version: string
  comp_id: number
  comp_name: string
  judge_id: number
  judge_hash: string
  judge_first_name: string
  judge_last_name: string
  federation: Federation
  blocks: Blocks
}

interface LaneAthlete {
  s_id: number
  OT: string
  Name: string
  AP: string
  PB: string
  Dis: string
  Card: string | null
  Remarks: string | null
}

/* result mask payload of GET /judge/athlete/result (CompyData.getAthleteResult) */
interface AthleteResult extends Envelope {
  Name: string
  OT: string
  Country: string
  AP: string
  PB: string
  NR: string
  Dis: string
  RP?: string
  Card?: string
  Penalty?: string | number | null
  Remarks?: string | null
  JudgeRemarks?: string | null
  lane_list?: LaneAthlete[]
}

type Step = 'rp' | 'card' | 'remarks' | 'penalty' | 'judge_remarks'

/* the values shown on the overview page; mirrors the info_* fields */
interface Draft {
  rp: string
  card: string
  penalty: string
  remarks: string
  judgeRemarks: string
}

function cleanNull(value: string | number | null | undefined): string {
  return value === null || value === undefined || value === 'null' ? '' : String(value)
}

export function JudgeApp() {
  const params = judgeParams()
  const [bootstrap, setBootstrap] = useState<JudgeBootstrap | 'invalid' | null>(null)

  useEffect(() => {
    if (params === null) {
      setBootstrap('invalid')
      return
    }
    api
      .get<JudgeBootstrap>(`/judge_json/${params.compId}/${params.judgeId}`, { hash: params.hash })
      .then((data) => {
        setBootstrap(data)
        document.title = `Compy ${data.version}`
      })
      .catch(() => setBootstrap('invalid'))
    /* the judge credentials come from the url and cannot change without a
     * page reload, so this runs exactly once */
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (bootstrap === null) {
    return null
  }
  if (bootstrap === 'invalid') {
    return <NotFound />
  }
  return <JudgeWizard bootstrap={bootstrap} />
}

/* invalid judge credentials. The judge endpoints answer with the json
 * envelope (404), so there is no flask error page to fall back on — the
 * message is rendered here. */
function NotFound() {
  return (
    <div id="judge_not_found" style={{ textAlign: 'center', paddingTop: '10vh' }}>
      <div style={{ color: 'var(--highlight)', fontSize: '5vh' }}>404</div>
      <div style={{ color: 'var(--white)', fontSize: '3vh' }}>
        This page could not be found.
        <br />
        Maybe it went diving?
      </div>
    </div>
  )
}

function JudgeWizard({ bootstrap }: { bootstrap: JudgeBootstrap }) {
  const { blocks, federation } = bootstrap
  const baseParams = {
    comp_id: bootstrap.comp_id,
    judge_id: bootstrap.judge_id,
    judge_hash: bootstrap.judge_hash,
  }

  const [nav, setNav] = useState<{ day: string | null; block: string | null; lane: string | null }>(
    { day: null, block: null, lane: null },
  )
  const [view, setView] = useState<'days' | 'blocks' | 'lanes' | 'athletes' | 'result'>('days')
  const [laneList, setLaneList] = useState<LaneAthlete[]>([])
  const [sId, setSId] = useState<number | null>(null)
  const [result, setResult] = useState<AthleteResult | null>(null)
  const [draft, setDraft] = useState<Draft>({
    rp: '',
    card: '',
    penalty: '',
    remarks: '',
    judgeRemarks: '',
  })
  const [mode, setMode] = useState<'info' | 'edit'>('info')
  const [step, setStep] = useState<Step>('rp')
  const [edited, setEdited] = useState(false)
  /* pending action while the unsaved-changes overlay is up (safeContinue) */
  const [confirmAction, setConfirmAction] = useState<(() => void) | null>(null)
  /* the judge screen is where a swallowed error costs most: on a flaky phone
   * connection the old code let "Save" do nothing without a word */
  const [error, setError] = useState<string | null>(null)
  const reportError = (err: unknown) => setError(errorMessage(err))

  /* per-step input state */
  const [rpInput, setRpInput] = useState('')
  const [cardInput, setCardInput] = useState<string>('')
  const [remarksInput, setRemarksInput] = useState<string[]>([])
  const [penaltyInput, setPenaltyInput] = useState('')
  const [judgeRemarksInput, setJudgeRemarksInput] = useState('')

  const dis = result?.Dis ?? ''
  const ap = result?.AP ?? ''

  const penUnder = useCallback(
    (card: string) => penaltyUnderAP(draft.rp, ap, card, federation, dis),
    [draft.rp, ap, federation, dis],
  )

  const showAthlete = useCallback(
    (startId: number) => {
      api
        .get<AthleteResult>('/judge/athlete/result', {
          ...baseParams,
          day: nav.day,
          block: nav.block,
          lane: nav.lane,
          s_id: startId,
        })
        .then((data) => {
          if (!('Name' in data)) {
            return
          }
          setError(null)
          setSId(startId)
          initResultMask(data)
          setView('result')
        })
        .catch(reportError)
    },
    /* baseParams and initResultMask are rebuilt every render but never
     * change meaning; only nav decides which athlete is fetched */
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [nav],
  )

  function initResultMask(data: AthleteResult) {
    setResult(data)
    setEdited(false)
    const card = data.Card != null && isValidCard(data.Card, federation) ? data.Card : ''
    const newDraft: Draft = {
      rp: cleanNull(data.RP),
      card,
      penalty: cleanNull(data.Penalty),
      remarks: cleanNull(data.Remarks),
      judgeRemarks: cleanNull(data.JudgeRemarks),
    }
    setDraft(newDraft)
    const showInfo = data.RP !== undefined && data.RP !== ''
    if (showInfo) {
      setMode('info')
    } else {
      setMode('edit')
      enterStep('rp', newDraft, data)
    }
  }

  /* prepare a step's input state from the draft (the show* functions) */
  function enterStep(next: Step, current: Draft, res: AthleteResult | null = result) {
    const stepDis = res?.Dis ?? ''
    const stepAp = res?.AP ?? ''
    if (next === 'rp') {
      let oldRp = current.rp
      if (oldRp === '') {
        oldRp = stepAp
      }
      if (stepDis === 'STA') {
        oldRp = oldRp.padStart(5, '0')
      }
      setRpInput(oldRp)
    } else if (next === 'card') {
      let card = current.card === '' ? 'WHITE' : current.card
      if (
        federation === 'aida' &&
        penaltyUnderAP(current.rp, stepAp, 'YELLOW', federation, stepDis) !== null
      ) {
        if (card === 'WHITE') {
          card = 'YELLOW'
        }
      }
      setCardInput(card)
    } else if (next === 'remarks') {
      const old = getRemarksFromStr(current.remarks, federation, stepDis)
      /* only pre-select UNDER AP when this card and discipline actually offer
       * it — a discipline that renders no remark list (getRemarksForCard
       * returns {} for anything outside POOL/DEPTH) used to end up with an
       * UNDER AP in the draft that nothing on screen could clear again */
      const offered =
        isValidCard(current.card, federation) &&
        current.card === 'YELLOW' &&
        getAllFrom(federation, 'YELLOW', stepDis).includes('UNDER AP')
      if (
        offered &&
        penaltyUnderAP(current.rp, stepAp, 'YELLOW', federation, stepDis) !== null &&
        !old.includes('UNDER AP')
      ) {
        old.push('UNDER AP')
      }
      setRemarksInput(old)
    } else if (next === 'penalty') {
      const under = penaltyUnderAP(current.rp, stepAp, current.card, federation, stepDis)
      let penalty = Number(current.penalty || 0)
      if (under !== null) {
        penalty = Math.max(penalty - under, 0)
      }
      setPenaltyInput(current.card === 'YELLOW' ? String(penalty) : '')
    } else if (next === 'judge_remarks') {
      setJudgeRemarksInput(current.judgeRemarks)
    }
    setStep(next)
  }

  /* commit the current step's input into the draft (the save* functions) */
  function commitStep(current: Draft): Draft {
    const next = { ...current }
    if (step === 'rp') {
      next.rp = rpInput
    } else if (step === 'card') {
      if (cardInput !== '') {
        next.card = cardInput
      }
    } else if (step === 'remarks') {
      next.remarks = remarksInput.join(',')
    } else if (step === 'penalty') {
      const under = penaltyUnderAP(next.rp, ap, next.card, federation, dis)
      next.penalty = String(Math.max(Number(penaltyInput || 0) + (under ?? 0), 0))
    } else if (step === 'judge_remarks') {
      next.judgeRemarks = judgeRemarksInput
    }
    return next
  }

  /* port of navAction() — shared step sequencing */
  function navAction(action: 'next' | 'prev' | 'ok' | 'edit_button' | Step) {
    if (mode === 'info' && action === 'edit_button') {
      setMode('edit')
      enterStep('rp', draft)
      return
    }
    if (
      mode === 'info' &&
      action !== 'next' &&
      action !== 'prev' &&
      action !== 'ok' &&
      action !== 'edit_button'
    ) {
      /* clicking one of the info fields jumps straight to that step */
      setMode('edit')
      enterStep(action, draft)
      return
    }

    let next = commitStep(draft)
    setDraft(next)
    const isNext = action === 'next'
    const isPrev = action === 'prev'

    if (isPrev && step === 'card') {
      enterStep('rp', next)
    } else if ((isNext && step === 'rp') || (isPrev && step === 'remarks')) {
      enterStep('card', next)
    } else if ((isNext && step === 'card') || (isPrev && step === 'penalty')) {
      enterStep('remarks', next)
    } else if ((isNext && step === 'remarks') || (isPrev && step === 'judge_remarks')) {
      /* valid non-yellow card: penalty is fixed to 0 and the step skipped */
      if (isValidCard(next.card, federation) && next.card !== 'YELLOW') {
        next = { ...next, penalty: '0' }
        setDraft(next)
        if (isNext) {
          enterStep('judge_remarks', next)
        } else {
          enterStep('remarks', next)
        }
      } else {
        enterStep('penalty', next)
      }
    } else if (isNext && step === 'penalty') {
      enterStep('judge_remarks', next)
    } else if (action === 'ok') {
      if (isValidCard(next.card, federation) && next.card !== 'YELLOW') {
        next = { ...next, penalty: '0' }
      }
      if (next.remarks === '' || next.card === 'WHITE') {
        next = { ...next, remarks: getDefaultRemark(next.card as Card, federation) }
      }
      setDraft(next)
      setMode('info')
    }
  }

  /* port of doSave() */
  function doSave() {
    let saved = { ...draft }
    const under = penUnder(saved.card)
    if (isValidCard(saved.card, federation) && saved.card !== 'YELLOW') {
      saved = { ...saved, penalty: '0' }
    }
    let remarks = saved.remarks
    if (remarks === '' || saved.card === 'WHITE') {
      remarks = getDefaultRemark(saved.card as Card, federation)
    }
    api
      .putJson<AthleteResult>('/result', {
        ...baseParams,
        id: sId,
        rp: saved.rp,
        penalty: Number(saved.penalty || 0) - (under ?? 0),
        card: saved.card,
        remarks,
        judge_remarks: saved.judgeRemarks,
      })
      .then((data) => {
        setError(null)
        if ('lane_list' in data && data.lane_list != null) {
          setLaneList(data.lane_list)
        }
        if ('Name' in data) {
          initResultMask(data)
        }
      })
      .catch((err) => reportError(err))
  }

  /* port of safeContinue() — guard against losing unsaved edits */
  function safeContinue(action: () => void) {
    if (edited) {
      setConfirmAction(() => action)
    } else {
      action()
    }
  }

  function openLane(lane: string) {
    api
      .get<Envelope & { lane_list?: LaneAthlete[] }>('/judge/athletes', {
        ...baseParams,
        day: nav.day,
        block: nav.block,
        lane,
        s_id: null,
      })
      .then((data) => {
        if (data.lane_list != null) {
          setError(null)
          setNav((old) => ({ ...old, lane }))
          setLaneList(data.lane_list)
          setView('athletes')
        }
      })
      .catch((err) => reportError(err))
  }

  const currentIndex = laneList.findIndex((athlete) => athlete.s_id === sId)
  const hasPrevAthlete = view === 'result' && currentIndex > 0
  const hasNextAthlete =
    view === 'result' && currentIndex >= 0 && currentIndex < laneList.length - 1

  /* keyboard shortcuts, port of the body.keydown handler; the ref always
   * points to a handler built from the current render's state */
  const keyHandler = useRef<(event: KeyboardEvent) => void>(() => {})
  keyHandler.current = (event: KeyboardEvent) => {
    if (view !== 'result') {
      return
    }
    const key = event.key.toLowerCase()
    if (event.key === 'Tab') {
      if (mode === 'info') {
        navAction('edit_button')
        event.preventDefault()
      } else if (event.shiftKey && step !== 'rp') {
        navAction('prev')
        event.preventDefault()
      } else if (!event.shiftKey && step !== 'judge_remarks') {
        navAction('next')
        event.preventDefault()
      }
    } else if (event.key === 'Enter' && event.ctrlKey) {
      if (mode === 'edit') {
        navAction('ok')
      } else if (edited) {
        doSave()
      }
      event.preventDefault()
      /* the old handler compared key codes (e.which), which are the same
       * shifted or with caps lock on; comparing event.key directly would let
       * caps lock silently disable the card keys */
    } else if (mode === 'edit' && step === 'card' && ['w', 'y', 'r'].includes(key)) {
      const byKey: Record<string, string> = { w: 'WHITE', y: 'YELLOW', r: 'RED' }
      setCardInput(byKey[key])
      setEdited(true)
      event.preventDefault()
    } else if (mode === 'info') {
      if (key === 'k' && hasPrevAthlete) {
        prevNextAthlete(-1)
      } else if (key === 'j' && hasNextAthlete) {
        prevNextAthlete(1)
      }
    }
  }
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => keyHandler.current(event)
    document.body.addEventListener('keydown', onKeyDown)
    return () => document.body.removeEventListener('keydown', onKeyDown)
  }, [])

  function prevNextAthlete(direction: -1 | 1) {
    const index = laneList.findIndex((athlete) => athlete.s_id === sId)
    const target = laneList[index + direction]
    if (target !== undefined) {
      safeContinue(() => showAthlete(target.s_id))
    }
  }

  const markEdited = () => setEdited(true)

  return (
    <>
      <div id="compy_title">Compy {bootstrap.version}</div>
      <div id="competition">{bootstrap.comp_name}</div>
      <div id="judge">
        Judge:{' '}
        <span id="judge_name">
          {bootstrap.judge_first_name} {bootstrap.judge_last_name}
        </span>
      </div>
      <ErrorBanner message={error} onDismiss={() => setError(null)} />
      {confirmAction !== null && (
        <div id="continue">
          <div id="continue_msg">
            You have unsaved changes.
            <br />
            Press 'Continue' if you want to discard them or 'Cancel' if you would like to get back.
          </div>
          <button
            id="continue_btn"
            onClick={() => {
              const action = confirmAction
              setConfirmAction(null)
              action()
            }}
          >
            Continue
          </button>
          <button onClick={() => setConfirmAction(null)}>Cancel</button>
        </div>
      )}
      <div id="content" style={confirmAction !== null ? { display: 'none' } : undefined}>
        {view === 'days' &&
          Object.keys(blocks).map((day) => (
            <button
              key={day}
              id={`block_${day}`}
              type="button"
              className="day_menu"
              onClick={() => {
                setNav({ day, block: null, lane: null })
                setView('blocks')
              }}
            >
              {day}
            </button>
          ))}
        {view === 'blocks' && nav.day !== null && (
          <>
            <button id="block_back" type="button" onClick={() => setView('days')}>
              Back
            </button>
            {Object.entries(blocks[nav.day] ?? {}).map(([key, block]) => (
              <button
                key={key}
                id={`menu_${key}`}
                type="button"
                className="block_menu"
                onClick={() => {
                  setNav((old) => ({ ...old, block: key }))
                  setView('lanes')
                }}
              >
                {block.dis_s}
              </button>
            ))}
          </>
        )}
        {view === 'lanes' && nav.day !== null && nav.block !== null && (
          <>
            <button id="lane_back" type="button" onClick={() => setView('blocks')}>
              Back
            </button>
            {(blocks[nav.day]?.[nav.block]?.lanes ?? []).map((lane) => (
              <button
                key={lane}
                id={`menu_${lane}`}
                type="button"
                className="lane_menu"
                onClick={() => openLane(lane)}
              >
                {lane}
              </button>
            ))}
          </>
        )}
        {view === 'athletes' && (
          <>
            <button id="athlete_back" type="button" onClick={() => setView('lanes')}>
              Back
            </button>
            <table>
              <tbody>
                <tr>
                  <th>OT</th>
                  <th>Name</th>
                  <th>{federation === 'cmas' ? 'PB' : 'AP'}</th>
                  <th>Dis</th>
                </tr>
                {laneList.map((athlete) => {
                  const card = (athlete.Card ?? '').toLowerCase()
                  let setClass = card !== '' ? '' : 'unset'
                  if (card === 'red' && athlete.Remarks === 'DNS') {
                    setClass = 'dns'
                  }
                  return (
                    <tr
                      key={athlete.s_id}
                      id={`athlete_${athlete.s_id}`}
                      className="athlete_menu"
                      onClick={() => showAthlete(athlete.s_id)}
                    >
                      <td className={setClass}>{athlete.OT}</td>
                      <td className={setClass}>{athlete.Name}</td>
                      <td className={`${setClass} ${card}`}>
                        {federation === 'cmas' ? athlete.PB : athlete.AP}
                      </td>
                      <td className={setClass}>{athlete.Dis}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </>
        )}
        {view === 'result' && result !== null && (
          <>
            {mode === 'info' && !edited && (
              <button
                id="result_back"
                type="button"
                onClick={() => safeContinue(() => setView('athletes'))}
              >
                Back
              </button>
            )}
            {hasPrevAthlete && mode === 'info' && !edited && (
              <button id="prev_athlete_btn" type="button" onClick={() => prevNextAthlete(-1)}>
                Previous athlete
              </button>
            )}
            <div className="info_all">
              <InfoPiece id="info_ot" head="OT" value={result.OT} />
              <InfoPiece id="info_name" head="Name" value={result.Name} />
              <InfoPiece id="info_nat" head="Nat." value={result.Country} />
            </div>
            <div className="info_all">
              {(federation !== 'cmas' || result.Dis === 'STA') && (
                <InfoPiece id="info_AP" head="AP" value={result.AP} />
              )}
              <InfoPiece id="info_dis" head="Dis." value={result.Dis} />
              <InfoPiece id="info_PB" head="PB" value={result.PB} />
              <InfoPiece id="info_NR" head="NR" value={result.NR} />
            </div>

            {mode === 'info' && (
              <div id="result_info">
                <div className="info_all">
                  <div id="info_RP" className="info_piece nav" onClick={() => navAction('rp')}>
                    <span className="info_head">RP</span>
                    <br />
                    <span className="info">{draft.rp}</span>
                  </div>
                  <div id="info_card" className="info_piece nav" onClick={() => navAction('card')}>
                    <span className="info_head">Card</span>
                    <br />
                    <span className="info">
                      {draft.card !== '' && (
                        <span id="card_title" className={`card ${draft.card.toLowerCase()}`}>
                          {draft.card}
                        </span>
                      )}
                    </span>
                  </div>
                  <div
                    id="info_penalty"
                    className="info_piece nav"
                    onClick={() => navAction('penalty')}
                  >
                    <span className="info_head">Penalty</span>
                    <br />
                    <span className="info">{draft.penalty}</span>
                  </div>
                </div>
                <div
                  id="info_remarks"
                  className="info_all nav"
                  onClick={() => navAction('remarks')}
                >
                  <div className="info_piece">
                    <span className="info_head">Remarks</span>
                    <br />
                    <span className="info">{draft.remarks}</span>
                  </div>
                </div>
                <div
                  id="info_judge_remarks"
                  className="info_all nav"
                  onClick={() => navAction('judge_remarks')}
                >
                  <div className="info_piece">
                    <span className="info_head">Judge Remarks</span>
                    <br />
                    <span className="info">{draft.judgeRemarks}</span>
                  </div>
                </div>
                <button
                  id="edit_button"
                  type="button"
                  className="nav"
                  onClick={() => navAction('edit_button')}
                >
                  Edit
                </button>
              </div>
            )}

            {mode === 'edit' && (
              <div id="result_entry">
                <div className="info_all" id="result_input">
                  {step === 'rp' && (
                    <div id="rp_entry" className="info_piece">
                      <span className="info_head">Realized Performance</span>
                      <br />
                      <input
                        id="rp_input"
                        autoFocus
                        type={getPerformanceInput(dis, federation).type}
                        step={getPerformanceInput(dis, federation).step}
                        value={rpInput}
                        onChange={(event) => {
                          setRpInput(event.target.value)
                          markEdited()
                        }}
                      />
                    </div>
                  )}
                  {step === 'card' && (
                    <div id="card_entry" className="info_piece">
                      <span className="info_head">Card</span>
                      <br />
                      {(['WHITE', 'YELLOW', 'RED'] as const).map((card) => {
                        /* AIDA: white is not offered while an under-AP penalty applies */
                        if (
                          card === 'WHITE' &&
                          federation === 'aida' &&
                          penaltyUnderAP(draft.rp, ap, 'YELLOW', federation, dis) !== null
                        ) {
                          return null
                        }
                        return (
                          <span
                            key={card}
                            id={`card_${card.toLowerCase()}`}
                            className={`card ${card.toLowerCase()} selector ${cardInput === card ? 'highlight' : ''}`}
                            onClick={() => {
                              setCardInput(card)
                              markEdited()
                            }}
                          >
                            {card}
                          </span>
                        )
                      })}
                    </div>
                  )}
                  {step === 'remarks' && (
                    <div id="remarks_entry" className="info_piece">
                      <span className="info_head">Remarks</span>
                      <br />
                      <RemarksInput
                        card={draft.card}
                        federation={federation}
                        discipline={dis}
                        selected={remarksInput}
                        onToggle={(remark) => {
                          setRemarksInput((old) =>
                            old.includes(remark)
                              ? old.filter((r) => r !== remark)
                              : [...old, remark],
                          )
                          markEdited()
                        }}
                      />
                    </div>
                  )}
                  {step === 'penalty' && (
                    <div id="penalty_entry" className="info_piece">
                      <span className="info_head">Penalty</span>
                      <br />
                      <input
                        id="penalty_input"
                        type="number"
                        autoFocus
                        disabled={draft.card !== 'YELLOW'}
                        value={penaltyInput}
                        onChange={(event) => {
                          setPenaltyInput(event.target.value)
                          markEdited()
                        }}
                      />
                      <span id="under_ap_penalty">
                        {draft.card === 'YELLOW' && penUnder('YELLOW') !== null
                          ? ` + ${penUnder('YELLOW')} (under AP)`
                          : ''}
                      </span>
                    </div>
                  )}
                  {step === 'judge_remarks' && (
                    <div id="judge_remarks_entry" className="info_piece">
                      <span className="info_head">Judge Remarks</span>
                      <br />
                      <input
                        id="judge_remarks_input"
                        type="text"
                        autoFocus
                        value={judgeRemarksInput}
                        onChange={(event) => {
                          setJudgeRemarksInput(event.target.value)
                          markEdited()
                        }}
                      />
                    </div>
                  )}
                </div>
                <div className="grouper">
                  {step !== 'rp' && (
                    <button id="prev" className="nav width50" onClick={() => navAction('prev')}>
                      Previous
                    </button>
                  )}
                  {step !== 'judge_remarks' && (
                    <button
                      id="next"
                      className={`nav width50 ${step === 'rp' ? 'shift50' : ''}`}
                      onClick={() => navAction('next')}
                    >
                      Next
                    </button>
                  )}
                </div>
                <button id="ok" className="nav" onClick={() => navAction('ok')}>
                  Ok
                </button>
                {/* edit-mode cancel returns to the overview without saving the
                 * current step; the overview's cancel is the one that discards
                 * by re-fetching (same as the original two-stage cancel) */}
                <button id="cancel" onClick={() => setMode('info')}>
                  Cancel
                </button>
              </div>
            )}

            {mode === 'info' && edited && (
              <>
                <button id="cancel" onClick={() => showAthlete(sId!)}>
                  Cancel
                </button>
                <button id="save" onClick={doSave}>
                  Save
                </button>
              </>
            )}
            {hasNextAthlete && mode === 'info' && !edited && (
              <button id="next_athlete_btn" type="button" onClick={() => prevNextAthlete(1)}>
                Next athlete
              </button>
            )}
          </>
        )}
      </div>
    </>
  )
}

function InfoPiece({ id, head, value }: { id: string; head: string; value: string }) {
  return (
    <div id={id} className="info_piece">
      <span className="info_head">{head}</span>
      <br />
      <span className="info">{value}</span>
    </div>
  )
}

function RemarksInput({
  card,
  federation,
  discipline,
  selected,
  onToggle,
}: {
  card: string
  federation: Federation
  discipline: string
  selected: string[]
  onToggle: (remark: string) => void
}) {
  if (!isValidCard(card, federation)) {
    return (
      <div id="remarks_input">
        <span className="error">Error: Card not set</span>
      </div>
    )
  }
  const remarks = getRemarksForCard(card as Card, federation, discipline)
  if (typeof remarks === 'string') {
    return (
      <div id="remarks_input">
        <span className="remark selector highlight">{remarks}</span>
      </div>
    )
  }
  return (
    <div id="remarks_input">
      {Object.entries(remarks).map(([group, list]) => (
        <div key={group}>
          <div className="remark_title">{group}:</div>
          {list.map((remark) => (
            <span
              key={remark}
              className={`remark selector ${selected.includes(remark) ? 'highlight' : ''}`}
              onClick={() => onToggle(remark)}
            >
              {remark}
            </span>
          ))}
        </div>
      ))}
    </div>
  )
}
