/*
 * URL parameter helpers.
 *
 * In production the React pages are served on the original Flask routes with
 * path parameters (/judge/<comp_id>/<judge_id>?hash=..., /clock/<comp_id>/<current>/<offset>).
 * On the Vite dev server the pages live at /app/judge.html etc., so the same
 * values are passed as query parameters instead. These helpers accept both.
 */

function query(name: string): string | null {
  return new URLSearchParams(window.location.search).get(name)
}

/* Path segments after the screen name, e.g. /judge/3/2 -> ['3', '2'] */
function pathSegments(screen: string): string[] {
  const parts = window.location.pathname.split('/').filter(Boolean)
  const idx = parts.indexOf(screen)
  if (idx === -1) {
    return []
  }
  return parts.slice(idx + 1)
}

export function judgeParams(): { compId: number; judgeId: number; hash: string } | null {
  const segments = pathSegments('judge')
  const compId = segments[0] ?? query('comp_id')
  const judgeId = segments[1] ?? query('judge_id')
  const hash = query('hash')
  if (compId === null || judgeId === null || hash === null) {
    return null
  }
  return { compId: Number(compId), judgeId: Number(judgeId), hash }
}

/* Number() accepts "" and " " as 0, which is how a malformed url used to
 * turn into a confident request for a competition nobody asked for. */
function toNumber(value: string | null): number | null {
  if (value === null || value.trim() === '') {
    return null
  }
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

/* null for a missing or non-numeric comp_id: the clock used to default it to
 * 1 and then show a different competition's starts on the venue screen
 * without any hint that the url was wrong. current/offset keep defaulting —
 * they are presentation details, not identity. */
export function clockParams(): { compId: number; current: number; offset: number } | null {
  const segments = pathSegments('clock')
  const compId = toNumber(segments[0] ?? query('comp_id'))
  if (compId === null) {
    return null
  }
  return {
    compId,
    current: toNumber(segments[1] ?? query('current')) ?? 0,
    offset: toNumber(segments[2] ?? query('offset')) ?? 0,
  }
}

/* An empty ?comp_id= counts as absent, so the results page falls back to the
 * competition list like the old page instead of asking for competition 0. */
export function resultsCompId(): number | null {
  return toNumber(query('comp_id'))
}
