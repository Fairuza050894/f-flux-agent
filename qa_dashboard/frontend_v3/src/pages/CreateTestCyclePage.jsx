import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  useNavigate,
} from 'react-router-dom'

import StatusBadge from '../components/StatusBadge'
import { useProjectEnvironmentStore } from '../stores/projectEnvironmentStore'
import { useTestCycleStore } from '../stores/testCycleStore'

const wizardSteps = [
  {
    number: 1,
    title: 'Basic Information',
    description:
      'Project, environment, and change context',
  },
  {
    number: 2,
    title: 'Test Scope',
    description:
      'UI, API, Unit, E2E, and Regression',
  },
  {
    number: 3,
    title: 'Test Assets',
    description:
      'Review recommended test definitions',
  },
  {
    number: 4,
    title: 'Execution Settings',
    description:
      'Runner, evidence, and stop policy',
  },
  {
    number: 5,
    title: 'Review',
    description:
      'Validate and run the test cycle',
  },
]

const cycleTypes = [
  'Full Product Cycle',
  'Feature Cycle',
  'Change Cycle',
]

const changeTypes = [
  'New Feature',
  'New Endpoint',
  'Endpoint Change',
  'Bug Fix',
  'Configuration Change',
  'Other Change',
]

const testScopeOptions = [
  {
    key: 'ui',
    title: 'UI Testing',
    runner: 'Browser Runner',
    description:
      'Validate pages, forms, navigation, validation, and visual behaviour.',
    assetCount: 3,
    recommended: true,
  },
  {
    key: 'api',
    title: 'API Testing',
    runner: 'API Runner',
    description:
      'Validate endpoints, status codes, payloads, authentication, and responses.',
    assetCount: 4,
    recommended: true,
  },
  {
    key: 'unit',
    title: 'Unit Testing',
    runner: 'Repository Runner',
    description:
      'Execute source-code tests and collect coverage from the connected repository.',
    assetCount: 3,
    recommended: false,
  },
  {
    key: 'e2e',
    title: 'E2E Testing',
    runner: 'Workflow Runner',
    description:
      'Validate complete business flows across interfaces and supporting services.',
    assetCount: 4,
    recommended: true,
  },
  {
    key: 'regression',
    title: 'Related Regression',
    runner: 'Regression Runner',
    description:
      'Run existing tests related to the affected module, feature, or change.',
    assetCount: 4,
    recommended: true,
  },
]

function createPreviewAssets(draft) {
  const moduleName =
    draft.module.trim() || 'Core Module'

  const featureName =
    draft.feature.trim() || 'Core Feature'

  return [
    {
      id: 'ui-001',
      type: 'ui',
      typeLabel: 'UI',
      name: `Open ${moduleName} page`,
      module: moduleName,
      feature: featureName,
      priority: 'Critical',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'ui-002',
      type: 'ui',
      typeLabel: 'UI',
      name: `Validate ${featureName} form`,
      module: moduleName,
      feature: featureName,
      priority: 'High',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'ui-003',
      type: 'ui',
      typeLabel: 'UI',
      name: `Submit valid ${featureName} data`,
      module: moduleName,
      feature: featureName,
      priority: 'Critical',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'ui-004',
      type: 'ui',
      typeLabel: 'UI',
      name: `Validate empty and invalid fields`,
      module: moduleName,
      feature: featureName,
      priority: 'High',
      automationStatus: 'Draft',
      recommended: false,
      executionReady: false,
    },
    {
      id: 'api-001',
      type: 'api',
      typeLabel: 'API',
      name: `Get ${featureName} data`,
      module: moduleName,
      feature: featureName,
      priority: 'High',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'api-002',
      type: 'api',
      typeLabel: 'API',
      name: `Create ${featureName} record`,
      module: moduleName,
      feature: featureName,
      priority: 'Critical',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'api-003',
      type: 'api',
      typeLabel: 'API',
      name: `Reject invalid ${featureName} payload`,
      module: moduleName,
      feature: featureName,
      priority: 'High',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'api-004',
      type: 'api',
      typeLabel: 'API',
      name: 'Validate unauthorized request',
      module: moduleName,
      feature: featureName,
      priority: 'Critical',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'unit-001',
      type: 'unit',
      typeLabel: 'Unit',
      name: `${featureName} service validation`,
      module: moduleName,
      feature: featureName,
      priority: 'Critical',
      automationStatus: 'Connected',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'unit-002',
      type: 'unit',
      typeLabel: 'Unit',
      name: `${featureName} business rule validation`,
      module: moduleName,
      feature: featureName,
      priority: 'High',
      automationStatus: 'Connected',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'unit-003',
      type: 'unit',
      typeLabel: 'Unit',
      name: `${featureName} repository error handling`,
      module: moduleName,
      feature: featureName,
      priority: 'Medium',
      automationStatus: 'Draft',
      recommended: false,
      executionReady: false,
    },
    {
      id: 'e2e-001',
      type: 'e2e',
      typeLabel: 'E2E',
      name: `Complete ${featureName} business flow`,
      module: moduleName,
      feature: featureName,
      priority: 'Critical',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'e2e-002',
      type: 'e2e',
      typeLabel: 'E2E',
      name: `${featureName} approval flow`,
      module: moduleName,
      feature: featureName,
      priority: 'High',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'e2e-003',
      type: 'e2e',
      typeLabel: 'E2E',
      name: `${featureName} failure recovery`,
      module: moduleName,
      feature: featureName,
      priority: 'High',
      automationStatus: 'Automated',
      recommended: false,
      executionReady: true,
    },
    {
      id: 'regression-001',
      type: 'regression',
      typeLabel: 'Regression',
      name: `${moduleName} navigation regression`,
      module: moduleName,
      feature: 'Related Module',
      priority: 'High',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'regression-002',
      type: 'regression',
      typeLabel: 'Regression',
      name: `${moduleName} data table regression`,
      module: moduleName,
      feature: 'Related Module',
      priority: 'High',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'regression-003',
      type: 'regression',
      typeLabel: 'Regression',
      name: 'Authentication and workspace regression',
      module: 'Authentication',
      feature: 'Login',
      priority: 'Critical',
      automationStatus: 'Automated',
      recommended: true,
      executionReady: true,
    },
    {
      id: 'regression-004',
      type: 'regression',
      typeLabel: 'Regression',
      name: 'Cross-module notification regression',
      module: 'Notification',
      feature: 'Message Delivery',
      priority: 'Medium',
      automationStatus: 'Automated',
      recommended: false,
      executionReady: true,
    },
  ]
}

