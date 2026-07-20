import { Link } from 'react-router-dom'

import MetricCard from '../components/MetricCard'
import StatusBadge from '../components/StatusBadge'

const metricCards = [
  {
    label: 'Active Cycles',
    value: '2',
    detail: 'Currently running or queued',
    tone: 'primary',
  },
  {
    label: 'Pass Rate',
    value: '92%',
    detail: 'Across recent executions',
    tone: 'success',
  },
  {
    label: 'Need Attention',
    value: '4',
    detail: 'Failed, blocked, or need review',
    tone: 'danger',
  },
  {
    label: 'Completed Today',
    value: '7',
    detail: 'Test cycles completed today',
    tone: 'neutral',
  },
]

const cycleExecutions = [
  {
    label: 'UI Testing',
    status: 'Completed',
    result: '13 / 13',
    progress: 100,
    tone: 'success',
  },
  {
    label: 'API Testing',
    status: 'Running',
    result: '8 / 12',
    progress: 67,
    tone: 'primary',
  },
  {
    label: 'Unit Testing',
    status: 'Completed',
    result: '20 / 20',
    progress: 100,
    tone: 'success',
  },
  {
    label: 'E2E Testing',
    status: 'Queued',
    result: '0 / 4',
    progress: 0,
    tone: 'neutral',
  },
  {
    label: 'Related Regression',
    status: 'Queued',
    result: '0 / 8',
    progress: 0,
    tone: 'neutral',
  },
]

const recentCycles = [
  {
    name: 'Uang Makan Driver',
    type: 'Feature',
    environment: 'Sandbox',
    result: 'Need Review',
    tone: 'warning',
    date: 'Today',
  },
  {
    name: 'Shipment Tracking',
    type: 'Change',
    environment: 'Staging',
    result: 'Passed',
    tone: 'success',
    date: 'Yesterday',
  },
  {
    name: 'Mobospace Regression',
    type: 'Full Product',
    environment: 'Sandbox',
    result: 'Failed',
    tone: 'danger',
    date: '18 Jul 2026',
  },
]

const qualityResults = [
  {
    label: 'Passed',
    value: 92,
    total: 110,
    tone: 'success',
  },
  {
    label: 'Failed',
    value: 4,
    total: 110,
    tone: 'danger',
  },
  {
    label: 'Need Review',
    value: 7,
    total: 110,
    tone: 'warning',
  },
  {
    label: 'Blocked',
    value: 2,
    total: 110,
    tone: 'neutral',
  },
  {
    label: 'Skipped',
    value: 5,
    total: 110,
    tone: 'muted',
  },
]

const attentionItems = [
  {
    title: 'Failed tests',
    detail: '4 tests require investigation',
    value: '4',
    tone: 'danger',
  },
  {
    title: 'Need review',
    detail: 'Manual verification is pending',
    value: '7',
    tone: 'warning',
  },
  {
    title: 'Blocked tests',
    detail: 'Dependencies or test data unavailable',
    value: '2',
    tone: 'neutral',
  },
  {
    title: 'Environment issue',
    detail: 'One environment needs verification',
    value: '1',
    tone: 'muted',
  },
]

