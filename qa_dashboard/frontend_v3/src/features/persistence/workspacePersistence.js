import {
  useProjectEnvironmentStore,
} from '../../stores/projectEnvironmentStore'
import {
  useTestAssetStore,
} from '../../stores/testAssetStore'
import {
  useTestCycleStore,
} from '../../stores/testCycleStore'
import {
  useTestPlanStore,
} from '../../stores/testPlanStore'
import {
  fetchWorkspaceState,
  saveWorkspaceState,
} from '../../services/workspaceStateService'

const SYNC_METADATA_KEY =
  'qa-dashboard-workspace-sync-v1'

function emitSyncStatus(
  status,
  details = {},
) {
  window.dispatchEvent(
    new CustomEvent(
      'qa-workspace-sync-status',
      {
        detail: {
          ...details,
          status,
        },
      },
    ),
  )
}

async function ensureStoreHydrated(
  store,
) {
  if (
    store.persist?.hasHydrated?.()
  ) {
    return
  }

  await Promise.resolve(
    store.persist?.rehydrate?.(),
  )
}

function captureWorkspaceState() {
  const projectEnvironment =
    useProjectEnvironmentStore
      .getState()

  const testAssets =
    useTestAssetStore.getState()

  const testPlans =
    useTestPlanStore.getState()

  const testCycles =
    useTestCycleStore.getState()

  return {
    projectEnvironment: {
      environments:
        projectEnvironment
          .environments,
      projects:
        projectEnvironment
          .projects,
      selectedEnvironmentId:
        projectEnvironment
          .selectedEnvironmentId,
      selectedProjectId:
        projectEnvironment
          .selectedProjectId,
    },

    testAssets: {
      assets:
        testAssets.assets,
    },

    testPlans: {
      plans:
        testPlans.plans,
    },

    testCycles: {
      currentStep:
        testCycles.currentStep,
      cycles:
        testCycles.cycles,
      draft:
        testCycles.draft,
      hasDraft:
        testCycles.hasDraft,
      lastCreatedCycleId:
        testCycles
          .lastCreatedCycleId,
    },
  }
}

function applyWorkspaceState(
  workspaceState,
) {
  const state =
    workspaceState &&
    typeof workspaceState ===
      'object'
      ? workspaceState
      : {}

  const projectEnvironment =
    state.projectEnvironment ?? {}

  const projects =
    Array.isArray(
      projectEnvironment.projects,
    )
      ? projectEnvironment.projects
      : []

  const environments =
    Array.isArray(
      projectEnvironment.environments,
    )
      ? projectEnvironment
          .environments
      : []

  useProjectEnvironmentStore
    .setState({
      environments,
      projects,
      selectedEnvironmentId:
        projectEnvironment
          .selectedEnvironmentId ??
        null,
      selectedProjectId:
        projectEnvironment
          .selectedProjectId ??
        null,
    })

  const assets =
    Array.isArray(
      state.testAssets?.assets,
    )
      ? state.testAssets.assets
      : []

  useTestAssetStore
    .getState()
    .replaceTestAssets(
      assets,
    )

  const plans =
    Array.isArray(
      state.testPlans?.plans,
    )
      ? state.testPlans.plans
      : []

  useTestPlanStore
    .getState()
    .replaceTestPlans(
      plans,
      assets,
    )

  const cycleState =
    state.testCycles ?? {}

  const currentCycleState =
    useTestCycleStore.getState()

  useTestCycleStore.setState({
    currentStep:
      Number.isFinite(
        Number(
          cycleState.currentStep,
        ),
      )
        ? Number(
            cycleState.currentStep,
          )
        : currentCycleState
            .currentStep,

    cycles:
      Array.isArray(
        cycleState.cycles,
      )
        ? cycleState.cycles
        : [],

    draft:
      cycleState.draft ??
      currentCycleState.draft,

    hasDraft:
      Boolean(
        cycleState.hasDraft,
      ),

    lastCreatedCycleId:
      cycleState
        .lastCreatedCycleId ??
      null,
  })
}

