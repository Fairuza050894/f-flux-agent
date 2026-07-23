import { create } from 'zustand'
import {
  createJSONStorage,
  persist,
} from 'zustand/middleware'

import {
  normalizeTestAsset,
} from '../features/test-assets/testAssetSelectors'

function createTestAssetId() {
  const timestamp =
    new Date()
      .toISOString()
      .replaceAll(/[-:.TZ]/g, '')
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

  return normalizeTestAsset({
    ...input,

    id:
      input?.id ||
      createTestAssetId(),

    createdAt:
      input?.createdAt ??
      timestamp,

    updatedAt:
      timestamp,
  })
}

export const useTestAssetStore = create(
  persist(
    (set, get) => ({
      /*
       * Intentionally empty.
       * Generated preview recommendations
       * are not persisted as real assets.
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
      ) => {
        let updatedAsset = null

        set((state) => ({
          assets:
            state.assets.map(
              (asset) => {
                if (
                  asset.id !== assetId
                ) {
                  return asset
                }

                updatedAsset =
                  normalizeTestAsset({
                    ...asset,
                    ...changes,

                    id:
                      asset.id,

                    createdAt:
                      asset.createdAt,

                    updatedAt:
                      new Date()
                        .toISOString(),
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
                asset.id !== assetId,
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

      replaceTestAssets: (
        assets,
      ) => {
        set({
          assets:
            Array.isArray(assets)
              ? assets.map(
                  normalizeTestAsset,
                )
              : [],
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

      version: 1,
    },
  ),
)
