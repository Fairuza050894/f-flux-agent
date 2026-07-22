import StatusBadge from '../StatusBadge'

function OverviewMetadata({
  formatDateTime,
  items,
}) {
  return (
    <dl className="cycle-overview-metadata">
      {items.map((item) => (
        <div key={item.key}>
          <dt>{item.label}</dt>

          <dd>
            {item.valueType ===
            'datetime'
              ? formatDateTime(
                  item.value,
                )
              : item.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}

function OverviewList({
  emptyMessage,
  items,
}) {
  if (items.length === 0) {
    return (
      <p className="cycle-overview-empty">
        {emptyMessage}
      </p>
    )
  }

  return (
    <ul className="cycle-overview-list">
      {items.map((item) => (
        <li key={item.key}>
          <span>{item.label}</span>
        </li>
      ))}
    </ul>
  )
}

function OverviewAssets({
  assets,
}) {
  if (assets.length === 0) {
    return (
      <p className="cycle-overview-empty">
        No test assets selected.
      </p>
    )
  }

  return (
    <ul className="cycle-overview-asset-list">
      {assets.map((assetId) => (
        <li key={assetId}>
          <span>Asset ID</span>

          <code title={assetId}>
            {assetId}
          </code>
        </li>
      ))}
    </ul>
  )
}

function OverviewConfiguration({
  model,
}) {
  return (
    <section className="dashboard-panel cycle-detail-panel cycle-overview-panel">
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            EXECUTION CONFIGURATION
          </span>

          <h3>Configuration</h3>

          <p>
            Runner behavior, evidence
            capture, notifications, and
            test assets.
          </p>
        </div>
      </div>

      <dl className="cycle-overview-settings">
        <div>
          <dt>Execution Mode</dt>

          <dd>{model.executionMode}</dd>
        </div>

        <div>
          <dt>Stop Policy</dt>

          <dd>{model.stopPolicy}</dd>
        </div>

        <div>
          <dt>Evidence Types</dt>

          <dd>{model.evidence.length}</dd>
        </div>

        <div>
          <dt>Notifications</dt>

          <dd>
            {model.notifications.length}
          </dd>
        </div>
      </dl>

      <div className="cycle-overview-groups">
        <section className="cycle-overview-group">
          <div className="cycle-overview-group-header">
            <h4>Evidence</h4>

            <span>
              {model.evidence.length}
            </span>
          </div>

          <OverviewList
            emptyMessage="No evidence types selected."
            items={model.evidence}
          />
        </section>

        <section className="cycle-overview-group">
          <div className="cycle-overview-group-header">
            <h4>Notifications</h4>

            <span>
              {model.notifications.length}
            </span>
          </div>

          <OverviewList
            emptyMessage="No notification channels selected."
            items={model.notifications}
          />
        </section>

        <section className="cycle-overview-group cycle-overview-group-wide">
          <div className="cycle-overview-group-header">
            <h4>Selected Test Assets</h4>

            <span>
              {model.assets.length}
            </span>
          </div>

          <OverviewAssets
            assets={model.assets}
          />
        </section>
      </div>
    </section>
  )
}

function OverviewRunners({
  runners,
}) {
  return (
    <section className="dashboard-panel cycle-detail-panel cycle-overview-panel">
      <div className="panel-header">
        <div>
          <span className="panel-eyebrow">
            TESTING SCOPE
          </span>

          <h3>Selected Runners</h3>

          <p>
            Runners included in this test
            cycle.
          </p>
        </div>

        <strong className="cycle-detail-count">
          {runners.length}
        </strong>
      </div>

      <div
        aria-label="Selected runners"
        className="cycle-runner-table"
        role="table"
      >
        <div
          className="cycle-runner-table-header"
          role="row"
        >
          <span role="columnheader">
            Scope
          </span>

          <span role="columnheader">
            Runner
          </span>

          <span role="columnheader">
            Status
          </span>
        </div>

        <div
          className="cycle-runner-table-body"
          role="rowgroup"
        >
          {runners.map((runner) => (
            <div
              className="cycle-runner-table-row"
              key={runner.key}
              role="row"
            >
              <strong
                className="cycle-runner-scope"
                role="cell"
              >
                {runner.label}
              </strong>

              <span
                className="cycle-runner-name"
                role="cell"
              >
                {runner.runner}
              </span>

              <div
                className="cycle-runner-status"
                role="cell"
              >
                <StatusBadge
                  tone={runner.tone}
                >
                  {runner.statusLabel}
                </StatusBadge>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function CycleOverviewTab({
  formatDateTime,
  model,
}) {
  return (
    <div className="cycle-detail-content cycle-overview-layout">
      <section className="dashboard-panel cycle-detail-panel cycle-overview-panel">
        <div className="panel-header">
          <div>
            <span className="panel-eyebrow">
              CYCLE CONTEXT
            </span>

            <h3>Cycle Overview</h3>

            <p>
              Configuration captured from
              the Create Test Cycle wizard.
            </p>
          </div>

          <StatusBadge tone="primary">
            Saved Record
          </StatusBadge>
        </div>

        <OverviewMetadata
          formatDateTime={
            formatDateTime
          }
          items={model.metadata}
        />

        <div className="cycle-overview-description">
          <span>Description</span>

          <p>{model.description}</p>
        </div>
      </section>

      <OverviewConfiguration
        model={model}
      />

      <OverviewRunners
        runners={model.runners}
      />
    </div>
  )
}

export default CycleOverviewTab
