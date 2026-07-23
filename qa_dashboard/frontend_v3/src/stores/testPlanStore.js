import { create } from 'zustand'
import {
  createJSONStorage,
  persist,
} from 'zustand/middleware'

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

function createTestPlanRecord(
  input,
) {
  const timestamp =
    new Date().toISOString()

  return normalizeTestPlan({
    ...input,

    id:
      input?.id ||
      createTestPlanId(),

    createdAt:
      input?.createdAt ??
      timestamp,

    updatedAt:
      timestamp,
  })
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

      addTestPlan: (input) => {
        const plan =
          createTestPlanRecord(
            input,
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

                updatedPlan =
                  normalizeTestPlan({
                    ...plan,
                    ...changes,

                    id:
                      plan.id,

                    createdAt:
                      plan.createdAt,

                    updatedAt:
                      new Date()
                        .toISOString(),
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

      replaceTestPlans: (
        plans,
      ) => {
        set({
          plans:
            Array.isArray(plans)
              ? plans.map(
                  normalizeTestPlan,
                )
              : [],
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

      version: 1,
    },
  ),
)
