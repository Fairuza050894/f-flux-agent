import {
  useMemo,
  useState,
} from 'react'

import StatusBadge from '../StatusBadge'
import {
  buildConsolidatedReport,
} from '../../features/reports/consolidatedReportModel'
import {
  downloadReportCsv,
  downloadReportJson,
} from '../../features/reports/reportExporters'
import {
  createReportDelivery,
  downloadReportPdf,
  getReportDeliveryConfiguration,
  listReportDeliveries,
  retryReportDelivery,
} from '../../services/reportDeliveryService'

const formatOptions = [
  {
    key: 'json',
    label: 'JSON',
    description:
      'Machine-readable integration payload.',
  },
  {
    key: 'csv',
    label: 'CSV',
    description:
      'Execution-level tabular result export.',
  },
  {
    key: 'pdf',
    label: 'PDF',
    description:
      'Formal release and traceability report.',
  },
]

function formatDateTime(
  value,
) {
  if (!value) {
    return 'Not available'
  }

  const date =
    new Date(value)

  return Number.isNaN(
    date.getTime(),
  )
    ? 'Not available'
    : date.toLocaleString()
}

function getDeliveryTone(
  status,
) {
  switch (
    String(status ?? '')
      .toLowerCase()
  ) {
    case 'sent':
      return 'success'
    case 'failed':
      return 'danger'
    case 'sending':
      return 'primary'
    default:
      return 'neutral'
  }
}

function getChecklistTone(
  status,
) {
  switch (status) {
    case 'pass':
      return 'success'
    case 'fail':
      return 'danger'
    default:
      return 'warning'
  }
}

