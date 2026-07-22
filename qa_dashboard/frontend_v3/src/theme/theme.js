const THEME_STORAGE_KEY =
  'qa-dashboard-theme'

const DEFAULT_THEME_PREFERENCE =
  'system'

const validThemePreferences =
  new Set([
    'system',
    'light',
    'dark',
  ])

export const themeOptions = [
  {
    value: 'system',
    label: 'System',
  },
  {
    value: 'light',
    label: 'Light',
  },
  {
    value: 'dark',
    label: 'Dark',
  },
]

function normalizeThemePreference(
  value,
) {
  return validThemePreferences.has(
    value,
  )
    ? value
    : DEFAULT_THEME_PREFERENCE
}

export function getStoredThemePreference() {
  if (typeof window === 'undefined') {
    return DEFAULT_THEME_PREFERENCE
  }

  try {
    return normalizeThemePreference(
      window.localStorage.getItem(
        THEME_STORAGE_KEY,
      ),
    )
  } catch {
    return DEFAULT_THEME_PREFERENCE
  }
}

export function resolveThemePreference(
  preference,
) {
  const normalizedPreference =
    normalizeThemePreference(
      preference,
    )

  if (
    normalizedPreference !==
    'system'
  ) {
    return normalizedPreference
  }

  if (
    typeof window === 'undefined' ||
    typeof window.matchMedia !==
      'function'
  ) {
    return 'light'
  }

  return window
    .matchMedia(
      '(prefers-color-scheme: dark)',
    )
    .matches
    ? 'dark'
    : 'light'
}

export function applyThemePreference(
  preference,
) {
  const normalizedPreference =
    normalizeThemePreference(
      preference,
    )

  const resolvedTheme =
    resolveThemePreference(
      normalizedPreference,
    )

  if (typeof document !== 'undefined') {
    const root =
      document.documentElement

    root.dataset.theme =
      resolvedTheme

    root.dataset.themePreference =
      normalizedPreference

    root.style.colorScheme =
      resolvedTheme
  }

  return resolvedTheme
}

export function persistThemePreference(
  preference,
) {
  const normalizedPreference =
    normalizeThemePreference(
      preference,
    )

  if (typeof window !== 'undefined') {
    try {
      window.localStorage.setItem(
        THEME_STORAGE_KEY,
        normalizedPreference,
      )
    } catch {
      // The selected theme still applies
      // when browser storage is unavailable.
    }
  }

  applyThemePreference(
    normalizedPreference,
  )

  return normalizedPreference
}
