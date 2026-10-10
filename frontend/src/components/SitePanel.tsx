import React from 'react';
import type { FactorContribution, Site } from '../types';

interface SitePanelProps {
  siteData: Site | null;
  loading: boolean;
  error: string | null;
}

// Confidence level to color mapping
const confidenceColors: Record<string, string> = {
  'High': '#4CAF50',    // Green
  'Medium': '#FF9800',  // Orange
  'Low': '#F44336',     // Red
  'Very High': '#8BC34A', // Light green
  'Very Low': '#E91E63'  // Pink
};

// Confidence level to label mapping
const confidenceLabels: Record<string, string> = {
  'high': 'High',
  'medium': 'Medium',
  'low': 'Low',
  'very_high': 'Very High',
  'very_low': 'Very Low'
};

// Safety verdict colors
const safetyColors: Record<string, string> = {
  'REJECTED': '#F44336',   // Red
  'CONDITIONAL': '#FF9800', // Orange
  'SAFE': '#4CAF50'        // Green
};

// Safety verdict labels
const safetyLabels: Record<string, string> = {
  'REJECTED': 'Not Recommended',
  'CONDITIONAL': 'Conditionally Recommended',
  'SAFE': 'Recommended'
};

// Provenance type colors
const provenanceColors: Record<string, string> = {
  'derived': '#2196F3',   // Blue
  'curated': '#9C27B0',   // Purple
  'assumed': '#FF5722'    // Deep orange
};

// Provenance type labels
const provenanceLabels: Record<string, string> = {
  'derived': 'Measured/Verified',
  'curated': 'Curated/Interpolated',
  'assumed': 'Estimated/Assumed'
};

const SitePanel: React.FC<SitePanelProps> = ({ siteData, loading, error }) => {
  if (loading) {
    return (
      <div className="site-panel">
        <div className="panel-loading">Loading site data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="site-panel">
        <div className="panel-error">{error}</div>
      </div>
    );
  }

  if (!siteData) {
    return (
      <div className="site-panel">
        <div className="panel-placeholder">Select a settlement to view details</div>
      </div>
    );
  }

  // Helper to format number with one decimal place
  const formatScore = (score: number): string => {
    return score.toFixed(1);
  };

  // Get confidence label and color
  const confidenceLevel = confidenceLabels[siteData.confidence_level.toLowerCase()] || siteData.confidence_level;
  const confidenceColor = confidenceColors[confidenceLevel] || '#9E9E9E';

  // Get safety verdict color and label
  const safetyColor = safetyColors[siteData.safety_verdict] || '#9E9E9E';
  const safetyLabel = safetyLabels[siteData.safety_verdict] || siteData.safety_verdict;

  return (
    <div className="site-panel">
      <div className="panel-header">
        <h2>Site Assessment: {siteData.site_id}</h2>
        <div className="safety-badge" style={{ backgroundColor: safetyColor }}>
          {safetyLabel}
        </div>
      </div>

      <div className="score-cards">
        {/* Recharge Suitability */}
        <div className="score-card">
          <h3>Groundwater Recharge</h3>
          <div className="score-value">{formatScore(siteData.recharge_suitability)}</div>
          <div className="score-tier">Tier: {siteData.recharge_tier}</div>
          <div className="score-drivers">
            <h4>Key Drivers:</h4>
            <div className="driver-bars">
              {siteData.recharge_factors.map((factor: FactorContribution, index: number) => (
                <div key={index} className="driver-bar">
                  <span className="driver-label">{factor.factor}</span>
                  <div className="driver-bar-container">
                    <div
                      className="driver-bar-fill"
                      style={{ width: `${factor.percentage}%` }}
                    ></div>
                  </div>
                  <span className="driver-value">{factor.percentage.toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Heat-Water Stress */}
        <div className="score-card">
          <h3>Heat-Water Stress</h3>
          <div className="score-value">{formatScore(siteData.heat_water_stress)}</div>
          <div className="score-tier">Tier: {siteData.heat_water_tier}</div>
          <div className="score-drivers">
            <h4>Key Drivers:</h4>
            <div className="driver-bars">
              {siteData.heat_water_factors.map((factor: FactorContribution, index: number) => (
                <div key={index} className="driver-bar">
                  <span className="driver-label">{factor.factor}</span>
                  <div className="driver-bar-container">
                    <div
                      className="driver-bar-fill"
                      style={{ width: `${factor.percentage}%` }}
                    ></div>
                  </div>
                  <span className="driver-value">{factor.percentage.toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Spring Risk */}
        <div className="score-card">
          <h3>Spring Desiccation Risk</h3>
          <div className="score-value">{formatScore(siteData.spring_risk)}</div>
          <div className="score-tier">Tier: {siteData.spring_risk_tier}</div>
          <div className="score-drivers">
            <h4>Key Drivers:</h4>
            <div className="driver-bars">
              {siteData.spring_risk_factors.map((factor: FactorContribution, index: number) => (
                <div key={index} className="driver-bar">
                  <span className="driver-label">{factor.factor}</span>
                  <div className="driver-bar-container">
                    <div
                      className="driver-bar-fill"
                      style={{ width: `${factor.percentage}%` }}
                    ></div>
                  </div>
                  <span className="driver-value">{factor.percentage.toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="metadata-section">
        <div className="confidence-badge" style={{ backgroundColor: confidenceColor, color: 'white' }}>
          Confidence: {confidenceLevel}
        </div>

        <div className="data-quality-note">
          <em>{siteData.data_quality_note}</em>
        </div>

        <div className="provenance-chips">
          <span className="provenance-chip"
                style={{ backgroundColor: provenanceColors.derived, color: 'white' }}>
            {provenanceLabels.derived}
          </span>
          <span className="provenance-chip"
                style={{ backgroundColor: provenanceColors.curated, color: 'white' }}>
            {provenanceLabels.curated}
          </span>
          <span className="provenance-chip"
                style={{ backgroundColor: provenanceColors.assumed, color: 'white' }}>
            {provenanceLabels.assumed}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SitePanel;