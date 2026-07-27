import { useMemo, useState } from 'react'

import {
  useDashboardAuth,
} from '../features/auth/dashboardAuthContext'
import {
  useProjectEnvironmentStore,
} from '../stores/projectEnvironmentStore'
import { themeOptions } from '../theme/theme'


function formatLabel(value) {
  return String(value || 'Not available')
    .trim()
    .replaceAll('_', ' ')
    .replaceAll('-', ' ')
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    )
}


function formatProvider(value) {
  const normalized = String(
    value || '',
  ).trim().toLowerCase()

  if (normalized === 'basic') {
    return 'Basic authentication'
  }

  return normalized
    ? formatLabel(normalized)
    : 'Dashboard session'
}


function defaultInitials(value) {
  const words = String(
    value || 'User',
  )
    .trim()
    .split(/\s+/)
    .filter(Boolean)

  if (!words.length) {
    return 'U'
  }

  if (words.length === 1) {
    return words[0]
      .slice(0, 2)
      .toUpperCase()
  }

  return (
    words[0][0]
    + words[words.length - 1][0]
  ).toUpperCase()
}


function SettingsNotice({
  children,
  tone = 'info',
}) {
  return (
    <div
      className={
        'account-center-notice '
        + `account-center-notice-${tone}`
      }
      role={
        tone === 'error'
          ? 'alert'
          : 'status'
      }
    >
      {children}
    </div>
  )
}


