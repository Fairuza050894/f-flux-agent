import {
  getReportFileBaseName,
  saveReportBlob,
} from '../features/reports/reportExporters'

async function getErrorMessage(
  response,
  fallback,
) {
  try {
    const payload =
      await response.json()

    return (
      payload?.detail ??
      payload?.message ??
      fallback
    )
  } catch {
    return fallback
  }
}

async function requestJson(
  url,
  options = {},
) {
  const response =
    await fetch(
      url,
      {
        ...options,
        headers: {
          'Content-Type':
            'application/json',
          ...(options.headers ?? {}),
        },
      },
    )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        `Request failed with status ${response.status}.`,
      ),
    )
  }

  return response.json()
}

function parseDownloadFileName(
  response,
  fallback,
) {
  const disposition =
    response.headers.get(
      'content-disposition',
    ) ?? ''

  const match =
    disposition.match(
      /filename="?([^";]+)"?/i,
    )

  return match?.[1] || fallback
}

export async function downloadReportPdf(
  report,
) {
  const response =
    await fetch(
      '/api/v1/reports/pdf',
      {
        method: 'POST',
        headers: {
          'Content-Type':
            'application/json',
        },
        body:
          JSON.stringify({
            report,
          }),
      },
    )

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(
        response,
        'PDF export failed.',
      ),
    )
  }

  const blob =
    await response.blob()

  saveReportBlob(
    blob,
    parseDownloadFileName(
      response,
      `${getReportFileBaseName(
        report,
      )}.pdf`,
    ),
  )
}

export function getReportDeliveryConfiguration() {
  return requestJson(
    '/api/v1/reports/configuration',
  )
}

export function listReportDeliveries({
  cycleId = '',
  limit = 50,
} = {}) {
  const searchParams =
    new URLSearchParams()

  if (cycleId) {
    searchParams.set(
      'cycle_id',
      cycleId,
    )
  }

  searchParams.set(
    'limit',
    String(limit),
  )

  return requestJson(
    `/api/v1/reports/deliveries?${searchParams.toString()}`,
  )
}

export function createReportDelivery({
  destination,
  formats,
  report,
}) {
  return requestJson(
    '/api/v1/reports/deliveries',
    {
      method: 'POST',
      body:
        JSON.stringify({
          destination,
          formats,
          report,
        }),
    },
  )
}

export function retryReportDelivery(
  deliveryId,
) {
  return requestJson(
    `/api/v1/reports/deliveries/${encodeURIComponent(
      deliveryId,
    )}/retry`,
    {
      method: 'POST',
      body: '{}',
    },
  )
}