function ReportDeliveryPanel({
  assets = [],
  cycles = [],
  environments = [],
  projects = [],
}) {
  const [
    selectedCycleId,
    setSelectedCycleId,
  ] = useState(
    () =>
      cycles[0]?.id ?? '',
  )

  const [
    destination,
    setDestination,
  ] = useState('both')

  const [
    selectedFormats,
    setSelectedFormats,
  ] = useState(
    () => ({
      json: true,
      csv: true,
      pdf: true,
    }),
  )

  const [
    isExportingPdf,
    setIsExportingPdf,
  ] = useState(false)

  const [
    isDelivering,
    setIsDelivering,
  ] = useState(false)

  const [
    isLoadingHistory,
    setIsLoadingHistory,
  ] = useState(false)

  const [
    retryingDeliveryId,
    setRetryingDeliveryId,
  ] = useState('')

  const [
    deliveries,
    setDeliveries,
  ] = useState([])

  const [
    historyLoaded,
    setHistoryLoaded,
  ] = useState(false)

  const [
    configuration,
    setConfiguration,
  ] = useState(null)

  const [
    message,
    setMessage,
  ] = useState(null)

  const selectedCycle =
    cycles.find(
      (cycle) =>
        cycle.id ===
        selectedCycleId,
    ) ??
    cycles[0] ??
    null

  const effectiveCycleId =
    selectedCycle?.id ?? ''

  const report =
    useMemo(
      () =>
        buildConsolidatedReport({
          assets,
          cycle:
            selectedCycle,
          environments,
          projects,
        }),
      [
        assets,
        environments,
        projects,
        selectedCycle,
      ],
    )

  const enabledFormats =
    formatOptions
      .filter(
        (option) =>
          selectedFormats[
            option.key
          ],
      )
      .map(
        (option) =>
          option.key,
      )

  function showMessage(
    tone,
    text,
  ) {
    setMessage({
      tone,
      text,
    })
  }

  function handleFormatToggle(
    format,
  ) {
    setSelectedFormats(
      (current) => ({
        ...current,
        [format]:
          !current[format],
      }),
    )
  }

  async function refreshHistory() {
    if (!effectiveCycleId) {
      return
    }

    setIsLoadingHistory(true)

    try {
      const [
        configurationPayload,
        deliveryPayload,
      ] = await Promise.all([
        getReportDeliveryConfiguration(),
        listReportDeliveries({
          cycleId:
            effectiveCycleId,
          limit: 50,
        }),
      ])

      setConfiguration(
        configurationPayload,
      )

      setDeliveries(
        Array.isArray(
          deliveryPayload?.items,
        )
          ? deliveryPayload.items
          : [],
      )

      setHistoryLoaded(true)
    } catch (error) {
      showMessage(
        'danger',
        error instanceof Error
          ? error.message
          : 'Delivery history could not be loaded.',
      )
    } finally {
      setIsLoadingHistory(false)
    }
  }

  async function handlePdfExport() {
    if (!report) {
      return
    }

    setIsExportingPdf(true)

    try {
      await downloadReportPdf(
        report,
      )

      showMessage(
        'success',
        'PDF report was generated.',
      )
    } catch (error) {
      showMessage(
        'danger',
        error instanceof Error
          ? error.message
          : 'PDF export failed.',
      )
    } finally {
      setIsExportingPdf(false)
    }
  }

  async function handleTelegramDelivery() {
    if (
      !report ||
      enabledFormats.length === 0
    ) {
      showMessage(
        'warning',
        'Select at least one delivery format.',
      )
      return
    }

    const shouldDeliver =
      window.confirm(
        `Send "${report.cycle.name}" to Telegram destination "${destination}"?`,
      )

    if (!shouldDeliver) {
      return
    }

    setIsDelivering(true)

    try {
      const delivery =
        await createReportDelivery({
          destination,
          formats:
            enabledFormats,
          report,
        })

      if (
        delivery.status ===
        'failed'
      ) {
        showMessage(
          'danger',
          delivery.error ||
            'Telegram delivery failed.',
        )
      } else {
        showMessage(
          'success',
          'Report delivered to Telegram.',
        )
      }

      await refreshHistory()
    } catch (error) {
      showMessage(
        'danger',
        error instanceof Error
          ? error.message
          : 'Telegram delivery failed.',
      )
    } finally {
      setIsDelivering(false)
    }
  }

  async function handleRetry(
    deliveryId,
  ) {
    const shouldRetry =
      window.confirm(
        'Retry this report delivery using the original report snapshot and destination?',
      )

    if (!shouldRetry) {
      return
    }

    setRetryingDeliveryId(
      deliveryId,
    )

    try {
      const delivery =
        await retryReportDelivery(
          deliveryId,
        )

      if (
        delivery.status ===
        'failed'
      ) {
        showMessage(
          'danger',
          delivery.error ||
            'Retry failed.',
        )
      } else {
        showMessage(
          'success',
          'Delivery retry completed.',
        )
      }

      await refreshHistory()
    } catch (error) {
      showMessage(
        'danger',
        error instanceof Error
          ? error.message
          : 'Delivery retry failed.',
      )
    } finally {
      setRetryingDeliveryId('')
    }
  }

  if (!selectedCycle || !report) {
    return (
      <section className="dashboard-panel report-panel report-delivery-empty">
        <strong>
          No Test Cycle available
        </strong>

        <p>
          Adjust the shared report filters or create a
          Test Cycle before generating a consolidated
          report.
        </p>
      </section>
    )
  }

  return (
    <div className="report-delivery-layout">
      <section className="dashboard-panel report-panel">
        <div className="panel-header report-panel-header">
          <div>
            <span className="panel-eyebrow">
              CONSOLIDATED REPORT
            </span>

            <h3>
              Export and Release Decision
            </h3>

            <p>
              Generate a version-aware report from one
              matching Test Cycle.
            </p>
          </div>

          <StatusBadge
            tone={
              report
                .releaseDecision
                .tone
            }
          >
            {
              report
                .releaseDecision
                .label
            }
          </StatusBadge>
        </div>

        <div className="report-delivery-cycle-selector">
          <label htmlFor="report-delivery-cycle">
            Test Cycle
          </label>

          <select
            id="report-delivery-cycle"
            onChange={(event) =>
              setSelectedCycleId(
                event.target.value,
              )
            }
            value={effectiveCycleId}
          >
            {cycles.map(
              (cycle) => (
                <option
                  key={cycle.id}
                  value={cycle.id}
                >
                  {cycle.name} · {cycle.id}
                </option>
              ),
            )}
          </select>
        </div>

        <div className="report-delivery-decision">
          <div>
            <span>
              Release Recommendation
            </span>

            <strong>
              {
                report
                  .releaseDecision
                  .label
              }
            </strong>

            <p>
              {
                report
                  .releaseDecision
                  .reason
              }
            </p>
          </div>

          <div className="report-delivery-metrics">
            <div>
              <span>Passed</span>
              <strong>
                {report.summary.passed}
              </strong>
            </div>

            <div>
              <span>Failed</span>
              <strong>
                {report.summary.failed}
              </strong>
            </div>

            <div>
              <span>Need Review</span>
              <strong>
                {report.summary.needReview}
              </strong>
            </div>

            <div>
              <span>Pass Rate</span>
              <strong>
                {
                  report
                    .summary
                    .passRateLabel
                }
              </strong>
            </div>
          </div>
        </div>

        <div className="report-release-checklist">
          <h4>Release Checklist</h4>

          <div>
            {
              report
                .releaseDecision
                .checklist
                .map(
                  (item) => (
                    <article
                      key={item.id}
                    >
                      <StatusBadge
                        tone={
                          getChecklistTone(
                            item.status,
                          )
                        }
                      >
                        {item.status}
                      </StatusBadge>

                      <div>
                        <strong>
                          {item.label}
                        </strong>

                        <span>
                          {item.detail}
                        </span>
                      </div>
                    </article>
                  ),
                )
            }
          </div>
        </div>

        <div className="report-export-actions">
          <button
            className="button button-secondary"
            onClick={() => {
              downloadReportJson(
                report,
              )

              showMessage(
                'success',
                'JSON report downloaded.',
              )
            }}
            type="button"
          >
            Export JSON
          </button>

          <button
            className="button button-secondary"
            onClick={() => {
              downloadReportCsv(
                report,
              )

              showMessage(
                'success',
                'CSV report downloaded.',
              )
            }}
            type="button"
          >
            Export CSV
          </button>

          <button
            className="button button-primary"
            disabled={
              isExportingPdf
            }
            onClick={
              handlePdfExport
            }
            type="button"
          >
            {isExportingPdf
              ? 'Generating PDF...'
              : 'Export PDF'}
          </button>
        </div>
      </section>

      <section className="dashboard-panel report-panel">
        <div className="panel-header report-panel-header">
          <div>
            <span className="panel-eyebrow">
              TELEGRAM DELIVERY
            </span>

            <h3>
              Delivery and Retry
            </h3>

            <p>
              Send the immutable consolidated report
              snapshot and track each delivery attempt.
            </p>
          </div>

          {configuration && (
            <StatusBadge
              tone={
                configuration
                  .configured &&
                configuration
                  .testing_topic_configured &&
                configuration
                  .documentation_topic_configured
                  ? 'success'
                  : 'warning'
              }
            >
              {configuration
                .configured
                ? 'Configured'
                : 'Not Configured'}
            </StatusBadge>
          )}
        </div>

        <div className="report-telegram-controls">
          <label>
            <span>Destination</span>

            <select
              onChange={(event) =>
                setDestination(
                  event.target.value,
                )
              }
              value={destination}
            >
              <option value="both">
                Testing summary + Documentation files
              </option>

              <option value="testing">
                Testing topic only
              </option>

              <option value="documentation">
                Documentation topic only
              </option>
            </select>
          </label>

          <div className="report-delivery-formats">
            <span>Delivery Formats</span>

            <div>
              {formatOptions.map(
                (option) => (
                  <label
                    key={option.key}
                  >
                    <input
                      checked={
                        selectedFormats[
                          option.key
                        ]
                      }
                      onChange={() =>
                        handleFormatToggle(
                          option.key,
                        )
                      }
                      type="checkbox"
                    />

                    <span>
                      <strong>
                        {option.label}
                      </strong>

                      <small>
                        {
                          option.description
                        }
                      </small>
                    </span>
                  </label>
                ),
              )}
            </div>
          </div>

          <div className="report-telegram-actions">
            <button
              className="button button-secondary"
              disabled={
                isLoadingHistory
              }
              onClick={
                refreshHistory
              }
              type="button"
            >
              {isLoadingHistory
                ? 'Refreshing...'
                : 'Refresh History'}
            </button>

            <button
              className="button button-primary"
              disabled={
                isDelivering ||
                enabledFormats.length === 0
              }
              onClick={
                handleTelegramDelivery
              }
              type="button"
            >
              {isDelivering
                ? 'Sending...'
                : 'Send to Telegram'}
            </button>
          </div>
        </div>

        {message && (
          <div
            className={[
              'report-delivery-message',
              `report-delivery-message-${message.tone}`,
            ].join(' ')}
          >
            {message.text}
          </div>
        )}

        <div className="report-delivery-history">
          <div className="report-delivery-history-heading">
            <div>
              <h4>Delivery History</h4>

              <p>
                Records are persisted by the QA
                backend and retain the original
                report snapshot for retries.
              </p>
            </div>

            <strong>
              {deliveries.length} Records
            </strong>
          </div>

          {!historyLoaded ? (
            <div className="report-delivery-history-empty">
              Click Refresh History to load Telegram
              configuration and previous deliveries.
            </div>
          ) : deliveries.length === 0 ? (
            <div className="report-delivery-history-empty">
              No delivery record exists for this Test
              Cycle.
            </div>
          ) : (
            <div className="report-delivery-table-wrapper">
              <table className="report-delivery-table">
                <thead>
                  <tr>
                    <th>Status</th>
                    <th>Destination</th>
                    <th>Formats</th>
                    <th>Attempt</th>
                    <th>Sent At</th>
                    <th>Error</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {deliveries.map(
                    (delivery) => (
                      <tr
                        key={
                          delivery.id
                        }
                      >
                        <td>
                          <StatusBadge
                            tone={
                              getDeliveryTone(
                                delivery.status,
                              )
                            }
                          >
                            {
                              delivery.status
                            }
                          </StatusBadge>
                        </td>

                        <td>
                          {
                            delivery.destination
                          }
                        </td>

                        <td>
                          {Array.isArray(
                            delivery.formats,
                          )
                            ? delivery
                                .formats
                                .join(', ')
                            : 'Not available'}
                        </td>

                        <td>
                          {
                            delivery.attempt
                          }
                        </td>

                        <td>
                          {formatDateTime(
                            delivery.sent_at ??
                            delivery.updated_at,
                          )}
                        </td>

                        <td>
                          <span
                            className="report-delivery-error"
                            title={
                              delivery.error
                            }
                          >
                            {delivery.error ||
                              '—'}
                          </span>
                        </td>

                        <td>
                          <button
                            className="button button-secondary"
                            disabled={
                              delivery.status !==
                                'failed' ||
                              retryingDeliveryId ===
                                delivery.id
                            }
                            onClick={() =>
                              handleRetry(
                                delivery.id,
                              )
                            }
                            type="button"
                          >
                            {retryingDeliveryId ===
                            delivery.id
                              ? 'Retrying...'
                              : 'Retry'}
                          </button>
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

export default ReportDeliveryPanel
