import { create } from 'zustand'
import {
  createJSONStorage,
  persist,
} from 'zustand/middleware'

import {
  captureTestPlanAssetSnapshots,
  normalizeTestPlanAssetSnapshots,
} from '../features/test-planning/testPlanAssetSnapshots'
import {
  selectLatestExecutionsByScope,
} from '../features/executions/executionAttemptSelectors'

const TEST_CYCLE_STORE_VERSION = 2

function createEmptyDraft(
  projectId = '',
  environmentId = '',
) {
  return {
    cycleName: '',
    projectId,
    environmentId,
    cycleType: 'Feature Cycle',
    releaseVersion: '',
    module: '',
    feature: '',
    changeType: 'New Feature',
    reference: '',
    description: '',
    sourcePlanId: '',

    scope: {
      ui: true,
      api: true,
      unit: false,
      e2e: true,
      regression: true,
    },

    selectedAssetIds: [],
    selectedAssetSnapshots: [],
    assetSelectionInitialized: false,

    executionSettings: {
      executionMode: 'Sequential',
      stopPolicy: 'Critical Failure',
      screenshot: true,
      video: false,
      consoleLogs: true,
      networkLogs: true,
      errorLogs: true,
      telegramTesting: true,
      telegramDocumentation: true,
    },

    createdAt: null,
    updatedAt: null,
  }
}

function createCycleId() {
  const now = new Date()

  const datePart = now
    .toISOString()
    .slice(0, 10)
    .replaceAll('-', '')

  const timePart = now
    .toTimeString()
    .slice(0, 8)
    .replaceAll(':', '')

  return `TC-${datePart}-${timePart}`
}

function normalizeExecutionStatus(status) {
  return String(status ?? '')
    .trim()
    .toLowerCase()
    .replaceAll(' ', '_')
}

function summarizeCycleExecutions(
  executions,
) {
  if (!Array.isArray(executions)) {
    return {
      status: 'Ready',
      progress: 0,
    }
  }

  if (executions.length === 0) {
    return {
      status: 'Ready',
      progress: 0,
    }
  }

  const currentExecutions =
    selectLatestExecutionsByScope(
      executions,
    )

  const statuses = currentExecutions.map(
    (execution) =>
      normalizeExecutionStatus(
        execution.status,
      ),
  )

  const progress = Math.round(
    currentExecutions.reduce(
      (total, execution) =>
        total +
        Number(
          execution.progress ?? 0,
        ),
      0,
    ) / currentExecutions.length,
  )

  if (
    statuses.some((status) =>
      [
        'running',
        'in_progress',
        'processing',
      ].includes(status),
    )
  ) {
    return {
      status: 'Running',
      progress,
    }
  }

  if (
    statuses.some((status) =>
      [
        'queued',
        'pending',
        'created',
        'not_started',
      ].includes(status),
    )
  ) {
    return {
      status: 'Queued',
      progress,
    }
  }

  if (
    statuses.some((status) =>
      [
        'failed',
        'error',
      ].includes(status),
    )
  ) {
    return {
      status: 'Failed',
      progress,
    }
  }

  if (
    statuses.some(
      (status) =>
        status === 'need_review',
    )
  ) {
    return {
      status: 'Need Review',
      progress,
    }
  }

  if (
    statuses.some(
      (status) =>
        status === 'cancelled',
    )
  ) {
    return {
      status: 'Cancelled',
      progress,
    }
  }

  if (
    statuses.every(
      (status) =>
        status === 'passed',
    )
  ) {
    return {
      status: 'Passed',
      progress,
    }
  }

  return {
    status: 'Completed',
    progress,
  }
}

function normalizeAssetIds(
  assetIds,
) {
  if (!Array.isArray(assetIds)) {
    return []
  }

  return Array.from(
    new Set(
      assetIds
        .map((assetId) =>
          String(assetId ?? '').trim(),
        )
        .filter(Boolean),
    ),
  )
}

