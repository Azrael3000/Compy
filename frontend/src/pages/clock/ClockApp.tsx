import { useEffect, useRef, useState } from 'react'
import { api, type Envelope } from '@/lib/api'
import { clockParams } from '@/lib/params'
import type { ClockStart } from '@/lib/types'

interface ClockData extends Envelope {
  version: string
  comp_name: string
  comp_id: number
  alist: ClockStart[] | null
  current: number
  offset: number
}

const POLL_MS = 10_000
/* after this many failed polls in a row the shown starts are called out as
 * stale; three misses is half a minute of silence from the backend */
const STALE_AFTER_FAILURES = 3

/*
 * Venue clock display. The old page reloaded itself every 10 s to alternate
 * between "Current starts" and "Next starts"; here the same alternation is
 * done by polling /clock_data with the previously returned 'current' flag
 * (the server flips it). On a fetch error the last good data stays on
 * screen — a venue display must not blank out on a network blip — but it is
 * marked stale so nobody reads an hour-old start list as current.
 */
export function ClockApp() {
  const params = clockParams()
  const [data, setData] = useState<ClockData | null>(null)
  const [time, setTime] = useState('')
  /* refresh counter keyed to the divider so its 10 s grow animation restarts */
  const [refreshCount, setRefreshCount] = useState(0)
  const [stale, setStale] = useState(false)
  const currentRef = useRef(params?.current ?? 0)

  const compId = params?.compId ?? null
  const offset = params?.offset ?? 0

  useEffect(() => {
    if (compId === null) {
      return
    }
    let cancelled = false
    let timer = 0
    let failures = 0
    /* chained setTimeout rather than setInterval: with a 10 s interval and a
     * slow backend two polls could overlap, send the same 'current' flag and
     * make the display repeat a cycle */
    const poll = async () => {
      try {
        const result = await api.get<ClockData>(
          `/clock_data/${compId}/${currentRef.current}/${offset}`,
        )
        if (cancelled) {
          return
        }
        failures = 0
        currentRef.current = result.current
        setData(result)
        setStale(false)
        setRefreshCount((count) => count + 1)
        document.title = `Compy ${result.version}`
      } catch {
        /* keep showing the last good data, but say that it is old */
        failures += 1
        if (!cancelled && failures >= STALE_AFTER_FAILURES) {
          setStale(true)
        }
      } finally {
        if (!cancelled) {
          timer = window.setTimeout(poll, POLL_MS)
        }
      }
    }
    poll()
    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [compId, offset])

  /* 10 Hz, not requestAnimationFrame: the display has a 1 s resolution, so
   * re-rendering react ~60 times a second bought nothing but cpu — and this
   * one runs unattended on a venue screen for hours */
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      const msAdjust = offset + now.getTimezoneOffset() * 60 * 1000
      now.setMilliseconds(now.getMilliseconds() + msAdjust)
      setTime(now.toLocaleTimeString())
    }
    updateTime()
    const timer = window.setInterval(updateTime, 100)
    return () => window.clearInterval(timer)
  }, [offset])

  /* a malformed url used to show competition 1's starts, or a permanently
   * blank clock, with no way to tell either from a working display */
  if (compId === null) {
    return (
      <div
        id="clock_invalid"
        className="m-0 flex aspect-video w-full items-center justify-center bg-black text-center font-sans text-white"
      >
        <div>
          <div className="text-[8vh]">Invalid clock URL</div>
          <div className="text-[4vh] text-[#888888]">
            Expected /clock/&lt;comp_id&gt;/&lt;current&gt;/&lt;offset&gt;
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="relative m-0 aspect-video w-full bg-black text-center font-sans text-white">
      {stale && (
        <div
          id="clock_stale"
          className="absolute top-[1vh] right-[1vw] rounded bg-[#f83741] px-[1vw] py-[0.5vh] text-[3vh]"
        >
          no connection &mdash; starts may be out of date
        </div>
      )}
      <span id="clock_comp_name" className="text-[8vh]">
        {data?.comp_name ?? ' '}
      </span>
      <div>
        <span id="clock_time" className="ml-[25%] block w-[30%] text-left text-[25vh]">
          {time || ' '}
        </span>
      </div>
      <div
        className={`w-[98%] overflow-hidden pl-[1%] text-left text-[8vh] ${stale ? 'opacity-50' : ''}`}
      >
        {data?.alist != null && (
          <>
            <span id="clock_starts_label" className="font-bold">
              {data.current === 0 ? 'Current starts:' : 'Next starts:'}
            </span>
            <div key={refreshCount} className="clock-divider" />
            <div id="clock_starts">
              {data.alist.map((start, index) => (
                <div key={index} className={start.dns ? 'text-[#888888] line-through' : undefined}>
                  {start.OT} ({start.lane}): {start.name} ({start.country})
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