function getPriorityTone(priority) {
  switch (priority) {
    case 'Critical':
      return 'danger'
    case 'High':
      return 'warning'
    case 'Medium':
      return 'primary'
    default:
      return 'neutral'
  }
}

function getAutomationTone(status) {
  switch (status) {
    case 'Automated':
      return 'success'
    case 'Connected':
      return 'primary'
    case 'Draft':
      return 'warning'
    default:
      return 'neutral'
  }
}

const executionModeOptions = [
  {
    value: 'Sequential',
    title: 'Sequential Execution',
    description:
      'Run each testing type one after another in a controlled order.',
    recommendation:
      'Recommended for stable debugging and limited runner capacity.',
  },
  {
    value: 'Parallel',
    title: 'Parallel Execution',
    description:
      'Run compatible testing types at the same time to reduce duration.',
    recommendation:
      'Recommended when multiple runners are available.',
  },
]

const stopPolicyOptions = [
  {
    value: 'Continue',
    title: 'Continue When Test Fails',
    description:
      'Complete all selected tests and collect every available result.',
  },
  {
    value: 'Critical Failure',
    title: 'Stop on Critical Failure',
    description:
      'Continue normal failures, but stop when a critical test fails.',
  },
  {
    value: 'Immediate',
    title: 'Stop Immediately',
    description:
      'Stop the cycle after the first failed execution.',
  },
]

const evidenceOptions = [
  {
    key: 'screenshot',
    title: 'Screenshots',
    description:
      'Capture screenshots for supported UI and E2E tests.',
  },
  {
    key: 'video',
    title: 'Video Recording',
    description:
      'Record supported browser execution sessions.',
  },
  {
    key: 'consoleLogs',
    title: 'Console Logs',
    description:
      'Collect browser console output and JavaScript errors.',
  },
  {
    key: 'networkLogs',
    title: 'Network Logs',
    description:
      'Collect failed requests and API communication details.',
  },
  {
    key: 'errorLogs',
    title: 'Error Logs',
    description:
      'Generate a consolidated error and bug log.',
  },
]

const notificationOptions = [
  {
    key: 'telegramTesting',
    title: 'Telegram Testing',
    description:
      'Send execution progress and result summary to the Testing topic.',
  },
  {
    key: 'telegramDocumentation',
    title: 'Telegram Documentation',
    description:
      'Send reports, evidence, and documentation artifacts.',
  },
]