function filterSnapshots({
  selectedAssetIds = [],
  snapshots = [],
} = {}) {
  const selectedIds =
    new Set(
      normalizeAssetIds(
        selectedAssetIds,
      ),
    )

  return normalizeTestPlanAssetSnapshots(
    snapshots,
  ).filter(
    (record) =>
      selectedIds.has(
        record.assetId,
      ),
  )
}

function resolveSnapshots({
  assets = [],
  capturedAt,
  existingSnapshots = [],
  selectedAssetIds = [],
} = {}) {
  const normalizedIds =
    normalizeAssetIds(
      selectedAssetIds,
    )

  const existingById =
    new Map(
      filterSnapshots({
        selectedAssetIds:
          normalizedIds,
        snapshots:
          existingSnapshots,
      }).map((record) => [
        record.assetId,
        record,
      ]),
    )

  const capturedById =
    new Map(
      captureTestPlanAssetSnapshots({
        assets,
        capturedAt,
        selectedAssetIds:
          normalizedIds,
      }).map((record) => [
        record.assetId,
        record,
      ]),
    )

  return normalizedIds
    .map(
      (assetId) =>
        existingById.get(
          assetId,
        ) ??
        capturedById.get(
          assetId,
        ) ??
        null,
    )
    .filter(Boolean)
}

function normalizeDraft(
  draft,
) {
  const selectedAssetIds =
    normalizeAssetIds(
      draft?.selectedAssetIds,
    )

  return {
    ...createEmptyDraft(
      draft?.projectId ?? '',
      draft?.environmentId ?? '',
    ),
    ...(draft ?? {}),
    selectedAssetIds,
    selectedAssetSnapshots:
      filterSnapshots({
        selectedAssetIds,
        snapshots:
          draft?.selectedAssetSnapshots,
      }),
  }
}

function normalizeCycle(
  cycle,
) {
  if (
    !cycle ||
    typeof cycle !== 'object'
  ) {
    return null
  }

  const selectedAssetIds =
    normalizeAssetIds(
      cycle.selectedAssetIds,
    )

  return {
    ...cycle,
    selectedAssetIds,
    selectedAssetSnapshots:
      filterSnapshots({
        selectedAssetIds,
        snapshots:
          cycle.selectedAssetSnapshots,
      }),
  }
}

function normalizeCycles(
  cycles,
) {
  return Array.isArray(cycles)
    ? cycles
        .map(normalizeCycle)
        .filter(Boolean)
    : []
}

function migrateTestCycleState(
  persistedState,
) {
  const state =
    persistedState &&
    typeof persistedState ===
      'object'
      ? persistedState
      : {}

  return {
    ...state,
    draft:
      normalizeDraft(
        state.draft,
      ),
    cycles:
      normalizeCycles(
        state.cycles,
      ),
  }
}

