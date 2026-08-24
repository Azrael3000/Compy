/*
 * Fetch wrapper for the Compy Flask API.
 *
 * Every endpoint answers with the uniform envelope
 *   {"status": "success", "status_msg"?: ..., ...payload}
 *   {"status": "error", "error_msg": ...}
 * (see handleRequest()/badRequest() in compy_flask.py). HTTP 401 means the
 * admin session expired — the backend expects the frontend to react, so we
 * redirect to the login page.
 */

export class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface Envelope {
  status: 'success' | 'error'
  status_msg?: string
  error_msg?: string
}

/* query parameters: anything with a sensible string form */
export type QueryValue = string | number | boolean | null | undefined

function buildQuery(params?: object): string {
  if (!params) {
    return ''
  }
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params) as [string, QueryValue][]) {
    if (value !== undefined && value !== null) {
      search.set(key, String(value))
    }
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

/* HTTP 401 means the admin session lapsed. Every request — json or binary —
 * has to go through this, otherwise a download silently does nothing once
 * the 12 h session expires instead of sending the user back to the login. */
function checkAuth(response: Response): void {
  if (response.status === 401) {
    window.location.href = '/admin/login'
    throw new ApiError('Authentication required')
  }
}

async function handleResponse<T extends Envelope>(response: Response): Promise<T> {
  checkAuth(response)
  let data: T | null = null
  try {
    data = (await response.json()) as T
  } catch {
    data = null
  }
  /* the error message can live in error_msg (badRequest) or, for some
   * endpoints, in status_msg of an HTTP 200 "error" envelope */
  if (data !== null && data.status === 'error') {
    throw new ApiError(data.error_msg ?? data.status_msg ?? 'Unknown error')
  }
  /* many endpoints answer plain "{}, 400"; never treat those as success */
  if (!response.ok || data === null) {
    throw new ApiError(data?.status_msg ?? `Request failed (HTTP ${response.status})`)
  }
  return data
}

async function requestJson<T extends Envelope>(
  method: string,
  path: string,
  body?: object,
): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    credentials: 'same-origin',
  })
  return handleResponse<T>(response)
}

export const api = {
  get<T extends Envelope>(path: string, params?: object): Promise<T> {
    return requestJson<T>('GET', path + buildQuery(params))
  },
  postJson<T extends Envelope>(path: string, body: object): Promise<T> {
    return requestJson<T>('POST', path, body)
  },
  putJson<T extends Envelope>(path: string, body: object): Promise<T> {
    return requestJson<T>('PUT', path, body)
  },
  patchJson<T extends Envelope>(path: string, body: object): Promise<T> {
    return requestJson<T>('PATCH', path, body)
  },
  deleteJson<T extends Envelope>(path: string, body: object): Promise<T> {
    return requestJson<T>('DELETE', path, body)
  },
  /* FormData uploads — the browser sets the multipart Content-Type itself. */
  async postForm<T extends Envelope>(path: string, form: FormData): Promise<T> {
    const response = await fetch(path, {
      method: 'POST',
      body: form,
      credentials: 'same-origin',
    })
    return handleResponse<T>(response)
  },
  /* File downloads (the *_pdf endpoints). */
  async getBlob(path: string, params?: object): Promise<Blob> {
    const response = await fetch(path + buildQuery(params), { credentials: 'same-origin' })
    return handleBlobResponse(response)
  },
  /* Upload that answers with a file (/store_results). */
  async postFormBlob(path: string, form: FormData): Promise<Blob> {
    const response = await fetch(path, {
      method: 'POST',
      body: form,
      credentials: 'same-origin',
    })
    return handleBlobResponse(response)
  },
}

/*
 * A file endpoint answers either with the file or with the ordinary json
 * envelope. /store_results even reports "no file uploaded" / "not a *.xlsx"
 * as an HTTP 200 envelope, so the content type — not the status — decides
 * whether this is a download; otherwise those messages get saved as a
 * .xlsx full of json.
 */
async function handleBlobResponse(response: Response): Promise<Blob> {
  checkAuth(response)
  if ((response.headers.get('Content-Type') ?? '').includes('application/json')) {
    let data: Envelope | null = null
    try {
      data = (await response.json()) as Envelope
    } catch {
      data = null
    }
    throw new ApiError(
      data?.error_msg ?? data?.status_msg ?? `Request failed (HTTP ${response.status})`,
    )
  }
  if (!response.ok) {
    throw new ApiError(`Request failed (HTTP ${response.status})`)
  }
  return response.blob()
}
