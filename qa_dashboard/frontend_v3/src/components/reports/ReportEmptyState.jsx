function ReportEmptyState({
  hasFilters,
  onReset,
}) {
  return (
    <div className="report-empty-state">
      <strong>
        {hasFilters
          ? 'No matching reports'
          : 'No test results available'}
      </strong>

      <p>
        {hasFilters
          ? 'Adjust or clear the current filters to display other reports.'
          : 'Consolidated quality reports will appear after supported test executions produce results.'}
      </p>

      {hasFilters && (
        <button
          className="button button-secondary"
          onClick={onReset}
          type="button"
        >
          Clear Filters
        </button>
      )}
    </div>
  )
}

export default ReportEmptyState
