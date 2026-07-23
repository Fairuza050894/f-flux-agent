import { create } from 'zustand'
import {
  createJSONStorage,
  persist,
} from 'zustand/middleware'

import {
  appendTestAssetVersion,
  createVersionedTestAsset,
  migrateLegacyTestAsset,
  normalizeVersionedTestAsset,
} from '../features/test-assets/testAssetVersioning'
import {
  TEST_ASSET_STORE_VERSION,
} from '../features/test-assets/testAssetVersionConstants'

function createTestAssetId() {
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

  return `TA-${timestamp}-${randomPart}`
}

function createAssetRecord(
  input,
) {
  const timestamp =
    new Date().toISOString()

  return createVersionedTestAsset(
    {
      ...input,

      id:
        input?.id ||
        createTestAssetId(),

      createdAt:
        input?.createdAt ??
        timestamp,
    },
    {
      timestamp,
    },
  )
}

function normalizeStoredAssets(
  assets,
) {
  if (!Array.isArray(assets)) {
    return []
  }

  return assets.map(
    normalizeVersionedTestAsset,
  )
}

function migrateTestAssetState(
  persistedState,
  persistedVersion,
) {
  const safeState =
    persistedState &&
    typeof persistedState ===
      'object'
      ? persistedState
      : {}

  const storedAssets =
    Array.isArray(
      safeState.assets,
    )
      ? safeState.assets
      : []

  const assets =
    persistedVersion <
    TEST_ASSET_STORE_VERSION
      ? storedAssets.map(
          migrateLegacyTestAsset,
        )
      : normalizeStoredAssets(
          storedAssets,
        )

  return {
    ...safeState,
    assets,
  }
}

function resolveChangeSummary(
  changes,
  options,
) {
  if (
    typeof options ===
    'string'
  ) {
    return options
  }

  return (
    options?.changeSummary ??
    changes?.changeSummary ??
    ''
  )
}

export const useTestAssetStore = create(
  persist(
    (set, get) => ({
      /*
       * Intentionally empty.
       * User-created Test Assets are
       * restored from persisted storage.
       */
      assets: [],

      addTestAsset: (input) => {
        const asset =
          createAssetRecord(input)

        set((state) => ({
          assets: [
            asset,
            ...state.assets,
          ],
        }))

        return asset
      },

      updateTestAsset: (
        assetId,
        changes,
        options = {},
      ) => {
        let updatedAsset = null

        const changeSummary =
          resolveChangeSummary(
            changes,
            options,
          )

        set((state) => ({
          assets:
            state.assets.map(
              (asset) => {
                if (
                  asset.id !==
                  assetId
                ) {
                  return asset
                }

                updatedAsset =
                  appendTestAssetVersion({
                    asset,
                    changes,
                    changeSummary,
                  })

                return updatedAsset
              },
            ),
        }))

        return updatedAsset
      },

      deleteTestAsset: (
        assetId,
      ) => {
        const exists =
          get().assets.some(
            (asset) =>
              asset.id === assetId,
          )

        if (!exists) {
          return false
        }

        set((state) => ({
          assets:
            state.assets.filter(
              (asset) =>
                asset.id !==
                assetId,
            ),
        }))

        return true
      },

      getTestAssetById: (
        assetId,
      ) =>
        get().assets.find(
          (asset) =>
            asset.id === assetId,
        ) ?? null,

      getTestAssetVersionById: (
        assetId,
        versionId,
      ) => {
        const asset =
          get().assets.find(
            (candidate) =>
              candidate.id ===
              assetId,
          )

        if (!asset) {
          return null
        }

        return (
          asset.versions?.find(
            (version) =>
              version.versionId ===
              versionId,
          ) ?? null
        )
      },

      replaceTestAssets: (
        assets,
      ) => {
        set({
          assets:
            normalizeStoredAssets(
              assets,
            ),
        })
      },

      resetTestAssets: () => {
        set({
          assets: [],
        })
      },
    }),
    {
      name:
        'qa-dashboard-test-assets-v1',

      storage:
        createJSONStorage(
          () => localStorage,
        ),

      version:
        TEST_ASSET_STORE_VERSION,

      migrate:
        migrateTestAssetState,

      merge: (
        persistedState,
        currentState,
      ) => ({
        ...currentState,
        ...(persistedState ?? {}),

        assets:
          normalizeStoredAssets(
            persistedState?.assets,
          ),
      }),

      partialize: (state) => ({
        assets: state.assets,
      }),
    },
  ),
)
