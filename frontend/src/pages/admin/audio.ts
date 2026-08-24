/*
 * Countdown audio engine, ported from static/compy.js.
 *
 * Lives outside React on purpose: the AudioContext, buffer source and
 * scheduling timers must survive re-renders untouched. React sets the
 * config (federation, time adjustment, OTs), subscribes to status changes
 * and renders the header UI from that.
 */

export type AudioStatus = 'loading' | 'blocked' | 'ready'

interface AudioState {
  status: AudioStatus
  stopEnabled: boolean
}

let audioContext: AudioContext | null = null
let audioSource: AudioBufferSourceNode | null = null
let audioBuffer: AudioBuffer | null = null
let stopBtnTimeout: ReturnType<typeof setTimeout> | undefined
let schedulingPlay = false

let federation: 'aida' | 'cmas' = 'aida'
let adjustMs = 0
let ots: string[] = [] // dates as YYYY:MM:DD:HH:MM:SS

let state: AudioState = { status: 'loading', stopEnabled: false }
const listeners = new Set<() => void>()

function notify() {
  listeners.forEach((listener) => listener())
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getState(): AudioState {
  return state
}

function setState(partial: Partial<AudioState>) {
  const next = { ...state, ...partial }
  if (next.status === state.status && next.stopEnabled === state.stopEnabled) {
    return
  }
  /* replace the object so useSyncExternalStore sees a new snapshot */
  state = next
  notify()
}

export function setFederation(value: 'aida' | 'cmas') {
  federation = value
}

export function setAdjustMs(value: number) {
  adjustMs = value
}

export function setOts(value: string[]) {
  ots = value
  schedulePlay()
}

export function getCountdownDuration(): number {
  return federation === 'aida' ? 2 * 60 : 3 * 60
}

export function getDateNow(): Date {
  const now = new Date()
  now.setMilliseconds(now.getMilliseconds() + adjustMs)
  return now
}

/* time until the next OT in ms, or -1 when there is none */
export function getTimeToNextOT(): number {
  const now = getDateNow()
  let nextPlayTime: Date | null = null

  ots.forEach((timeStr) => {
    const p = timeStr.split(':').map((part) => parseInt(part, 10))
    const playTime = new Date(p[0], p[1] - 1, p[2], p[3], p[4], p[5])
    if (!nextPlayTime || (playTime >= now && (playTime < nextPlayTime || nextPlayTime < now))) {
      nextPlayTime = playTime
    }
  })

  if (nextPlayTime === null || (nextPlayTime as Date) <= now) {
    return -1
  }
  return (nextPlayTime as Date).getTime() - getDateNow().getTime()
}

export function schedulePlay() {
  if (schedulingPlay) {
    return
  }
  schedulingPlay = true
  stopAudio()
  if (audioBuffer === null) {
    schedulingPlay = false
    return
  }
  const timeToNextOT = getTimeToNextOT()
  if (timeToNextOT >= 0) {
    const delay = Math.max(0, timeToNextOT - getCountdownDuration() * 1000)
    const offset = Math.max(0, getCountdownDuration() * 1000 - timeToNextOT) / 1000.0
    playAudio(delay / 1000.0, offset)
  }
  schedulingPlay = false
}

export function stopAudio() {
  clearTimeout(stopBtnTimeout)
  setState({ stopEnabled: false })
  if (audioSource !== null) {
    audioSource.removeEventListener('ended', audioEnded)
    audioSource.stop()
    audioSource = null
  }
}

function audioEnded() {
  audioSource = null
  schedulePlay()
}

export function playAudio(time = 0, offset = 0, duration: number | null = null) {
  if (audioBuffer === null || audioContext === null) {
    return
  }
  audioSource = audioContext.createBufferSource()
  audioSource.buffer = audioBuffer
  audioSource.connect(audioContext.destination)
  if (duration !== null) {
    audioSource.start(audioContext.currentTime + time, offset, duration)
    stopBtnTimeout = setTimeout(() => setState({ stopEnabled: true }), (duration * 1000) / 2)
  } else {
    audioSource.start(audioContext.currentTime + time, offset)
    stopBtnTimeout = setTimeout(
      () => setState({ stopEnabled: true }),
      (time + getCountdownDuration() - offset) * 1000,
    )
  }
  audioSource.addEventListener('ended', audioEnded)
}

export function testCountdown() {
  stopAudio()
  playAudio(0, getCountdownDuration() - 5, 10)
}

export async function initAudio() {
  if (audioContext !== null) {
    audioContext.close()
  }
  audioContext = new AudioContext()
  audioBuffer = null
  audioSource = null
  setState({ status: 'loading' })

  try {
    const response = await fetch(`/static/countdown_${federation}.wav`)
    const encoded = await response.arrayBuffer()
    audioBuffer = await audioContext.decodeAudioData(encoded)
  } catch {
    return
  }

  if (audioContext.state === 'suspended') {
    /* autoplay restriction — the UI shows a "Try again" button that calls
     * initAudio() again from a user gesture */
    setState({ status: 'blocked' })
    return
  }
  setState({ status: 'ready' })
  schedulePlay()
}
