import { create } from 'zustand'
import {
  createJSONStorage,
  persist,
} from 'zustand/middleware'

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

    scope: {
      ui: true,
      api: true,
      unit: false,
      e2e: true,
      regression: true,
    },

    selectedAssetIds: [],
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

  const statuses = executions.map(
    (execution) =>
      normalizeExecutionStatus(
        execution.status,
      ),
  )

  const progress = Math.round(
    executions.reduce(
      (total, execution) =>
        total +
        Number(
          execution.progress ?? 0,
        ),
      0,
    ) / executions.length,
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
            assetSelectionInitialized: false,
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
            selectedAssetIds: assetIds,
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

      createCycleFromDraft: () => {
        const state = get()

        if (!state.hasDraft) {
          return null
        }

        const timestamp =
          new Date().toISOString()

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
          scope: {
            ...state.draft.scope,
          },
          selectedAssetIds: [
            ...state.draft.selectedAssetIds,
          ],
          executions: [],
          executionError: '',
          executionSettings: {
            ...state.draft.executionSettings,
          },
          status: 'Ready',
          progress: 0,
          triggerSource: 'Manual',
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
      version: 1,
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
