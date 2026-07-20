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

export const useTestCycleStore = create(
  persist(
    (set) => ({
      draft: createEmptyDraft(),
      currentStep: 1,
      hasDraft: false,

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
        currentStep: state.currentStep,
        hasDraft: state.hasDraft,
      }),
    },
  ),
)
