import {
  useMemo,
  useState,
} from 'react'

import {
  TEST_PLAN_CYCLE_TYPES,
  TEST_PLAN_EMPTY_FORM,
  TEST_PLAN_EXECUTION_MODES,
  TEST_PLAN_SCOPE_OPTIONS,
  TEST_PLAN_STATUSES,
  TEST_PLAN_STOP_POLICIES,
} from '../../features/test-planning/testPlanConstants'
import {
  selectCycleEligibleAssets,
} from '../../features/test-assets/testAssetSelectors'

const evidenceOptions = [
  {
    key: 'screenshot',
    label: 'Screenshots',
  },
  {
    key: 'video',
    label: 'Video Recording',
  },
  {
    key: 'consoleLogs',
    label: 'Console Logs',
  },
  {
    key: 'networkLogs',
    label: 'Network Logs',
  },
  {
    key: 'errorLogs',
    label: 'Error Logs',
  },
]

const notificationOptions = [
  {
    key: 'telegramTesting',
    label: 'Telegram Testing',
  },
  {
    key: 'telegramDocumentation',
    label: 'Telegram Documentation',
  },
]

function createInitialForm(
  initialPlan,
) {
  return {
    ...TEST_PLAN_EMPTY_FORM,
    ...(initialPlan ?? {}),

    scope: {
      ...TEST_PLAN_EMPTY_FORM.scope,
      ...(initialPlan?.scope ?? {}),
    },

    selectedAssetIds: [
      ...(initialPlan
        ?.selectedAssetIds ?? []),
    ],

    executionSettings: {
      ...TEST_PLAN_EMPTY_FORM
        .executionSettings,
      ...(initialPlan
        ?.executionSettings ?? {}),
    },
  }
}

function hasSelectedScope(scope) {
  return Object.values(
    scope ?? {},
  ).some(Boolean)
}

