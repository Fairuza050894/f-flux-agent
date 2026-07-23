function TestAssetDefinition({
  asset,
}) {
  return (
    <section className="dashboard-panel test-asset-detail-section">
      <div className="test-asset-detail-section-heading">
        <div>
          <span className="panel-eyebrow">
            TEST DEFINITION
          </span>

          <h3>
            Current Test Definition
          </h3>

          <p>
            Active definition from Test Asset
            version {asset.currentVersionNumber}.
          </p>
        </div>
      </div>

      <div className="test-asset-definition-block">
        <span>Description</span>

        <p>
          {asset.description ||
            'No description provided.'}
        </p>
      </div>

      <div className="test-asset-definition-block">
        <span>Preconditions</span>

        <p>
          {asset.preconditions ||
            'No preconditions provided.'}
        </p>
      </div>

      <div className="test-asset-definition-block">
        <span>Test Steps</span>

        {asset.steps.length > 0 ? (
          <ol className="test-asset-step-list">
            {asset.steps.map(
              (
                step,
                index,
              ) => (
                <li
                  key={`${index}-${step}`}
                >
                  <span>
                    {index + 1}
                  </span>

                  <p>{step}</p>
                </li>
              ),
            )}
          </ol>
        ) : (
          <p>
            No test steps provided.
          </p>
        )}
      </div>

      <div className="test-asset-definition-block">
        <span>Expected Result</span>

        <p>
          {asset.expectedResult ||
            'No expected result provided.'}
        </p>
      </div>
    </section>
  )
}

export default TestAssetDefinition
