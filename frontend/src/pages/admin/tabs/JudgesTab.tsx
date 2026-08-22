import { useState } from 'react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { DialogTitle } from '@/components/ui/dialog'
import type { DataPayload, QrCodeResponse } from '../contracts'
import { useAdmin } from '../AdminApp'

export function JudgesTab() {
  const { state, applyResponse, withCompId, showOverlay, hideOverlay, reportError } = useAdmin()
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')

  function addJudge() {
    /* a judge without a name would render as an empty row */
    if (firstName.trim() === '' || lastName.trim() === '') {
      return
    }
    api
      .postJson<DataPayload>('/judge', withCompId({ first_name: firstName, last_name: lastName }))
      .then((data) => {
        applyResponse(data)
        setFirstName('')
        setLastName('')
      })
      .catch(reportError)
  }

  function showQr(judgeId: number) {
    api
      .get<QrCodeResponse>('/judge/qr_code', withCompId({ judge_id: judgeId }))
      .then((data) =>
        showOverlay(
          <div className="flex flex-col items-center gap-4">
            <DialogTitle>
              QR Code for {data.judge_first_name} {data.judge_last_name}
            </DialogTitle>
            <a href={data.judge_url} target="_blank" rel="noopener noreferrer">
              {/* the code carries its own quiet zone, so it only needs the
                  border to separate its white from the dialog's */}
              <img
                src={data.judge_qr_code}
                alt={`QR code for ${data.judge_first_name} ${data.judge_last_name}`}
                className="block w-[250px] rounded-md border"
              />
            </a>
            <Button id="overlay_cancel" type="button" onClick={hideOverlay}>
              Close
            </Button>
          </div>,
        ),
      )
      .catch(reportError)
  }

  function deleteJudge(judgeId: number) {
    api
      .deleteJson<DataPayload>('/judge', withCompId({ judge_id: judgeId }))
      .then((data) => applyResponse(data))
      .catch(reportError)
  }

  return (
    <table id="judges_table">
      <tbody>
        <tr>
          <td>First name</td>
          <td>Last name</td>
          <td>Action</td>
        </tr>
        <tr>
          <td>
            <input
              type="text"
              id="judge_first_name"
              value={firstName}
              onChange={(event) => setFirstName(event.target.value)}
            />
          </td>
          <td>
            <input
              type="text"
              id="judge_last_name"
              value={lastName}
              onChange={(event) => setLastName(event.target.value)}
            />
          </td>
          <td>
            <Button
              id="add_judge"
              type="button"
              disabled={firstName.trim() === '' || lastName.trim() === ''}
              onClick={addJudge}
            >
              Add
            </Button>
          </td>
        </tr>
        {state.judges.map((judge) => (
          <tr key={judge.id}>
            <td>{judge.first_name}</td>
            <td>{judge.last_name}</td>
            <td>
              <Button
                id={`show_judge_${judge.id}`}
                type="button"
                className="show"
                variant="outline"
                onClick={() => showQr(judge.id)}
              >
                Show QR
              </Button>
              <Button
                id={`del_judge_${judge.id}`}
                type="button"
                className="delete"
                variant="destructive"
                onClick={() => deleteJudge(judge.id)}
              >
                Delete
              </Button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
