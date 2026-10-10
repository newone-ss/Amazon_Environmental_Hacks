import React from 'react';

interface PathwaysPanelProps {
  siteData: any; // Site type
  pathwaysData: any | null;
  onGeneratePathway: (sspScenario: string, baseRainfallFraction: number) => Promise<void>;
  loading: boolean;
  error: string | null;
}

const PathwaysPanel: React.FC<PathwaysPanelProps> = ({
  siteData,
  pathwaysData,
  onGeneratePathway,
  loading,
  error
}) => {
  const [sspScenario, setSspScenario] = React.useState<string>('SSP2-4.5');
  const [baseRainfallFraction, setBaseRainfallFraction] = React.useState<number>(1.0);

  const SSP_SCENARIOS = [
    { value: 'SSP1-2.6', label: 'SSP1-2.6: Low Challenges' },
    { value: 'SSP2-4.5', label: 'SSP2-4.5: Medium Challenges' },
    { value: 'SSP3-7.0', label: 'SSP3-7.0: High Challenges' },
    { value: 'SSP5-8.5', label: 'SSP5-8.5: Very High Challenges' }
  ];

  const handleGeneratePathway = async () => {
    await onGeneratePathway(sspScenario, baseRainfallFraction);
  };

  if (!siteData) {
    return (
      <div className="pathways-panel">
        <div className="panel-placeholder">Select a settlement to view pathways</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="pathways-panel">
        <div className="panel-loading">Generating pathways...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pathways-panel">
        <div className="panel-error">{error}</div>
      </div>
    );
  }

  // Format INR currency
  const formatINR = (amount: number): string => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className="pathways-panel">
      <div className="panel-header">
        <h2>Adaptation Pathways</h2>
        <p className="illustrative-note">Illustrative scenario for long-term planning</p>
      </div>

      <div className="pathways-controls">
        <div className="control-group">
          <label>SSP Scenario:</label>
          <select
            value={sspScenario}
            onChange={(e) => setSspScenario(e.target.value)}
          >
            {SSP_SCENARIOS.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Base Rainfall Fraction:</label>
          <div className="slider-container">
            <input
              type="range"
              min="0.5"
              max="1.5"
              step="0.05"
              value={baseRainfallFraction}
              onChange={(e) => setBaseRainfallFraction(parseFloat(e.target.value))}
            />
            <span>{baseRainfallFraction.toFixed(2)}x</span>
          </div>
        </div>

        <button className="generate-pathway-btn" onClick={handleGeneratePathway}>
          Generate Pathway
        </button>
      </div>

      {pathwaysData ? (
        <div className="pathways-results">
          <div className="pathway-metrics">
            <div className="metric-card">
              <h3>Total Cost</h3>
              <div className="metric-value">{formatINR(pathwaysData.total_cost)}</div>
            </div>
            <div className="metric-card">
              <h3>Total Benefit</h3>
              <div className="metric-value">{formatINR(pathwaysData.total_benefit)}</div>
            </div>
            <div className="metric-card">
              <h3>Cost-Benefit Ratio</h3>
              <div className="metric-value">{pathwaysData.cost_benefit_ratio.toFixed(2)}</div>
            </div>
          </div>

          <div className="pathway-timeline">
            <h3>Intervention Timeline</h3>
            {pathwaysData.interventions.map((intervention: any, index: number) => (
              <div key={index} className="timeline-item">
                <div className="timeline-year">{intervention.year}</div>
                <div className="timeline-content">
                  <h4>{intervention.type.replace(/_/g, ' ')}</h4>
                  <p>{intervention.description}</p>
                  <p className="cost">Cost: {formatINR(intervention.cost)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="pathways-placeholder">
          <p>Adjust parameters and click "Generate Pathway" to see adaptation strategies</p>
        </div>
      )}
    </div>
  );
};

export default PathwaysPanel;