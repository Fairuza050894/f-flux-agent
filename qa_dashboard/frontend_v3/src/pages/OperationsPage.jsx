import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  getAuditEvents,
  getOperationalIncidents,
  getOperationsStatus,
  recoverStaleExecutions,
} from '../services/operationsService'
import '../styles/operations.css'

const REFRESH_INTERVAL_MS = 15000
const AUDIT_PAGE_SIZE = 5

function formatDate(value) {
  if (!value) {
    return '-'
  }

  const parsed = new Date(value)

  if (
    Number.isNaN(
      parsed.getTime(),
    )
  ) {
    return String(value)
  }

  return parsed.toLocaleString()
}

function compactIdentifier(value) {
  const normalized =
    String(value ?? '').trim()

  if (!normalized) {
    return '-'
  }

  if (normalized.length <= 22) {
    return normalized
  }

  return (
    `${normalized.slice(0, 12)}…`
    + normalized.slice(-6)
  )
}

function readableError(error) {
  if (
    typeof error?.message === 'string'
  ) {
    return error.message
  }

  if (
    typeof error?.payload?.error
      ?.message === 'string'
  ) {
    return error.payload.error.message
  }

  return (
    'Operational information could not be loaded.'
  )
}

function StatusPill({
  value,
}) {
  const normalized = String(
    value ?? 'unknown',
  )
    .toLowerCase()
    .replaceAll('_', '-')

  return (
    <span
      className={
        `operations-status operations-status--${normalized}`
      }
    >
      {String(
        value ?? 'Unknown',
      ).replaceAll('_', ' ')}
    </span>
  )
}

function SummaryCard({
  label,
  value,
  detail,
}) {
  return (
    <article className="operations-summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </article>
  )
}

