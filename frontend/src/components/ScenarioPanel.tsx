import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ScenarioPanelProps {
  siteData: any; // Site type
  scenarioResult: any | null;
  onRunScenario: (rainfallFraction: number, includeIntervention: boolean) => Promise<void>;
  loading: boolean;
  error: string | null;
}

const ScenarioPanel: React.FC<ScenarioPanelProps> = ({
  siteData,
  scenarioResult,
  onRunScenario,
  loading,
  error
}) => {
  const [rainfallFraction, setRainfallFraction] = useState<number>(1.0);
  const [includeIntervention, setIncludeIntervention] = useState<boolean>(true);


  const handleRunScenario = async () => {
    await onRunScenario(rainfallFraction, includeIntervention);
  };

  if (!siteData) {
    return (
      <div className="scenario-panel">
        <div className="panel-placeholder">Select a settlement to run scenarios</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="scenario-panel">
        <div className="panel-loading">Running scenario...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="scenario-panel">
        <div className="panel-error">{error}</div>
      </div>
    );
  }

  // Calculate summer deficit (simplified)
  const calculateSummerDeficit = (rainfallFraction: number): number => {
    // This would be calculated based on actual data
    // For demo, we'll use a simple inverse relationship
    return Math.max(0, (1 - rainfallFraction) * 50); // 0-50 scale
  };

  const summerDeficit = calculateSummerDeficit(rainfallFraction);

  // Prepare chart data
  const chartData = scenarioResult ? [
    {
      name: 'Recharge Suitability',
      recharge: siteData.recharge_suitability,
      scenario: scenarioResult.recharge_suitability
    },
    {
      name: 'Heat-Water Stress',
      stress: siteData.heat_water_stress,
      scenario: scenarioResult.heat_water_stress
    },
    {
      name: 'Spring Risk',
      spring: siteData.spring_risk,
      scenario: scenarioResult.spring_risk
    }
  ] : [
    {
      name: 'Recharge Suitability',
      recharge: siteData.recharge_suitability,
      scenario: siteData.recharge_suitability
    },
    {
      name: 'Heat-Water Stress',
      stress: siteData.heat_water_stress,
      scenario: siteData.heat_water_stress
    },
    {
      name: 'Spring Risk',
      spring: siteData.spring_risk,
      scenario: siteData.spring_risk
    }
  ];

  return (
    <div className="scenario-panel">
      <div className="panel-header">
        <h2>Climate Scenario Analysis</h2>
        <p>Adjust rainfall and intervention to see impacts</p>
      </div>

      <div className="scenario-controls">
        <div className="control-group">
          <label>Rainfall Fraction:</label>
          <div className="slider-container">
            <input
              type="range"
              min="0.5"
              max="1.5"
              step="0.05"
              value={rainfallFraction}
              onChange={(e) => setRainfallFraction(parseFloat(e.target.value))}
            />
            <span>{rainfallFraction.toFixed(2)}x</span>
          </div>
          <p className="help-text">0.5x = Severe drought, 1.5x = Severe flooding</p>
        </div>

        <div className="control-group">
          <label>
            <input
              type="checkbox"
              checked={includeIntervention}
              onChange={(e) => setIncludeIntervention(e.target.checked)}
            />
            Include Intervention Benefits
          </label>
          <p className="help-text">Show how recommended interventions perform under this scenario</p>
        </div>

        <button className="run-scenario-btn" onClick={handleRunScenario}>
          Run Scenario
        </button>
      </div>

      <div className="scenario-results">
        {scenarioResult ? (
          <>
            <div className="result-card">
              <h3>Summer Deficit Index</h3>
              <div className="metric-value">{summerDeficit.toFixed(1)}</div>
              <p className="metric-label">(0 = No deficit, 50 = Extreme deficit)</p>
            </div>

            <div className="result-card">
              <h3>Safety Verdict</h3>
              <div className={`safety-badge ${scenarioResult.safety_verdict.toLowerCase()}`}>
                {scenarioResult.safety_verdict}
              </div>
              <p className="confidence-note">
                Confidence: {scenarioResult.confidence_level} ({scenarioResult.data_quality_note})
              </p>
            </div>

            {scenarioResult.intervention_performance && (
              <div className="result-card">
                <h3>Intervention Performance</h3>
                <p>Cost Effectiveness: {scenarioResult.intervention_performance.cost_effectiveness.toFixed(2)}</p>
                <p>Benefit Ratio: {scenarioResult.intervention_performance.benefit_ratio.toFixed(2)}</p>
              </div>
            )}
          </>
        ) : (
          <div className="current-conditions">
            <h3>Current Conditions (Baseline)</h3>
            <p>Showing site-specific scores without scenario modification</p>
          </div>
        )}
      </div>

      {/* Recharts Chart */}
      <div className="scenario-chart">
        <h3>Score Comparison: Current vs Scenario</h3>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart
            data={chartData}
            margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="recharge" stroke="#FF6B6B" name="Recharge" />
            <Line type="monotone" dataKey="stress" stroke="#4ECDC4" name="Heat-Water Stress" />
            <Line type="monotone" dataKey="spring" stroke="#45B7D1" name="Spring Risk" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ScenarioPanel;