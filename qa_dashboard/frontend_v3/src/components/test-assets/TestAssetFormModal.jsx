import {
  useState,
} from 'react'

import {
  TEST_ASSET_AUTOMATION_STATUSES,
  TEST_ASSET_EMPTY_FORM,
  TEST_ASSET_PRIORITIES,
  TEST_ASSET_TYPES,
} from '../../features/test-assets/testAssetConstants'

function createInitialForm(
  initialAsset,
) {
  return {
    ...TEST_ASSET_EMPTY_FORM,
    ...(initialAsset ?? {}),
  }
}

function validateForm(
  form,
  steps,
  {
    changeSummary = '',
    isEditing = false,
  } = {},
) {
  const errors = {}

  if (!form.projectId) {
    errors.projectId =
      'Select a project.'
  }

  if (!form.name.trim()) {
    errors.name =
      'Test Asset name is required.'
  }

  if (!form.module.trim()) {
    errors.module =
      'Module is required.'
  }

  if (!form.feature.trim()) {
    errors.feature =
      'Feature is required.'
  }

  if (
    form.executionReady &&
    steps.length === 0
  ) {
    errors.steps =
      'Add at least one test step before marking this asset as execution ready.'
  }

  if (
    form.executionReady &&
    !form.expectedResult.trim()
  ) {
    errors.expectedResult =
      'Expected result is required for an execution-ready asset.'
  }

  if (
    isEditing &&
    !changeSummary.trim()
  ) {
    errors.changeSummary =
      'Describe what changed in this version.'
  }

  return errors
}

