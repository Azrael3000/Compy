import { useState } from 'react'
import { api } from '@/lib/api'
import type { LaneListResponse, LaneRow } from '../contracts'
import { useAdmin } from '../AdminApp'

export function LaneListsTab() {
  const { state, withCompId, getPDF, reportError } = useAdmin()
  const [curDay, setCurDay] = useState<string | null>(null)
  const [curBlock, setCurBlock] = useState<string | null>(null)
  const [curLane, setCurLane] = useState<string | null>(null)
  const [laneList, setLaneList] = useState<LaneRow[] | null>(null)

  function loadLane(day: string, block: string, lane: string) {
    setCurLane(lane)
    api
      .get<LaneListResponse>('/lane_list', withCompId({ day, block, lane }))
      .then((data) => setLaneList(data.lane_list ?? null))
      .catch(reportError)
  }

  const days = Object.keys(state.daysWithDisciplinesLanes ?? {})
  const blocks =
    curDay !== null && state.blocks != null ? Object.entries(state.blocks[curDay] ?? {}) : []
  const lanes =
    curDay !== null && curBlock !== null ? (state.blocks?.[curDay]?.[curBlock]?.lanes ?? []) : []

  return (
    <>
      <div id="ll_date_menu">
        {days.map((day) => (
          <a
            key={day}
            href="#"
            onClick={(event) => {
              event.preventDefault()
              setCurDay(day)
              setCurBlock(null)
              setCurLane(null)
              setLaneList(null)
            }}
          >
            {day}
          </a>
        ))}
      </div>
      <div id="ll_discipline_menu">
        {blocks.map(([key, block]) => (
          <a
            key={key}
            href="#"
            onClick={(event) => {
              event.preventDefault()
              setCurBlock(key)
              setCurLane(null)
              setLaneList(null)
            }}
          >
            {block.dis_s}
          </a>
        ))}
      </div>
      <div id="ll_lane_menu">
        {curBlock !== null &&
          lanes.map((lane) => (
            <a
              key={String(lane)}
              href="#"
              className="ll_lane_button"
              id={`ll_${curDay}_${curBlock}_${lane}`}
              onClick={(event) => {
                event.preventDefault()
                loadLane(curDay!, curBlock!, String(lane))
              }}
            >
              {lane}
            </a>
          ))}
      </div>
      <a
        href="#"
        id="ll_all_pdf_button"
        onClick={(event) => {
          event.preventDefault()
          getPDF('lane_list')
        }}
      >
        Print all
      </a>
      <br />
      <a
        href="#"
        id="ll_safety_all_pdf_button"
        onClick={(event) => {
          event.preventDefault()
          getPDF('lane_list', { type: 'safety' })
        }}
      >
        Print Safety all
      </a>
      <div id="ll_content">
        {laneList !== null && (
          <>
            <a
              href="#"
              className="ll_pdf_button"
              id={`ll_pdf_${curDay}_${curBlock}_${curLane}`}
              onClick={(event) => {
                event.preventDefault()
                getPDF('lane_list', { day: curDay!, block: curBlock!, lane: curLane! })
              }}
            >
              Print PDF
            </a>
            <table>
              <tbody>
                <tr>
                  <td>OT</td>
                  <td>Dis</td>
                  <td>Name</td>
                  <td>AP</td>
                  <td>PB</td>
                  <td>Nat.</td>
                  <td>NR</td>
                  <td>RP</td>
                  <td>Card</td>
                  <td>Remarks</td>
                </tr>
                {laneList.map((row, index) => (
                  <tr key={index}>
                    <td>{row.OT}</td>
                    <td>{row.Dis}</td>
                    <td>{row.Name}</td>
                    <td>{row.AP}</td>
                    <td>{row.PB}</td>
                    <td>{row.Nat}</td>
                    <td>{row.NR}</td>
                    <td>{row.RP}</td>
                    <td>{row.Card}</td>
                    <td>{row.Remarks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>
    </>
  )
}
