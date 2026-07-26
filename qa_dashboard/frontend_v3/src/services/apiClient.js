const DEFAULT_TIMEOUT_MS =
  30000

function buildRequestId() {
  if (
    typeof crypto !== 'undefined' &&
    typeof crypto.randomUUID ===
      'function'
  ) {
    return `req-${crypto.randomUUID()}`
  }

  return (
    `req-${Date.now()}-` +
    Math.random()
      .toString(16)
      .slice(2)
  )
}

function buildIdempotencyKey() {
  if (
    typeof crypto !== 'undefined' &&
    typeof crypto.randomUUID ===
      'function'
  ) {
    return crypto.randomUUID()
  }

  return (
    `${Date.now()}-` +
    Math.random()
      .toString(16)
      .slice(2)
  )
}

function isUnsafeMethod(method) {
  return ![
    'GET',
    'HEAD',
    'OPTIONS',
  ].includes(
    String(
      method ?? 'GET',
    ).toUpperCase(),
  )
}

async function readJsonSafely(
  response,
) {
  try {
    return await response
      .clone()
      .json()
  } catch {
    return {}
  }
}

function resolveLoginUrl(
  loginUrl,
) {
  const value =
    String(
      loginUrl ?? '/login',
    ).trim() || '/login'

  if (
    value.startsWith('http://') ||
    value.startsWith('https://')
  ) {
    return value
  }

  return value.startsWith('/')
    ? value
    : `/${value}`
}

function redirectForAuthentication(
  payload,
) {
  const loginUrl =
    payload?.login_url ??
    payload?.error?.login_url ??
    '/login'

  window.location.assign(
    resolveLoginUrl(
      loginUrl,
    ),
  )
}

export async function apiFetch(
  input,
  options = {},
) {
  const controller =
    new AbortController()

  const timeoutMs =
    Number(
      options.timeoutMs ??
      DEFAULT_TIMEOUT_MS,
    )

  const timeoutId =
    window.setTimeout(
      () => controller.abort(),
      Number.isFinite(timeoutMs)
        ? Math.max(
            1000,
            timeoutMs,
          )
        : DEFAULT_TIMEOUT_MS,
    )

  const method =
    String(
      options.method ?? 'GET',
    ).toUpperCase()

  const headers =
    new Headers(
      options.headers ?? {},
    )

  if (
    !headers.has('X-Request-ID')
  ) {
    headers.set(
      'X-Request-ID',
      buildRequestId(),
    )
  }

  if (
    isUnsafeMethod(method) &&
    !headers.has(
      'X-Idempotency-Key',
    )
  ) {
    headers.set(
      'X-Idempotency-Key',
      buildIdempotencyKey(),
    )
  }

  try {
    const response =
      await fetch(
        input,
        {
          ...options,
          credentials:
            options.credentials ??
            'include',
          headers,
          method,
          signal:
            options.signal ??
            controller.signal,
        },
      )

    if (response.status === 401) {
      const payload =
        await readJsonSafely(
          response,
        )

      redirectForAuthentication(
        payload,
      )
    }

    return response
  } finally {
    window.clearTimeout(
      timeoutId,
    )
  }
}

export async function readApiError(
  response,
  fallback,
) {
  const payload =
    await readJsonSafely(
      response,
    )

  return {
    message:
      payload?.error?.message ??
      payload?.detail?.message ??
      payload?.detail ??
      payload?.message ??
      fallback,
    payload,
    requestId:
      payload?.error?.request_id ??
      response.headers.get(
        'x-request-id',
      ),
  }
}
