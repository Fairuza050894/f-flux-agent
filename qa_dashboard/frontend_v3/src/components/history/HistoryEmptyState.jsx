function HistoryEmptyState({
  hasFilters,
  onReset,
}) {
  return (
    <div className="history-empty-state">
      <strong>
        {hasFilters
          ? 'No matching history'
          : 'No test cycle history yet'}
      </strong>

      <p>
        {hasFilters
          ? 'Adjust or clear the current filters to display other test cycles.'
          : 'Completed and active test cycles will appear here after they are created.'}
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

export default HistoryEmptyState
