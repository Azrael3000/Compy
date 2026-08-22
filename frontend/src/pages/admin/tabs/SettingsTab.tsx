import { useEffect, useRef, useState } from 'react'
import { api, type Envelope } from '@/lib/api'
import { downloadBlob, errorMessage } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import type { DataPayload, SaveCompResponse } from '../contracts'
import * as audio from '../audio'
import { useAdmin } from '../AdminApp'

/* "" and "-" are legitimate intermediate states while typing a negative
 * adjustment; both mean "no adjustment yet" rather than NaN */
function parseAdjust(text: string): number {
  const value = Number(text)
  return text === '' || Number.isNaN(value) ? 0 : value
}

export function SettingsTab() {
  const admin = useAdmin()
  const { state, update, applyResponse, loadCompetition, withCompId, reportError } = admin
  const [showSave, setShowSave] = useState(false)
  const [showOverwrite, setShowOverwrite] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [aidaStatus, setAidaStatus] = useState<string | null>(null)
  const [aidaBusy, setAidaBusy] = useState(false)
  const [nrsBusy, setNrsBusy] = useState(false)
  /* the upload buttons stay disabled until their file input has a file */
  const [hasFile, setHasFile] = useState(false)
  const [hasSponsor, setHasSponsor] = useState(false)
  /* the two time-adjustment fields keep their raw text so an intermediate
   * "-" survives typing; a controlled number input coerces it to 0 and the
   * negative values become unreachable except through the spinner arrows */
  const [secondsText, setSecondsText] = useState(String(state.secondsAdjust))
  const [decisecondsText, setDecisecondsText] = useState(String(state.decisecondsAdjust))
  const prevNameRef = useRef('')
  const fileRef = useRef<HTMLInputElement>(null)
  const sponsorRef = useRef<HTMLInputElement>(null)
  const aidaKeyRef = useRef<HTMLInputElement>(null)
  /* the old page fired /change_special_ranking_name from a .change() handler,
   * i.e. only on a real edit; a plain onBlur re-saves (and resets all the
   * submenus) every time the field merely loses focus. Remembering the value
   * as of focus reproduces .change() without tracking server updates. */
  const nameOnFocusRef = useRef(state.specialRankingName)

  /* clear the api key whenever a different competition is loaded — what the
   * old populateAidaSettings() did on every load. Without it a key typed for
   * competition A and left unsaved gets stored on competition B. */
  useEffect(() => {
    if (aidaKeyRef.current) {
      aidaKeyRef.current.value = ''
    }
  }, [state.compId])

  const showStatus = (message: string) => setStatus(message)

  /* a real name plus the extension — a file literally named ".xlsx" is a
   * dotfile without extension and gets rejected by the server */
  const validUpload = (input: HTMLInputElement, extension: string) => {
    const name = input.files?.[0]?.name ?? ''
    return name.length > extension.length && name.toLowerCase().endsWith(extension)
  }

  function saveComp(overwrite: boolean) {
    setShowSave(false)
    api
      .postJson<SaveCompResponse>(
        '/competition',
        withCompId({ comp_name: state.compName, overwrite }),
      )
      .then((data) => {
        if (data.file_exists && !overwrite) {
          prevNameRef.current = data.prev_name ?? ''
          setShowOverwrite(true)
        } else {
          setShowOverwrite(false)
          if (data.comp_id != null) {
            update({ compId: data.comp_id })
          }
          applyResponse(data)
        }
      })
      .catch(reportError)
  }

  function uploadFile() {
    const file = fileRef.current?.files?.[0]
    const form = new FormData()
    if (file) {
      form.append('file', file)
    }
    form.append('comp_id', String(state.compId))
    api
      .postForm<DataPayload>('/upload_file', form)
      .then((data) => {
        showStatus(data.status_msg ?? '')
        if (typeof data.special_ranking_name === 'string') {
          update({ specialRankingName: data.special_ranking_name })
        }
        applyResponse(data, true)
      })
      .catch((error) => showStatus(String(error.message ?? error)))
  }

  async function storeResults() {
    const file = fileRef.current?.files?.[0]
    const form = new FormData()
    if (file) {
      form.append('file', file)
    }
    form.append('comp_id', String(state.compId))
    try {
      /* api.postFormBlob carries the 401 -> login redirect and recognises the
       * HTTP 200 json envelope this endpoint answers with when the upload is
       * rejected — a raw fetch saved that envelope as a .xlsx */
      const blob = await api.postFormBlob('/store_results', form)
      downloadBlob(blob, 'Result_' + (file?.name ?? 'results.xlsx'))
    } catch (err) {
      showStatus('Storing results failed: ' + errorMessage(err))
    }
  }

  function uploadSponsor() {
    const file = sponsorRef.current?.files?.[0]
    const form = new FormData()
    if (file) {
      form.append('sponsor_img', file)
    }
    form.append('comp_id', String(state.compId))
    api
      .postForm<Envelope>('/upload_sponsor_img', form)
      .then((data) => showStatus(data.status_msg ?? ''))
      .catch((error) => showStatus(String(error.message ?? error)))
  }

  function aidaCall(path: string, body: object, before: string | null, refresh: boolean) {
    if (before !== null) {
      setAidaStatus(before)
    }
    setAidaBusy(true)
    api
      .postJson<DataPayload>(path, withCompId(body))
      .then((data) => {
        setAidaStatus(data.status_msg ?? '')
        if ('aida_event_id' in data) {
          update({ aidaEventId: data.aida_event_id ?? null })
        }
        if ('aida_has_key' in data) {
          update({ aidaHasKey: Boolean(data.aida_has_key) })
          if (aidaKeyRef.current) {
            aidaKeyRef.current.value = ''
          }
        }
        if (refresh && data.status === 'success') {
          applyResponse(data, true)
        }
      })
      .catch((error) => setAidaStatus(String(error.message ?? error)))
      .finally(() => setAidaBusy(false))
  }

  function refreshNrs() {
    showStatus('Update of national records started.')
    setNrsBusy(true)
    api
      .get<Envelope>('/national_records', withCompId())
      .then(() => showStatus('Update of national records completed.'))
      .catch((error) => showStatus('Update of national records failed: ' + (error.message ?? '')))
      .finally(() => setNrsBusy(false))
  }

  function deleteCompetition(compId: number) {
    api
      .deleteJson<DataPayload>('/competition', { comp_id: compId })
      .then((data) => {
        applyResponse(data)
        if (compId === state.compId) {
          loadCompetition(1)
        }
      })
      .catch(reportError)
  }

  return (
    <>
      <p>Competition settings</p>
      <form id="upload_file" onSubmit={(event) => event.preventDefault()}>
        <div>
          <label htmlFor="comp_name">Competition name</label>
          <br />
          <input
            type="text"
            id="comp_name"
            value={state.compName}
            onChange={(event) => {
              update({ compName: event.target.value })
              setShowSave(true)
            }}
          />
          <Button
            id="save_comp"
            type="button"
            style={{ display: showSave ? 'inline-block' : 'none' }}
            onClick={() => saveComp(false)}
          >
            Save
          </Button>
          {showOverwrite && (
            <div id="overwrite">
              <p>Overwrite?</p>
              <Button id="overwrite_yes" type="button" onClick={() => saveComp(true)}>
                Yes
              </Button>
              <Button
                id="overwrite_no"
                type="button"
                onClick={() => {
                  update({ compName: prevNameRef.current })
                  setShowOverwrite(false)
                }}
              >
                No
              </Button>
            </div>
          )}
          <br />
          <label htmlFor="file">Choose file to upload</label>
          <br />
          <input
            type="file"
            id="file"
            name="file"
            accept=".xlsx"
            ref={fileRef}
            onChange={(event) => setHasFile(validUpload(event.target, '.xlsx'))}
          />
        </div>
        <div>
          <Button id="upload_file_button" type="button" disabled={!hasFile} onClick={uploadFile}>
            Refresh data
          </Button>
          <Button
            id="store_results_button"
            type="button"
            disabled={!hasFile}
            onClick={storeResults}
          >
            Store results
          </Button>
        </div>
      </form>
      <form id="upload_sponsor_img" onSubmit={(event) => event.preventDefault()}>
        <div>
          <label htmlFor="sponsor_img">Sponsor image (ideal aspect ratio: 19x5, format: png)</label>
          <br />
          <input
            type="file"
            id="sponsor_img"
            name="sponsor_img"
            accept=".png"
            ref={sponsorRef}
            onChange={(event) => setHasSponsor(validUpload(event.target, '.png'))}
          />
        </div>
        <div>
          <Button
            id="upload_sponsor_img_button"
            type="button"
            disabled={!hasSponsor}
            onClick={uploadSponsor}
          >
            Upload Sponsor Image
          </Button>
        </div>
      </form>
      {status !== null && <div id="file_upload_status">{status}</div>}
      <div id="aida_integration">
        <p>AIDA API (read only)</p>
        <label htmlFor="aida_event_id">Event id</label>
        <input
          type="number"
          id="aida_event_id"
          min={1}
          value={state.aidaEventId ?? ''}
          onChange={(event) =>
            update({ aidaEventId: event.target.value === '' ? null : Number(event.target.value) })
          }
        />
        <label htmlFor="aida_api_key">API key</label>
        <input
          type="password"
          id="aida_api_key"
          autoComplete="off"
          ref={aidaKeyRef}
          placeholder={state.aidaHasKey ? 'key stored (type to replace)' : 'no key stored'}
        />
        <Button
          id="aida_save_settings"
          type="button"
          onClick={() =>
            aidaCall(
              '/aida/settings',
              {
                aida_event_id: state.aidaEventId ?? '',
                aida_api_key: aidaKeyRef.current?.value ?? '',
              },
              null,
              false,
            )
          }
        >
          Save
        </Button>
        <Button
          id="aida_test_button"
          type="button"
          disabled={aidaBusy}
          onClick={() => aidaCall('/aida/test', {}, 'Testing connection to AIDA...', false)}
        >
          Test connection
        </Button>
        <Button
          id="aida_sync_button"
          type="button"
          disabled={aidaBusy}
          onClick={() => aidaCall('/aida/sync', {}, 'Sync from AIDA started...', true)}
        >
          Sync from AIDA
        </Button>
        {aidaStatus !== null && <div id="aida_status">{aidaStatus}</div>}
      </div>
      <label>Choose Lane Style:</label>
      <div id="lane_style_chooser">
        {(['numeric', 'alphabetic'] as const).map((styleOption) => (
          <span key={styleOption}>
            <input
              type="radio"
              name="lane_style"
              value={styleOption}
              id={`${styleOption}_radio`}
              checked={state.laneStyle === styleOption}
              onChange={() => {
                update({ laneStyle: styleOption })
                api
                  .postJson<DataPayload>(
                    '/change_lane_style',
                    withCompId({ lane_style: styleOption }),
                  )
                  .then((data) => applyResponse(data))
                  .catch(reportError)
              }}
            />
            <label htmlFor={`${styleOption}_radio`}>
              {styleOption[0].toUpperCase() + styleOption.slice(1)}
            </label>
          </span>
        ))}
      </div>
      <label>Choose federation:</label>
      <div id="comp_type_chooser">
        {(['aida', 'cmas'] as const).map((federation) => (
          <span key={federation}>
            <input
              type="radio"
              name="comp_type"
              value={federation}
              id={`${federation}_radio`}
              checked={state.compType === federation}
              onChange={() => {
                update({ compType: federation })
                audio.setFederation(federation)
                api
                  .postJson<DataPayload>('/change_comp_type', withCompId({ comp_type: federation }))
                  .then((data) => {
                    applyResponse(data)
                    audio.initAudio()
                  })
                  .catch(reportError)
              }}
            />
            <label htmlFor={`${federation}_radio`}>{federation.toUpperCase()}</label>
          </span>
        ))}
      </div>
      <div id="special_ranking_chooser">
        <label htmlFor="special_ranking_name">Name of special ranking</label>
        <br />
        <input
          type="text"
          id="special_ranking_name"
          value={state.specialRankingName}
          onChange={(event) => update({ specialRankingName: event.target.value })}
          onFocus={() => (nameOnFocusRef.current = state.specialRankingName)}
          onBlur={() => {
            if (state.specialRankingName === nameOnFocusRef.current) {
              return
            }
            nameOnFocusRef.current = state.specialRankingName
            api
              .postJson<DataPayload>(
                '/change_special_ranking_name',
                withCompId({ special_ranking_name: state.specialRankingName }),
              )
              .then((data) => applyResponse(data, true))
              .catch(reportError)
          }}
        />
      </div>
      {state.countries != null && (
        <div id="country_chooser">
          Country specific results for:{' '}
          <select
            id="country_select"
            value={state.selectedCountry}
            onChange={(event) => {
              update({ selectedCountry: event.target.value })
              api
                .postJson<DataPayload>(
                  '/change_selected_country',
                  withCompId({ selected_country: event.target.value }),
                )
                .then((data) => applyResponse(data))
                .catch(reportError)
            }}
          >
            <option value="none">None</option>
            {state.countries
              .filter((country, index) => country !== 'International' && index !== 0)
              .map((country) => (
                <option key={country} value={country}>
                  {country}
                </option>
              ))}
          </select>
        </div>
      )}
      <div id="publish_results_selector">
        <input
          type="checkbox"
          name="publish_results"
          id="publish_results"
          checked={state.publishResults}
          onChange={(event) => {
            /* optimistic, but rolled back on failure: without this the ui
             * claims results are published when the patch never landed */
            const wanted = event.target.checked
            const previous = state.publishResults
            update({ publishResults: wanted })
            api
              .patchJson<Envelope>('/publish_results', {
                publish_results: wanted,
                comp_id: state.compId,
              })
              .catch((error) => {
                update({ publishResults: previous })
                reportError(error)
              })
          }}
        />
        <label htmlFor="publish_results">Publish results</label>
      </div>
      <div>
        Time adjustment:{' '}
        {/* the audio module is driven by the effect in AdminApp that watches
            these two values — calling audio.setAdjustMs() here as well was a
            second source of truth for the same setting */}
        <input
          type="number"
          value={secondsText}
          step={1}
          id="seconds_adjust"
          name="seconds_adjust"
          onChange={(event) => {
            setSecondsText(event.target.value)
            update({ secondsAdjust: parseAdjust(event.target.value) })
          }}
          onBlur={() => setSecondsText(String(state.secondsAdjust))}
        />{' '}
        seconds{' '}
        <input
          type="number"
          value={decisecondsText}
          step={1}
          min={-9}
          max={9}
          id="deciseconds_adjust"
          name="deciseconds_adjust"
          onChange={(event) => {
            setDecisecondsText(event.target.value)
            update({ decisecondsAdjust: parseAdjust(event.target.value) })
          }}
          onBlur={() => setDecisecondsText(String(state.decisecondsAdjust))}
        />{' '}
        deciseconds
      </div>
      <div>
        Load competition
        <ul id="competition_list">
          {state.competitions == null ? (
            <li>No previous competition available</li>
          ) : (
            state.competitions.map((comp) => (
              <li key={comp.comp_id}>
                {comp.name} (last save: {comp.save_date}){' '}
                <Button
                  id={`load_${comp.comp_id}`}
                  className="load_comp_button"
                  variant="outline"
                  type="button"
                  onClick={() => loadCompetition(comp.comp_id)}
                >
                  Load
                </Button>
                {comp.comp_id !== 1 && (
                  <Button
                    id={`delete_${comp.comp_id}`}
                    className="delete_comp_button"
                    variant="destructive"
                    type="button"
                    onClick={() => deleteCompetition(comp.comp_id)}
                  >
                    Delete
                  </Button>
                )}
              </li>
            ))
          )}
        </ul>
      </div>
      <div>
        <Button id="refresh_nrs" type="button" disabled={nrsBusy} onClick={refreshNrs}>
          Refresh national records
        </Button>
      </div>
    </>
  )
}