function writeSyncMetadata(
  values,
) {
  localStorage.setItem(
    SYNC_METADATA_KEY,
    JSON.stringify({
      ...values,
      updatedAt:
        new Date().toISOString(),
    }),
  )
}

export function startWorkspacePersistence() {
  let disposed = false
  let ready = false
  let revision = 0
  let saveTimer = null
  let saveQueue =
    Promise.resolve()
  let unsubscribeStores = []

  function saveCurrentState(
    source = 'frontend-sync',
    options = {},
  ) {
    if (
      !ready ||
      disposed
    ) {
      return Promise.resolve()
    }

    const state =
      captureWorkspaceState()

    emitSyncStatus(
      'saving',
      {
        revision,
      },
    )

    saveQueue =
      saveQueue
        .catch(() => undefined)
        .then(
          async () => {
            const result =
              await saveWorkspaceState(
                {
                  expectedRevision:
                    revision,
                  source,
                  state,
                },
                options,
              )

            revision =
              result.revision

            writeSyncMetadata({
              revision,
              status: 'synced',
            })

            emitSyncStatus(
              'synced',
              {
                revision,
              },
            )
          },
        )
        .catch(
          (error) => {
            const isConflict =
              error?.status === 409

            writeSyncMetadata({
              revision,
              status:
                isConflict
                  ? 'conflict'
                  : 'error',
            })

            emitSyncStatus(
              isConflict
                ? 'conflict'
                : 'error',
              {
                message:
                  error?.message ??
                  'Workspace sync failed.',
                revision,
              },
            )
          },
        )

    return saveQueue
  }

  function scheduleSave() {
    if (
      !ready ||
      disposed
    ) {
      return
    }

    window.clearTimeout(
      saveTimer,
    )

    saveTimer =
      window.setTimeout(
        () => {
          void saveCurrentState()
        },
        900,
      )
  }

  function subscribeStores() {
    const stores = [
      useProjectEnvironmentStore,
      useTestAssetStore,
      useTestPlanStore,
      useTestCycleStore,
    ]

    unsubscribeStores =
      stores.map(
        (store) =>
          store.subscribe(
            scheduleSave,
          ),
      )
  }

  function handlePageHide() {
    if (!ready) {
      return
    }

    void saveWorkspaceState(
      {
        expectedRevision:
          revision,
        source:
          'frontend-pagehide',
        state:
          captureWorkspaceState(),
      },
      {
        keepalive: true,
      },
    ).catch(
      () => undefined,
    )
  }

  async function bootstrap() {
    emitSyncStatus(
      'loading',
    )

    try {
      await Promise.all([
        ensureStoreHydrated(
          useProjectEnvironmentStore,
        ),
        ensureStoreHydrated(
          useTestAssetStore,
        ),
        ensureStoreHydrated(
          useTestPlanStore,
        ),
        ensureStoreHydrated(
          useTestCycleStore,
        ),
      ])

      const remote =
        await fetchWorkspaceState()

      if (disposed) {
        return
      }

      if (remote.exists) {
        applyWorkspaceState(
          remote.state,
        )
        revision =
          remote.revision
      } else {
        const imported =
          await saveWorkspaceState({
            expectedRevision: 0,
            source:
              'legacy-zustand-import',
            state:
              captureWorkspaceState(),
          })

        revision =
          imported.revision
      }

      if (disposed) {
        return
      }

      ready = true
      subscribeStores()

      window.addEventListener(
        'pagehide',
        handlePageHide,
      )

      writeSyncMetadata({
        revision,
        status: 'synced',
      })

      emitSyncStatus(
        'synced',
        {
          revision,
        },
      )
    } catch (error) {
      if (disposed) {
        return
      }

      writeSyncMetadata({
        revision,
        status: 'offline',
      })

      emitSyncStatus(
        'offline',
        {
          message:
            error?.message ??
            'Workspace backend is unavailable.',
          revision,
        },
      )
    }
  }

  void bootstrap()

  return () => {
    disposed = true

    window.clearTimeout(
      saveTimer,
    )

    unsubscribeStores.forEach(
      (unsubscribe) =>
        unsubscribe(),
    )

    window.removeEventListener(
      'pagehide',
      handlePageHide,
    )
  }
}
