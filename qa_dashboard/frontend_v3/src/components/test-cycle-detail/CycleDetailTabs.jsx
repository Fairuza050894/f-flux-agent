function CycleDetailTabs({
  activeTab,
  onChange,
  tabs,
}) {
  return (
    <nav
      aria-label="Test Cycle detail tabs"
      className="cycle-detail-tabs"
    >
      {tabs.map((tab) => {
        const isActive =
          activeTab === tab.id

        return (
          <button
            aria-current={
              isActive
                ? 'page'
                : undefined
            }
            className={[
              'cycle-detail-tab',
              isActive
                ? 'cycle-detail-tab-active'
                : '',
            ]
              .filter(Boolean)
              .join(' ')}
            key={tab.id}
            onClick={() =>
              onChange(tab.id)
            }
            type="button"
          >
            {tab.label}
          </button>
        )
      })}
    </nav>
  )
}

export default CycleDetailTabs
