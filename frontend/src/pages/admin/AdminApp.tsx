import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from 'react'
import { api } from '@/lib/api'
import { downloadBlob, errorMessage } from '@/lib/utils'
import { ErrorBanner } from '@/components/ErrorBanner'
import { Dialog, DialogContent } from '@/components/ui/dialog'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import type { Athlete, Blocks, Competition, DaysWithDisciplinesLanes, Judge } from '@/lib/types'
import type { AdminDataResponse, DataPayload, LoadCompResponse } from './contracts'
import * as audio from './audio'
import { formatCountdown, formatTime } from './sl_utils'
import { SettingsTab } from './tabs/SettingsTab'
import { JudgesTab } from './tabs/JudgesTab'
import { AthletesTab } from './tabs/AthletesTab'
import { RegistrationTab } from './tabs/RegistrationTab'
import { BreaksTab } from './tabs/BreaksTab'
import { StartListsTab } from './tabs/StartListsTab'
import { LaneListsTab } from './tabs/LaneListsTab'
import { ResultsTab } from './tabs/ResultsTab'

export type { Athlete, Blocks, Competition, Judge } from '@/lib/types'

export interface AdminState {
  compId: number
  version: string
  compName: string
  competitions: Competition[] | null
  athletes: Athlete[]
  judges: Judge[]
  specialRankingName: string
  blocks: Blocks | null
  daysWithDisciplinesLanes: DaysWithDisciplinesLanes | null
  disciplines: string[] | null
  countries: string[] | null
  resultCountries: string[] | null
  selectedCountry: string
  laneStyle: 'numeric' | 'alphabetic'
  compType: 'aida' | 'cmas'
  publishResults: boolean
  aidaEventId: number | null
  aidaHasKey: boolean
  secondsAdjust: number
  decisecondsAdjust: number
  enableRemote: boolean
}

interface AdminContextValue {
  state: AdminState
  update: (partial: Partial<AdminState>) => void
  /* merge a mutation response's payload into the state; the react analog
   * of populate* / initSubmenus in the old jquery app */
  applyResponse: (data: DataPayload, reset?: boolean) => void
  loadCompetition: (compId: number) => void
  withCompId: <T extends object>(data?: T) => T & { comp_id: number }
  showOverlay: (content: ReactNode) => void
  hideOverlay: () => void
  getPDF: (type: 'start_list' | 'lane_list' | 'result', params?: Record<string, string>) => void
  /* surface a failed request in the page-level banner */
  reportError: (error: unknown) => void
}

const AdminContext = createContext<AdminContextValue | null>(null)

export function useAdmin(): AdminContextValue {
  const value = useContext(AdminContext)
  if (value === null) {
    throw new Error('useAdmin outside provider')
  }
  return value
}

/* resetOnData: tabs whose local state (selected day/block, loaded tables)
 * belongs to the competition dataset; they are remounted whenever a
 * response resets that dataset — the equivalent of the old initSubmenus
 * clearing all lower-tier menus. Without this, e.g. the Results tab could
 * keep showing (and editing!) rows of a previously loaded competition. */
const TABS = [
  { id: 'settings', label: 'Settings', component: SettingsTab, resetOnData: false },
  { id: 'judges', label: 'Judges', component: JudgesTab, resetOnData: false },
  { id: 'athletes', label: 'Athletes', component: AthletesTab, resetOnData: false },
  { id: 'registration', label: 'Registration', component: RegistrationTab, resetOnData: false },
  { id: 'breaks', label: 'Breaks', component: BreaksTab, resetOnData: true },
  { id: 'start_lists', label: 'Start lists', component: StartListsTab, resetOnData: true },
  { id: 'lane_lists', label: 'Lane lists', component: LaneListsTab, resetOnData: true },
  { id: 'results', label: 'Results', component: ResultsTab, resetOnData: true },
] as const

