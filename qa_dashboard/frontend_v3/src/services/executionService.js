const EXECUTION_BASE_URL =
  '/api/v1/executions'

async function readResponse(response) {
  const contentType =
    response.headers.get('content-type') ?? ''

  if (
    contentType.includes(
      'application/json',
    )
  ) {
    return response.json()
  }

  const text = await response.text()

  return text
    ? { message: text }
    : {}
}

function getErrorMessage(payload, status) {
  if (typeof payload?.detail === 'string') {
    return payload.detail
  }

  if (payload?.detail?.message) {
    return payload.detail.message
  }

  if (Array.isArray(payload?.detail)) {
    return payload.detail
      .map((item) => {
        const location =
          item.loc?.join('.') ?? 'request'

        return `${location}: ${item.msg}`
      })
      .join(', ')
  }

  if (payload?.message) {
    return payload.message
  }

  return `Execution request failed with status ${status}.`
}

function normalizeExecution(payload) {
  const record =
    payload?.run ??
    payload?.execution ??
    payload

  const runId =
    record?.run_id ??
    record?.execution_id ??
    record?.id ??
    record?.runId ??
    null

  return {
    ...record,
    runId,
    status:
      record?.status ??
      'queued',
    progress: Number(
      record?.progress ?? 0,
    ),
  }
}

async function requestExecution(
  path,
  options = {},
) {
  const response = await fetch(
    `${EXECUTION_BASE_URL}${path}`,
    {
      ...options,
      headers: {
        'Content-Type':
          'application/json',
        ...options.headers,
      },
    },
  )

  const payload =
    await readResponse(response)

  if (!response.ok) {
    throw new Error(
      getErrorMessage(
        payload,
        response.status,
      ),
    )
  }

  return normalizeExecution(payload)
}

export function createExecution(payload) {
  return requestExecution('', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getExecution(runId) {
  return requestExecution(
    `/${encodeURIComponent(runId)}`,
  )
}

export async function listActiveExecutions(
  projectId = '',
) {
  const query = projectId
    ? `?project_id=${encodeURIComponent(
        projectId,
      )}`
    : ''

  const response = await fetch(
    `${EXECUTION_BASE_URL}/active${query}`,
  )

  const payload =
    await readResponse(response)

  if (!response.ok) {
    throw new Error(
      getErrorMessage(
        payload,
        response.status,
      ),
    )
  }

  const records =
    payload?.items ??
    payload?.runs ??
    payload?.executions ??
    payload ??
    []

  return Array.isArray(records)
    ? records.map(normalizeExecution)
    : []
}
