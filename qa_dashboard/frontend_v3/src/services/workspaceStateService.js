const WORKSPACE_STATE_URL =
  '/api/v1/workspace/state'

async function requestJson(
  url,
  {
    body,
    keepalive = false,
    method = 'GET',
    timeoutMs = 15000,
  } = {},
) {
  const controller =
    new AbortController()

  const timeoutId =
    window.setTimeout(
      () => controller.abort(),
      timeoutMs,
    )

  try {
    const response =
      await fetch(
        url,
        {
          body:
            body === undefined
              ? undefined
              : JSON.stringify(body),
          headers:
            body === undefined
              ? undefined
              : {
                  'Content-Type':
                    'application/json',
                },
          keepalive,
          method,
          signal:
            controller.signal,
        },
      )

    const payload =
      await response
        .json()
        .catch(() => ({}))

    if (!response.ok) {
      const error =
        new Error(
          payload?.detail?.message ||
          payload?.message ||
          `Workspace request failed (${response.status}).`,
        )

      error.status =
        response.status
      error.payload =
        payload
      throw error
    }

    return payload
  } finally {
    window.clearTimeout(
      timeoutId,
    )
  }
}

export function fetchWorkspaceState() {
  return requestJson(
    WORKSPACE_STATE_URL,
  )
}

export function saveWorkspaceState(
  {
    expectedRevision,
    source,
    state,
  },
  {
    keepalive = false,
  } = {},
) {
  return requestJson(
    WORKSPACE_STATE_URL,
    {
      body: {
        expected_revision:
          expectedRevision,
        schema_version: 1,
        source,
        state,
      },
      keepalive,
      method: 'PUT',
    },
  )
}
