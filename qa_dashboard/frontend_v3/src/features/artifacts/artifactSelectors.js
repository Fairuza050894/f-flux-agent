import {
  ARTIFACT_IMAGE_EXTENSIONS,
  ARTIFACT_TEXT_EXTENSIONS,
  ARTIFACT_TYPE_LABELS,
} from './artifactConstants'
import {
  formatArtifactToken,
  getArtifactFileExtension,
  normalizeArtifactToken,
} from './artifactFormatters'

function toArray(value) {
  return Array.isArray(value)
    ? value
    : []
}

function toArtifactRecord(value) {
  return (
    value !== null &&
    typeof value === 'object' &&
    !Array.isArray(value)
  )
    ? value
    : {}
}

export function getArtifactTypeLabel(
  artifactType,
) {
  const normalizedType =
    normalizeArtifactToken(
      artifactType,
    )

  if (!normalizedType) {
    return 'Artifact'
  }

  return (
    ARTIFACT_TYPE_LABELS[
      normalizedType
    ] ??
    formatArtifactToken(
      normalizedType,
    )
  )
}

export function getArtifactPreviewKind(
  artifact,
) {
  const artifactType =
    normalizeArtifactToken(
      artifact?.type,
    )

  const extension =
    getArtifactFileExtension(
      artifact?.name,
    )

  if (
    artifactType === 'screenshot' ||
    ARTIFACT_IMAGE_EXTENSIONS.includes(
      extension,
    )
  ) {
    return 'image'
  }

  if (
    artifactType === 'json' ||
    extension === 'json'
  ) {
    return 'json'
  }

  if (
    [
      'documentation',
      'error_log',
      'report',
    ].includes(artifactType) ||
    ARTIFACT_TEXT_EXTENSIONS.includes(
      extension,
    )
  ) {
    return 'text'
  }

  if (extension === 'pdf') {
    return 'pdf'
  }

  return 'unsupported'
}

export function buildCycleArtifacts(
  executions,
) {
  return toArray(executions).flatMap(
    (execution) => {
      const runId =
        execution?.runId ??
        execution?.run_id ??
        null

      const scopeLabel =
        execution?.scopeLabel ??
        execution?.scope_label ??
        execution?.source ??
        'Execution'

      const executionStatus =
        execution?.status ?? ''

      return toArray(
        execution?.artifacts,
      ).map(
        (
          rawArtifact,
          artifactIndex,
        ) => {
          const artifact =
            toArtifactRecord(
              rawArtifact,
            )

          const previewKind =
            getArtifactPreviewKind(
              artifact,
            )

          const available =
            artifact.exists !== false &&
            Boolean(runId)

          const name =
            artifact.name ??
            'Unnamed artifact'

          return {
            ...artifact,
            artifactIndex,
            runId,
            scopeLabel,
            executionStatus,
            name,
            available,
            previewKind,

            canPreview:
              available &&
              previewKind !==
                'unsupported',

            typeLabel:
              getArtifactTypeLabel(
                artifact.type,
              ),

            previewLabel:
              previewKind ===
              'unsupported'
                ? 'Download only'
                : `${
                    formatArtifactToken(
                      previewKind,
                    )
                  } preview`,

            key: [
              runId ?? 'no-run',
              artifactIndex,
              name,
            ].join('-'),
          }
        },
      )
    },
  )
}
