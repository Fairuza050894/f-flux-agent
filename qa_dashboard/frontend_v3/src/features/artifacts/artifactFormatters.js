export function normalizeArtifactToken(
  value,
) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replaceAll('-', '_')
    .replaceAll(' ', '_')
}

export function formatArtifactToken(
  value,
) {
  const normalizedValue =
    normalizeArtifactToken(value)

  if (!normalizedValue) {
    return 'Artifact'
  }

  return normalizedValue
    .split('_')
    .filter(Boolean)
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1),
    )
    .join(' ')
}

export function getArtifactFileExtension(
  fileName,
) {
  const normalizedName =
    String(fileName ?? '').trim()

  if (
    !normalizedName ||
    !normalizedName.includes('.')
  ) {
    return ''
  }

  return normalizedName
    .split('.')
    .pop()
    .toLowerCase()
}
