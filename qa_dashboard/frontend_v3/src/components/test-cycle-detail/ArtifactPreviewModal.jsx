import {
  useEffect,
  useRef,
} from 'react'

function ArtifactPreviewContent({
  artifact,
  content,
  error,
  loading,
}) {
  if (loading) {
    return (
      <div className="cycle-artifact-preview-message">
        Loading artifact preview...
      </div>
    )
  }

  if (error) {
    return (
      <div
        className="cycle-artifact-preview-error"
        role="alert"
      >
        {error}
      </div>
    )
  }

  if (
    artifact.previewKind === 'image'
  ) {
    return (
      <img
        alt={
          artifact.name ??
          'QA artifact'
        }
        className="cycle-artifact-modal-image"
        src={artifact.previewUrl}
      />
    )
  }

  if (
    artifact.previewKind === 'pdf'
  ) {
    return (
      <iframe
        className="cycle-artifact-modal-frame"
        src={artifact.previewUrl}
        title={
          artifact.name ??
          'PDF artifact'
        }
      />
    )
  }

  if (
    [
      'json',
      'text',
    ].includes(
      artifact.previewKind,
    )
  ) {
    return (
      <pre className="cycle-artifact-modal-code">
        {content ||
          'The artifact is empty.'}
      </pre>
    )
  }

  return null
}

function ArtifactPreviewModal({
  artifact,
  content,
  error,
  loading,
  onClose,
}) {
  const closeButtonRef =
    useRef(null)

  useEffect(() => {
    if (!artifact) {
      return undefined
    }

    const previousOverflow =
      document.body.style.overflow

    document.body.style.overflow =
      'hidden'

    closeButtonRef.current?.focus()

    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener(
      'keydown',
      handleKeyDown,
    )

    return () => {
      document.body.style.overflow =
        previousOverflow

      window.removeEventListener(
        'keydown',
        handleKeyDown,
      )
    }
  }, [
    artifact,
    onClose,
  ])

  if (!artifact) {
    return null
  }

  return (
    <div
      className="cycle-artifact-modal-backdrop"
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose()
        }
      }}
    >
      <section
        aria-labelledby="artifact-preview-title"
        aria-modal="true"
        className="cycle-artifact-modal"
        role="dialog"
      >
        <header className="cycle-artifact-modal-header">
          <div>
            <span>
              {artifact.typeLabel}
            </span>

            <h4 id="artifact-preview-title">
              {artifact.name ??
                'Artifact Preview'}
            </h4>
          </div>

          <button
            aria-label="Close artifact preview"
            className="cycle-artifact-modal-close"
            onClick={onClose}
            ref={closeButtonRef}
            type="button"
          >
            ×
          </button>
        </header>

        <div
          aria-busy={loading}
          className="cycle-artifact-modal-body"
        >
          <ArtifactPreviewContent
            artifact={artifact}
            content={content}
            error={error}
            loading={loading}
          />
        </div>

        <footer className="cycle-artifact-modal-footer">
          <div>
            <span>Execution</span>

            <strong>
              {artifact.scopeLabel}
            </strong>
          </div>

          <div className="cycle-artifact-modal-actions">
            <button
              className="button button-secondary"
              onClick={onClose}
              type="button"
            >
              Close
            </button>

            <a
              className="button button-primary"
              href={artifact.downloadUrl}
            >
              Download
            </a>
          </div>
        </footer>
      </section>
    </div>
  )
}

export default ArtifactPreviewModal