function OperationsPage() {
  const [status, setStatus] =
    useState(null)
  const [audit, setAudit] =
    useState({
      items: [],
      count: 0,
    })
  const [auditPage, setAuditPage] =
    useState(1)
  const [incidents, setIncidents] =
    useState({
      items: [],
      count: 0,
    })
  const [loading, setLoading] =
    useState(true)
  const [refreshing, setRefreshing] =
    useState(false)
  const [error, setError] =
    useState('')
  const [
    recoveryMessage,
    setRecoveryMessage,
  ] = useState('')
  const [
    recoveryBusy,
    setRecoveryBusy,
  ] = useState(false)

  const loadOperations =
    useCallback(
      async ({
        background = false,
      } = {}) => {
        if (background) {
          setRefreshing(true)
        } else {
          setLoading(true)
        }

        try {
          const [
            nextStatus,
            nextAudit,
            nextIncidents,
          ] = await Promise.all([
            getOperationsStatus(),
            getAuditEvents({
              limit: 100,
            }),
            getOperationalIncidents(),
          ])

          setStatus(nextStatus)
          setAudit(nextAudit)
          setIncidents(nextIncidents)
          setError('')
        } catch (loadError) {
          setError(
            readableError(loadError),
          )
        } finally {
          setLoading(false)
          setRefreshing(false)
        }
      },
      [],
    )

  useEffect(() => {
    const initialLoadId =
      window.setTimeout(
        () => {
          void loadOperations()
        },
        0,
      )

    const intervalId =
      window.setInterval(
        () => {
          void loadOperations({
            background: true,
          })
        },
        REFRESH_INTERVAL_MS,
      )

    return () => {
      window.clearTimeout(
        initialLoadId,
      )
      window.clearInterval(
        intervalId,
      )
    }
  }, [loadOperations])

  const components = useMemo(
    () =>
      status?.readiness
        ?.components ?? [],
    [status],
  )

  const auditItems = useMemo(
    () => audit?.items ?? [],
    [audit],
  )

  const auditTotalPages =
    Math.max(
      1,
      Math.ceil(
        auditItems.length
        / AUDIT_PAGE_SIZE,
      ),
    )

  const currentAuditPage =
    Math.min(
      auditPage,
      auditTotalPages,
    )

  const paginatedAuditItems =
    useMemo(
      () => {
        const start =
          (
            currentAuditPage - 1
          ) * AUDIT_PAGE_SIZE

        return auditItems.slice(
          start,
          start + AUDIT_PAGE_SIZE,
        )
      },
      [
        auditItems,
        currentAuditPage,
      ],
    )

  const auditRangeStart =
    auditItems.length
      ? (
          (
            currentAuditPage - 1
          ) * AUDIT_PAGE_SIZE
        ) + 1
      : 0

  const auditRangeEnd =
    Math.min(
      currentAuditPage
        * AUDIT_PAGE_SIZE,
      auditItems.length,
    )

  async function runRecovery(
    dryRun,
  ) {
    setRecoveryBusy(true)
    setRecoveryMessage('')

    try {
      const result =
        await recoverStaleExecutions({
          dryRun,
          reason:
            'P8-C stale execution recovery from Operations.',
        })

      setRecoveryMessage(
        dryRun
          ? (
              `${result.candidate_count} stale execution candidate(s) found.`
            )
          : (
              `${result.recovered_count} stale execution(s) recovered.`
            ),
      )

      await loadOperations({
        background: true,
      })
    } catch (recoveryError) {
      setRecoveryMessage(
        readableError(
          recoveryError,
        ),
      )
    } finally {
      setRecoveryBusy(false)
    }
  }

  if (loading && !status) {
    return (
      <section className="operations-page">
        <p>Loading operational status…</p>
      </section>
    )
  }

  return (
    <section className="operations-page">
      <header className="operations-header">
        <div>
          <p className="operations-eyebrow">
            MVP1 · P8-C
          </p>
          <h1>
            Reliability, Audit &amp;
            Observability
          </h1>
          <p>
            Monitor runtime readiness,
            stalled executions, report
            delivery, incidents, and
            security-aware audit activity.
          </p>
        </div>

        <div className="operations-header-actions">
          <StatusPill
            value={
              status?.status ??
              'unknown'
            }
          />
          <button
            type="button"
            onClick={() =>
              loadOperations({
                background: true,
              })
            }
            disabled={refreshing}
          >
            {refreshing
              ? 'Refreshing…'
              : 'Refresh'}
          </button>
        </div>
      </header>

      {error ? (
        <div
          className="operations-alert operations-alert--error"
          role="alert"
        >
          {error}
        </div>
      ) : null}

      <div className="operations-summary-grid">
        <SummaryCard
          label="Active executions"
          value={
            status?.summary
              ?.active_executions ?? 0
          }
          detail="Currently non-terminal"
        />
        <SummaryCard
          label="Stale executions"
          value={
            status?.summary
              ?.stale_executions ?? 0
          }
          detail="Exceeded update threshold"
        />
        <SummaryCard
          label="Failed deliveries"
          value={
            status?.summary
              ?.failed_deliveries ?? 0
          }
          detail="Persisted Telegram failures"
        />
        <SummaryCard
          label="Open incidents"
          value={
            incidents?.count ?? 0
          }
          detail="Operational attention"
        />
        <SummaryCard
          label="Audit events"
          value={
            status?.summary
              ?.audit_events ?? 0
          }
          detail="Persisted dashboard events"
        />
      </div>

      <div className="operations-grid">
        <article className="operations-panel">
          <div className="operations-panel-header">
            <div>
              <h2>Component readiness</h2>
              <p>
                Required components must
                be ready before production
                traffic is accepted.
              </p>
            </div>
            <StatusPill
              value={
                status?.readiness
                  ?.status ?? 'unknown'
              }
            />
          </div>

          <div className="operations-component-list">
            {components.map(
              (component) => (
                <div
                  className="operations-component-row"
                  key={component.name}
                >
                  <div>
                    <strong>
                      {component.name}
                    </strong>
                    <small>
                      {component.required
                        ? 'Required'
                        : 'Optional'}
                    </small>
                  </div>
                  <StatusPill
                    value={
                      component.status
                    }
                  />
                </div>
              ),
            )}
          </div>
        </article>

        <article className="operations-panel">
          <div className="operations-panel-header">
            <div>
              <h2>Stale recovery</h2>
              <p>
                Preview first. Applying
                recovery closes stale runs
                as failed while preserving
                evidence and metadata.
              </p>
            </div>
          </div>

          <div className="operations-recovery-actions">
            <button
              type="button"
              disabled={recoveryBusy}
              onClick={() =>
                runRecovery(true)
              }
            >
              Preview recovery
            </button>
            <button
              type="button"
              className="operations-danger-button"
              disabled={
                recoveryBusy ||
                !status?.summary
                  ?.stale_executions
              }
              onClick={() =>
                runRecovery(false)
              }
            >
              Apply recovery
            </button>
          </div>

          {recoveryMessage ? (
            <p className="operations-recovery-message">
              {recoveryMessage}
            </p>
          ) : null}
        </article>
      </div>

      <article className="operations-panel">
        <div className="operations-panel-header">
          <div>
            <h2>Operational incidents</h2>
            <p>
              Derived from readiness,
              execution, delivery, and
              audit state.
            </p>
          </div>
          <span>
            {incidents?.count ?? 0}
          </span>
        </div>

        {incidents?.items?.length ? (
          <div className="operations-incident-list">
            {incidents.items.map(
              (incident) => (
                <div
                  className="operations-incident"
                  key={incident.id}
                >
                  <div>
                    <StatusPill
                      value={
                        incident.severity
                      }
                    />
                    <strong>
                      {incident.title}
                    </strong>
                  </div>
                  <p>{incident.detail}</p>
                  <small>
                    {
                      incident
                        .recommended_action
                    }
                  </small>
                </div>
              ),
            )}
          </div>
        ) : (
          <p className="operations-empty">
            No operational incident is
            currently detected.
          </p>
        )}
      </article>

      <article className="operations-panel">
        <div className="operations-panel-header">
          <div>
            <h2>Recent audit activity</h2>
            <p>
              Latest dashboard and
              authentication activity.
            </p>
          </div>
          <span>{audit?.count ?? 0}</span>
        </div>

        <div className="operations-table-wrap">
          <table
            className={
              'operations-table '
              + 'operations-audit-table'
            }
          >
            <thead>
              <tr>
                <th>Time</th>
                <th>Activity</th>
                <th>Status</th>
                <th>Target</th>
              </tr>
            </thead>
            <tbody>
              {paginatedAuditItems.length ? (
                paginatedAuditItems.map(
                  (event) => (
                    <tr key={event.id}>
                      <td className="operations-audit-time">
                        <time
                          dateTime={
                            event.timestamp
                            || undefined
                          }
                        >
                          {formatDate(
                            event.timestamp,
                          )}
                        </time>
                      </td>
                      <td className="operations-audit-activity">
                        <strong>
                          {event.action}
                        </strong>
                        <small>
                          {[
                            event.actor
                              || 'System',
                            event.actor_role,
                            event.category,
                          ]
                            .filter(Boolean)
                            .join(' · ')}
                        </small>
                      </td>
                      <td>
                        <StatusPill
                          value={
                            event.result
                          }
                        />
                      </td>
                      <td className="operations-audit-target">
                        <span
                          title={
                            event.resource
                            || ''
                          }
                        >
                          {event.resource
                            || '-'}
                        </span>
                        <code
                          title={
                            event.request_id
                            || ''
                          }
                        >
                          {compactIdentifier(
                            event.request_id,
                          )}
                        </code>
                      </td>
                    </tr>
                  ),
                )
              ) : (
                <tr>
                  <td colSpan="4">
                    No audit event is
                    available yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {auditItems.length ? (
          <div className="operations-pagination">
            <span className="operations-pagination-summary">
              Showing {auditRangeStart}
              –{auditRangeEnd} of{' '}
              {auditItems.length}
            </span>

            <div className="operations-pagination-controls">
              <button
                type="button"
                disabled={
                  currentAuditPage <= 1
                }
                onClick={() =>
                  setAuditPage(
                    Math.max(
                      1,
                      currentAuditPage - 1,
                    ),
                  )
                }
              >
                Previous
              </button>

              <span>
                Page {currentAuditPage}
                {' '}of {auditTotalPages}
              </span>

              <button
                type="button"
                disabled={
                  currentAuditPage
                  >= auditTotalPages
                }
                onClick={() =>
                  setAuditPage(
                    Math.min(
                      auditTotalPages,
                      currentAuditPage + 1,
                    ),
                  )
                }
              >
                Next
              </button>
            </div>
          </div>
        ) : null}
      </article>

      <footer className="operations-footer">
        Last generated:{' '}
        {formatDate(
          status?.generated_at,
        )}
        {' · '}
        Automatic refresh every 15 seconds.
      </footer>
    </section>
  )
}

export default OperationsPage
