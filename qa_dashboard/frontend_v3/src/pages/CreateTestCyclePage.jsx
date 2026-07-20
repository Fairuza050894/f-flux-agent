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

function CreateTestCyclePage() {
  const navigate = useNavigate()

  const [errors, setErrors] =
    useState({})

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
