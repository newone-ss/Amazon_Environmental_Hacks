/**
 * Bhujal - Thin API Client (Pure JavaScript)
 * Governed by VITE_API_URL with automatic fallback to curated mock data for 13 settlements.
 */

import { MOCK_META, MOCK_VILLAGES, MOCK_SITES } from '../data/mockData.js';
import { MOCK_TELEMETRY } from '../data/mockTelemetry.js';

const API_BASE = (
  import.meta.env.VITE_API_URL !== undefined
    ? import.meta.env.VITE_API_URL
    : (typeof window !== 'undefined' && (window.location.port === '8000' || window.location.port === '5173') ? '' : 'http://localhost:8000')
).replace(/\/$/, '');

const FORCE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export class BhujalApiClient {
  constructor(base = API_BASE, forceMock = FORCE_MOCK) {
    this.base = base;
    this.forceMock = forceMock;
    this.isBackendOnline = null;
    this.lastHealthCheck = 0;
    this.healthCheckPromise = null;
  }

  async checkHealth() {
    const now = Date.now();
    if (this.healthCheckPromise) return this.healthCheckPromise;
    if (this.isBackendOnline === false && now - this.lastHealthCheck < 10000) {
      return false;
    }

    this.healthCheckPromise = (async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 1200);
        const res = await fetch(`${this.base}/meta`, {
          signal: controller.signal,
          headers: { 'X-Requested-With': 'Bhujal-Client' },
        });
        clearTimeout(timeoutId);
        const online = res.ok && res.status !== 503;
        this.isBackendOnline = online;
        this.lastHealthCheck = Date.now();
        return online;
      } catch {
        this.isBackendOnline = false;
        this.lastHealthCheck = Date.now();
        return false;
      } finally {
        this.healthCheckPromise = null;
      }
    })();

    return this.healthCheckPromise;
  }

  async fetchJson(path, options) {
    if (this.forceMock) {
      throw new Error('Mock mode enabled');
    }

    // Fast-fail non-essential requests if backend was recently confirmed offline
    if (this.isBackendOnline === false && path !== '/meta') {
      const now = Date.now();
      if (now - this.lastHealthCheck < 10000) {
        throw new Error('Backend service currently offline');
      }
      this.checkHealth();
    }

    const headers = {
      'Content-Type': 'application/json',
      'X-Requested-With': 'Bhujal-Client',
      ...(import.meta.env.VITE_API_KEY ? { 'X-API-Key': import.meta.env.VITE_API_KEY } : {}),
      ...(options?.headers || {}),
    };

    try {
      const res = await fetch(`${this.base}${path}`, {
        ...options,
        headers,
      });

      if (res.status === 503) {
        this.isBackendOnline = false;
        this.lastHealthCheck = Date.now();
        throw new Error('Backend service offline (503)');
      }

      if (!res.ok) {
        throw new Error(`API request failed: ${res.status} ${res.statusText}`);
      }

      this.isBackendOnline = true;
      return await res.json();
    } catch (err) {
      if (
        err.name === 'TypeError' ||
        err.message.includes('Failed to fetch') ||
        err.message.includes('NetworkError') ||
        err.message.includes('503')
      ) {
        this.isBackendOnline = false;
        this.lastHealthCheck = Date.now();
      }
      throw err;
    }
  }

  async getMeta() {
    try {
      return await this.fetchJson('/meta');
    } catch {
      return MOCK_META;
    }
  }

  async getVillages(state) {
    try {
      const q = state && state !== 'All states' ? `?state=${encodeURIComponent(state)}` : '';
      return await this.fetchJson(`/villages${q}`);
    } catch {
      if (!state || state === 'All states') {
        return MOCK_VILLAGES;
      }
      return MOCK_VILLAGES.filter(
        (v) => v.state.toLowerCase() === state.trim().toLowerCase()
      );
    }
  }

  async getSite(siteId) {
    try {
      return await this.fetchJson(`/sites/${siteId}`);
    } catch {
      const site = MOCK_SITES[siteId] || MOCK_SITES['site_001'];
      if (!site) {
        throw new Error(`Site not found: ${siteId}`);
      }
      return site;
    }
  }

  async getTelemetry(siteId) {
    try {
      return await this.fetchJson(`/telemetry/${siteId}`);
    } catch {
      return MOCK_TELEMETRY[siteId] || null;
    }
  }

  async runScenario(request) {
    try {
      return await this.fetchJson('/scenario', {
        method: 'POST',
        body: JSON.stringify(request),
      });
    } catch {
      const baseSite = MOCK_SITES[request.site_id] || MOCK_SITES['site_001'];
      const baseScores = baseSite.scores || [];
      const rf = request.rainfall_fraction || 1.0;

      const adjustedScores = baseScores.map((s) => {
        if (s.score_type === 'recharge_score') {
          const delta = (rf - 1.0) * 22;
          const newVal = Math.min(100, Math.max(0, +(s.value + delta).toFixed(1)));
          return {
            ...s,
            value: newVal,
            data_quality_note: `Simulated at ${(rf * 100).toFixed(0)}% monsoon baseline`,
          };
        }
        if (s.score_type === 'heat_water_stress') {
          const delta = -(rf - 1.0) * 16;
          const newVal = Math.min(100, Math.max(0, +(s.value + delta).toFixed(1)));
          return {
            ...s,
            value: newVal,
            data_quality_note: `Simulated at ${(rf * 100).toFixed(0)}% monsoon baseline`,
          };
        }
        if (s.score_type === 'spring_drying_index') {
          const delta = -(rf - 1.0) * 20;
          const newVal = Math.min(100, Math.max(0, +(s.value + delta).toFixed(1)));
          return {
            ...s,
            value: newVal,
            data_quality_note: `Simulated at ${(rf * 100).toFixed(0)}% monsoon baseline`,
          };
        }
        return s;
      });

      return {
        site_id: request.site_id,
        baseline_scores: baseScores,
        adjusted_scores: adjustedScores,
        rainfall_mm_baseline: 1150.0,
        rainfall_mm_adjusted: +(1150.0 * rf).toFixed(1),
        intervention_applied: request.include_intervention || null,
        notes: [
          `Rainfall fraction ${rf.toFixed(2)}x applied to site catchment baseline.`,
          `Deterministic sensitivity scenario; not a weather forecast.`,
        ],
      };
    }
  }

  async getRecommendations(siteId) {
    try {
      return await this.fetchJson('/recommendation', {
        method: 'POST',
        body: JSON.stringify({ site_id: siteId }),
      });
    } catch {
      const site = MOCK_SITES[siteId];
      return site?.recommendations || [];
    }
  }

  async getUploadUrl(filename, contentType = 'image/jpeg') {
    try {
      return await this.fetchJson(`/upload-url?filename=${encodeURIComponent(filename)}&content_type=${encodeURIComponent(contentType)}`);
    } catch {
      return {
        upload_url: `https://bhujal-observations-bucket.s3.ap-south-1.amazonaws.com/uploads/${Date.now()}_${filename}?mock_presigned=true`,
        file_key: `uploads/${Date.now()}_${filename}`,
      };
    }
  }

  async submitObservation(obs) {
    try {
      return await this.fetchJson('/observations', {
        method: 'POST',
        body: JSON.stringify(obs),
      });
    } catch {
      return {
        ...obs,
        observation_id: `obs_${Date.now()}`,
        timestamp: new Date().toISOString(),
        photo_url: null,
      };
    }
  }

  async generateReport(req) {
    try {
      return await this.fetchJson('/report', {
        method: 'POST',
        body: JSON.stringify(req),
      });
    } catch {
      return {
        report_id: `rep_${Date.now()}`,
        title: `Bhujal Site Action Brief (${req.site_ids.length} settlements)`,
        generated_at: new Date().toISOString(),
        site_count: req.site_ids.length,
        download_url: '#',
        format: 'html',
        summary: `Planner action dossier compiled across ${req.site_ids.length} settlement locations.`,
      };
    }
  }

  async generateDpr(siteIds, projectName = 'Bhujal Watershed Plan') {
    try {
      return await this.fetchJson('/dpr/generate', {
        method: 'POST',
        body: JSON.stringify({
          site_ids: siteIds,
          project_name: projectName,
          include_pdf: false,
        }),
      });
    } catch {
      return {
        project_name: projectName,
        download_url: `/dpr/download/${siteIds[0] || 'demo'}.zip`,
        sites_included: siteIds.length,
        total_budget_inr: 850000,
        total_cost_inr: 850000,
        total_labour_days: 140,
        artifacts: [
          'dpr_executive_summary.md',
          'mgnrega_schedule_of_rates.csv',
          'site_engineering_estimates.json',
          'verification_checklist.pdf',
        ],
        sha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
        generated_at: new Date().toISOString(),
      };
    }
  }

  async getAgentBriefing(siteId) {
    try {
      return await this.fetchJson(`/agent/briefing/${encodeURIComponent(siteId)}`);
    } catch {
      const site = MOCK_SITES[siteId] || MOCK_SITES['site_001'];
      const vname = site.village?.name || 'Target Site';
      const isRej = site.safety?.status === 'REJECTED';
      return {
        site_id: siteId,
        village_name: vname,
        safety_status: site.safety?.status || 'SAFE',
        executive_decision: isRej
          ? `ACTION PROHIBITED: ${vname} has been issued a formal SAFETY VETO. Construction is strictly rejected.`
          : `ACTION APPROVED: ${vname} is cleared for civil development (${site.safety?.status || 'SAFE'}).`,
        agent_briefings: {
          hydrogeology: {
            agent_name: 'HydrogeologyAgent',
            role: 'Senior Hard-Rock Hydrogeologist',
            summary: `Evaluated ${vname} lithological secondary porosity and groundwater recharge potential.`,
            narrative: `Hydrogeological regime indicates fracture permeability in weathered crystalline basement.`,
            recommendations: ['Prioritize ridge-to-valley recharge cascading structures.'],
            mode: 'deterministic_fallback',
          },
          heat_water_stress: {
            agent_name: 'HeatWaterStressAgent',
            role: 'Heat-Water Nexus Climatologist',
            summary: `Summer heat stress and water deficit index analysis for ${vname}.`,
            narrative: `Compound heat-water stress escalates pre-monsoon distress for tribal farmsteads.`,
            recommendations: ['Sanction surface pondage and water retention bodies before May.'],
            mode: 'deterministic_fallback',
          },
          springshed: {
            agent_name: 'SpringshedAgent',
            role: 'Mountain Springshed Hydrologist',
            summary: `Assessed gravity-fed springhead catchment protection.`,
            narrative: `Recharge zone protection in upper elevation ridges maintains dry-season spring baseflow.`,
            recommendations: ['Construct Continuous Staggered Contour Trenches on upper slopes.'],
            mode: 'deterministic_fallback',
          },
          safety_audit: {
            agent_name: 'SafetyAuditorAgent',
            role: 'Geotechnical Safety Auditor',
            summary: `Geotechnical hazard audit verdict: ${site.safety?.status || 'SAFE'}.`,
            narrative: `Reviewed slope gradients (>35°), active landslide zones, and scarp stability.`,
            recommendations: isRej ? ['Enforce strict construction stop.'] : ['Proceed with standard safety setbacks.'],
            mode: 'deterministic_fallback',
          },
          civil_engineering: {
            agent_name: 'InterventionComposerAgent',
            role: 'MGNREGA Principal Civil Engineer',
            summary: `Engineering intervention specifications and state wage schedules.`,
            narrative: `Recommended structures calibrated to state schedule of rates and 60:40 labor ratios.`,
            recommendations: site.recommendations?.map((r) => r.intervention_name) || ['Bio-engineering soil conservation'],
            mode: 'deterministic_fallback',
          },
        },
      };
    }
  }

  async consultAgent(siteId, query, agentType = null) {
    try {
      return await this.fetchJson('/agent/consult', {
        method: 'POST',
        body: JSON.stringify({
          site_id: siteId,
          query: query,
          agent_type: agentType,
        }),
      });
    } catch {
      const site = MOCK_SITES[siteId] || MOCK_SITES['site_001'];
      const vname = site.village?.name || 'Target Site';
      const isRej = site.safety?.status === 'REJECTED';
      const qLower = query.toLowerCase();

      let ans = `Lead District Planner Assessment for ${vname}: Ground investigation indicates cleared suitability for development. Coordinate with Gram Panchayat.`;
      let recs = ['Verify field benchmarks with Junior Engineer.'];

      if (isRej) {
        ans = `SAFETY VETO ENFORCED: As Lead District Planner, I must advise that ${vname} is REJECTED due to geotechnical hazard rules (${site.safety?.rule_ids?.join(', ') || 'SLOPE_STEEP'}). Heavy civil structures are prohibited to prevent slope destabilization.`;
        recs = [
          'Prohibit capital expenditure for heavy masonry civil works.',
          'Redirect funds to bio-engineering and vegetative stabilization.',
        ];
      } else if (qLower.includes('spring') || qLower.includes('water')) {
        ans = `Springshed Assessment for ${vname}: Catchment recharge zone protection is prioritized. Continuous contour trenches on upper ridges will improve infiltration.`;
        recs = [
          'Map upper micro-catchment recharge zone using GPS tracking.',
          'Construct loose boulder structures in 1st order drainage streams.',
        ];
      } else if (qLower.includes('cost') || qLower.includes('budget') || qLower.includes('mgnrega')) {
        const topRec = site.recommendations?.[0];
        ans = `MGNREGA Budget Specification for ${vname}: Recommended intervention '${topRec?.intervention_name || 'Check Dam'}' estimated at INR ${(topRec?.cost_range_inr?.low || 150000).toLocaleString()} - ${(topRec?.cost_range_inr?.high || 450000).toLocaleString()} (${topRec?.labour_days || 120} person-days).`;
        recs = [`Submit proposal under MGNREGA 60:40 schedule for ${topRec?.intervention_name || 'structures'}.`];
      }

      return {
        site_id: siteId,
        village_name: vname,
        query: query,
        agent_name: 'LeadPlannerOrchestratorAgent',
        role: 'Lead District Planner & Dossier Orchestrator',
        safety_status: site.safety?.status || 'SAFE',
        response: ans,
        recommendations: recs,
        mode: 'deterministic_fallback',
        timestamp: new Date().toISOString(),
      };
    }
  }

  async synthesizePlan(siteIds) {
    try {
      return await this.fetchJson('/agent/synthesize', {
        method: 'POST',
        body: JSON.stringify({ site_ids: siteIds }),
      });
    } catch {
      return {
        summary: `Synthesized multi-site plan across ${siteIds.length} settlements.`,
        narrative: `Executive watershed planning dossier compiled for ${siteIds.length} target locations.`,
        recommendations: [
          'Forward approved site dossiers to District Watershed Committee.',
          'Enforce geotechnical safety vetoes on flagged terrain.',
        ],
        mode: 'deterministic_fallback',
      };
    }
  }

  // ── Observations & Participatory Community Telemetry ─────────

  async getObservations(siteId = null) {
    try {
      const q = siteId ? `?site_id=${encodeURIComponent(siteId)}` : '';
      return await this.fetchJson(`/observations${q}`);
    } catch {
      return [];
    }
  }

  async getDistrictGroundwater(district) {
    try {
      return await this.fetchJson(`/telemetry/districts/${encodeURIComponent(district)}/groundwater`);
    } catch {
      return null;
    }
  }

  async getParticipatoryLeaderboard(state = null, limit = 20) {
    try {
      const params = new URLSearchParams();
      if (state) params.append('state', state);
      if (limit) params.append('limit', limit);
      const q = params.toString() ? `?${params.toString()}` : '';
      return await this.fetchJson(`/participatory/leaderboard${q}`);
    } catch {
      return [];
    }
  }

  async getObserverStats(observerId) {
    try {
      return await this.fetchJson(`/participatory/stats/${encodeURIComponent(observerId)}`);
    } catch {
      return null;
    }
  }

  async submitTextObservation(text, observerId, observerName = '', languageCode = 'en-IN') {
    const form = new FormData();
    form.append('text', text);
    form.append('observer_id', observerId);
    form.append('observer_name', observerName);
    form.append('language_code', languageCode);
    const res = await fetch(`${this.base}/participatory/observe/text`, {
      method: 'POST',
      body: form,
    });
    if (!res.ok) throw new Error('Text observation failed');
    return res.json();
  }

  async submitWhatsAppObservation(fromPhone, body) {
    return await this.fetchJson('/participatory/observe/whatsapp', {
      method: 'POST',
      body: JSON.stringify({
        From: fromPhone.startsWith('whatsapp:') ? fromPhone : `whatsapp:${fromPhone}`,
        Body: body,
      }),
    });
  }

  // ── Climate Adaptation Pathways ───────────────────────────────

  async getPathwayScenarios() {
    try {
      return await this.fetchJson('/pathways/scenarios');
    } catch {
      return [
        { id: 'SSP1-2.6', name: 'Low Emissions (Sustainability)', description: 'Paris 1.5°C goal' },
        { id: 'SSP2-4.5', name: 'Middle of the Road (Current Trends)', description: 'Intermediate emissions' },
        { id: 'SSP3-7.0', name: 'Regional Rivalry (High Vulnerability)', description: 'High emissions, low resilience' },
        { id: 'SSP5-8.5', name: 'Fossil-Fueled Development (Worst Case)', description: 'Extreme heating & variability' },
      ];
    }
  }

  async generatePathway(siteId, sspScenario = 'SSP2-4.5', baseRainfallFraction = 1.0) {
    try {
      return await this.fetchJson('/pathways/generate', {
        method: 'POST',
        body: JSON.stringify({
          site_id: siteId,
          ssp_scenario: sspScenario,
          base_rainfall_fraction: baseRainfallFraction,
        }),
      });
    } catch {
      return null;
    }
  }

  async comparePathways(siteId, scenarios = 'SSP1-2.6,SSP2-4.5,SSP3-7.0,SSP5-8.5', baseRainfallFraction = 1.0) {
    try {
      return await this.fetchJson('/pathways/compare', {
        method: 'POST',
        body: JSON.stringify({
          site_id: siteId,
          scenarios: scenarios,
          base_rainfall_fraction: baseRainfallFraction,
        }),
      });
    } catch {
      return {};
    }
  }

  async getPathwayVisualization(siteId, sspScenario = 'SSP2-4.5', baseRainfallFraction = 1.0) {
    try {
      return await this.fetchJson(
        `/pathways/visualize/${encodeURIComponent(siteId)}/${encodeURIComponent(sspScenario)}?base_rainfall_fraction=${baseRainfallFraction}`
      );
    } catch {
      return null;
    }
  }

  // ── DPR Engineering & Government Scheme Mapping ───────────────

  async getDprSchemes() {
    try {
      return await this.fetchJson('/dpr/schemes');
    } catch {
      return {};
    }
  }

  // ── Spatial AOI Boundary ──────────────────────────────────────

  async getAoiGeoJson() {
    try {
      const res = await fetch(`${this.base}/aoi.geojson`);
      if (!res.ok) throw new Error('Failed to load AOI geojson');
      return res.json();
    } catch {
      return null;
    }
  }
}

export const api = new BhujalApiClient();


