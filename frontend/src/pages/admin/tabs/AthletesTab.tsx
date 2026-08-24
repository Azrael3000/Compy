import { useState } from 'react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import type { DataPayload } from '../contracts'
import { useAdmin } from '../AdminApp'

const EMPTY = { first_name: '', last_name: '', gender: 'F', country: '', club: '', aida_id: '' }

export function AthletesTab() {
  const { state, applyResponse, withCompId, reportError } = useAdmin()
  const [draft, setDraft] = useState(EMPTY)

  function addAthlete() {
    api
      .postJson<DataPayload>('/athlete', withCompId(draft))
      .then((data) => {
        applyResponse(data)
        setDraft(EMPTY)
      })
      .catch(reportError)
  }

  function deleteAthlete(athleteId: number) {
    api
      .deleteJson<DataPayload>('/athlete', withCompId({ athlete_id: athleteId }))
      .then((data) => applyResponse(data))
      .catch(reportError)
  }

  const field = (key: keyof typeof EMPTY, id: string) => (
    <input
      type="text"
      id={id}
      value={draft[key]}
      onChange={(event) => setDraft((old) => ({ ...old, [key]: event.target.value }))}
    />
  )

  return (
    <>
      <table id="athletes_table">
        <tbody>
          <tr>
            <td>First name</td>
            <td>Last name</td>
            <td>Gender</td>
            <td>Country</td>
            <td>Club</td>
            <td>AIDA Id</td>
            <td></td>
          </tr>
          <tr>
            <td>{field('first_name', 'athlete_first_name')}</td>
            <td>{field('last_name', 'athlete_last_name')}</td>
            <td>
              <select
                name="athlete_gender"
                id="athlete_gender"
                value={draft.gender}
                onChange={(event) => setDraft((old) => ({ ...old, gender: event.target.value }))}
              >
                <option value="F">F</option>
                <option value="M">M</option>
              </select>
            </td>
            <td>{field('country', 'athlete_country')}</td>
            <td>{field('club', 'athlete_club')}</td>
            <td>{field('aida_id', 'athlete_aida_id')}</td>
            <td>
              <Button id="add_athlete" type="button" onClick={addAthlete}>
                Add
              </Button>
            </td>
          </tr>
          {state.athletes.map((athlete) => (
            <tr key={athlete.id}>
              <td>{athlete.first_name}</td>
              <td>{athlete.last_name}</td>
              <td>{athlete.gender}</td>
              <td>{athlete.country}</td>
              <td>{athlete.club}</td>
              <td>{athlete.aida_id}</td>
              <td>
                <Button
                  id={`del_athlete_${athlete.id}`}
                  type="button"
                  className="delete"
                  variant="destructive"
                  onClick={() => deleteAthlete(athlete.id)}
                >
                  Delete
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div id="total_athletes">
        <b>Total athletes: {state.athletes.length}</b>
      </div>
    </>
  )
}