function MainDashboardPage() {
  return (
    <div className="dashboard-page">
      <div className="page-heading-row">
        <div>
          <div className="page-heading-meta">
            <span>OVERVIEW</span>
            <StatusBadge tone="primary">
              Static Preview
            </StatusBadge>
          </div>

          <h2>Quality Operations Dashboard</h2>

          <p>
            Monitor test cycles, execution health,
            quality signals, and items requiring attention.
          </p>
        </div>

        <div className="page-heading-actions">
          <Link
            className="button button-secondary"
            to="/history"
          >
            View History
          </Link>

          <Link
            className="button button-primary"
            to="/test-cycles/new"
          >
            Create Test Cycle
          </Link>
        </div>
      </div>

      <section
        aria-label="Quality summary"
        className="metric-grid"
      >
        {metricCards.map((metric) => (
          <MetricCard
            detail={metric.detail}
            key={metric.label}
            label={metric.label}
            tone={metric.tone}
            value={metric.value}
          />
        ))}
      </section>

      <section className="dashboard-content-grid dashboard-content-grid-primary">
        <article className="dashboard-panel active-cycle-panel">
          <div className="panel-header">
            <div>
              <span className="panel-eyebrow">
                ACTIVE TEST CYCLE
              </span>

              <h3>Uang Makan Driver – Release 1.2</h3>

              <p>
                Feature Cycle · Mobospace · Sandbox
              </p>
            </div>

            <StatusBadge tone="primary">
              Running
            </StatusBadge>
          </div>

          <div className="cycle-overall-progress">
            <div className="progress-heading">
              <span>Overall progress</span>
              <strong>68%</strong>
            </div>

            <div
              aria-label="Overall test cycle progress"
              aria-valuemax="100"
              aria-valuemin="0"
              aria-valuenow="68"
              className="progress-track progress-track-large"
              role="progressbar"
            >
              <span style={{ width: '68%' }} />
            </div>

            <div className="cycle-meta">
              <span>Started 8 minutes ago</span>
              <span>Estimated remaining: 6 minutes</span>
            </div>
          </div>

          <div className="execution-list">
            {cycleExecutions.map((execution) => (
              <div
                className="execution-row"
                key={execution.label}
              >
                <div className="execution-name">
                  <strong>{execution.label}</strong>
                  <span>{execution.status}</span>
                </div>

                <div className="execution-progress">
                  <div
                    aria-label={`${execution.label} progress`}
                    aria-valuemax="100"
                    aria-valuemin="0"
                    aria-valuenow={execution.progress}
                    className="progress-track"
                    role="progressbar"
                  >
                    <span
                      className={`progress-fill-${execution.tone}`}
                      style={{
                        width: `${execution.progress}%`,
                      }}
                    />
                  </div>
                </div>

                <strong className="execution-result">
                  {execution.result}
                </strong>
              </div>
            ))}
          </div>

          <div className="panel-actions">
            <Link
              className="button button-secondary"
              to="/test-cycles"
            >
              Open Live Logs
            </Link>

            <Link
              className="button button-primary"
              to="/test-cycles"
            >
              View Cycle
            </Link>
          </div>
        </article>

        <article className="dashboard-panel environment-panel">
          <div className="panel-header">
            <div>
              <span className="panel-eyebrow">
                ENVIRONMENT HEALTH
              </span>

              <h3>Mobospace Sandbox</h3>
            </div>

            <StatusBadge tone="success">
              Healthy
            </StatusBadge>
          </div>

          <div className="environment-health-list">
            <div>
              <span>Web Application</span>
              <strong>Online</strong>
            </div>

            <div>
              <span>API Service</span>
              <strong>Online</strong>
            </div>

            <div>
              <span>Authentication</span>
              <strong>Healthy</strong>
            </div>

            <div>
              <span>UI Runner</span>
              <strong>Available</strong>
            </div>
          </div>

          <div className="environment-response">
            <div>
              <span>Web response</span>
              <strong>220 ms</strong>
            </div>

            <div>
              <span>API response</span>
              <strong>140 ms</strong>
            </div>
          </div>

          <p className="environment-last-check">
            Last checked 2 minutes ago
          </p>

          <Link
            className="text-link"
            to="/environments"
          >
            Open environment configuration
          </Link>
        </article>
      </section>

      <section className="dashboard-content-grid dashboard-content-grid-secondary">
        <article className="dashboard-panel recent-cycles-panel">
          <div className="panel-header">
            <div>
              <span className="panel-eyebrow">
                RECENT ACTIVITY
              </span>

              <h3>Recent Test Cycles</h3>
            </div>

            <Link
              className="text-link"
              to="/history"
            >
              View all
            </Link>
          </div>

          <div className="table-wrapper">
            <table className="dashboard-table">
              <thead>
                <tr>
                  <th>Cycle</th>
                  <th>Type</th>
                  <th>Environment</th>
                  <th>Result</th>
                  <th>Date</th>
                </tr>
              </thead>

              <tbody>
                {recentCycles.map((cycle) => (
                  <tr key={cycle.name}>
                    <td>
                      <strong>{cycle.name}</strong>
                      <span>Mobospace</span>
                    </td>

                    <td>{cycle.type}</td>
                    <td>{cycle.environment}</td>

                    <td>
                      <StatusBadge tone={cycle.tone}>
                        {cycle.result}
                      </StatusBadge>
                    </td>

                    <td>{cycle.date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="dashboard-panel quality-panel">
          <div className="panel-header">
            <div>
              <span className="panel-eyebrow">
                QUALITY OVERVIEW
              </span>

              <h3>Execution Results</h3>
            </div>

            <select
              aria-label="Quality overview period"
              defaultValue="7-days"
            >
              <option value="7-days">
                Last 7 days
              </option>

              <option value="30-days">
                Last 30 days
              </option>

              <option value="release">
                Current release
              </option>
            </select>
          </div>

          <div className="quality-result-list">
            {qualityResults.map((result) => {
              const percentage =
                (result.value / result.total) * 100

              return (
                <div
                  className="quality-result-row"
                  key={result.label}
                >
                  <div>
                    <span
                      className={`quality-dot quality-dot-${result.tone}`}
                    />
                    <span>{result.label}</span>
                  </div>

                  <div className="quality-result-bar">
                    <span
                      className={`quality-bar-${result.tone}`}
                      style={{
                        width: `${percentage}%`,
                      }}
                    />
                  </div>

                  <strong>{result.value}</strong>
                </div>
              )
            })}
          </div>

          <div className="quality-total">
            <span>Total executions</span>
            <strong>110</strong>
          </div>
        </article>
      </section>

      <section className="dashboard-panel attention-panel">
        <div className="panel-header">
          <div>
            <span className="panel-eyebrow">
              ACTION REQUIRED
            </span>

            <h3>Attention Required</h3>

            <p>
              Review failures, blocked tests, and pending
              manual verification.
            </p>
          </div>

          <Link
            className="text-link"
            to="/reports"
          >
            Open quality report
          </Link>
        </div>

        <div className="attention-grid">
          {attentionItems.map((item) => (
            <article
              className="attention-item"
              key={item.title}
            >
              <span
                className={`attention-value attention-value-${item.tone}`}
              >
                {item.value}
              </span>

              <div>
                <strong>{item.title}</strong>
                <p>{item.detail}</p>
              </div>

              <Link
                aria-label={`Review ${item.title}`}
                className="attention-action"
                to="/history"
              >
                Review
              </Link>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}

export default MainDashboardPage