export const useTestCycleStore = create(
  persist(
    (set, get) => ({
      draft: createEmptyDraft(),
      cycles: [],
      currentStep: 1,
      hasDraft: false,
      lastCreatedCycleId: null,

      startNewDraft: (
        projectId,
        environmentId,
      ) => {
        const timestamp =
          new Date().toISOString()

        set({
          draft: {
            ...createEmptyDraft(
              projectId,
              environmentId,
            ),
            createdAt: timestamp,
            updatedAt: timestamp,
          },
          currentStep: 1,
          hasDraft: true,
        })
      },

      startDraftFromPlan: ({
        plan,
        selectedAssetIds = [],
      }) => {
        const timestamp =
          new Date().toISOString()

        const defaultDraft =
          createEmptyDraft(
            plan?.projectId ?? '',
            plan?.environmentId ?? '',
          )

        const validAssetIds =
          Array.from(
            new Set(
              Array.isArray(
                selectedAssetIds,
              )
                ? selectedAssetIds
                : [],
            ),
          )

        const inheritedSnapshots =
          filterSnapshots({
            selectedAssetIds:
              validAssetIds,
            snapshots:
              plan?.selectedAssetSnapshots,
          })

        set({
          draft: {
            ...defaultDraft,

            cycleName:
              String(
                plan?.name ?? '',
              ).trim(),

            projectId:
              String(
                plan?.projectId ?? '',
              ),

            environmentId:
              String(
                plan?.environmentId ?? '',
              ),

            cycleType:
              plan?.cycleType ??
              defaultDraft.cycleType,

            module:
              String(
                plan?.module ?? '',
              ).trim(),

            feature:
              String(
                plan?.feature ?? '',
              ).trim(),

            reference:
              String(
                plan?.id ?? '',
              ),

            description:
              String(
                plan?.objective ?? '',
              ).trim(),

            sourcePlanId:
              String(
                plan?.id ?? '',
              ),

            scope: {
              ...defaultDraft.scope,
              ...(plan?.scope ?? {}),
            },

            selectedAssetIds:
              validAssetIds,

            selectedAssetSnapshots:
              inheritedSnapshots,

            assetSelectionInitialized:
              true,

            executionSettings: {
              ...defaultDraft
                .executionSettings,

              ...(plan
                ?.executionSettings ??
                {}),
            },

            createdAt: timestamp,
            updatedAt: timestamp,
          },

          currentStep: 1,
          hasDraft: true,
        })
      },

      setDraftField: (field, value) => {
        set((state) => ({
          draft: {
            ...state.draft,
            [field]: value,
            updatedAt:
              new Date().toISOString(),
          },
          hasDraft: true,
        }))
      },

      setScopeField: (field, value) => {
        set((state) => ({
          draft: {
            ...state.draft,
            scope: {
              ...state.draft.scope,
              [field]: value,
            },
            selectedAssetIds: [],
            selectedAssetSnapshots: [],
            assetSelectionInitialized: false,
            updatedAt:
              new Date().toISOString(),
          },
          hasDraft: true,
        }))
      },

      resetAssetSelection: () => {
        set((state) => ({
          draft: {
            ...state.draft,
            selectedAssetIds: [],
            selectedAssetSnapshots: [],
            assetSelectionInitialized:
              false,
            updatedAt:
              new Date().toISOString(),
          },
          hasDraft: true,
        }))
      },

      initializeAssetSelection: (
        assetIds,
      ) => {
        set((state) => ({
          draft: {
            ...state.draft,
            selectedAssetIds:
              normalizeAssetIds(
                assetIds,
              ),
            selectedAssetSnapshots:
              filterSnapshots({
                selectedAssetIds:
                  assetIds,
                snapshots:
                  state.draft
                    .selectedAssetSnapshots,
              }),
            assetSelectionInitialized: true,
            updatedAt:
              new Date().toISOString(),
          },
          hasDraft: true,
        }))
      },

      setSelectedAssetIds: (
        assetIds,
      ) => {
        set((state) => ({
          draft: {
            ...state.draft,
            selectedAssetIds: assetIds,
            assetSelectionInitialized: true,
            updatedAt:
              new Date().toISOString(),
          },
          hasDraft: true,
        }))
      },

      setExecutionField: (
        field,
        value,
      ) => {
        set((state) => ({
          draft: {
            ...state.draft,
            executionSettings: {
              ...state.draft
                .executionSettings,
              [field]: value,
            },
            updatedAt:
              new Date().toISOString(),
          },
          hasDraft: true,
        }))
      },

      setCurrentStep: (step) => {
        set({
          currentStep: step,
        })
      },

      createCycleFromDraft: (
        assets = [],
      ) => {
        const state = get()

        if (!state.hasDraft) {
          return null
        }

        const timestamp =
          new Date().toISOString()

        const selectedAssetIds =
          normalizeAssetIds(
            state.draft
              .selectedAssetIds,
          )

        const selectedAssetSnapshots =
          resolveSnapshots({
            assets,
            capturedAt: timestamp,
            existingSnapshots:
              state.draft
                .selectedAssetSnapshots,
            selectedAssetIds,
          })

        if (
          selectedAssetIds.length > 0 &&
          selectedAssetSnapshots.length !==
            selectedAssetIds.length
        ) {
          return null
        }

        const cycle = {
          id: createCycleId(),
          name:
            state.draft.cycleName.trim() ||
            'Untitled Test Cycle',
          projectId:
            state.draft.projectId,
          environmentId:
            state.draft.environmentId,
          cycleType:
            state.draft.cycleType,
          releaseVersion:
            state.draft.releaseVersion,
          module:
            state.draft.module,
          feature:
            state.draft.feature,
          changeType:
            state.draft.changeType,
          reference:
            state.draft.reference,
          description:
            state.draft.description,
          sourcePlanId:
            state.draft.sourcePlanId ?? '',
          scope: {
            ...state.draft.scope,
          },
          selectedAssetIds,

          selectedAssetSnapshots,

          executions: [],
          executionError: '',
          executionSettings: {
            ...state.draft.executionSettings,
          },
          status: 'Ready',
          progress: 0,
          triggerSource:
            state.draft.sourcePlanId
              ? 'Test Plan'
              : 'Manual',
          createdAt: timestamp,
          updatedAt: timestamp,
        }

        set({
          cycles: [
            cycle,
            ...state.cycles,
          ],
          draft: createEmptyDraft(),
          currentStep: 1,
          hasDraft: false,
          lastCreatedCycleId: cycle.id,
        })

        return cycle
      },

      registerCycleExecutions: (
        cycleId,
        executions,
      ) => {
        set((state) => ({
          cycles: state.cycles.map(
            (cycle) => {
              if (cycle.id !== cycleId) {
                return cycle
              }

              const currentExecutions =
                cycle.executions ?? []

              const currentRunIds =
                new Set(
                  currentExecutions.map(
                    (execution) =>
                      execution.runId,
                  ),
                )

              const nextExecutions = [
                ...currentExecutions,
                ...executions.filter(
                  (execution) =>
                    !currentRunIds.has(
                      execution.runId,
                    ),
                ),
              ]

              const summary =
                summarizeCycleExecutions(
                  nextExecutions,
                )

              return {
                ...cycle,
                executions:
                  nextExecutions,
                executionError: '',
                status: summary.status,
                progress:
                  summary.progress,
                updatedAt:
                  new Date().toISOString(),
              }
            },
          ),
        }))
      },

      updateCycleExecution: (
        cycleId,
        runId,
        executionPatch,
      ) => {
        set((state) => ({
          cycles: state.cycles.map(
            (cycle) => {
              if (cycle.id !== cycleId) {
                return cycle
              }

              const nextExecutions = (
                cycle.executions ?? []
              ).map((execution) =>
                execution.runId === runId
                  ? {
                      ...execution,
                      ...executionPatch,
                      runId:
                        executionPatch.runId ??
                        runId,
                    }
                  : execution,
              )

              const summary =
                summarizeCycleExecutions(
                  nextExecutions,
                )

              return {
                ...cycle,
                executions:
                  nextExecutions,
                status: summary.status,
                progress:
                  summary.progress,
                updatedAt:
                  new Date().toISOString(),
              }
            },
          ),
        }))
      },

      setCycleExecutionError: (
        cycleId,
        message,
      ) => {
        set((state) => ({
          cycles: state.cycles.map(
            (cycle) =>
              cycle.id === cycleId
                ? {
                    ...cycle,
                    executionError:
                      message,
                    updatedAt:
                      new Date().toISOString(),
                  }
                : cycle,
          ),
        }))
      },

      clearDraft: () => {
        set({
          draft: createEmptyDraft(),
          currentStep: 1,
          hasDraft: false,
        })
      },
    }),
    {
      name: 'qa-dashboard-test-cycle-draft-v1',
      storage: createJSONStorage(
        () => localStorage,
      ),
      version:
        TEST_CYCLE_STORE_VERSION,

      migrate:
        migrateTestCycleState,

      merge: (
        persistedState,
        currentState,
      ) => ({
        ...currentState,
        ...(persistedState ?? {}),
        draft:
          normalizeDraft(
            persistedState?.draft,
          ),
        cycles:
          normalizeCycles(
            persistedState?.cycles,
          ),
      }),

      partialize: (state) => ({
        draft: state.draft,
        cycles: state.cycles,
        currentStep: state.currentStep,
        hasDraft: state.hasDraft,
        lastCreatedCycleId:
          state.lastCreatedCycleId,
      }),
    },
  ),
)