function CreateTestCyclePage() {
  const navigate = useNavigate()

  const [errors, setErrors] =
    useState({})

  const [scopeError, setScopeError] =
    useState('')

  const [assetError, setAssetError] =
    useState('')

  const [
    assetSearchTerm,
    setAssetSearchTerm,
  ] = useState('')

  const [
    assetTypeFilter,
    setAssetTypeFilter,
  ] = useState('all')

  const [
    assetPriorityFilter,
    setAssetPriorityFilter,
  ] = useState('all')

  const [
    assetStatusFilter,
    setAssetStatusFilter,
  ] = useState('all')

  const projects =
    useProjectEnvironmentStore(
      (state) => state.projects,
    )

  const environments =
    useProjectEnvironmentStore(
      (state) => state.environments,
    )

  const selectedProjectId =
    useProjectEnvironmentStore(
      (state) => state.selectedProjectId,
    )

  const selectedEnvironmentId =
    useProjectEnvironmentStore(
      (state) =>
        state.selectedEnvironmentId,
    )

  const draft = useTestCycleStore(
    (state) => state.draft,
  )

  const currentStep = useTestCycleStore(
    (state) => state.currentStep,
  )

  const hasDraft = useTestCycleStore(
    (state) => state.hasDraft,
  )

  const startNewDraft =
    useTestCycleStore(
      (state) => state.startNewDraft,
    )

  const setDraftField =
    useTestCycleStore(
      (state) => state.setDraftField,
    )

  const setScopeField =
    useTestCycleStore(
      (state) => state.setScopeField,
    )

  const initializeAssetSelection =
    useTestCycleStore(
      (state) =>
        state.initializeAssetSelection,
    )

  const setSelectedAssetIds =
    useTestCycleStore(
      (state) =>
        state.setSelectedAssetIds,
    )

  const setExecutionField =
    useTestCycleStore(
      (state) =>
        state.setExecutionField,
    )

  const setCurrentStep =
    useTestCycleStore(
      (state) => state.setCurrentStep,
    )

  const clearDraft = useTestCycleStore(
    (state) => state.clearDraft,
  )

  useEffect(() => {
    if (!hasDraft) {
      startNewDraft(
        selectedProjectId ?? '',
        selectedEnvironmentId ?? '',
      )
    }
  }, [
    hasDraft,
    selectedEnvironmentId,
    selectedProjectId,
    startNewDraft,
  ])

  const projectEnvironments = useMemo(
    () =>
      environments.filter(
        (environment) =>
          environment.projectId ===
          draft.projectId,
      ),
    [
      draft.projectId,
      environments,
    ],
  )

  const selectedProject =
    projects.find(
      (project) =>
        project.id === draft.projectId,
    ) ?? null

  const selectedEnvironment =
    environments.find(
      (environment) =>
        environment.id ===
        draft.environmentId,
    ) ?? null

  const selectedScopeCount =
    Object.values(draft.scope).filter(Boolean)
      .length

  const selectedAssetPreviewCount =
    testScopeOptions.reduce(
      (total, option) =>
        draft.scope[option.key]
          ? total + option.assetCount
          : total,
      0,
    )

  const previewAssets = useMemo(
    () => createPreviewAssets(draft),
    [
      draft.feature,
      draft.module,
    ],
  )

  const eligibleAssets = useMemo(
    () =>
      previewAssets.filter(
        (asset) =>
          Boolean(draft.scope[asset.type]),
      ),
    [
      draft.scope,
      previewAssets,
    ],
  )

  const filteredAssets = useMemo(() => {
    const normalizedSearch =
      assetSearchTerm.trim().toLowerCase()

    return eligibleAssets.filter((asset) => {
      const matchesSearch =
        normalizedSearch.length === 0 ||
        asset.name
          .toLowerCase()
          .includes(normalizedSearch) ||
        asset.module
          .toLowerCase()
          .includes(normalizedSearch) ||
        asset.feature
          .toLowerCase()
          .includes(normalizedSearch)

      const matchesType =
        assetTypeFilter === 'all' ||
        asset.type === assetTypeFilter

      const matchesPriority =
        assetPriorityFilter === 'all' ||
        asset.priority.toLowerCase() ===
          assetPriorityFilter

      const matchesStatus =
        assetStatusFilter === 'all' ||
        asset.automationStatus
          .toLowerCase() ===
          assetStatusFilter

      return (
        matchesSearch &&
        matchesType &&
        matchesPriority &&
        matchesStatus
      )
    })
  }, [
    assetPriorityFilter,
    assetSearchTerm,
    assetStatusFilter,
    assetTypeFilter,
    eligibleAssets,
  ])

  const selectedAssetIds =
    draft.selectedAssetIds ?? []

  const selectedAssetCount =
    eligibleAssets.filter((asset) =>
      selectedAssetIds.includes(asset.id),
    ).length

  const readyAssetCount =
    eligibleAssets.filter(
      (asset) => asset.executionReady,
    ).length

  const recommendedAssetCount =
    eligibleAssets.filter(
      (asset) =>
        asset.recommended &&
        asset.executionReady,
    ).length

  useEffect(() => {
    if (
      currentStep !== 3 ||
      draft.assetSelectionInitialized
    ) {
      return
    }

    const recommendedAssetIds =
      eligibleAssets
        .filter(
          (asset) =>
            asset.recommended &&
            asset.executionReady,
        )
        .map((asset) => asset.id)

    initializeAssetSelection(
      recommendedAssetIds,
    )
  }, [
    currentStep,
    draft.assetSelectionInitialized,
    eligibleAssets,
    initializeAssetSelection,
  ])

  const selectedEvidenceCount =
    evidenceOptions.filter(
      (option) =>
        Boolean(
          draft.executionSettings[
            option.key
          ],
        ),
    ).length

  const selectedNotificationCount =
    notificationOptions.filter(
      (option) =>
        Boolean(
          draft.executionSettings[
            option.key
          ],
        ),
    ).length

  function updateField(field, value) {
    setDraftField(field, value)

    setErrors((currentErrors) => ({
      ...currentErrors,
      [field]: '',
    }))
  }

  function handleProjectChange(projectId) {
    const firstEnvironment =
      environments.find(
        (environment) =>
          environment.projectId === projectId,
      )

    updateField('projectId', projectId)

    setDraftField(
      'environmentId',
      firstEnvironment?.id ?? '',
    )
  }

  function validateStepOne() {
    const nextErrors = {}

    if (!draft.cycleName.trim()) {
      nextErrors.cycleName =
        'Cycle name is required.'
    }

    if (!draft.projectId) {
      nextErrors.projectId =
        'Project is required.'
    }

    if (!draft.environmentId) {
      nextErrors.environmentId =
        'Environment is required.'
    }

    if (!draft.cycleType) {
      nextErrors.cycleType =
        'Cycle type is required.'
    }

    if (
      draft.cycleType ===
        'Feature Cycle' &&
      !draft.module.trim()
    ) {
      nextErrors.module =
        'Module is required for a Feature Cycle.'
    }

    if (
      draft.cycleType ===
        'Feature Cycle' &&
      !draft.feature.trim()
    ) {
      nextErrors.feature =
        'Feature is required for a Feature Cycle.'
    }

    if (
      draft.cycleType ===
        'Change Cycle' &&
      !draft.reference.trim()
    ) {
      nextErrors.reference =
        'Reference is required for a Change Cycle.'
    }

    setErrors(nextErrors)

    return (
      Object.keys(nextErrors).length === 0
    )
  }

  function handleContinue(event) {
    event.preventDefault()

    if (!validateStepOne()) {
      return
    }

    setCurrentStep(2)
    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }

  function handleScopeToggle(
    scopeKey,
    checked,
  ) {
    setScopeField(scopeKey, checked)

    if (checked) {
      setScopeError('')
    }
  }

  function handleScopeContinue() {
    if (selectedScopeCount === 0) {
      setScopeError(
        'Select at least one testing scope before continuing.',
      )

      return
    }

    setScopeError('')
    setCurrentStep(3)

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }

  function handleAssetToggle(
    assetId,
    checked,
  ) {
    const nextAssetIds = checked
      ? Array.from(
          new Set([
            ...selectedAssetIds,
            assetId,
          ]),
        )
      : selectedAssetIds.filter(
          (id) => id !== assetId,
        )

    setSelectedAssetIds(nextAssetIds)

    if (checked) {
      setAssetError('')
    }
  }

  function handleSelectVisibleAssets() {
    const visibleReadyIds =
      filteredAssets
        .filter(
          (asset) => asset.executionReady,
        )
        .map((asset) => asset.id)

    setSelectedAssetIds(
      Array.from(
        new Set([
          ...selectedAssetIds,
          ...visibleReadyIds,
        ]),
      ),
    )

    setAssetError('')
  }

  function handleClearAssetSelection() {
    setSelectedAssetIds([])
  }

  function handleAssetsContinue() {
    if (selectedAssetCount === 0) {
      setAssetError(
        'Select at least one execution-ready Test Asset before continuing.',
      )

      return
    }

    setAssetError('')
    setCurrentStep(4)

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }

  function handleExecutionSettingChange(
    field,
    value,
  ) {
    setExecutionField(field, value)
  }

  function handleExecutionContinue() {
    setCurrentStep(5)

    window.scrollTo({
      top: 0,
      behavior: 'smooth',
    })
  }

  function handleDiscard() {
    const shouldDiscard =
      window.confirm(
        'Hapus draft Test Cycle dan kembali ke daftar cycle?',
      )

    if (!shouldDiscard) {
      return
    }

    clearDraft()
    navigate('/test-cycles')
  }

  return (
    <div className="dashboard-page create-cycle-page">
      <div className="page-heading-row">
        <div>
          <div className="page-heading-meta">
            <span>TESTING</span>

            <StatusBadge tone="warning">
              Draft
            </StatusBadge>
          </div>

          <h2>Create Test Cycle</h2>

          <p>
            Configure one unified test cycle for
            product, feature, endpoint, release, or
            bug-fix validation.
          </p>
        </div>

        <div className="page-heading-actions">
          <button
            className="button button-secondary"
            onClick={handleDiscard}
            type="button"
          >
            Discard Draft
          </button>

          <button
            className="button button-secondary"
            onClick={() =>
              navigate('/test-cycles')
            }
            type="button"
          >
            Save and Exit
          </button>
        </div>
      </div>

      <section
        aria-label="Test cycle wizard steps"
        className="cycle-stepper"
      >
        {wizardSteps.map((step) => {
          const isActive =
            currentStep === step.number

          const isCompleted =
            currentStep > step.number

          return (
            <div
              className={[
                'cycle-step',
                isActive
                  ? 'cycle-step-active'
                  : '',
                isCompleted
                  ? 'cycle-step-completed'
                  : '',
              ]
                .filter(Boolean)
                .join(' ')}
              key={step.number}
            >
              <div className="cycle-step-number">
                {isCompleted
                  ? '✓'
                  : step.number}
              </div>

              <div>
                <strong>{step.title}</strong>
                <span>
                  {step.description}
                </span>
              </div>
            </div>
          )
        })}
      </section>

      {currentStep === 1 ? (
        <form
          className="dashboard-panel cycle-wizard-panel"
          onSubmit={handleContinue}
        >
          <div className="cycle-wizard-heading">
            <div>
              <span className="panel-eyebrow">
                STEP 1 OF 5
              </span>

              <h3>Basic Information</h3>

              <p>
                Define the project, environment,
                cycle type, and scope context.
              </p>
            </div>

            <StatusBadge tone="primary">
              Auto-saved
            </StatusBadge>
          </div>

          <div className="cycle-form-section">
            <div className="cycle-form-section-heading">
              <h4>Cycle Identity</h4>

              <p>
                Give the execution a clear and
                searchable identity.
              </p>
            </div>

            <div className="form-grid">
              <label className="form-field form-field-full">
                <span>
                  Cycle Name
                  <strong>*</strong>
                </span>

                <input
                  aria-invalid={
                    Boolean(errors.cycleName)
                  }
                  onChange={(event) =>
                    updateField(
                      'cycleName',
                      event.target.value,
                    )
                  }
                  placeholder="Example: Uang Makan Driver Release 1.2"
                  type="text"
                  value={draft.cycleName}
                />

                {errors.cycleName && (
                  <small className="form-error">
                    {errors.cycleName}
                  </small>
                )}
              </label>

              <label className="form-field">
                <span>
                  Project
                  <strong>*</strong>
                </span>

                <select
                  aria-invalid={
                    Boolean(errors.projectId)
                  }
                  onChange={(event) =>
                    handleProjectChange(
                      event.target.value,
                    )
                  }
                  value={draft.projectId}
                >
                  <option value="">
                    Select project
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

                {errors.projectId && (
                  <small className="form-error">
                    {errors.projectId}
                  </small>
                )}
              </label>

              <label className="form-field">
                <span>
                  Environment
                  <strong>*</strong>
                </span>

                <select
                  aria-invalid={
                    Boolean(
                      errors.environmentId,
                    )
                  }
                  disabled={
                    projectEnvironments.length ===
                    0
                  }
                  onChange={(event) =>
                    updateField(
                      'environmentId',
                      event.target.value,
                    )
                  }
                  value={
                    draft.environmentId
                  }
                >
                  <option value="">
                    {projectEnvironments.length ===
                    0
                      ? 'No environment configured'
                      : 'Select environment'}
                  </option>

                  {projectEnvironments.map(
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

                {errors.environmentId && (
                  <small className="form-error">
                    {errors.environmentId}
                  </small>
                )}
              </label>

              <label className="form-field">
                <span>
                  Cycle Type
                  <strong>*</strong>
                </span>

                <select
                  onChange={(event) =>
                    updateField(
                      'cycleType',
                      event.target.value,
                    )
                  }
                  value={draft.cycleType}
                >
                  {cycleTypes.map((type) => (
                    <option
                      key={type}
                      value={type}
                    >
                      {type}
                    </option>
                  ))}
                </select>
              </label>

              <label className="form-field">
                <span>
                  Release / Version
                </span>

                <input
                  onChange={(event) =>
                    updateField(
                      'releaseVersion',
                      event.target.value,
                    )
                  }
                  placeholder="Example: 1.2.0"
                  type="text"
                  value={draft.releaseVersion}
                />
              </label>
            </div>
          </div>

          {draft.cycleType ===
            'Feature Cycle' && (
            <div className="cycle-form-section">
              <div className="cycle-form-section-heading">
                <h4>Feature Context</h4>

                <p>
                  Identify the module and feature
                  included in this cycle.
                </p>
              </div>

              <div className="form-grid">
                <label className="form-field">
                  <span>
                    Module
                    <strong>*</strong>
                  </span>

                  <input
                    aria-invalid={
                      Boolean(errors.module)
                    }
                    onChange={(event) =>
                      updateField(
                        'module',
                        event.target.value,
                      )
                    }
                    placeholder="Example: Uang Makan Driver"
                    type="text"
                    value={draft.module}
                  />

                  {errors.module && (
                    <small className="form-error">
                      {errors.module}
                    </small>
                  )}
                </label>

                <label className="form-field">
                  <span>
                    Feature
                    <strong>*</strong>
                  </span>

                  <input
                    aria-invalid={
                      Boolean(errors.feature)
                    }
                    onChange={(event) =>
                      updateField(
                        'feature',
                        event.target.value,
                      )
                    }
                    placeholder="Example: Pengecualian"
                    type="text"
                    value={draft.feature}
                  />

                  {errors.feature && (
                    <small className="form-error">
                      {errors.feature}
                    </small>
                  )}
                </label>
              </div>
            </div>
          )}

          {draft.cycleType ===
            'Change Cycle' && (
            <div className="cycle-form-section">
              <div className="cycle-form-section-heading">
                <h4>Change Context</h4>

                <p>
                  Describe the endpoint, bug fix,
                  or change being validated.
                </p>
              </div>

              <div className="form-grid">
                <label className="form-field">
                  <span>Change Type</span>

                  <select
                    onChange={(event) =>
                      updateField(
                        'changeType',
                        event.target.value,
                      )
                    }
                    value={draft.changeType}
                  >
                    {changeTypes.map((type) => (
                      <option
                        key={type}
                        value={type}
                      >
                        {type}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="form-field">
                  <span>
                    Reference
                    <strong>*</strong>
                  </span>

                  <input
                    aria-invalid={
                      Boolean(errors.reference)
                    }
                    onChange={(event) =>
                      updateField(
                        'reference',
                        event.target.value,
                      )
                    }
                    placeholder="Ticket, endpoint, PR, or bug ID"
                    type="text"
                    value={draft.reference}
                  />

                  {errors.reference && (
                    <small className="form-error">
                      {errors.reference}
                    </small>
                  )}
                </label>
              </div>
            </div>
          )}

          <div className="cycle-form-section">
            <div className="cycle-form-section-heading">
              <h4>Description</h4>

              <p>
                Add execution goals, known risks,
                or notes for reviewers.
              </p>
            </div>

            <div className="form-grid">
              <label className="form-field form-field-full">
                <span>Cycle Description</span>

                <textarea
                  onChange={(event) =>
                    updateField(
                      'description',
                      event.target.value,
                    )
                  }
                  placeholder="Describe what should be validated in this cycle."
                  rows="4"
                  value={draft.description}
                />
              </label>
            </div>
          </div>

          <div className="cycle-wizard-actions">
            <button
              className="button button-secondary"
              onClick={() =>
                navigate('/test-cycles')
              }
              type="button"
            >
              Save and Exit
            </button>

            <button
              className="button button-primary"
              type="submit"
            >
              Continue to Test Scope
            </button>
          </div>
        </form>
      ) : currentStep === 2 ? (
        <section className="dashboard-panel cycle-wizard-panel">
          <div className="cycle-wizard-heading">
            <div>
              <span className="panel-eyebrow">
                STEP 2 OF 5
              </span>

              <h3>Test Scope</h3>

              <p>
                Select the testing types included
                in this unified Test Cycle.
              </p>
            </div>

            <StatusBadge tone="primary">
              Auto-saved
            </StatusBadge>
          </div>

          <div className="cycle-form-section">
            <div className="cycle-context-summary">
              <div>
                <span>Project</span>

                <strong>
                  {selectedProject?.name ??
                    'Not selected'}
                </strong>
              </div>

              <div>
                <span>Environment</span>

                <strong>
                  {selectedEnvironment?.name ??
                    'Not selected'}
                </strong>
              </div>

              <div>
                <span>Cycle Type</span>

                <strong>
                  {draft.cycleType}
                </strong>
              </div>

              <div>
                <span>Target</span>

                <strong>
                  {draft.cycleType ===
                  'Feature Cycle'
                    ? `${draft.module} / ${draft.feature}`
                    : draft.cycleType ===
                        'Change Cycle'
                      ? draft.reference
                      : 'Full Product'}
                </strong>
              </div>
            </div>
          </div>

          <div className="cycle-form-section">
            <div className="cycle-form-section-heading">
              <h4>Select Test Scope</h4>

              <p>
                Testing runners remain modular, but
                their results will be consolidated
                into one cycle report.
              </p>
            </div>

            <div className="scope-option-grid">
              {testScopeOptions.map((option) => {
                const isSelected = Boolean(
                  draft.scope[option.key],
                )

                return (
                  <label
                    className={[
                      'scope-option',
                      isSelected
                        ? 'scope-option-selected'
                        : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    key={option.key}
                  >
                    <input
                      checked={isSelected}
                      onChange={(event) =>
                        handleScopeToggle(
                          option.key,
                          event.target.checked,
                        )
                      }
                      type="checkbox"
                    />

                    <div className="scope-option-content">
                      <div className="scope-option-heading">
                        <div>
                          <strong>
                            {option.title}
                          </strong>

                          <span>
                            {option.runner}
                          </span>
                        </div>

                        {option.recommended && (
                          <StatusBadge tone="primary">
                            Recommended
                          </StatusBadge>
                        )}
                      </div>

                      <p>
                        {option.description}
                      </p>

                      <div className="scope-option-footer">
                        <span>
                          Available assets
                        </span>

                        <strong>
                          {option.assetCount}
                        </strong>
                      </div>
                    </div>
                  </label>
                )
              })}
            </div>

            {scopeError && (
              <div
                className="scope-validation-message"
                role="alert"
              >
                {scopeError}
              </div>
            )}
          </div>

          <div className="cycle-scope-summary">
            <div>
              <span>Selected test types</span>

              <strong>
                {selectedScopeCount} of{' '}
                {testScopeOptions.length}
              </strong>
            </div>

            <div>
              <span>
                Preview available assets
              </span>

              <strong>
                {selectedAssetPreviewCount}
              </strong>
            </div>

            <div>
              <span>Execution result</span>

              <strong>
                One consolidated cycle
              </strong>
            </div>
          </div>

          <div className="cycle-wizard-actions">
            <button
              className="button button-secondary"
              onClick={() => setCurrentStep(1)}
              type="button"
            >
              Back to Basic Information
            </button>

            <button
              className="button button-primary"
              onClick={handleScopeContinue}
              type="button"
            >
              Continue to Test Assets
            </button>
          </div>
        </section>
      ) : currentStep === 3 ? (
        <section className="dashboard-panel cycle-wizard-panel">
          <div className="cycle-wizard-heading">
            <div>
              <span className="panel-eyebrow">
                STEP 3 OF 5
              </span>

              <h3>Test Assets</h3>

              <p>
                Review and select reusable tests
                included in this Test Cycle.
              </p>
            </div>

            <StatusBadge tone="primary">
              Auto-saved
            </StatusBadge>
          </div>

          <div className="cycle-form-section">
            <div className="cycle-context-summary">
              <div>
                <span>Available Assets</span>

                <strong>
                  {eligibleAssets.length}
                </strong>
              </div>

              <div>
                <span>Execution Ready</span>

                <strong>
                  {readyAssetCount}
                </strong>
              </div>

              <div>
                <span>Recommended</span>

                <strong>
                  {recommendedAssetCount}
                </strong>
              </div>

              <div>
                <span>Selected</span>

                <strong>
                  {selectedAssetCount}
                </strong>
              </div>
            </div>
          </div>

          <div className="cycle-form-section">
            <div className="asset-toolbar">
              <div>
                <h4>Recommended Test Assets</h4>

                <p>
                  Assets are filtered from the
                  selected testing scope.
                </p>
              </div>

              <div className="asset-toolbar-actions">
                <button
                  className="button button-secondary"
                  onClick={
                    handleClearAssetSelection
                  }
                  type="button"
                >
                  Clear Selection
                </button>

                <button
                  className="button button-secondary"
                  onClick={
                    handleSelectVisibleAssets
                  }
                  type="button"
                >
                  Select Visible
                </button>
              </div>
            </div>

            <div className="asset-filter-grid">
              <label>
                <span className="sr-only">
                  Search test assets
                </span>

                <input
                  onChange={(event) =>
                    setAssetSearchTerm(
                      event.target.value,
                    )
                  }
                  placeholder="Search asset..."
                  type="search"
                  value={assetSearchTerm}
                />
              </label>

              <label>
                <span className="sr-only">
                  Filter asset type
                </span>

                <select
                  onChange={(event) =>
                    setAssetTypeFilter(
                      event.target.value,
                    )
                  }
                  value={assetTypeFilter}
                >
                  <option value="all">
                    All types
                  </option>

                  {testScopeOptions
                    .filter(
                      (option) =>
                        draft.scope[
                          option.key
                        ],
                    )
                    .map((option) => (
                      <option
                        key={option.key}
                        value={option.key}
                      >
                        {option.title}
                      </option>
                    ))}
                </select>
              </label>

              <label>
                <span className="sr-only">
                  Filter asset priority
                </span>

                <select
                  onChange={(event) =>
                    setAssetPriorityFilter(
                      event.target.value,
                    )
                  }
                  value={assetPriorityFilter}
                >
                  <option value="all">
                    All priorities
                  </option>

                  <option value="critical">
                    Critical
                  </option>

                  <option value="high">
                    High
                  </option>

                  <option value="medium">
                    Medium
                  </option>
                </select>
              </label>

              <label>
                <span className="sr-only">
                  Filter automation status
                </span>

                <select
                  onChange={(event) =>
                    setAssetStatusFilter(
                      event.target.value,
                    )
                  }
                  value={assetStatusFilter}
                >
                  <option value="all">
                    All statuses
                  </option>

                  <option value="automated">
                    Automated
                  </option>

                  <option value="connected">
                    Connected
                  </option>

                  <option value="draft">
                    Draft
                  </option>
                </select>
              </label>
            </div>

            <div className="asset-table-wrapper">
              <table className="asset-table">
                <thead>
                  <tr>
                    <th aria-label="Selection" />
                    <th>Test Asset</th>
                    <th>Type</th>
                    <th>Module / Feature</th>
                    <th>Priority</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredAssets.length > 0 ? (
                    filteredAssets.map((asset) => (
                      <tr
                        className={
                          asset.executionReady
                            ? ''
                            : 'asset-row-disabled'
                        }
                        key={asset.id}
                      >
                        <td>
                          <input
                            aria-label={`Select ${asset.name}`}
                            checked={selectedAssetIds.includes(
                              asset.id,
                            )}
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
                        </td>

                        <td>
                          <strong>
                            {asset.name}
                          </strong>

                          <span>{asset.id}</span>
                        </td>

                        <td>
                          <StatusBadge tone="neutral">
                            {asset.typeLabel}
                          </StatusBadge>
                        </td>

                        <td>
                          <strong>
                            {asset.module}
                          </strong>

                          <span>
                            {asset.feature}
                          </span>
                        </td>

                        <td>
                          <StatusBadge
                            tone={getPriorityTone(
                              asset.priority,
                            )}
                          >
                            {asset.priority}
                          </StatusBadge>
                        </td>

                        <td>
                          <StatusBadge
                            tone={getAutomationTone(
                              asset.automationStatus,
                            )}
                          >
                            {
                              asset.automationStatus
                            }
                          </StatusBadge>

                          {!asset.executionReady && (
                            <span className="asset-not-ready">
                              Not execution ready
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        className="asset-empty-cell"
                        colSpan="6"
                      >
                        No Test Assets match the
                        current filters.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {assetError && (
              <div
                className="scope-validation-message"
                role="alert"
              >
                {assetError}
              </div>
            )}
          </div>

          <div className="cycle-scope-summary">
            <div>
              <span>Selected Assets</span>

              <strong>
                {selectedAssetCount}
              </strong>
            </div>

            <div>
              <span>Testing Types</span>

              <strong>
                {selectedScopeCount}
              </strong>
            </div>

            <div>
              <span>Result</span>

              <strong>
                Consolidated Report
              </strong>
            </div>
          </div>

          <div className="cycle-wizard-actions">
            <button
              className="button button-secondary"
              onClick={() => setCurrentStep(2)}
              type="button"
            >
              Back to Test Scope
            </button>

            <button
              className="button button-primary"
              onClick={handleAssetsContinue}
              type="button"
            >
              Continue to Execution Settings
            </button>
          </div>
        </section>
      ) : currentStep === 4 ? (
        <section className="dashboard-panel cycle-wizard-panel">
          <div className="cycle-wizard-heading">
            <div>
              <span className="panel-eyebrow">
                STEP 4 OF 5
              </span>

              <h3>Execution Settings</h3>

              <p>
                Configure runner behaviour, failure
                policy, evidence, and notifications.
              </p>
            </div>

            <StatusBadge tone="primary">
              Auto-saved
            </StatusBadge>
          </div>

          <div className="cycle-form-section">
            <div className="cycle-context-summary">
              <div>
                <span>Selected Assets</span>

                <strong>
                  {selectedAssetCount}
                </strong>
              </div>

              <div>
                <span>Test Types</span>

                <strong>
                  {selectedScopeCount}
                </strong>
              </div>

              <div>
                <span>Project</span>

                <strong>
                  {selectedProject?.name ??
                    'Not selected'}
                </strong>
              </div>

              <div>
                <span>Environment</span>

                <strong>
                  {selectedEnvironment?.name ??
                    'Not selected'}
                </strong>
              </div>
            </div>
          </div>

          <div className="cycle-form-section">
            <div className="cycle-form-section-heading">
              <h4>Execution Mode</h4>

              <p>
                Choose how the selected testing
                runners should be executed.
              </p>
            </div>

            <div className="execution-option-grid">
              {executionModeOptions.map((option) => {
                const isSelected =
                  draft.executionSettings
                    .executionMode === option.value

                return (
                  <label
                    className={[
                      'execution-option',
                      isSelected
                        ? 'execution-option-selected'
                        : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    key={option.value}
                  >
                    <input
                      checked={isSelected}
                      name="executionMode"
                      onChange={() =>
                        handleExecutionSettingChange(
                          'executionMode',
                          option.value,
                        )
                      }
                      type="radio"
                    />

                    <div>
                      <strong>{option.title}</strong>

                      <p>{option.description}</p>

                      <span>
                        {option.recommendation}
                      </span>
                    </div>
                  </label>
                )
              })}
            </div>
          </div>

          <div className="cycle-form-section">
            <div className="cycle-form-section-heading">
              <h4>Failure Stop Policy</h4>

              <p>
                Define what the cycle should do
                after a failed test.
              </p>
            </div>

            <div className="stop-policy-list">
              {stopPolicyOptions.map((option) => {
                const isSelected =
                  draft.executionSettings
                    .stopPolicy === option.value

                return (
                  <label
                    className={[
                      'stop-policy-option',
                      isSelected
                        ? 'stop-policy-option-selected'
                        : '',
                    ]
                      .filter(Boolean)
                      .join(' ')}
                    key={option.value}
                  >
                    <input
                      checked={isSelected}
                      name="stopPolicy"
                      onChange={() =>
                        handleExecutionSettingChange(
                          'stopPolicy',
                          option.value,
                        )
                      }
                      type="radio"
                    />

                    <div>
                      <strong>{option.title}</strong>

                      <p>{option.description}</p>
                    </div>
                  </label>
                )
              })}
            </div>
          </div>

          <div className="cycle-form-section execution-settings-columns">
            <div>
              <div className="cycle-form-section-heading">
                <h4>Execution Evidence</h4>

                <p>
                  Select the artifacts collected
                  during execution.
                </p>
              </div>

              <div className="execution-checkbox-list">
                {evidenceOptions.map((option) => (
                  <label
                    className="execution-checkbox-option"
                    key={option.key}
                  >
                    <input
                      checked={Boolean(
                        draft.executionSettings[
                          option.key
                        ],
                      )}
                      onChange={(event) =>
                        handleExecutionSettingChange(
                          option.key,
                          event.target.checked,
                        )
                      }
                      type="checkbox"
                    />

                    <div>
                      <strong>{option.title}</strong>

                      <p>{option.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <div className="cycle-form-section-heading">
                <h4>Notifications</h4>

                <p>
                  Select where execution updates
                  and artifacts will be sent.
                </p>
              </div>

              <div className="execution-checkbox-list">
                {notificationOptions.map((option) => (
                  <label
                    className="execution-checkbox-option"
                    key={option.key}
                  >
                    <input
                      checked={Boolean(
                        draft.executionSettings[
                          option.key
                        ],
                      )}
                      onChange={(event) =>
                        handleExecutionSettingChange(
                          option.key,
                          event.target.checked,
                        )
                      }
                      type="checkbox"
                    />

                    <div>
                      <strong>{option.title}</strong>

                      <p>{option.description}</p>
                    </div>
                  </label>
                ))}
              </div>

              <div className="execution-notification-note">
                <strong>
                  Notification configuration
                </strong>

                <p>
                  Telegram thread IDs and credentials
                  remain managed by backend configuration.
                </p>
              </div>
            </div>
          </div>

          <div className="cycle-scope-summary">
            <div>
              <span>Execution Mode</span>

              <strong>
                {
                  draft.executionSettings
                    .executionMode
                }
              </strong>
            </div>

            <div>
              <span>Evidence Types</span>

              <strong>
                {selectedEvidenceCount}
              </strong>
            </div>

            <div>
              <span>Notifications</span>

              <strong>
                {selectedNotificationCount}
              </strong>
            </div>
          </div>

          <div className="cycle-wizard-actions">
            <button
              className="button button-secondary"
              onClick={() => setCurrentStep(3)}
              type="button"
            >
              Back to Test Assets
            </button>

            <button
              className="button button-primary"
              onClick={handleExecutionContinue}
              type="button"
            >
              Continue to Review
            </button>
          </div>
        </section>
      ) : (
        <section className="dashboard-panel cycle-placeholder-panel">
          <span className="panel-eyebrow">
            STEP {currentStep} OF 5
          </span>

          <h3>
            {
              wizardSteps.find(
                (step) =>
                  step.number ===
                  currentStep,
              )?.title
            }
          </h3>

          <p>
            Fondasi wizard sudah berfungsi.
            Isi lengkap tahap ini akan dibangun
            pada langkah berikutnya.
          </p>

          <div className="cycle-placeholder-actions">
            <button
              className="button button-secondary"
              onClick={() =>
                setCurrentStep(
                  Math.max(
                    1,
                    currentStep - 1,
                  ),
                )
              }
              type="button"
            >
              Back
            </button>

            <button
              className="button button-primary"
              disabled
              type="button"
            >
              Next Step
            </button>
          </div>
        </section>
      )}
    </div>
  )
}

export default CreateTestCyclePage
