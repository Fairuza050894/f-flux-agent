import {
  createContext,
  useContext,
} from 'react'

export const DashboardAuthContext =
  createContext(null)

export function useDashboardAuth() {
  return useContext(
    DashboardAuthContext,
  )
}
