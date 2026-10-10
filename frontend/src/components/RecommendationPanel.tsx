import React from 'react';
import type { Recommendation } from '../types';

interface RecommendationPanelProps {
  recommendations: Recommendation[] | null;
  siteData: any; // Site type
  onGenerateDPR: (siteIds: string, projectName: string, includePdf: boolean) => Promise<void>;
}

// Intervention type icons (using emojis for simplicity)
const interventionIcons: Record<string, string> = {
  'check_dam': '💧',
  'percolation_tank': '💧',
  'contour_trench': '🌱',
  'spring_shed': '🏞️',
  'recharge_shaft': '⛏️',
  'gully_plug': '🚧',
  'pond': '💧',
  'well': '⛓️',
  'default': '🏗️'
};

const RecommendationPanel: React.FC<RecommendationPanelProps> = ({
  recommendations,
  siteData,
  onGenerateDPR
}) => {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="recommendation-panel">
        <div className="panel-placeholder">No recommendations available for this site</div>
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

  // Get intervention icon
  const getInterventionIcon = (type: string): string => {
    return interventionIcons[type.toLowerCase().replace(/\s+/g, '_')] || interventionIcons.default;
  };

  return (
    <div className="recommendation-panel">
      <div className="panel-header">
        <h2>Recommended Interventions</h2>
        <button
          className="generate-dpr-btn"
          onClick={() => {
            const siteIds = siteData ? siteData.site_id : '';
            const projectName = `Bhujal Project - ${siteData?.site_id || 'Unknown'}`;
            onGenerateDPR(siteIds, projectName, false); // include_pdf: false for now
          }}
        >
          Generate DPR Package
        </button>
      </div>

      <div className="recommendations-list">
        {recommendations.map((rec, index) => (
          <div key={index} className="recommendation-card">
            <div className="recommendation-header">
              <span className="intervention-icon">{getInterventionIcon(rec.intervention_type)}</span>
              <h3>{rec.intervention_type.replace(/_/g, ' ')}</h3>
            </div>

            <div className="recommendation-body">
              <p className="description">{rec.description}</p>

              <div className="specs-row">
                <div className="spec-item">
                  <strong>Dimensions:</strong> <span>{rec.dimensions}</span>
                </div>
                <div className="spec-item">
                  <strong>Cost Range:</strong> <span>{formatINR(rec.cost_range_low)} - {formatINR(rec.cost_range_high)}</span>
                </div>
                <div className="spec-item">
                  <strong>Labour Days:</strong> <span>{rec.labour_days_low} - {rec.labour_days_high}</span>
                </div>
              </div>

              <div className="reason-box">
                <strong>Why chosen:</strong> <p>{rec.reason}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecommendationPanel;