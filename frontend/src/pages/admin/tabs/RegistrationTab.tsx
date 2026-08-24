import { api } from '@/lib/api'
import type { DataPayload } from '../contracts'
import { useAdmin, type Athlete } from '../AdminApp'

/* checkbox column order matches populateSpecialRanking in compy.js; the
 * checkbox id prefix (with '_' stripped once) doubles as the change type
 * sent to /change_registration */
const CHECK_COLUMNS: (keyof Athlete)[] = [
  'eligible_national',
  'special_ranking',
  'paid',
  'medical_checked',
  'registered',
]

export function RegistrationTab() {
  const { state, update, applyResponse, withCompId, reportError } = useAdmin()

  function changeRegistration(athleteId: number, column: keyof Athlete, checked: boolean) {
    const type = column.replace('_', '')
    /* flip the flag locally right away (the checkbox is a controlled
     * input); the response carries the stored athlete list and confirms */
    update({
      athletes: state.athletes.map((athlete) =>
        athlete.id === athleteId ? { ...athlete, [column]: checked ? 1 : 0 } : athlete,
      ),
    })
    /* the id travels as a string, like the old checkbox-id-derived value */
    api
      .postJson<DataPayload>(
        '/change_registration',
        withCompId({ id: String(athleteId), checked, type }),
      )
      .then((data) => applyResponse(data))
      .catch(reportError)
  }

  return (
    <table id="registration_table">
      <tbody>
        <tr>
          <td>Last name</td>
          <td>First name</td>
          <td>Gender</td>
          <td>Country</td>
          <td>Eligible National</td>
          <td>{state.specialRankingName}</td>
          <td>Paid</td>
          <td>Medical</td>
          <td>Registered</td>
        </tr>
        {state.athletes.map((athlete) => (
          <tr key={athlete.id}>
            <td>{athlete.last_name}</td>
            <td>{athlete.first_name}</td>
            <td>{athlete.gender}</td>
            <td>{athlete.country}</td>
            {CHECK_COLUMNS.map((column) => (
              <td key={column}>
                <input
                  type="checkbox"
                  id={`${column.replace('_', '')}_cb_${athlete.id}`}
                  name={String(athlete.id)}
                  value="true"
                  className="registration_checkbox"
                  checked={Boolean(athlete[column])}
                  onChange={(event) => changeRegistration(athlete.id, column, event.target.checked)}
                />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