function AccountSettingsForm({
  account,
  accountError,
  actor,
  onRefresh,
  onUpdate,
}) {
  const identity =
    account?.identity ?? actor ?? {}
  const savedProfile =
    account?.profile ?? {}
  const savedPreferences =
    account?.preferences ?? {}

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )
  const environments =
    useProjectEnvironmentStore(
      (state) => state.environments,
    )

  const fallbackName = (
    identity.display_name
    || identity.email
    || identity.user_id
    || 'Dashboard user'
  )

  const [displayName, setDisplayName] =
    useState(
      savedProfile.display_name
      || fallbackName,
    )
  const [jobTitle, setJobTitle] =
    useState(
      savedProfile.job_title || '',
    )
  const [avatarInitials, setAvatarInitials] =
    useState(
      savedProfile.avatar_initials
      || defaultInitials(fallbackName),
    )
  const [theme, setTheme] = useState(
    savedPreferences.theme || 'system',
  )
  const [defaultProjectId, setDefaultProjectId] =
    useState(
      savedPreferences.default_project_id
      || '',
    )
  const [defaultEnvironmentId, setDefaultEnvironmentId] =
    useState(
      savedPreferences.default_environment_id
      || '',
    )
  const [savingSection, setSavingSection] =
    useState('')
  const [saveError, setSaveError] =
    useState('')
  const [saveMessage, setSaveMessage] =
    useState('')

  const availableEnvironments = useMemo(
    () => environments.filter(
      (environment) => (
        !defaultProjectId
        || environment.projectId
          === defaultProjectId
      ),
    ),
    [defaultProjectId, environments],
  )

  const profile = {
    display_name: displayName.trim(),
    job_title: jobTitle.trim(),
    avatar_initials:
      avatarInitials.trim(),
  }

  const preferences = {
    theme,
    default_project_id:
      defaultProjectId,
    default_environment_id:
      defaultEnvironmentId,
  }

  async function saveSection(section) {
    setSavingSection(section)
    setSaveError('')
    setSaveMessage('')

    try {
      await onUpdate({
        profile,
        preferences,
        expectedRevision:
          account?.revision ?? 0,
      })

      setSaveMessage(
        section === 'profile'
          ? 'Profile changes saved.'
          : 'Preference changes saved.',
      )
    } catch (error) {
      setSaveError(
        error?.message
        || 'Account changes could not be saved.',
      )
    } finally {
      setSavingSection('')
    }
  }

  function handleProjectChange(event) {
    const nextProjectId =
      event.target.value
    setDefaultProjectId(nextProjectId)

    const currentEnvironmentValid =
      environments.some(
        (environment) => (
          environment.id
            === defaultEnvironmentId
          && (
            !nextProjectId
            || environment.projectId
              === nextProjectId
          )
        ),
      )

    if (!currentEnvironmentValid) {
      setDefaultEnvironmentId('')
    }
  }

  return (
    <div className="account-center-page">
      <header className="account-center-hero">
        <div>
          <p className="account-center-eyebrow">
            Account Center
          </p>
          <h1>Profile and preferences</h1>
          <p>
            Manage your QA Dashboard identity,
            workspace defaults, and access details.
          </p>
        </div>

        <div
          aria-label="Current account"
          className="account-center-identity-card"
        >
          <span
            aria-hidden="true"
            className="account-center-avatar"
          >
            {(
              avatarInitials
              || defaultInitials(displayName)
            ).slice(0, 3).toUpperCase()}
          </span>
          <div>
            <strong>
              {displayName || fallbackName}
            </strong>
            <span>
              {jobTitle
                || formatLabel(
                  identity.role,
                )}
            </span>
          </div>
        </div>
      </header>

      {accountError ? (
        <SettingsNotice tone="error">
          <span>{accountError}</span>
          <button
            className="button button-secondary"
            onClick={onRefresh}
            type="button"
          >
            Retry
          </button>
        </SettingsNotice>
      ) : null}

      {saveError ? (
        <SettingsNotice tone="error">
          {saveError}
        </SettingsNotice>
      ) : null}

      {saveMessage ? (
        <SettingsNotice tone="success">
          {saveMessage}
        </SettingsNotice>
      ) : null}

      <div className="account-center-layout">
        <div className="account-center-main-column">
          <section className="account-center-card">
            <header className="account-center-card-header">
              <div>
                <h2>Profile</h2>
                <p>
                  Application-specific details shown
                  throughout the QA Dashboard.
                </p>
              </div>
              <span className="account-center-chip">
                Editable
              </span>
            </header>

            <div className="account-center-form-grid">
              <label className="account-center-field">
                <span>Display name</span>
                <input
                  maxLength="80"
                  onChange={(event) =>
                    setDisplayName(
                      event.target.value,
                    )
                  }
                  required
                  type="text"
                  value={displayName}
                />
                <small>
                  Used in the account menu and
                  activity context.
                </small>
              </label>

              <label className="account-center-field">
                <span>Job title</span>
                <input
                  maxLength="80"
                  onChange={(event) =>
                    setJobTitle(
                      event.target.value,
                    )
                  }
                  placeholder="Example: QA Lead"
                  type="text"
                  value={jobTitle}
                />
                <small>
                  Optional operational title.
                </small>
              </label>

              <label className="account-center-field account-center-field-compact">
                <span>Avatar initials</span>
                <input
                  maxLength="3"
                  onChange={(event) =>
                    setAvatarInitials(
                      event.target.value
                        .replace(
                          /[^A-Za-z0-9]/g,
                          '',
                        )
                        .toUpperCase(),
                    )
                  }
                  type="text"
                  value={avatarInitials}
                />
                <small>
                  Up to three letters or numbers.
                </small>
              </label>
            </div>

            <footer className="account-center-card-footer">
              <button
                className="button button-primary"
                disabled={
                  savingSection !== ''
                  || !displayName.trim()
                }
                onClick={() =>
                  void saveSection('profile')
                }
                type="button"
              >
                {savingSection === 'profile'
                  ? 'Saving profile…'
                  : 'Save profile'}
              </button>
            </footer>
          </section>

          <section className="account-center-card">
            <header className="account-center-card-header">
              <div>
                <h2>Preferences</h2>
                <p>
                  Set the dashboard appearance and
                  the workspace opened by default.
                </p>
              </div>
              <span className="account-center-chip">
                Synced
              </span>
            </header>

            <div className="account-center-form-grid">
              <label className="account-center-field">
                <span>Theme</span>
                <select
                  onChange={(event) =>
                    setTheme(event.target.value)
                  }
                  value={theme}
                >
                  {themeOptions.map(
                    (option) => (
                      <option
                        key={option.value}
                        value={option.value}
                      >
                        {option.label}
                      </option>
                    ),
                  )}
                </select>
                <small>
                  Applied after saving and restored
                  on your next session.
                </small>
              </label>

              <label className="account-center-field">
                <span>Default project</span>
                <select
                  onChange={handleProjectChange}
                  value={defaultProjectId}
                >
                  <option value="">
                    Use last selected project
                  </option>
                  {projects.map((project) => (
                    <option
                      key={project.id}
                      value={project.id}
                    >
                      {project.name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="account-center-field">
                <span>Default environment</span>
                <select
                  onChange={(event) =>
                    setDefaultEnvironmentId(
                      event.target.value,
                    )
                  }
                  value={defaultEnvironmentId}
                >
                  <option value="">
                    Use last selected environment
                  </option>
                  {availableEnvironments.map(
                    (environment) => (
                      <option
                        key={environment.id}
                        value={environment.id}
                      >
                        {environment.name}
                      </option>
                    ),
                  )}
                </select>
              </label>
            </div>

            <footer className="account-center-card-footer">
              <button
                className="button button-primary"
                disabled={savingSection !== ''}
                onClick={() =>
                  void saveSection('preferences')
                }
                type="button"
              >
                {savingSection === 'preferences'
                  ? 'Saving preferences…'
                  : 'Save preferences'}
              </button>
            </footer>
          </section>
        </div>

        <aside className="account-center-side-column">
          <section className="account-center-card account-center-security-card">
            <header className="account-center-card-header">
              <div>
                <h2>Access &amp; security</h2>
                <p>
                  Verified session information from
                  the authentication provider.
                </p>
              </div>
              <span className="account-center-chip account-center-chip-readonly">
                Read only
              </span>
            </header>

            <dl className="account-center-definition-list">
              <div>
                <dt>Email or username</dt>
                <dd>
                  {identity.email
                    || identity.user_id
                    || 'Not available'}
                </dd>
              </div>
              <div>
                <dt>Role</dt>
                <dd>
                  {formatLabel(identity.role)}
                </dd>
              </div>
              <div>
                <dt>Authentication provider</dt>
                <dd>
                  {formatProvider(
                    identity.provider,
                  )}
                </dd>
              </div>
              <div>
                <dt>Permissions</dt>
                <dd>
                  {Array.isArray(
                    identity.permissions,
                  )
                    ? identity.permissions.length
                    : 0}
                  {' '}granted
                </dd>
              </div>
              <div>
                <dt>Settings revision</dt>
                <dd>
                  {account?.revision ?? 0}
                </dd>
              </div>
            </dl>

            <div className="account-center-security-note">
              <strong>
                Credential management
              </strong>
              <p>
                Sign-in credentials are managed by
                the deployment authentication
                provider. For Basic authentication,
                update the protected environment
                configuration and restart the
                service. The dashboard does not
                expose or store passwords.
              </p>
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}


function AccountPage() {
  const auth = useDashboardAuth() ?? {}

  if (
    auth.accountError
    && !auth.account
  ) {
    return (
      <div className="account-center-page">
        <header className="account-center-hero">
          <div>
            <p className="account-center-eyebrow">
              Account Center
            </p>
            <h1>Profile and preferences</h1>
          </div>
        </header>

        <SettingsNotice tone="error">
          <span>{auth.accountError}</span>
          <button
            className="button button-secondary"
            onClick={auth.refreshAccount}
            type="button"
          >
            Retry
          </button>
        </SettingsNotice>
      </div>
    )
  }

  const identityKey = (
    auth.account?.identity?.user_id
    || auth.account?.identity?.email
    || auth.actor?.user_id
    || auth.actor?.email
    || 'account-user'
  )

  return (
    <AccountSettingsForm
      key={identityKey}
      account={auth.account}
      accountError={auth.accountError}
      actor={auth.actor}
      onRefresh={auth.refreshAccount}
      onUpdate={auth.updateAccount}
    />
  )
}


export default AccountPage