function TestAssetFormModal({
  initialAsset = null,
  onClose,
  onSubmit,
  projects,
}) {
  const [form, setForm] =
    useState(() =>
      createInitialForm(
        initialAsset,
      ),
    )

  const [stepsText, setStepsText] =
    useState(() =>
      Array.isArray(
        initialAsset?.steps,
      )
        ? initialAsset.steps.join(
            '\n',
          )
        : '',
    )

  const [errors, setErrors] =
    useState({})

  const isEditing =
    Boolean(initialAsset?.id)

  const [
    changeSummary,
    setChangeSummary,
  ] = useState('')

  function updateField(
    field,
    value,
  ) {
    setForm((currentForm) => ({
      ...currentForm,
      [field]: value,
    }))

    setErrors((currentErrors) => ({
      ...currentErrors,
      [field]: '',
    }))
  }

  function handleStepsChange(
    value,
  ) {
    setStepsText(value)

    setErrors((currentErrors) => ({
      ...currentErrors,
      steps: '',
    }))
  }

  function handleSubmit(event) {
    event.preventDefault()

    const steps =
      stepsText
        .split('\n')
        .map((step) =>
          step.trim(),
        )
        .filter(Boolean)

    const nextErrors =
      validateForm(
        form,
        steps,
        {
          changeSummary,
          isEditing,
        },
      )

    if (
      Object.keys(
        nextErrors,
      ).length > 0
    ) {
      setErrors(nextErrors)
      return
    }

    const submission = {
      ...form,

      name:
        form.name.trim(),

      module:
        form.module.trim(),

      feature:
        form.feature.trim(),

      description:
        form.description.trim(),

      preconditions:
        form.preconditions.trim(),

      expectedResult:
        form.expectedResult.trim(),

      steps,
    }

    if (isEditing) {
      submission.changeSummary =
        changeSummary.trim()
    }

    onSubmit(submission)
  }

  return (
    <div
      aria-labelledby="test-asset-modal-title"
      aria-modal="true"
      className="test-asset-modal-overlay"
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
        className="test-asset-modal"
        onSubmit={handleSubmit}
      >
        <header className="test-asset-modal-header">
          <div>
            <span className="panel-eyebrow">
              TEST ASSET
            </span>

            <h2 id="test-asset-modal-title">
              {isEditing
                ? 'Edit Test Asset'
                : 'Create Test Asset'}
            </h2>

            <p>
              Define a reusable test that
              can be selected in a Test
              Cycle.
            </p>
          </div>

          <button
            aria-label="Close Test Asset form"
            className="button button-secondary"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        </header>

        <div className="test-asset-modal-body">
          <section className="test-asset-form-section">
            <div className="test-asset-form-section-heading">
              <h3>Asset Information</h3>

              <p>
                Identify the project, testing
                type, module, and feature.
              </p>
            </div>

            <div className="test-asset-form-grid">
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
                    updateField(
                      'projectId',
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
                  Test Type
                  <em>*</em>
                </span>

                <select
                  onChange={(event) =>
                    updateField(
                      'type',
                      event.target.value,
                    )
                  }
                  value={form.type}
                >
                  {TEST_ASSET_TYPES.map(
                    (option) => (
                      <option
                        key={option.value}
                        value={option.value}
                      >
                        {option.label}
                      </option>
                    ),
                  )}
                </select>
              </label>

              <label className="test-asset-form-wide">
                <span>
                  Test Asset Name
                  <em>*</em>
                </span>

                <input
                  aria-invalid={
                    Boolean(errors.name)
                  }
                  autoFocus
                  maxLength="160"
                  onChange={(event) =>
                    updateField(
                      'name',
                      event.target.value,
                    )
                  }
                  placeholder="Example: Submit valid driver allowance request"
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
                  Module
                  <em>*</em>
                </span>

                <input
                  aria-invalid={
                    Boolean(errors.module)
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
                  <em>*</em>
                </span>

                <input
                  aria-invalid={
                    Boolean(errors.feature)
                  }
                  maxLength="120"
                  onChange={(event) =>
                    updateField(
                      'feature',
                      event.target.value,
                    )
                  }
                  placeholder="Example: Tambah Pengecualian"
                  type="text"
                  value={form.feature}
                />

                {errors.feature && (
                  <small role="alert">
                    {errors.feature}
                  </small>
                )}
              </label>

              <label>
                <span>Priority</span>

                <select
                  onChange={(event) =>
                    updateField(
                      'priority',
                      event.target.value,
                    )
                  }
                  value={form.priority}
                >
                  {TEST_ASSET_PRIORITIES.map(
                    (priority) => (
                      <option
                        key={priority}
                        value={priority}
                      >
                        {priority}
                      </option>
                    ),
                  )}
                </select>
              </label>

              <label>
                <span>
                  Automation Status
                </span>

                <select
                  onChange={(event) =>
                    updateField(
                      'automationStatus',
                      event.target.value,
                    )
                  }
                  value={
                    form.automationStatus
                  }
                >
                  {TEST_ASSET_AUTOMATION_STATUSES.map(
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
            </div>
          </section>

          <section className="test-asset-form-section">
            <div className="test-asset-form-section-heading">
              <h3>Test Definition</h3>

              <p>
                Document the preparation,
                execution steps, and expected
                outcome.
              </p>
            </div>

            <div className="test-asset-form-grid">
              <label className="test-asset-form-wide">
                <span>Description</span>

                <textarea
                  maxLength="1000"
                  onChange={(event) =>
                    updateField(
                      'description',
                      event.target.value,
                    )
                  }
                  placeholder="Describe the purpose and coverage of this Test Asset."
                  rows="3"
                  value={form.description}
                />
              </label>

              <label className="test-asset-form-wide">
                <span>Preconditions</span>

                <textarea
                  maxLength="1000"
                  onChange={(event) =>
                    updateField(
                      'preconditions',
                      event.target.value,
                    )
                  }
                  placeholder="Describe required data, user role, login state, or environment."
                  rows="3"
                  value={form.preconditions}
                />
              </label>

              <label className="test-asset-form-wide">
                <span>
                  Test Steps
                  {form.executionReady && (
                    <em>*</em>
                  )}
                </span>

                <textarea
                  aria-invalid={
                    Boolean(errors.steps)
                  }
                  onChange={(event) =>
                    handleStepsChange(
                      event.target.value,
                    )
                  }
                  placeholder={'Enter one step per line.\nExample:\nOpen Monitoring > Pengecualian\nClick Tambah Pengecualian\nComplete all required fields'}
                  rows="7"
                  value={stepsText}
                />

                <small className="test-asset-field-help">
                  Each non-empty line will
                  become one test step.
                </small>

                {errors.steps && (
                  <small role="alert">
                    {errors.steps}
                  </small>
                )}
              </label>

              <label className="test-asset-form-wide">
                <span>
                  Expected Result
                  {form.executionReady && (
                    <em>*</em>
                  )}
                </span>

                <textarea
                  aria-invalid={
                    Boolean(
                      errors.expectedResult,
                    )
                  }
                  maxLength="1500"
                  onChange={(event) =>
                    updateField(
                      'expectedResult',
                      event.target.value,
                    )
                  }
                  placeholder="Describe the expected system response and final state."
                  rows="4"
                  value={
                    form.expectedResult
                  }
                />

                {errors.expectedResult && (
                  <small role="alert">
                    {
                      errors.expectedResult
                    }
                  </small>
                )}
              </label>
            </div>
          </section>

          <section className="test-asset-form-section">
            <div className="test-asset-form-section-heading">
              <h3>Availability</h3>

              <p>
                Control recommendation and
                execution readiness.
              </p>
            </div>

            <div className="test-asset-option-grid">
              <label className="test-asset-option">
                <input
                  checked={form.recommended}
                  onChange={(event) =>
                    updateField(
                      'recommended',
                      event.target.checked,
                    )
                  }
                  type="checkbox"
                />

                <span>
                  <strong>
                    Recommended
                  </strong>

                  <small>
                    Automatically recommend
                    this asset for compatible
                    Test Cycles.
                  </small>
                </span>
              </label>

              <label className="test-asset-option">
                <input
                  checked={
                    form.executionReady
                  }
                  onChange={(event) =>
                    updateField(
                      'executionReady',
                      event.target.checked,
                    )
                  }
                  type="checkbox"
                />

                <span>
                  <strong>
                    Execution Ready
                  </strong>

                  <small>
                    Allow this asset to be
                    selected and executed in
                    a Test Cycle.
                  </small>
                </span>
              </label>
            </div>
          </section>
          {isEditing && (
            <section className="test-asset-form-section test-asset-version-summary">
              <div className="test-asset-form-section-heading">
                <h3>Version Change</h3>

                <p>
                  Saving this edit creates
                  Test Asset version{' '}
                  {Number(
                    initialAsset
                      ?.currentVersionNumber ??
                      1,
                  ) + 1}
                  .
                </p>
              </div>

              <div className="test-asset-form-grid">
                <label className="test-asset-form-wide">
                  <span>
                    Change Summary
                    <em>*</em>
                  </span>

                  <textarea
                    aria-invalid={
                      Boolean(
                        errors.changeSummary,
                      )
                    }
                    maxLength="300"
                    onChange={(event) => {
                      setChangeSummary(
                        event.target.value,
                      )

                      setErrors(
                        (
                          currentErrors,
                        ) => ({
                          ...currentErrors,
                          changeSummary: '',
                        }),
                      )
                    }}
                    placeholder="Example: Added validation for the maximum Reason length."
                    rows="3"
                    value={changeSummary}
                  />

                  <small className="test-asset-field-help">
                    Explain the functional or
                    documentation changes made
                    in this version.
                  </small>

                  {errors.changeSummary && (
                    <small role="alert">
                      {
                        errors.changeSummary
                      }
                    </small>
                  )}
                </label>
              </div>
            </section>
          )}
        </div>

        <footer className="test-asset-modal-footer">
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
              : 'Create Test Asset'}
          </button>
        </footer>
      </form>
    </div>
  )
}

export default TestAssetFormModal
