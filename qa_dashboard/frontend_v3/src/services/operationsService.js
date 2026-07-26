import {
  apiFetch,
  readApiError,
} from './apiClient'

async function readJson(
  path,
  options = {},
  fallbackMessage =
    'Operational data could not be loaded.',
) {
  const response = await apiFetch(
    path,
    options,
  )

  if (!response.ok) {
    throw await readApiError(
      response,
      fallbackMessage,
    )
  }

  return response.json()
}

export function getOperationsStatus() {
  return readJson(
    '/api/v1/operations/status',
  )
}

export function getOperationalIncidents() {
  return readJson(
    '/api/v1/operations/incidents',
  )
}

export function getAuditEvents(
  {
    limit = 100,
    category = '',
    action = '',
    result = '',
    actor = '',
    requestId = '',
  } = {},
) {
  const params = new URLSearchParams({
    limit: String(limit),
    include_authentication: 'true',
  })

  if (category) {
    params.set('category', category)
  }

  if (action) {
    params.set('action', action)
  }

  if (result) {
    params.set('result', result)
  }

  if (actor) {
    params.set('actor', actor)
  }

  if (requestId) {
    params.set(
      'request_id',
      requestId,
    )
  }

  return readJson(
    `/api/v1/operations/audit-events?${params.toString()}`,
  )
}

export function recoverStaleExecutions(
  {
    dryRun = true,
    reason = '',
  } = {},
) {
  return readJson(
    '/api/v1/operations/recovery/stale-executions',
    {
      method: 'POST',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        dry_run: dryRun,
        reason,
      }),
    },
    'Stale execution recovery could not be completed.',
  )
}
