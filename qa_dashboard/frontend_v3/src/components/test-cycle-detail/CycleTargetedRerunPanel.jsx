import {
  useMemo,
  useState,
} from 'react'

function normalizeSearch(
  value,
) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
}

function CycleTargetedRerunPanel({
  model,
  onSubmit,
}) {
  const [
    searchTerm,
    setSearchTerm,
  ] = useState('')

  const [
    selectedAssetIds,
    setSelectedAssetIds,
  ] = useState(
    () => new Set(),
  )

  const [
    selectedScopeKey,
    setSelectedScopeKey,
  ] = useState('')

  const eligibleScopes =
    useMemo(
      () =>
        model.scopes.filter(
          (scope) =>
            scope.eligible,
        ),
      [model.scopes],
    )

  const effectiveScopeKey =
    eligibleScopes.some(
      (scope) =>
        scope.key ===
        selectedScopeKey,
    )
      ? selectedScopeKey
      : (
          eligibleScopes[0]
            ?.key ?? ''
        )

  const normalizedSearch =
    normalizeSearch(
      searchTerm,
    )

  const visibleAssets =
    useMemo(
      () => {
        if (!normalizedSearch) {
          return model.assets
        }

        return model.assets.filter(
          (asset) =>
            [
              asset.assetId,
              asset.name,
              asset.module,
              asset.feature,
              asset.typeLabel,
            ]
              .map(normalizeSearch)
              .join(' ')
              .includes(
                normalizedSearch,
              ),
        )
      },
      [
        model.assets,
        normalizedSearch,
      ],
    )

  const effectiveSelectedAssetIds =
    useMemo(
      () => {
        const availableIds =
          new Set(
            model.assets.map(
              (asset) =>
                asset.assetId,
            ),
          )

        return new Set(
          Array.from(
            selectedAssetIds,
          ).filter(
            (assetId) =>
              availableIds.has(
                assetId,
              ),
          ),
        )
      },
      [
        model.assets,
        selectedAssetIds,
      ],
    )

  const allVisibleSelected =
    visibleAssets.length > 0 &&
    visibleAssets.every(
      (asset) =>
        effectiveSelectedAssetIds.has(
          asset.assetId,
        ),
    )

  function toggleAsset(
    assetId,
  ) {
    setSelectedAssetIds(
      (current) => {
        const next =
          new Set(current)

        if (next.has(assetId)) {
          next.delete(assetId)
        } else {
          next.add(assetId)
        }

        return next
      },
    )
  }

  function toggleVisibleAssets() {
    setSelectedAssetIds(
      (current) => {
        const next =
          new Set(current)

        if (allVisibleSelected) {
          visibleAssets.forEach(
            (asset) =>
              next.delete(
                asset.assetId,
              ),
          )
        } else {
          visibleAssets.forEach(
            (asset) =>
              next.add(
                asset.assetId,
              ),
          )
        }

        return next
      },
    )
  }

  async function handleSubmit() {
    if (
      typeof onSubmit !==
        'function' ||
      !effectiveScopeKey ||
      effectiveSelectedAssetIds
        .size === 0
    ) {
      return
    }

    const created =
      await onSubmit({
        assetIds:
          Array.from(
            effectiveSelectedAssetIds,
          ),

        scopeKey:
          effectiveScopeKey,
      })

    if (
      Array.isArray(created) &&
      created.length > 0
    ) {
      setSelectedAssetIds(
        new Set(),
      )
    }
  }

  const disabled =
    model.isSubmitting ||
    !effectiveScopeKey ||
    effectiveSelectedAssetIds
      .size === 0

  return (
    <section className="cycle-targeted-rerun">
      <div className="cycle-targeted-rerun-heading">
        <div>
          <span className="panel-eyebrow">
            TARGETED EXECUTION
          </span>

          <h4>
            Rerun Selected Test Assets
          </h4>

          <p>
            Create a child execution for captured
            Test Assets while preserving the full
            scope result and execution history.
          </p>
        </div>

        <strong>
          {
            effectiveSelectedAssetIds
              .size
          } selected
        </strong>
      </div>

      {model.assets.length === 0 ? (
        <div className="cycle-targeted-rerun-empty">
          <strong>
            No captured Test Assets available
          </strong>

          <span>
            Targeted rerun requires immutable Test
            Asset snapshots. Legacy cycles with only
            asset IDs cannot be targeted safely.
          </span>
        </div>
      ) : (
        <>
          <div className="cycle-targeted-rerun-controls">
            <label>
              <span>Execution Scope</span>

              <select
                disabled={
                  eligibleScopes.length ===
                  0
                }
                onChange={(event) =>
                  setSelectedScopeKey(
                    event.target.value,
                  )
                }
                value={
                  effectiveScopeKey
                }
              >
                {eligibleScopes.length ===
                0 ? (
                  <option value="">
                    No eligible scope
                  </option>
                ) : (
                  eligibleScopes.map(
                    (scope) => (
                      <option
                        key={scope.key}
                        value={scope.key}
                      >
                        {scope.label}
                      </option>
                    ),
                  )
                )}
              </select>
            </label>

            <label>
              <span>Search Assets</span>

              <input
                onChange={(event) =>
                  setSearchTerm(
                    event.target.value,
                  )
                }
                placeholder="Search name, ID, module, or feature"
                type="search"
                value={searchTerm}
              />
            </label>

            <button
              className="button button-primary"
              disabled={disabled}
              onClick={
                handleSubmit
              }
              type="button"
            >
              {model.isSubmitting
                ? 'Creating targeted rerun...'
                : `Rerun ${effectiveSelectedAssetIds.size} Assets`}
            </button>
          </div>

          {eligibleScopes.length === 0 && (
            <div className="cycle-targeted-rerun-warning">
              UI Testing or Related Regression must
              have a completed, failed, review, or
              cancelled execution before an asset
              rerun can be created.
            </div>
          )}

          <div className="cycle-targeted-rerun-list-heading">
            <label>
              <input
                checked={
                  allVisibleSelected
                }
                disabled={
                  visibleAssets.length ===
                  0
                }
                onChange={
                  toggleVisibleAssets
                }
                type="checkbox"
              />

              <span>
                Select visible assets
              </span>
            </label>

            <span>
              {visibleAssets.length} visible
            </span>
          </div>

          <div className="cycle-targeted-rerun-assets">
            {visibleAssets.length > 0 ? (
              visibleAssets.map(
                (asset) => (
                  <label
                    className={[
                      'cycle-targeted-rerun-asset',
                      effectiveSelectedAssetIds
                        .has(
                          asset.assetId,
                        )
                        ? 'cycle-targeted-rerun-asset-selected'
                        : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    key={asset.assetId}
                  >
                    <input
                      checked={
                        effectiveSelectedAssetIds
                          .has(
                            asset.assetId,
                          )
                      }
                      onChange={() =>
                        toggleAsset(
                          asset.assetId,
                        )
                      }
                      type="checkbox"
                    />

                    <div>
                      <strong>
                        {asset.name}
                      </strong>

                      <span>
                        {asset.module}
                        {' / '}
                        {asset.feature}
                      </span>

                      <code>
                        {asset.assetId}
                      </code>
                    </div>
                  </label>
                ),
              )
            ) : (
              <div className="cycle-targeted-rerun-empty">
                <strong>
                  No matching Test Assets
                </strong>

                <span>
                  Adjust the asset search term.
                </span>
              </div>
            )}
          </div>


          {model.targetedRuns.length > 0 && (
            <div className="cycle-targeted-rerun-history">
              <div className="cycle-targeted-rerun-list-heading">
                <strong>
                  Targeted Run History
                </strong>

                <span>
                  {model.targetedRuns.length} runs
                </span>
              </div>

              <div className="cycle-targeted-rerun-history-list">
                {model.targetedRuns.map(
                  (run) => (
                    <article key={run.runId}>
                      <div>
                        <strong>
                          {run.reasonLabel}
                          {' · '}
                          Attempt {run.attemptNumber}
                        </strong>

                        <code>
                          {run.runId}
                        </code>
                      </div>

                      <div>
                        <span>
                          {run.targetAssetIds.length}
                          {' assets'}
                        </span>

                        <span>
                          {run.status}
                          {' · '}
                          {run.progress}%
                        </span>
                      </div>
                    </article>
                  ),
                )}
              </div>
            </div>
          )}

          <p className="cycle-targeted-rerun-note">
            Built-in Hermes Playwright currently
            applies selected assets as a structured
            result filter after the suite runs. Runs
            without an explicit case mapping are
            marked Need Review instead of being
            reported as a false pass.
          </p>
        </>
      )}
    </section>
  )
}

export default CycleTargetedRerunPanel
