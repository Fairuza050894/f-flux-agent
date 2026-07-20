import { create } from 'zustand'
import {
  createJSONStorage,
  persist,
} from 'zustand/middleware'

const initialProjects = [
  {
    id: 'mobospace',
    name: 'Mobospace',
    key: 'MOB',
    description:
      'Logistics platform for shipment monitoring, driver operations, tracking, and supporting operational workflows.',
    applicationType: 'Full Stack Application',
    status: 'Active',
    defaultBranch: 'develop',
    repositoryUrl: '',
    workingDirectory: '',
    technologyStack: 'React, Node.js, Python',
    environmentCount: 1,
    moduleCount: 12,
    testAssetCount: 0,
    defaultEnvironment: 'Sandbox',
    lastExecution: 'Not available',
  },
]

const initialEnvironments = [
  {
    id: 'mobospace-sandbox',
    projectId: 'mobospace',
    name: 'Sandbox',
    type: 'Sandbox',
    status: 'Not Checked',
    webBaseUrl: '',
    apiBaseUrl: '',
    authenticationUrl: '',
    authenticationType: 'Username and Password',
    credentialReference: 'Not configured',
    workspace: 'Not configured',
    defaultBrowser: 'Chromium',
    timeout: 30,
    healthCheckEndpoint: '',
    lastChecked: 'Never',
  },
]

export const useProjectEnvironmentStore = create(
  persist(
    (set, get) => ({
      projects: initialProjects,
      environments: initialEnvironments,

      selectedProjectId: 'mobospace',
      selectedEnvironmentId: 'mobospace-sandbox',

      addProject: (project) => {
        set((state) => ({
          projects: [
            ...state.projects,
            project,
          ],
          selectedProjectId: project.id,
          selectedEnvironmentId: null,
        }))
      },

      updateProject: (projectId, changes) => {
        set((state) => ({
          projects: state.projects.map((project) =>
            project.id === projectId
              ? {
                  ...project,
                  ...changes,
                }
              : project,
          ),
        }))
      },

      addEnvironment: (environment) => {
        set((state) => ({
          environments: [
            ...state.environments,
            environment,
          ],

          projects: state.projects.map((project) => {
            if (project.id !== environment.projectId) {
              return project
            }

            const existingCount =
              project.environmentCount ?? 0

            return {
              ...project,
              environmentCount: existingCount + 1,
              defaultEnvironment:
                existingCount === 0
                  ? environment.name
                  : project.defaultEnvironment,
            }
          }),

          selectedEnvironmentId:
            state.selectedProjectId ===
            environment.projectId
              ? environment.id
              : state.selectedEnvironmentId,
        }))
      },

      updateEnvironment: (
        environmentId,
        changes,
      ) => {
        set((state) => ({
          environments: state.environments.map(
            (environment) =>
              environment.id === environmentId
                ? {
                    ...environment,
                    ...changes,
                  }
                : environment,
          ),
        }))
      },

      setSelectedProjectId: (projectId) => {
        const firstEnvironment =
          get().environments.find(
            (environment) =>
              environment.projectId === projectId,
          )

        set({
          selectedProjectId: projectId,
          selectedEnvironmentId:
            firstEnvironment?.id ?? null,
        })
      },

      setSelectedEnvironmentId: (
        environmentId,
      ) => {
        set({
          selectedEnvironmentId: environmentId,
        })
      },

      resetWorkspaceData: () => {
        set({
          projects: initialProjects,
          environments: initialEnvironments,
          selectedProjectId: 'mobospace',
          selectedEnvironmentId:
            'mobospace-sandbox',
        })
      },
    }),
    {
      name: 'qa-dashboard-project-environment-v1',
      storage: createJSONStorage(
        () => localStorage,
      ),
      version: 1,
    },
  ),
)
