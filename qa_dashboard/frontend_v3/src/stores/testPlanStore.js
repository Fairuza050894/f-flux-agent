import { create } from 'zustand'
import {
  createJSONStorage,
  persist,
} from 'zustand/middleware'

import {
  TEST_PLAN_STORE_VERSION,
} from '../features/test-planning/testPlanConstants'
import {
  captureTestPlanAssetSnapshots,
  mergeTestPlanAssetSnapshots,
  normalizeTestPlanAssetSnapshots,
} from '../features/test-planning/testPlanAssetSnapshots'
import {
  normalizeTestPlan,
} from '../features/test-planning/testPlanSelectors'

function createTestPlanId() {
  const timestamp =
    new Date()
      .toISOString()
      .replaceAll(
        /[-:.TZ]/g,
        '',
      )
      .slice(0, 14)

  const randomPart =
    Math.random()
      .toString(36)
      .slice(2, 7)
      .toUpperCase()

  return `TP-${timestamp}-${randomPart}`
}

function normalizeStoredPlans(
  plans,
) {
  if (!Array.isArray(plans)) {
    return []
  }

  return plans.map(
    normalizeTestPlan,
  )
}

function createTestPlanRecord(
  input,
  assets = [],
) {
  const timestamp =
    new Date().toISOString()

  const selectedAssetIds =
    Array.isArray(
      input?.selectedAssetIds,
    )
      ? input.selectedAssetIds
      : []

  return normalizeTestPlan({
    ...input,

    id:
      input?.id ||
      createTestPlanId(),

    selectedAssetIds,

    selectedAssetSnapshots:
      captureTestPlanAssetSnapshots({
        assets,
        capturedAt: timestamp,
        selectedAssetIds,
      }),

    createdAt:
      input?.createdAt ??
      timestamp,

    updatedAt: timestamp,
  })
}

function migrateTestPlanState(
  persistedState,
) {
  const safeState =
    persistedState &&
    typeof persistedState ===
      'object'
      ? persistedState
      : {}

  return {
    ...safeState,

    plans:
      normalizeStoredPlans(
        safeState.plans,
      ),
  }
}

function snapshotsAreEqual(
  firstSnapshots,
  secondSnapshots,
) {
  return (
    JSON.stringify(
      normalizeTestPlanAssetSnapshots(
        firstSnapshots,
      ),
    ) ===
    JSON.stringify(
      normalizeTestPlanAssetSnapshots(
        secondSnapshots,
      ),
    )
  )
}

export const useTestPlanStore = create(
  persist(
    (set, get) => ({
      /*
       * Test Plans start empty.
       * No sample plan is presented
       * as user-created data.
       */
      plans: [],

      addTestPlan: (
        input,
        assets = [],
      ) => {
        const plan =
          createTestPlanRecord(
            input,
            assets,
          )

        set((state) => ({
          plans: [
            plan,
            ...state.plans,
          ],
        }))

        return plan
      },

      updateTestPlan: (
        planId,
        changes,
        assets = [],
      ) => {
        let updatedPlan = null

        set((state) => ({
          plans:
            state.plans.map(
              (plan) => {
                if (
                  plan.id !== planId
                ) {
                  return plan
                }

                const timestamp =
                  new Date()
                    .toISOString()

                const normalizedPlan =
                  normalizeTestPlan(
                    plan,
                  )

                const hasAssetSelection =
                  Object.prototype
                    .hasOwnProperty.call(
                      changes ?? {},
                      'selectedAssetIds',
                    )

                const selectedAssetIds =
                  hasAssetSelection
                    ? changes
                        .selectedAssetIds
                    : normalizedPlan
                        .selectedAssetIds

                const selectedAssetSnapshots =
                  hasAssetSelection
                    ? mergeTestPlanAssetSnapshots({
                        assets,

                        capturedAt:
                          timestamp,

                        existingSnapshots:
                          normalizedPlan
                            .selectedAssetSnapshots,

                        refreshExisting:
                          true,

                        selectedAssetIds,
                      })
                    : normalizedPlan
                        .selectedAssetSnapshots

                updatedPlan =
                  normalizeTestPlan({
                    ...normalizedPlan,
                    ...changes,

                    id:
                      normalizedPlan.id,

                    selectedAssetIds,

                    selectedAssetSnapshots,

                    createdAt:
                      normalizedPlan
                        .createdAt,

                    updatedAt:
                      timestamp,
                  })

                return updatedPlan
              },
            ),
        }))

        return updatedPlan
      },

      archiveTestPlan: (
        planId,
      ) =>
        get().updateTestPlan(
          planId,
          {
            status: 'Archived',
          },
        ),

      restoreTestPlan: (
        planId,
      ) =>
        get().updateTestPlan(
          planId,
          {
            status: 'Draft',
          },
        ),

      deleteTestPlan: (
        planId,
      ) => {
        const exists =
          get().plans.some(
            (plan) =>
              plan.id === planId,
          )

        if (!exists) {
          return false
        }

        set((state) => ({
          plans:
            state.plans.filter(
              (plan) =>
                plan.id !== planId,
            ),
        }))

        return true
      },

      getTestPlanById: (
        planId,
      ) =>
        get().plans.find(
          (plan) =>
            plan.id === planId,
        ) ?? null,

      backfillTestPlanAssetSnapshots: (
        assets = [],
      ) => {
        const capturedAt =
          new Date().toISOString()

        let didChange = false

        const plans =
          get().plans.map(
            (storedPlan) => {
              const plan =
                normalizeTestPlan(
                  storedPlan,
                )

              const nextSnapshots =
                mergeTestPlanAssetSnapshots({
                  assets,

                  capturedAt,

                  existingSnapshots:
                    plan
                      .selectedAssetSnapshots,

                  refreshExisting:
                    false,

                  selectedAssetIds:
                    plan.selectedAssetIds,
                })

              if (
                snapshotsAreEqual(
                  plan
                    .selectedAssetSnapshots,

                  nextSnapshots,
                )
              ) {
                return plan
              }

              didChange = true

              return normalizeTestPlan({
                ...plan,

                selectedAssetSnapshots:
                  nextSnapshots,
              })
            },
          )

        if (!didChange) {
          return false
        }

        set({
          plans,
        })

        return true
      },

      replaceTestPlans: (
        plans,
        assets = [],
      ) => {
        const capturedAt =
          new Date().toISOString()

        set({
          plans:
            normalizeStoredPlans(
              plans,
            ).map((plan) =>
              normalizeTestPlan({
                ...plan,

                selectedAssetSnapshots:
                  mergeTestPlanAssetSnapshots({
                    assets,

                    capturedAt,

                    existingSnapshots:
                      plan
                        .selectedAssetSnapshots,

                    refreshExisting:
                      false,

                    selectedAssetIds:
                      plan
                        .selectedAssetIds,
                  }),
              }),
            ),
        })
      },

      resetTestPlans: () => {
        set({
          plans: [],
        })
      },
    }),
    {
      name:
        'qa-dashboard-test-plans-v1',

      storage:
        createJSONStorage(
          () => localStorage,
        ),

      version:
        TEST_PLAN_STORE_VERSION,

      migrate:
        migrateTestPlanState,

      merge: (
        persistedState,
        currentState,
      ) => ({
        ...currentState,
        ...(persistedState ?? {}),

        plans:
          normalizeStoredPlans(
            persistedState?.plans,
          ),
      }),

      partialize: (state) => ({
        plans: state.plans,
      }),
    },
  ),
)
