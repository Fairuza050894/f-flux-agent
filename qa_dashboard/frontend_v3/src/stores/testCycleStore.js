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
