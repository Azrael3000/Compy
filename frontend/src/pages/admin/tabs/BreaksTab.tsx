import { useState } from 'react'
import { api } from '@/lib/api'
import type { BreaksResponse } from '../contracts'
import { useAdmin } from '../AdminApp'

export function BreaksTab() {
  const { state, withCompId, reportError } = useAdmin()
  const [content, setContent] = useState<BreaksResponse | null>(null)

  function selectDay(day: string) {
    api.get<BreaksResponse>('/breaks', withCompId({ day })).then(setContent).catch(reportError)
  }

  const days = Object.keys(state.daysWithDisciplinesLanes ?? {})

  return (
    <>
      <div id="breaks_date_menu">
        {days.map((day) => (
          <a
            key={day}
            href="#"
            id={`breaks_${day}`}
            onClick={(event) => {
              event.preventDefault()
              selectDay(day)
            }}
          >
            {day}
          </a>
        ))}
      </div>
      <div id="breaks_content">
        {content?.min_break != null && (
          <>
            Minimal break: {content.min_break}
            <br />
          </>
        )}
        {content?.breaks_list != null && (
          <table>
            <tbody>
              <tr>
                <td>Name</td>
                <td>1st Discipline (OT)</td>
                <td>2nd Discipline (OT)</td>
                <td>Break (h:min)</td>
              </tr>
              {content.breaks_list.map((row, index) => (
                <tr key={index}>
                  <td>{row.Name}</td>
                  <td>
                    {row.Dis1} ({row.OT1})
                  </td>
                  <td>
                    {row.Dis2} ({row.OT2})
                  </td>
                  <td>{row.Break}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