function TestPlanFormModal({
  assets,
  environments,
  initialPlan = null,
  onClose,
  onSubmit,
  projects,
}) {
  const [form, setForm] =
    useState(() =>
      createInitialForm(
        initialPlan,
      ),
    )

  const [assetSearch, setAssetSearch] =
    useState('')

  const [errors, setErrors] =
    useState({})

  const isEditing =
    Boolean(initialPlan?.id)

  const projectEnvironments =
    useMemo(
      () =>
        environments.filter(
          (environment) =>
            environment.projectId ===
            form.projectId,
        ),
      [
        environments,
        form.projectId,
      ],
    )

  const compatibleAssets =
    useMemo(
      () =>
        selectCycleEligibleAssets({
          assets,
          projectId:
            form.projectId,
          scope:
            form.scope,
        }),
      [
        assets,
        form.projectId,
        form.scope,
      ],
    )

  const filteredAssets =
    useMemo(() => {
      const query =
        assetSearch
          .trim()
          .toLowerCase()

      if (!query) {
        return compatibleAssets
      }

      return compatibleAssets.filter(
        (asset) =>
          [
            asset.id,
            asset.name,
            asset.module,
            asset.feature,
          ].some((value) =>
            String(value ?? '')
              .toLowerCase()
              .includes(query),
          ),
      )
    }, [
      assetSearch,
      compatibleAssets,
    ])

  const selectableAssetIds =
    useMemo(
      () =>
        new Set(
          compatibleAssets
            .filter(
              (asset) =>
                asset.executionReady,
            )
            .map(
              (asset) =>
                asset.id,
            ),
        ),
      [compatibleAssets],
    )

  const validSelectedAssetIds =
    form.selectedAssetIds.filter(
      (assetId) =>
        selectableAssetIds.has(
          assetId,
        ),
    )

  function clearError(field) {
    setErrors(
      (currentErrors) => ({
        ...currentErrors,
        [field]: '',
      }),
    )
  }

  function updateField(
    field,
    value,
  ) {
    setForm((currentForm) => ({
      ...currentForm,
      [field]: value,
    }))

    clearError(field)
  }

  function updateExecutionSetting(
    field,
    value,
  ) {
    setForm((currentForm) => ({
      ...currentForm,

      executionSettings: {
        ...currentForm
          .executionSettings,

        [field]: value,
      },
    }))
  }

  function handleProjectChange(
    projectId,
  ) {
    const firstEnvironment =
      environments.find(
        (environment) =>
          environment.projectId ===
          projectId,
      )

    setForm((currentForm) => ({
      ...currentForm,

      projectId,

      environmentId:
        firstEnvironment?.id ?? '',

      selectedAssetIds: [],
    }))

    setAssetSearch('')

    setErrors(
      (currentErrors) => ({
        ...currentErrors,
        projectId: '',
        environmentId: '',
        selectedAssetIds: '',
      }),
    )
  }

  function handleScopeChange(
    scopeKey,
    checked,
  ) {
    setForm((currentForm) => {
      const nextScope = {
        ...currentForm.scope,
        [scopeKey]: checked,
      }

      const validAssetIds =
        currentForm
          .selectedAssetIds
          .filter((assetId) => {
            const asset =
              assets.find(
                (candidate) =>
                  candidate.id ===
                  assetId,
              )

            return Boolean(
              asset &&
              asset.projectId ===
                currentForm.projectId &&
              asset.executionReady &&
              nextScope[asset.type],
            )
          })

      return {
        ...currentForm,
        scope: nextScope,
        selectedAssetIds:
          validAssetIds,
      }
    })

    clearError('scope')
    clearError('selectedAssetIds')
  }

  function handleAssetToggle(
    assetId,
    checked,
  ) {
    setForm((currentForm) => ({
      ...currentForm,

      selectedAssetIds:
        checked
          ? Array.from(
              new Set([
                ...currentForm
                  .selectedAssetIds,
                assetId,
              ]),
            )
          : currentForm
              .selectedAssetIds
              .filter(
                (currentAssetId) =>
                  currentAssetId !==
                  assetId,
              ),
    }))

    if (checked) {
      clearError(
        'selectedAssetIds',
      )
    }
  }

  function handleSelectVisible() {
    const visibleReadyIds =
      filteredAssets
        .filter(
          (asset) =>
            asset.executionReady,
        )
        .map(
          (asset) =>
            asset.id,
        )

    setForm((currentForm) => ({
      ...currentForm,

      selectedAssetIds:
        Array.from(
          new Set([
            ...currentForm
              .selectedAssetIds,
            ...visibleReadyIds,
          ]),
        ),
    }))

    clearError('selectedAssetIds')
  }

  function handleClearAssets() {
    setForm((currentForm) => ({
      ...currentForm,
      selectedAssetIds: [],
    }))
  }

  function validateForm() {
    const nextErrors = {}

    if (!form.name.trim()) {
      nextErrors.name =
        'Test Plan name is required.'
    }

    if (!form.projectId) {
      nextErrors.projectId =
        'Select a project.'
    }

    if (
      !hasSelectedScope(
        form.scope,
      )
    ) {
      nextErrors.scope =
        'Select at least one testing scope.'
    }

    if (
      form.cycleType ===
        'Feature Cycle' &&
      !form.module.trim()
    ) {
      nextErrors.module =
        'Module is required for a Feature Cycle.'
    }

    if (
      form.cycleType ===
        'Feature Cycle' &&
      !form.feature.trim()
    ) {
      nextErrors.feature =
        'Feature is required for a Feature Cycle.'
    }

    if (
      form.status === 'Ready' &&
      !form.environmentId
    ) {
      nextErrors.environmentId =
        'A default environment is required before marking the plan Ready.'
    }

    if (
      form.status === 'Ready' &&
      validSelectedAssetIds.length ===
        0
    ) {
      nextErrors.selectedAssetIds =
        'Select at least one execution-ready Test Asset before marking the plan Ready.'
    }

    return nextErrors
  }

  function handleSubmit(event) {
    event.preventDefault()

    const nextErrors =
      validateForm()

    if (
      Object.keys(
        nextErrors,
      ).length > 0
    ) {
      setErrors(nextErrors)
      return
    }

    onSubmit({
      ...form,

      name:
        form.name.trim(),

      objective:
        form.objective.trim(),

      module:
        form.module.trim(),

      feature:
        form.feature.trim(),

      selectedAssetIds:
        validSelectedAssetIds,
    })
  }

  return (
    <div
      aria-labelledby="test-plan-modal-title"
      aria-modal="true"
      className="test-plan-modal-overlay"
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose()
        }
      }}
      role="dialog"
    >
      <form
        className="test-plan-modal"
        onSubmit={handleSubmit}
      >
        <header className="test-plan-modal-header">
          <div>
            <span className="panel-eyebrow">
              TEST PLANNING
            </span>

            <h2 id="test-plan-modal-title">
              {isEditing
                ? 'Edit Test Plan'
                : 'Create Test Plan'}
            </h2>

            <p>
              Prepare reusable scope,
              Test Assets, and execution
              settings.
            </p>
          </div>

          <button
            aria-label="Close Test Plan form"
            className="button button-secondary"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        </header>

        <div className="test-plan-modal-body">
          <section className="test-plan-form-section">
            <div className="test-plan-form-section-heading">
              <h3>Plan Information</h3>

              <p>
                Define the plan identity,
                project, environment, and
                intended cycle type.
              </p>
            </div>

            <div className="test-plan-form-grid">
              <label className="test-plan-form-wide">
                <span>
                  Plan Name
                  <em>*</em>
                </span>

                <input
                  aria-invalid={
                    Boolean(
                      errors.name,
                    )
                  }
                  autoFocus
                  maxLength="160"
                  onChange={(event) =>
                    updateField(
                      'name',
                      event.target.value,
                    )
                  }
                  placeholder="Example: Meal Allowance Regression Plan"
                  type="text"
                  value={form.name}
                />

                {errors.name && (
                  <small role="alert">
                    {errors.name}
                  </small>
                )}
              </label>

              <label>
                <span>
                  Project
                  <em>*</em>
                </span>

                <select
                  aria-invalid={
                    Boolean(
                      errors.projectId,
                    )
                  }
                  onChange={(event) =>
                    handleProjectChange(
                      event.target.value,
                    )
                  }
                  value={form.projectId}
                >
                  <option value="">
                    Select project
                  </option>

                  {projects.map(
                    (project) => (
                      <option
                        key={project.id}
                        value={project.id}
                      >
                        {project.name}
                      </option>
                    ),
                  )}
                </select>

                {errors.projectId && (
                  <small role="alert">
                    {errors.projectId}
                  </small>
                )}
              </label>

              <label>
                <span>
                  Default Environment
                </span>

                <select
                  aria-invalid={
                    Boolean(
                      errors.environmentId,
                    )
                  }
                  disabled={
                    !form.projectId ||
                    projectEnvironments
                      .length === 0
                  }
                  onChange={(event) =>
                    updateField(
                      'environmentId',
                      event.target.value,
                    )
                  }
                  value={
                    form.environmentId
                  }
                >
                  <option value="">
                    {projectEnvironments
                      .length === 0
                      ? 'No environment available'
                      : 'Select environment'}
                  </option>

                  {projectEnvironments.map(
                    (environment) => (
                      <option
                        key={
                          environment.id
                        }
                        value={
                          environment.id
                        }
                      >
                        {
                          environment.name
                        }
                      </option>
                    ),
                  )}
                </select>

                {errors.environmentId && (
                  <small role="alert">
                    {
                      errors.environmentId
                    }
                  </small>
                )}
              </label>

              <label>
                <span>Plan Status</span>

                <select
                  onChange={(event) =>
                    updateField(
                      'status',
                      event.target.value,
                    )
                  }
                  value={form.status}
                >
                  {TEST_PLAN_STATUSES.map(
                    (status) => (
                      <option
                        key={status}
                        value={status}
                      >
                        {status}
                      </option>
                    ),
                  )}
                </select>
              </label>

              <label>
                <span>Cycle Type</span>

                <select
                  onChange={(event) =>
                    updateField(
                      'cycleType',
                      event.target.value,
                    )
                  }
                  value={form.cycleType}
                >
                  {TEST_PLAN_CYCLE_TYPES.map(
                    (cycleType) => (
                      <option
                        key={cycleType}
                        value={cycleType}
                      >
                        {cycleType}
                      </option>
                    ),
                  )}
                </select>
              </label>

              <label>
                <span>
                  Module
                  {form.cycleType ===
                    'Feature Cycle' && (
                    <em>*</em>
                  )}
                </span>

                <input
                  aria-invalid={
                    Boolean(
                      errors.module,
                    )
                  }
                  maxLength="120"
                  onChange={(event) =>
                    updateField(
                      'module',
                      event.target.value,
                    )
                  }
                  placeholder="Example: Uang Makan Driver"
                  type="text"
                  value={form.module}
                />

                {errors.module && (
                  <small role="alert">
                    {errors.module}
                  </small>
                )}
              </label>

              <label>
                <span>
                  Feature
                  {form.cycleType ===
                    'Feature Cycle' && (
                    <em>*</em>
                  )}
                </span>

                <input
                  aria-invalid={
                    Boolean(
                      errors.feature,
                    )
                  }
                  maxLength="120"
                  onChange={(event) =>
                    updateField(
                      'feature',
                      event.target.value,
                    )
                  }
                  placeholder="Example: Pengecualian"
                  type="text"
                  value={form.feature}
                />

                {errors.feature && (
                  <small role="alert">
                    {errors.feature}
                  </small>
                )}
              </label>

              <label className="test-plan-form-wide">
                <span>Test Objective</span>

                <textarea
                  maxLength="1500"
                  onChange={(event) =>
                    updateField(
                      'objective',
                      event.target.value,
                    )
                  }
                  placeholder="Describe the testing objective and expected coverage."
                  rows="4"
                  value={form.objective}
                />
              </label>
            </div>
          </section>

          <section className="test-plan-form-section">
            <div className="test-plan-form-section-heading">
              <h3>Testing Scope</h3>

              <p>
                Select the testing types
                covered by this plan.
              </p>
            </div>

            <div className="test-plan-option-grid">
              {TEST_PLAN_SCOPE_OPTIONS.map(
                (option) => (
                  <label
                    className="test-plan-option"
                    key={option.key}
                  >
                    <input
                      checked={
                        form.scope[
                          option.key
                        ]
                      }
                      onChange={(event) =>
                        handleScopeChange(
                          option.key,
                          event.target
                            .checked,
                        )
                      }
                      type="checkbox"
                    />

                    <span>
                      <strong>
                        {option.label}
                      </strong>
                    </span>
                  </label>
                ),
              )}
            </div>

            {errors.scope && (
              <div
                className="test-plan-form-error"
                role="alert"
              >
                {errors.scope}
              </div>
            )}
          </section>

          <section className="test-plan-form-section">
            <div className="test-plan-form-section-heading test-plan-asset-heading">
              <div>
                <h3>Test Assets</h3>

                <p>
                  Only assets from the
                  selected project and scope
                  are displayed.
                </p>
              </div>

              <strong>
                {
                  validSelectedAssetIds
                    .length
                }{' '}
                selected
              </strong>
            </div>

            <div className="test-plan-asset-toolbar">
              <input
                onChange={(event) =>
                  setAssetSearch(
                    event.target.value,
                  )
                }
                placeholder="Search Test Assets"
                type="search"
                value={assetSearch}
              />

              <button
                className="button button-secondary"
                onClick={
                  handleClearAssets
                }
                type="button"
              >
                Clear
              </button>

              <button
                className="button button-secondary"
                onClick={
                  handleSelectVisible
                }
                type="button"
              >
                Select Visible
              </button>
            </div>

            <div className="test-plan-asset-list">
              {filteredAssets.length > 0 ? (
                filteredAssets.map(
                  (asset) => (
                    <label
                      className={[
                        'test-plan-asset-option',
                        asset.executionReady
                          ? ''
                          : 'test-plan-asset-option-disabled',
                      ]
                        .filter(Boolean)
                        .join(' ')}
                      key={asset.id}
                    >
                      <input
                        checked={
                          validSelectedAssetIds
                            .includes(
                              asset.id,
                            )
                        }
                        disabled={
                          !asset.executionReady
                        }
                        onChange={(event) =>
                          handleAssetToggle(
                            asset.id,
                            event.target
                              .checked,
                          )
                        }
                        type="checkbox"
                      />

                      <span>
                        <strong>
                          {asset.name}
                        </strong>

                        <small>
                          {asset.typeLabel}
                          {' · '}
                          {asset.module}
                          {' / '}
                          {asset.feature}
                        </small>

                        {!asset.executionReady && (
                          <em>
                            Not execution ready
                          </em>
                        )}
                      </span>
                    </label>
                  ),
                )
              ) : (
                <div className="test-plan-asset-empty">
                  <strong>
                    No compatible Test Assets
                  </strong>

                  <span>
                    Select a project and scope,
                    or create an execution-ready
                    Test Asset first.
                  </span>
                </div>
              )}
            </div>

            {errors.selectedAssetIds && (
              <div
                className="test-plan-form-error"
                role="alert"
              >
                {
                  errors.selectedAssetIds
                }
              </div>
            )}
          </section>

          <section className="test-plan-form-section">
            <div className="test-plan-form-section-heading">
              <h3>Execution Settings</h3>

              <p>
                Configure the default runner
                behaviour and failure policy.
              </p>
            </div>

            <div className="test-plan-form-grid">
              <label>
                <span>Execution Mode</span>

                <select
                  onChange={(event) =>
                    updateExecutionSetting(
                      'executionMode',
                      event.target.value,
                    )
                  }
                  value={
                    form.executionSettings
                      .executionMode
                  }
                >
                  {TEST_PLAN_EXECUTION_MODES.map(
                    (mode) => (
                      <option
                        key={mode}
                        value={mode}
                      >
                        {mode}
                      </option>
                    ),
                  )}
                </select>
              </label>

              <label>
                <span>Stop Policy</span>

                <select
                  onChange={(event) =>
                    updateExecutionSetting(
                      'stopPolicy',
                      event.target.value,
                    )
                  }
                  value={
                    form.executionSettings
                      .stopPolicy
                  }
                >
                  {TEST_PLAN_STOP_POLICIES.map(
                    (policy) => (
                      <option
                        key={policy}
                        value={policy}
                      >
                        {policy}
                      </option>
                    ),
                  )}
                </select>
              </label>
            </div>

            <div className="test-plan-setting-group">
              <h4>Evidence</h4>

              <div className="test-plan-option-grid">
                {evidenceOptions.map(
                  (option) => (
                    <label
                      className="test-plan-option"
                      key={option.key}
                    >
                      <input
                        checked={
                          Boolean(
                            form
                              .executionSettings[
                              option.key
                            ],
                          )
                        }
                        onChange={(event) =>
                          updateExecutionSetting(
                            option.key,
                            event.target
                              .checked,
                          )
                        }
                        type="checkbox"
                      />

                      <span>
                        <strong>
                          {option.label}
                        </strong>
                      </span>
                    </label>
                  ),
                )}
              </div>
            </div>

            <div className="test-plan-setting-group">
              <h4>Notifications</h4>

              <div className="test-plan-option-grid">
                {notificationOptions.map(
                  (option) => (
                    <label
                      className="test-plan-option"
                      key={option.key}
                    >
                      <input
                        checked={
                          Boolean(
                            form
                              .executionSettings[
                              option.key
                            ],
                          )
                        }
                        onChange={(event) =>
                          updateExecutionSetting(
                            option.key,
                            event.target
                              .checked,
                          )
                        }
                        type="checkbox"
                      />

                      <span>
                        <strong>
                          {option.label}
                        </strong>
                      </span>
                    </label>
                  ),
                )}
              </div>
            </div>
          </section>
        </div>

        <footer className="test-plan-modal-footer">
          <button
            className="button button-secondary"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>

          <button
            className="button button-primary"
            disabled={
              projects.length === 0
            }
            type="submit"
          >
            {isEditing
              ? 'Save Changes'
              : 'Create Test Plan'}
          </button>
        </footer>
      </form>
    </div>
  )
}

export default TestPlanFormModal
