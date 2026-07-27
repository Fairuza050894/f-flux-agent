import {
  apiFetch,
  readApiError,
} from './apiClient'


export async function fetchAccountSettings() {
  const response = await apiFetch(
    '/api/v1/account',
  )

  if (!response.ok) {
    const error = await readApiError(
      response,
      'Unable to load account settings.',
    )

    throw new Error(error.message)
  }

  return response.json()
}


export async function saveAccountSettings({
  profile,
  preferences,
  expectedRevision,
}) {
  const response = await apiFetch(
    '/api/v1/account',
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        profile,
        preferences,
        expected_revision:
          expectedRevision,
      }),
    },
  )

  if (!response.ok) {
    const error = await readApiError(
      response,
      'Unable to save account settings.',
    )

    const saveError = new Error(
      error.message,
    )
    saveError.code = error.code
    saveError.details = error.details
    throw saveError
  }

  return response.json()
}