export function AdminApp() {
  const [state, setState] = useState<AdminState>({
    compId: 1,
    version: '',
    compName: 'undefined',
    competitions: null,
    athletes: [],
    judges: [],
    specialRankingName: 'Newcomer',
    blocks: null,
    daysWithDisciplinesLanes: null,
    disciplines: null,
    countries: null,
    resultCountries: null,
    selectedCountry: 'none',
    laneStyle: 'numeric',
    compType: 'aida',
    publishResults: false,
    aidaEventId: null,
    aidaHasKey: false,
    secondsAdjust: 0,
    decisecondsAdjust: 0,
    enableRemote: false,
  })
  const [activeTab, setActiveTab] = useState<string>('settings')
  const [overlay, setOverlay] = useState<ReactNode | null>(null)
  /* the dialog is opened imperatively (no DialogTrigger), so Radix has no
   * trigger element to return focus to on close; remember whatever was
   * focused when showOverlay was called and restore it ourselves */
  const overlayOpenerRef = useRef<HTMLElement | null>(null)
  const showOverlay = useCallback((content: ReactNode) => {
    overlayOpenerRef.current = document.activeElement as HTMLElement | null
    setOverlay(content)
  }, [])
  /* bumped whenever the competition dataset is replaced; keys the
   * resetOnData tabs so their local state is discarded */
  const [dataEpoch, setDataEpoch] = useState(0)
  /* the old page had its bootstrap data server-rendered into the html; here
   * it arrives via /admin_data + /load_comp, so the interactive UI waits for
   * that to avoid acting on (and then clobbering) half-initialized state */
  const [booted, setBooted] = useState(false)
  /* a failed boot must not look like a slow one: /admin_data or /load_comp
   * failing used to leave the spinner up forever with nothing in the console */
  const [bootError, setBootError] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const stateRef = useRef(state)
  stateRef.current = state

  const reportError = useCallback((err: unknown) => setError(errorMessage(err)), [])

  const update = useCallback((partial: Partial<AdminState>) => {
    setState((old) => ({ ...old, ...partial }))
  }, [])

  const applyResponse = useCallback((data: DataPayload, reset = false) => {
    if (reset) {
      setDataEpoch((epoch) => epoch + 1)
    }
    setState((old) => {
      const next = { ...old }
      if (reset) {
        next.daysWithDisciplinesLanes = null
        next.blocks = null
        next.disciplines = null
        next.countries = null
        next.resultCountries = null
      }
      if (data.days_with_disciplines_lanes != null) {
        next.daysWithDisciplinesLanes = data.days_with_disciplines_lanes
      }
      if (data.blocks != null) {
        next.blocks = data.blocks
      }
      if (data.disciplines != null) {
        next.disciplines = data.disciplines
      }
      if (data.countries != null) {
        next.countries = data.countries
      }
      if (data.result_countries != null) {
        next.resultCountries = data.result_countries
      }
      if (data.athletes != null) {
        next.athletes = data.athletes
      }
      if (data.judges != null) {
        next.judges = data.judges
      }
      if (data.competitions != null) {
        next.competitions = data.competitions
      }
      if (typeof data.special_ranking_name === 'string') {
        next.specialRankingName = data.special_ranking_name
      }
      if ('aida_event_id' in data) {
        next.aidaEventId = data.aida_event_id ?? null
      }
      if ('aida_has_key' in data) {
        next.aidaHasKey = Boolean(data.aida_has_key)
      }
      return next
    })
    if (data.ots != null) {
      audio.setOts(data.ots)
    }
  }, [])

  const withCompId = useCallback(
    <T extends object>(data?: T) =>
      ({ comp_id: stateRef.current.compId, ...data }) as T & { comp_id: number },
    [],
  )

  /* the first /load_comp is part of the boot; a later one is a user action
   * on the Settings tab, so the two report their failures differently */
  const bootedRef = useRef(false)

  const loadCompetition = useCallback(
    (compId: number) => {
      api
        .postJson<LoadCompResponse>('/load_comp', { comp_id: compId })
        .then((data) => {
          applyResponse(data, true)
          const compType = data.comp_type ?? 'aida'
          audio.setFederation(compType)
          setState((old) => ({
            ...old,
            compId,
            compName: data.comp_name ?? old.compName,
            selectedCountry: data.selected_country ?? 'none',
            laneStyle: data.lane_style === 'alphabetic' ? 'alphabetic' : 'numeric',
            compType,
            publishResults: Boolean(data.publish_results),
          }))
          audio.initAudio()
          bootedRef.current = true
          setBootError(null)
          setBooted(true)
        })
        .catch((err) => {
          if (bootedRef.current) {
            reportError(err)
          } else {
            setBootError(errorMessage(err))
          }
        })
    },
    [applyResponse, reportError],
  )

  /* boot: bootstrap data, then competition 1 (same order as the old page) */
  const boot = useCallback(() => {
    setBootError(null)
    api
      .get<AdminDataResponse>('/admin_data')
      .then((data) => {
        document.title = `Compy ${data.version}`
        update({
          version: data.version,
          competitions: data.competitions,
          compName: data.comp_name,
        })
        loadCompetition(1)
      })
      .catch((err) => setBootError(errorMessage(err)))
  }, [update, loadCompetition])

  /* boot once on mount: re-running this on a new `boot` identity would
   * reload the competition out from under whatever the user is doing */
  useEffect(() => {
    boot()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* time adjustment -> audio module + reschedule */
  useEffect(() => {
    const adjust = state.decisecondsAdjust * 100 + state.secondsAdjust * 1000
    audio.setAdjustMs(adjust)
  }, [state.secondsAdjust, state.decisecondsAdjust])

  /* keyboard remote: 'o' restarts the countdown scheduling. The old code
   * compared key codes (e.which == 79), which ignores shift and caps lock —
   * hence the toLowerCase() rather than a bare event.key === 'o' */
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (
        event.key.toLowerCase() === 'o' &&
        overlay === null &&
        stateRef.current.enableRemote &&
        audio.getState().stopEnabled
      ) {
        audio.schedulePlay()
      }
    }
    document.body.addEventListener('keydown', onKeyDown)
    return () => document.body.removeEventListener('keydown', onKeyDown)
  }, [overlay])

  const getPDF = useCallback(
    async (
      type: 'start_list' | 'lane_list' | 'result',
      params: Record<string, string> = { type: 'all' },
    ) => {
      const compName = stateRef.current.compName
      const blocks = stateRef.current.blocks
      let filename: string
      if (params.type === 'all') {
        filename = `${compName}_${type}s.pdf`
      } else if (params.type === 'safety') {
        filename = `${compName}_${type}s_safety.pdf`
      } else if (params.type === 'top3') {
        filename = `${compName}_${type}s_top3.pdf`
      } else if (type === 'start_list' || type === 'lane_list') {
        let dis = params.block
        if (blocks != null) {
          dis = blocks[params.day][params.block].dis_s.replace(', ', '_')
        }
        filename =
          type === 'start_list'
            ? `${compName}_${type}_${params.day}_${dis}.pdf`
            : `${compName}_${type}_${params.day}_${dis}_${params.lane}.pdf`
      } else {
        filename = `${compName}_${type}_${params.discipline}_${params.country}_${params.gender}.pdf`
      }
      try {
        /* api.getBlob, not a bare fetch: it carries the 401 -> login
         * redirect, so "Print all" no longer does nothing at all once the
         * admin session has expired */
        const blob = await api.getBlob(`/${type}_pdf`, {
          comp_id: stateRef.current.compId,
          ...params,
        })
        downloadBlob(blob, filename)
      } catch (err) {
        reportError(err)
      }
    },
    [reportError],
  )

  const context: AdminContextValue = {
    state,
    update,
    applyResponse,
    loadCompetition,
    withCompId,
    showOverlay,
    hideOverlay: () => setOverlay(null),
    getPDF,
    reportError,
  }

  /* clock link carries the utc-adjusted time offset like the old page */
  const clockAdjust =
    state.decisecondsAdjust * 100 +
    state.secondsAdjust * 1000 -
    new Date().getTimezoneOffset() * 60 * 1000

  return (
    <AdminContext.Provider value={context}>
      <h1>Compy {state.version}</h1>
      <ErrorBanner message={error} onDismiss={() => setError(null)} />
      {!booted && bootError === null && (
        <div id="timers">
          Loading <span className="loader"></span>
        </div>
      )}
      {!booted && bootError !== null && (
        <div id="timers">
          Could not load the competition data: {bootError}{' '}
          <Button id="boot_retry" type="button" onClick={boot}>
            Retry
          </Button>
        </div>
      )}
      {booted && (
        <>
          <Timers />
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <div id="main_nav_row">
              <TabsList id="main_nav">
                {TABS.map((tab) => (
                  <TabsTrigger
                    key={tab.id}
                    id={`${tab.id}_button`}
                    value={tab.id}
                    aria-controls={tab.id}
                  >
                    {tab.label}
                  </TabsTrigger>
                ))}
              </TabsList>
              <span id="clock_button">
                <a href={`clock/${state.compId}/0/${clockAdjust}`} target="_blank">
                  Clock
                </a>
              </span>
              <span id="logout_button">
                <a href="/admin/logout">Logout</a>
              </span>
            </div>
            {TABS.map((tab) => (
              <TabsContent
                key={tab.id}
                value={tab.id}
                id={tab.id}
                aria-labelledby={`${tab.id}_button`}
                forceMount
                hidden={tab.id !== activeTab}
              >
                <tab.component key={tab.resetOnData ? dataEpoch : 0} />
              </TabsContent>
            ))}
          </Tabs>
          <Dialog open={overlay !== null} onOpenChange={(open) => !open && setOverlay(null)}>
            <DialogContent
              id="overlay_box"
              onCloseAutoFocus={(event) => {
                /* Radix's own default only refocuses a DialogTrigger, which
                 * this overlay does not use since it opens imperatively */
                event.preventDefault()
                overlayOpenerRef.current?.focus()
              }}
            >
              {overlay}
            </DialogContent>
          </Dialog>
        </>
      )}
    </AdminContext.Provider>
  )
}

