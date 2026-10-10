// TypeScript interfaces for Bhujal API responses

export interface MetaResponse {
  version: string;
  aoi_name: string;
  aoi_state: string;
  total_villages: number;
  scoring_weights_hash: string;
  data_tags_in_use: string[];
  last_pipeline_run: string; // ISO date string
  supported_states: string[];
}

export interface Village {
  village_id: string;
  name: string;
  state: string;
  district: string;
  lat: number;
  lon: number;
}

export interface Site {
  site_id: string;
  village_id: string;
  lat: number;
  lon: number;
  // Scores (0-100)
  recharge_suitability: number;
  heat_water_stress: number;
  spring_risk: number;
  // Classification tiers
  recharge_tier: string;
  heat_water_tier: string;
  spring_risk_tier: string;
  // Safety verdict
  safety_verdict: 'REJECTED' | 'CONDITIONAL' | 'SAFE';
  // Confidence metadata
  confidence_level: string;
  confidence_scalar: number;
  data_quality_note: string;
  // Recommendations
  recommendations: Recommendation[];
  // Factor contributions
  recharge_factors: FactorContribution[];
  heat_water_factors: FactorContribution[];
  spring_risk_factors: FactorContribution[];
}

export interface Recommendation {
  intervention_type: string;
  description: string;
  dimensions: string;
  cost_range_low: number;
  cost_range_high: number;
  cost_unit: string;
  labour_days_low: number;
  labour_days_high: number;
  reason: string;
}

export interface FactorContribution {
  factor: string;
  weight: number;
  value: number;
  contribution: number;
  // For driver bars: percentage of total score
  percentage: number;
}

export interface ScenarioResult {
  site_id: string;
  rainfall_fraction: number;
  recharge_suitability: number;
  heat_water_stress: number;
  spring_risk: number;
  recharge_tier: string;
  heat_water_tier: string;
  spring_risk_tier: string;
  safety_verdict: 'REJECTED' | 'CONDITIONAL' | 'SAFE';
  confidence_level: string;
  confidence_scalar: number;
  data_quality_note: string;
  intervention_performance: {
    // How interventions perform under this scenario
    cost_effectiveness: number;
    benefit_ratio: number;
  };
}

export interface Pathway {
  ssp_scenario: string;
  years: number[]; // e.g., [2025, 2030, 2035, 2040, 2050]
  rainfall_fractions: number[]; // Rainfall multiplier for each year
  interventions: {
    year: number;
    type: string;
    description: string;
    cost: number;
  }[];
  // Aggregated metrics
  total_cost: number;
  total_benefit: number;
  cost_benefit_ratio: number;
}

export interface Observation {
  observation_id: string;
  site_id: string;
  observer_name: string;
  observation_type: string;
  value: number;
  unit: string;
  notes: string;
  timestamp: string; // ISO date string
  photo_url?: string;
}

export interface LeaderboardEntry {
  observer_id: string;
  observer_name: string;
  total_observations: number;
  by_type: Record<string, number>;
  rank: number;
}

export interface DPRResult {
  project_id: string;
  project_name: string;
  site_count: number;
  total_cost_inr: number;
  total_labour_days: number;
  presigned_url: string;
  manifest: {
    // DPR manifest details
    [key: string]: any;
  };
}

export interface ReportResult {
  report_id: string;
  title: string;
  generated_at: string; // ISO date string
  sites: SiteSummary[];
  narrative: string;
  // Scenario info if included
  scenario_info?: {
    rainfall_fraction: number;
    notes: string[];
  };
}

export interface SiteSummary {
  site_id: string;
  name: string;
  safety_verdict: 'REJECTED' | 'CONDITIONAL' | 'SAFE';
  recharge_suitability: number;
  heat_water_stress: number;
  spring_risk: number;
}