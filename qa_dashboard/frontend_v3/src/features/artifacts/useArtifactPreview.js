import {
  useCallback,
  useRef,
  useState,
} from 'react'

import {
  readExecutionArtifact,
} from '../../services/executionService'

function formatPreviewContent(
  rawContent,
  previewKind,
) {
  if (previewKind !== 'json') {
    return rawContent
  }

  try {
    return JSON.stringify(
      JSON.parse(rawContent),
      null,
      2,
    )
  } catch {
    return rawContent
  }
}

export function useArtifactPreview() {
  const [
    preview,
    setPreview,
  ] = useState(null)

  const [
    previewContent,
    setPreviewContent,
  ] = useState('')

  const [
    previewLoading,
    setPreviewLoading,
  ] = useState(false)

  const [
    previewError,
    setPreviewError,
  ] = useState('')

  const requestIdRef = useRef(0)

  const closePreview = useCallback(
    () => {
      requestIdRef.current += 1

      setPreview(null)
      setPreviewContent('')
      setPreviewError('')
      setPreviewLoading(false)
    },
    [],
  )

  const openPreview = useCallback(
    async (artifact) => {
      if (
        !artifact?.canPreview ||
        !artifact?.runId
      ) {
        return
      }

      const requestId =
        requestIdRef.current + 1

      requestIdRef.current =
        requestId

      setPreview(artifact)
      setPreviewContent('')
      setPreviewError('')

      if (
        artifact.previewKind ===
          'image' ||
        artifact.previewKind ===
          'pdf'
      ) {
        setPreviewLoading(false)
        return
      }

      setPreviewLoading(true)

      try {
        const rawContent =
          await readExecutionArtifact(
            artifact.runId,
            artifact.artifactIndex,
          )

        if (
          requestIdRef.current !==
          requestId
        ) {
          return
        }

        setPreviewContent(
          formatPreviewContent(
            rawContent,
            artifact.previewKind,
          ),
        )
      } catch (error) {
        if (
          requestIdRef.current !==
          requestId
        ) {
          return
        }

        setPreviewError(
          error instanceof Error
            ? error.message
            : 'Artifact preview could not be loaded.',
        )
      } finally {
        if (
          requestIdRef.current ===
          requestId
        ) {
          setPreviewLoading(false)
        }
      }
    },
    [],
  )

  return {
    closePreview,
    openPreview,
    preview,
    previewContent,
    previewError,
    previewLoading,
  }
}
