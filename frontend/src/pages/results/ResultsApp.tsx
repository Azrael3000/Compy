import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, type Envelope } from '@/lib/api'
import { resultsCompId } from '@/lib/params'

interface ResultsData extends Envelope {
  version: string
  data?: {
    comp_list?: { id: number; name: string }[]
    disciplines?: string[]
    countries?: string[]
    comp_name?: string
    comp_id?: number
  }
}

interface IndividualResult {
  dis: string
  rp: string
}

interface ResultRow {
  rank: number | string
  name: string
  value: string | number
  country?: string
  card?: string | null
  ap?: string | null
  penalty?: string | number | null
  remarks?: string | null
  points?: string | number | null
  individual_results?: IndividualResult[]
}

interface ResultList extends Envelope {
  results: ResultRow[]
}

/*
 * Public results page, port of static/results.js. Navigation model is
 * unchanged: competition list -> discipline menu -> result table, with the
 * header cells switching gender / reopening the discipline and country
 * menus, and result rows expanding on tap.
 */
export function ResultsApp() {
  const compId = resultsCompId()
  const [bootstrap, setBootstrap] = useState<ResultsData | null>(null)
  const [menu, setMenu] = useState<{
    discipline: number | null
    gender: 'Female' | 'Male'
    country: number | null
  }>({ discipline: null, gender: 'Female', country: null })
  const [picking, setPicking] = useState<'discipline' | 'country' | null>('discipline')
  const [rows, setRows] = useState<ResultRow[] | null>(null)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<ResultsData>('/results_data', compId === null ? undefined : { comp_id: compId })
      .then((data) => {
        setBootstrap(data)
        document.title = `Compy ${data.version}`
      })
      .catch(() => setError('Failed to load results.'))
  }, [compId])

  /* memoized so the `?? []` fallback does not hand showResult a new array
   * identity on every render */
  const disciplines = useMemo(() => bootstrap?.data?.disciplines ?? [], [bootstrap])
  const countries = useMemo(() => bootstrap?.data?.countries ?? [], [bootstrap])

  const showResult = useCallback(
    (discipline: number, gender: 'Female' | 'Male', country: number | null) => {
      /* same defaults as the old showResult(): Female, country International */
      let countryIdx = country
      if (countryIdx === null) {
        countryIdx = Math.max(countries.indexOf('International'), 0)
      }
      setMenu({ discipline, gender, country: countryIdx })
      setPicking(null)
      setRows(null)
      setExpanded(new Set())
      setError(null)
      api
        .get<ResultList>('/results_list', {
          comp_id: compId,
          discipline,
          gender,
          country: countryIdx,
        })
        .then((data) => setRows(data.results))
        .catch(() => setError('Failed to get result data.'))
    },
    [compId, countries],
  )

  const toggleRow = (index: number) => {
    setExpanded((old) => {
      const next = new Set(old)
      if (next.has(index)) {
        next.delete(index)
      } else {
        next.add(index)
      }
      return next
    })
  }

  const disciplineName = menu.discipline === null ? '' : disciplines[menu.discipline]
  const countryName = menu.country === null ? '' : countries[menu.country]

  return (
    <>
      <div id="compy_title">Compy {bootstrap?.version ?? ''}</div>
      <div id="header">
        {bootstrap?.data?.comp_name != null && (
          /* back to the competition list = this page without ?comp_id.
           * A relative 'results' resolves to /app/results on the vite dev
           * server (404); the current pathname is right in both setups. */
          <div id="title" onClick={() => location.assign(location.pathname)}>
            {bootstrap.data.comp_name}
          </div>
        )}
        {picking === null && (
          <div>
            <div id="discipline" onClick={() => setPicking('discipline')}>
              {disciplineName}
            </div>
            <div
              id="gender"
              onClick={() =>
                menu.discipline !== null &&
                showResult(
                  menu.discipline,
                  menu.gender === 'Female' ? 'Male' : 'Female',
                  menu.country,
                )
              }
            >
              {menu.gender}
            </div>
            <div id="country" onClick={() => setPicking('country')}>
              {countryName}
            </div>
          </div>
        )}
      </div>
      <div id="content">
        {error !== null && (
          <div id="results_error" className="error">
            {error}
          </div>
        )}
        {/* competition menu (no comp_id in the url) */}
        {bootstrap?.data?.comp_list != null &&
          bootstrap.data.comp_list.map((comp) => (
            <button
              key={comp.id}
              id={`comp_${comp.id}`}
              type="button"
              className="comp_menu"
              onClick={() => (location.href = `?comp_id=${comp.id}`)}
            >
              {comp.name}
            </button>
          ))}
        {/* discipline / country menus */}
        {/* keyed by index, not by name: the api addresses both menus by
            index, and a special ranking may legitimately be named after a
            discipline ("STA"), which duplicated the react key */}
        {picking === 'discipline' &&
          disciplines.map((discipline, index) => (
            <button
              key={index}
              id={`list_${index}`}
              type="button"
              className="list_menu discipline"
              onClick={() => showResult(index, menu.gender, menu.country)}
            >
              {discipline}
            </button>
          ))}
        {picking === 'country' &&
          countries.map((country, index) => (
            <button
              key={index}
              id={`list_${index}`}
              type="button"
              className="list_menu country"
              onClick={() =>
                menu.discipline !== null && showResult(menu.discipline, menu.gender, index)
              }
            >
              {country}
            </button>
          ))}
        {/* result table */}
        {picking === null && rows != null && (
          <table>
            <tbody>
              {rows.map((row, index) => {
                const cardClass = row.card != null && row.card !== 'WHITE' ? row.card : ''
                const isOpen = expanded.has(index)
                return (
                  <ResultRowGroup
                    key={index}
                    row={row}
                    index={index}
                    cardClass={cardClass}
                    isOpen={isOpen}
                    /* the payload, not the name, decides which sub-rows to
                     * render: an aggregate ranking carries individual_results,
                     * and a special ranking named like a discipline ("STA")
                     * used to be mistaken for the discipline itself */
                    isMain={row.individual_results == null}
                    onToggle={() => toggleRow(index)}
                  />
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}

function ResultRowGroup({
  row,
  index,
  cardClass,
  isOpen,
  isMain,
  onToggle,
}: {
  row: ResultRow
  index: number
  cardClass: string
  isOpen: boolean
  isMain: boolean
  onToggle: () => void
}) {
  return (
    <>
      <tr className="spacer" />
      <tr
        className={`toggle first ${isOpen ? '' : 'last'}`}
        id={`main_${index}`}
        onClick={onToggle}
      >
        <td>{row.rank}</td>
        <td>{row.name}</td>
        <td className={cardClass}>{row.value}</td>
      </tr>
      {isOpen &&
        (isMain ? (
          <>
            <tr className={`toggle sub sub_${index}`} id={`sub1_${index}`} onClick={onToggle}>
              <td>
                <span className="head">Nat.</span>
                <br />
                {row.country}
              </td>
              <td className={cardClass}>
                <span className="head">Card</span>
                <br />
                {row.card}
              </td>
              <td>
                <span className="head">AP</span>
                <br />
                {row.ap}
              </td>
            </tr>
            <tr className={`toggle sub sub_${index} last`} id={`sub2_${index}`} onClick={onToggle}>
              <td>
                <span className="head">Penalty</span>
                <br />
                {row.penalty}
              </td>
              <td>
                <span className="head">Remarks</span>
                <br />
                {row.remarks}
              </td>
              <td>
                <span className="head">Points</span>
                <br />
                {row.points}
              </td>
            </tr>
          </>
        ) : (
          (row.individual_results ?? []).map((individual, subIndex, all) => (
            <tr
              key={subIndex}
              className={`toggle sub sub_${index} ${subIndex === all.length - 1 ? 'last' : ''}`}
              id={`sub${subIndex}_${index}`}
              onClick={onToggle}
            >
              <td />
              <td>{individual.dis}</td>
              <td>{individual.rp}</td>
            </tr>
          ))
        ))}
    </>
  )
}
