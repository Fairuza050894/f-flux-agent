import {
  useEffect,
} from 'react'

import {
  startWorkspacePersistence,
} from './workspacePersistence'

function WorkspacePersistenceBridge() {
  useEffect(
    () =>
      startWorkspacePersistence(),
    [],
  )

  return null
}

export default WorkspacePersistenceBridge