/* header clock + countdown + audio controls */
function Timers() {
  const { state, update } = useAdmin()
  const audioState = useSyncExternalStore(audio.subscribe, audio.getState)
  const [now, setNow] = useState('')
  const [countdown, setCountdown] = useState('')

  /* 10 Hz, not requestAnimationFrame: the display has a 1 s resolution, so
   * re-rendering react ~60 times a second bought nothing but cpu */
  useEffect(() => {
    const updateTime = () => {
      setNow(formatTime(audio.getDateNow()))
      setCountdown(formatCountdown(audio.getTimeToNextOT()))
    }
    updateTime()
    const timer = window.setInterval(updateTime, 100)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <div id="timers">
      Time: <span id="time">{now}</span>
      {' | '}
      <span id="countdown">
        {audioState.status === 'loading' && (
          <>
            Loading countdown <span className="loader"></span>
          </>
        )}
        {audioState.status === 'blocked' && (
          <>
            <b>Audio autoplay is disabled. Countdown will not be played!</b>{' '}
            <Button onClick={() => audio.initAudio()}>Try again</Button>
          </>
        )}
        {audioState.status === 'ready' && (
          <>
            Countdown to next OT: <span id="countdown_ot">{countdown}</span>
            {' | '}
            <span id="stop_countdown_div">
              <Button
                id="stop_countdown_btn"
                disabled={!audioState.stopEnabled}
                onClick={() => audio.schedulePlay()}
              >
                Stop Countdown
              </Button>
            </span>
            {' | '}
            <span id="test_countdown_div">
              <Button id="test_countdown_btn" onClick={() => audio.testCountdown()}>
                Test Countdown
              </Button>
            </span>
            {' | '}
            <span>
              <input
                type="checkbox"
                name="enable_remote"
                id="enable_remote"
                checked={state.enableRemote}
                onChange={(event) => update({ enableRemote: event.target.checked })}
              />
              <label htmlFor="enable_remote">Enable Remote</label>
            </span>
          </>
        )}
      </span>
    </div>
  )
}
