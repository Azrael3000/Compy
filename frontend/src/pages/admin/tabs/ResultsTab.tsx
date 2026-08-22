import { useState } from 'react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { DialogTitle } from '@/components/ui/dialog'
import type { AdminResultResponse, ResultRow } from '../contracts'
import { getRemarksForCard, penaltyUnderAP, timeToMinutes } from '@/lib/results_utils'
import { minutesToStr } from '../sl_utils'
import { useAdmin } from '../AdminApp'

export function ResultsTab() {
  const admin = useAdmin()
  const { state, withCompId, showOverlay, hideOverlay, getPDF, reportError } = admin
  const [menu, setMenu] = useState<{
    discipline: string | null
    gender: string | null
    country: string | null
  }>({ discipline: null, gender: null, country: null })
  const [rows, setRows] = useState<ResultRow[] | null>(null)
  const [keys, setKeys] = useState<string[] | null>(null)

  function getResult(discipline: string, gender: string, country: string) {
    setMenu({ discipline, gender, country })
    api
      .get<AdminResultResponse>('/result', withCompId({ discipline, gender, country }))
      .then((data) => {
        setRows(data.results ?? null)
        setKeys(data.keys ?? null)
      })
      .catch(reportError)
  }

  function selectGender(discipline: string, gender: string) {
    const countries = state.resultCountries ?? []
    if (countries.length === 0) {
      getResult(discipline, gender, 'International')
    } else {
      setMenu({ discipline, gender, country: null })
    }
  }

  function openResultDialog(row: ResultRow, add: boolean) {
    const discipline = menu.discipline!
    showOverlay(
      <ResultDialog
        add={add}
        row={row}
        discipline={discipline}
        federation={state.compType}
        onCancel={hideOverlay}
        onSave={(values) => {
          api
            .putJson<AdminResultResponse>(
              '/result',
              withCompId({
                id: row.Id,
                ...values,
                discipline,
                gender: menu.gender,
                country: menu.country,
              }),
            )
            .then((data) => {
              hideOverlay()
              setRows(data.results ?? null)
              setKeys(data.keys ?? null)
            })
            .catch(reportError)
        }}
      />,
    )
  }

  /* rows without a result come last; the original showed a divider row */
  const firstUnset = rows?.findIndex((row) => row.Remarks === '') ?? -1
  const editable =
    menu.discipline !== null &&
    menu.discipline !== 'Overall' &&
    menu.discipline !== state.specialRankingName

  return (
    <>
      <div id="result_discipline_menu">
        {(state.disciplines ?? []).map((discipline) => (
          <a
            key={discipline}
            href="#"
            onClick={(event) => {
              event.preventDefault()
              setMenu({ discipline, gender: null, country: null })
              setRows(null)
            }}
          >
            {discipline}
          </a>
        ))}
      </div>
      <div id="result_gender_menu">
        {menu.discipline !== null &&
          ['Female', 'Male'].map((gender) => (
            <a
              key={gender}
              href="#"
              onClick={(event) => {
                event.preventDefault()
                selectGender(menu.discipline!, gender === 'Female' ? 'F' : 'M')
              }}
            >
              {gender}
            </a>
          ))}
      </div>
      <div id="result_country_menu">
        {menu.discipline !== null &&
          menu.gender !== null &&
          (state.resultCountries ?? []).map((country) => (
            <a
              key={country}
              href="#"
              className="result_button"
              id={`result_${menu.discipline}_${menu.gender}_${country}`}
              onClick={(event) => {
                event.preventDefault()
                getResult(menu.discipline!, menu.gender!, country)
              }}
            >
              {country}
            </a>
          ))}
      </div>
      <a
        href="#"
        id="result_all_pdf_button"
        onClick={(event) => {
          event.preventDefault()
          getPDF('result')
        }}
      >
        Print all
      </a>
      <br />
      <a
        href="#"
        id="result_all_top3_pdf_button"
        onClick={(event) => {
          event.preventDefault()
          getPDF('result', { type: 'top3' })
        }}
      >
        Print all (top 3 only)
      </a>
      <div id="results_content">
        {rows !== null && rows.length === 0 && (
          <div className="text-muted-foreground">No results yet.</div>
        )}
        {rows !== null && keys !== null && rows.length > 0 && (
          <>
            <a
              href="#"
              className="results_pdf_button"
              id={`result_pdf_${menu.discipline}_${menu.gender}_${menu.country}`}
              onClick={(event) => {
                event.preventDefault()
                getPDF('result', {
                  discipline: menu.discipline!,
                  gender: menu.gender!,
                  country: menu.country!,
                })
              }}
            >
              Print PDF
            </a>
            <table>
              <tbody>
                <tr>
                  {keys.map((key) => (
                    <td key={key}>{key}</td>
                  ))}
                  <td />
                </tr>
                {rows.map((row, index) => (
                  <RowWithDivider
                    key={index}
                    showDivider={index === firstUnset}
                    colSpan={keys.length + 1}
                  >
                    {keys.map((key) => (
                      <td key={key} id={`result_${key}_${row.Id}`}>
                        {row[key]}
                      </td>
                    ))}
                    {editable && (
                      <td>
                        <Button
                          className={
                            firstUnset !== -1 && index >= firstUnset ? 'result_add' : 'result_edit'
                          }
                          id={`result_${row.Id}`}
                          onClick={() =>
                            openResultDialog(row, firstUnset !== -1 && index >= firstUnset)
                          }
                        >
                          {firstUnset !== -1 && index >= firstUnset ? 'Add result' : 'Edit result'}
                        </Button>
                      </td>
                    )}
                  </RowWithDivider>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
    </>
  )
}

function RowWithDivider({
  showDivider,
  colSpan,
  children,
}: {
  showDivider: boolean
  colSpan: number
  children: React.ReactNode
}) {
  return (
    <>
      {showDivider && (
        <tr>
          <td colSpan={colSpan} style={{ paddingTop: 10 }}>
            <b>Athletes without result</b>
          </td>
        </tr>
      )}
      <tr>{children}</tr>
    </>
  )
}

function ResultDialog({
  add,
  row,
  discipline,
  federation,
  onCancel,
  onSave,
}: {
  add: boolean
  row: ResultRow
  discipline: string
  federation: 'aida' | 'cmas'
  onCancel: () => void
  onSave: (values: {
    rp: string
    penalty: string
    card: string
    remarks: string
    judge_remarks: string
  }) => void
}) {
  const isSta = discipline === 'STA'
  const initialCard = add ? 'WHITE' : String(row.Card ?? '')
  const underAp = add
    ? null
    : penaltyUnderAP(
        String(row.RP ?? ''),
        String(row.AP ?? ''),
        initialCard,
        federation,
        discipline,
      )
  let initialPenalty = add ? 0 : Number(row.Penalty ?? 0)
  if (underAp !== null) {
    initialPenalty -= underAp
  }
  let initialRp = add ? '0' : String(row.RP ?? '0')
  if (isSta && !add) {
    initialRp = String(timeToMinutes(initialRp))
  }
  if (isSta) {
    initialRp = minutesToStr(Number(initialRp), true)
  }

  const cards = federation === 'aida' ? ['WHITE', 'YELLOW', 'RED'] : ['WHITE', 'RED']
  const remarksForRed =
    federation === 'aida' ? getRemarksForCard('RED', federation, discipline) : {}
  /* a RED card always yields the grouped list, never the WHITE string */
  const allRemarks: Record<string, string[]> =
    typeof remarksForRed === 'string' ? {} : remarksForRed
  /* like the old checkbox dialog, only recognized remarks are seeded and
   * saved — display-only additions in the Remarks column (e.g. record
   * flags such as ", NR") must not be written back to the database */
  const validRemarks = Object.values(allRemarks).flat()

  const [rp, setRp] = useState(initialRp)
  const [penalty, setPenalty] = useState(String(initialPenalty))
  const [card, setCard] = useState(initialCard)
  const [remarks, setRemarks] = useState<string[]>(
    add
      ? []
      : String(row.Remarks ?? '')
          .split(',')
          .map((remark) => remark.trim())
          .filter((remark) => validRemarks.includes(remark)),
  )
  const [judgeRemarks, setJudgeRemarks] = useState(add ? '' : String(row.JudgeRemarks ?? ''))

  return (
    <div>
      <DialogTitle>
        {add ? 'Add' : 'Edit'} result for {row.Name}
      </DialogTitle>
      <table>
        <tbody>
          <tr>
            <td>RP</td>
            <td>
              <input
                type={isSta ? 'time' : 'number'}
                id="result_rp"
                value={rp}
                onChange={(event) => setRp(event.target.value)}
              />
            </td>
          </tr>
          <tr>
            <td>Penalty</td>
            <td>
              <input
                type="number"
                id="result_penalty"
                value={penalty}
                onChange={(event) => setPenalty(event.target.value)}
              />
              {underAp !== null ? ` + ${underAp} (UNDER AP)` : ''}
            </td>
          </tr>
          <tr>
            <td>Card</td>
            <td>
              <div id="result_card_chooser">
                {cards.map((cardOption) => (
                  <span key={cardOption}>
                    <input
                      type="radio"
                      name="result_card"
                      value={cardOption}
                      id={`result_card_${cardOption.toLowerCase()}`}
                      checked={card === cardOption}
                      onChange={() => setCard(cardOption)}
                    />
                    <label htmlFor={`result_card_${cardOption.toLowerCase()}`}>{cardOption}</label>
                  </span>
                ))}
              </div>
            </td>
          </tr>
          <tr>
            <td>Remark</td>
            <td>
              <div id="result_remark_chooser">
                {Object.entries(allRemarks).map(([group, list]) => (
                  <span key={group}>
                    <span>{group}:</span>
                    <br />
                    {list.map((remark) => (
                      <span key={remark}>
                        <input
                          type="checkbox"
                          name="result_remark"
                          value={remark}
                          id={`result_remark_${remark}`}
                          checked={remarks.includes(remark)}
                          onChange={(event) =>
                            setRemarks((old) =>
                              event.target.checked
                                ? [...old, remark]
                                : old.filter((r) => r !== remark),
                            )
                          }
                        />
                        <label htmlFor={`result_remark_${remark}`}>{remark}</label>
                        <br />
                      </span>
                    ))}
                  </span>
                ))}
              </div>
            </td>
          </tr>
          <tr>
            <td>Judge Remarks</td>
            <td>
              <input
                type="text"
                id="result_judge_remarks"
                value={judgeRemarks}
                onChange={(event) => setJudgeRemarks(event.target.value)}
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
                id="result_save"
                type="button"
                onClick={() =>
                  onSave({
                    rp,
                    penalty,
                    card,
                    remarks: remarks.join(),
                    judge_remarks: judgeRemarks,
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
