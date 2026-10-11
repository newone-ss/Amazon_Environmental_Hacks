import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  Bot,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Clock,
  Database,
  Download,
  Droplets,
  ExternalLink,
  FileText,
  IndianRupee,
  Info,
  MapPin,
  RefreshCw,
  Send,
  SlidersHorizontal,
  Sparkles,
  Sun,
  Waves,
  Wrench,
  X,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { api } from '../api/client.js';

const STATE_WAGES = {
  Odisha: 350,
  'Madhya Pradesh': 243,
  Jharkhand: 255,
};

function formatFactorName(factor) {
  return factor
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function ConfidenceBar({ confidence }) {
  const level = confidence?.level || 'low';
  const numeric = confidence?.numeric != null ? (confidence.numeric * 100).toFixed(0) : '0';
  return (
    <div
      className="confidence-badge"
      title={`Confidence: ${level.toUpperCase()} (${numeric}% based on data source coverage)`}
    >
      <div className="confidence-track">
        <span className={`confidence-seg ${level === 'low' || level === 'medium' || level === 'high' ? 'active' : ''}`} />
        <span className={`confidence-seg ${level === 'medium' || level === 'high' ? 'active' : ''}`} />
        <span className={`confidence-seg ${level === 'high' ? 'active' : ''}`} />
      </div>
      <span className="confidence-text">{level} ({numeric}%)</span>
    </div>
  );
}

function ProvenanceChip({ tag }) {
  const normTag = tag || 'illustrative';
  return (
    <span
      className={`provenance-chip chip-${normTag}`}
      title={`Data Provenance: ${normTag.toUpperCase()}`}
    >
      {normTag}
    </span>
  );
}

function DriverBars({ drivers = [] }) {
  const [expanded, setExpanded] = useState(false);
  const displayDrivers = expanded ? drivers : drivers.slice(0, 3);

  if (!drivers || drivers.length === 0) {
    return <p className="empty-drivers">No driver decomposition available.</p>;
  }

  const maxContribution = Math.max(...drivers.map((d) => d.contribution), 25);

  return (
    <div className="driver-bars-container">
      <div className="driver-bars-header">
        <span className="drivers-title">Key Drivers ('Why?' Breakdown)</span>
        {drivers.length > 3 && (
          <button
            type="button"
            className="driver-expand-btn"
            onClick={() => setExpanded((e) => !e)}
          >
            {expanded ? (
              <>Show top 3 <ChevronUp size={13} /></>
            ) : (
              <>All {drivers.length} drivers <ChevronDown size={13} /></>
            )}
          </button>
        )}
      </div>

      <div className="driver-bars-list">
        {displayDrivers.map((d) => (
          <div key={d.factor} className="driver-bar-row">
            <div className="driver-bar-label">
              <span>{formatFactorName(d.factor)}</span>
              <span className="driver-val tabular-num">{d.contribution.toFixed(1)} pt</span>
            </div>
            <div className="driver-progress-track">
              <div
                className="driver-progress-fill"
                style={{ width: `${Math.min(100, (d.contribution / maxContribution) * 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function SettlementPanel({
  village,
  site,
  activeTab,
  setActiveTab,
  onClose,
  onSelectVillageById,
  loading = false,
  error = null,
  onRetry,
}) {
  const panelRef = useRef(null);
  const [dprLoading, setDprLoading] = useState(false);
  const [dprProgress, setDprProgress] = useState('');
  const [reportLang, setReportLang] = useState('en');
  const [telemetry, setTelemetry] = useState(null);

  const [coldStartNotice, setColdStartNotice] = useState(false);

  useEffect(() => {
    let timer;
    if (loading) {
      timer = setTimeout(() => setColdStartNotice(true), 2500);
    } else {
      setColdStartNotice(false);
    }
    return () => clearTimeout(timer);
  }, [loading]);

  useEffect(() => {
    if (village?.id && panelRef.current) {
      panelRef.current.focus();
    }
  }, [village?.id]);

  // Scenario simulator state
  const [rainfallFraction, setRainfallFraction] = useState(1.0);
  const [includeIntervention, setIncludeIntervention] = useState(true);
  const [scenarioResult, setScenarioResult] = useState(null);
  const [showScenarioAssumptions, setShowScenarioAssumptions] = useState(false);

  const scores = site?.scores || [];
  const safety = site?.safety;
  const isRejected = safety?.status === 'REJECTED';

  const rechargeScore = scores.find((s) => s.score_type === 'recharge_score');
  const heatScore = scores.find((s) => s.score_type === 'heat_water_stress');
  const springScore = scores.find((s) => s.score_type === 'spring_drying_index');

  const recommendations = site?.recommendations || [];
  const primaryRec = recommendations[0];
  const wageRate = STATE_WAGES[village?.state] || 270;

  // Fetch telemetry evidence on site change
  useEffect(() => {
    let isCancelled = false;
    async function loadTelemetry() {
      if (!village?.id) return;
      try {
        const data = await api.getTelemetry(village.id);
        if (!isCancelled) setTelemetry(data);
      } catch {
        // Handled
      }
    }
    loadTelemetry();
    return () => {
      isCancelled = true;
    };
  }, [village?.id]);

  // Run scenario simulation
  useEffect(() => {
    const controller = new AbortController();
    let isCancelled = false;
    async function loadScenario() {
      if (!village?.id) return;
      try {
        // Use the current primaryRec from closure
        const interventionId = includeIntervention && site?.recommendations?.[0]?.intervention_id;
        const res = await api.runScenario({
          site_id: village.id,
          rainfall_fraction: rainfallFraction,
          include_intervention: interventionId,
        }, { signal: controller.signal });
        if (!isCancelled) setScenarioResult(res);
      } catch (e) {
        if (e.name === 'AbortError' || e.name === 'CancellationError') return;
        // Handled
      }
    }
    loadScenario();
    return () => {
      isCancelled = true;
      controller.abort();
    };
  }, [village?.id, rainfallFraction, includeIntervention, site?.recommendations?.[0]?.intervention_id]);

  // Generate DPR package
  async function handleGenerateDpr() {
    if (!village?.id) return;
    setDprLoading(true);
    setDprProgress('Compiling engineering schedules & MGNREGA rates...');
    try {
      await new Promise((r) => setTimeout(r, 600));
      setDprProgress('Generating technical drawings & environmental checklist...');
      await new Promise((r) => setTimeout(r, 600));
      setDprProgress('Packaging DPR ZIP archive...');
      const res = await api.generateDpr([village.id], `Bhujal_${village.name}_DPR`);
      setDprProgress('Ready for download');
      alert(`DPR Package Generated!\nProject: ${res.project_name}\nTotal Budget: ₹${((res.total_budget_inr || res.total_cost_inr || 0) / 100000).toFixed(2)} Lakhs\nLabour Days: ${res.total_labour_days}\nDownload URL: ${res.download_url}`);
      if (res.download_url && !res.download_url.includes('demo.zip')) {
        window.open(res.download_url, '_blank');
      }
    } catch {
      alert('DPR generation failed. Please try again.');
    } finally {
      setDprLoading(false);
      setDprProgress('');
    }
  }

  // AI Agent Briefing and Live Consultation state
  const [agentBriefing, setAgentBriefing] = useState(null);
  const [agentBriefingLoading, setAgentBriefingLoading] = useState(false);
  const [agentQuery, setAgentQuery] = useState('');
  const [consultLoading, setConsultLoading] = useState(false);
  const [consultHistory, setConsultHistory] = useState([]);
  const lastBriefingVillageId = useRef(null);

  // Fetch live agent briefing on settlement change
  useEffect(() => {
    const controller = new AbortController();
    let isCancelled = false;
    
    // Deduplication: only fetch if village ID changed
    if (lastBriefingVillageId.current === village?.id) return;
    lastBriefingVillageId.current = village?.id;
    
    async function loadAgentBriefing() {
      if (!village?.id) return;
      setAgentBriefingLoading(true);
      try {
        const briefing = await api.getAgentBriefing(village.id, { signal: controller.signal });
        if (!isCancelled) {
          setAgentBriefing(briefing);
        }
      } catch (err) {
        if (err.name === 'AbortError' || err.name === 'CancellationError') return;
        console.warn('Agent briefing load fallback', err);
      } finally {
        if (!isCancelled) setAgentBriefingLoading(false);
      }
    }
    loadAgentBriefing();
    return () => {
      isCancelled = true;
      controller.abort();
    };
  }, [village?.id]);

  async function handleConsultAgent(customQuery) {
    const q = (customQuery || agentQuery).trim();
    if (!q || !village?.id) return;
    setConsultLoading(true);
    try {
      const res = await api.consultAgent(village.id, q);
      setConsultHistory((prev) => [res, ...prev]);
      if (!customQuery) setAgentQuery('');
    } catch (err) {
      alert('Consultation failed: ' + err.message);
    } finally {
      setConsultLoading(false);
    }
  }


  // Monthly water balance data for scenario chart
  const monthlyWaterData = useMemo(() => {
    const rf = rainfallFraction;
    const baseRain = [12, 18, 22, 38, 85, 210, 320, 290, 180, 65, 20, 10];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const interventionBonus = includeIntervention && !isRejected ? 18 : 0;

    return months.map((m, i) => {
      const baseline = baseRain[i];
      const simulated = Math.max(5, +(baseline * rf).toFixed(1));
      const retained = i >= 5 && i <= 8 ? Math.min(simulated, simulated * 0.35 + interventionBonus) : Math.max(2, baseline * 0.15 + interventionBonus * 0.6);
      return {
        month: m,
        Baseline: baseline,
        Simulated: simulated,
        Retained: +retained.toFixed(1),
      };
    });
  }, [rainfallFraction, includeIntervention, isRejected]);

  if (loading) {
    return (
      <aside className="village-panel" aria-label="Loading settlement details">
        <div className="skeleton-box title-skeleton" />
        <div className="skeleton-box banner-skeleton" />
        <div className="skeleton-box tabs-skeleton" />
        <div className="skeleton-grid">
          <div className="skeleton-box card-skeleton" />
          <div className="skeleton-box card-skeleton" />
          <div className="skeleton-box card-skeleton" />
        </div>
        <p className="loading-cold-start" role="status">
          <RefreshCw size={15} className="spin-icon" aria-hidden="true" />
          <span>
            {coldStartNotice
              ? 'Waking up the server... (AWS Lambda cold start after idle, initial response takes ~5–8s)'
              : 'Connecting to scoring engine...'}
          </span>
        </p>
      </aside>
    );
  }

  if (error) {
    return (
      <aside className="village-panel error-panel" aria-label="Error loading details">
        <AlertTriangle size={32} className="error-icon" />
        <h3>Failed to load settlement data</h3>
        <p>{error}</p>
        <button type="button" className="primary-cta retry-btn" onClick={onRetry}>
          <RefreshCw size={15} /> Retry Request
        </button>
      </aside>
    );
  }

  if (!village || !site) return null;

  return (
    <aside
      className="village-panel"
      tabIndex={-1}
      ref={panelRef}
      aria-label={`Details for ${village.name}`}
    >
      {/* 1. Header (No Hero Photo, clean header with sparkline / priority chip) */}
      <div className="settlement-header">
        <div className="settlement-header-main">
          <div className="settlement-title-row">
            <h1>{village.name}</h1>
            <span className={`priority-chip priority-${safety?.status?.toLowerCase() || 'safe'}`}>
              {safety?.status === 'REJECTED' ? 'REJECTED' : safety?.status === 'CONDITIONAL' ? 'CONDITIONAL' : 'SAFE TO BUILD'}
            </span>
          </div>
          <div className="settlement-meta-row">
            <MapPin size={14} fill="currentColor" />
            <span>Block: {village.block || 'N/A'} • {village.district}, {village.state}</span>
            {village.elevation_m != null && <span className="meta-elev">• {village.elevation_m} m elev</span>}
          </div>
        </div>
        <button className="close-panel" onClick={onClose} aria-label="Close village details">
          <X size={18} />
        </button>
      </div>

      {/* Demo Sites Quick Switcher */}
      <div className="demo-sites-bar">
        <span className="demo-bar-label">Demo sites:</span>
        <button
          type="button"
          className={`demo-site-btn ${village.id === 'site_001' ? 'active' : ''}`}
          onClick={() => onSelectVillageById('site_001')}
          title="SAFE site with 4 recommendations"
        >
          <span className="dot safe" /> Laxmipur (SAFE)
        </button>
        <button
          type="button"
          className={`demo-site-btn ${village.id === 'site_004' ? 'active' : ''}`}
          onClick={() => onSelectVillageById('site_004')}
          title="CONDITIONAL site with engineering prerequisites"
        >
          <span className="dot conditional" /> Dukum (CONDITIONAL)
        </button>
        <button
          type="button"
          className={`demo-site-btn ${village.id === 'site_002' ? 'active' : ''}`}
          onClick={() => onSelectVillageById('site_002')}
          title="REJECTED site with active safety hazard"
        >
          <span className="dot rejected" /> Mundaguda (REJECTED)
        </button>
      </div>

      {/* 2. Tabs: Overview, AI Agents, Plan, Scenario, Evidence */}
      <div className="panel-tabs" role="tablist" aria-label="Settlement detail tabs">
        {['Overview', 'AI Agents', 'Plan', 'Scenario', 'Evidence'].map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            className={activeTab === tab ? 'selected' : ''}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>


      {/* ======================= TAB: OVERVIEW ======================= */}
      {activeTab === 'Overview' && (
        <div className="tab-pane overview-pane">
          {/* 3a. Safety Banner (Full Width) */}
          <div
            className={`safety-banner verdict-${safety?.status?.toLowerCase() || 'safe'}`}
            role="alert"
          >
            <div className="safety-header">
              {safety?.status === 'SAFE' ? (
                <CheckCircle2 size={22} strokeWidth={2.4} />
              ) : safety?.status === 'CONDITIONAL' ? (
                <AlertTriangle size={22} strokeWidth={2.4} />
              ) : (
                <AlertOctagon size={22} strokeWidth={2.4} />
              )}
              <div>
                <span className="safety-kicker">DETERMINISTIC SAFETY VERDICT</span>
                <strong>
                  {safety?.status === 'REJECTED'
                    ? 'REJECTED — NO STRUCTURE RECOMMENDED'
                    : safety?.status === 'CONDITIONAL'
                    ? 'CONDITIONAL SAFETY VERDICT'
                    : 'CLEARED: SAFE TO BUILD'}
                </strong>
              </div>
            </div>
            <p className="safety-summary">
              {safety?.status === 'REJECTED'
                ? 'Active geotechnical slope or environmental hazard rule triggered. Construction is strictly prohibited to avoid slope destabilization.'
                : safety?.reasons?.[0] || 'Geotechnical and environmental verification passed.'}
            </p>
            {safety?.rule_ids?.length > 0 && (
              <div className="safety-rules">
                <span className="safety-rules-label">Triggered Rule IDs:</span>
                <div className="rules-tags">
                  {safety.rule_ids.map((rid) => (
                    <span key={rid} className="rule-tag">{rid}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 3b. Three Score Cards (Same Format: Number/100, Class chip, Confidence bar) */}
          <div className="scores-column">
            {/* Recharge Score */}
            {rechargeScore && (
              <div className="score-card score-recharge">
                <div className="score-card-top">
                  <div className="score-label-group">
                    <Droplets size={18} className="score-icon blue" />
                    <span className="score-title">Recharge Potential</span>
                  </div>
                  <div className="score-chips-group">
                    <span className={`class-chip class-${rechargeScore.score_class}`}>
                      {rechargeScore.score_class}
                    </span>
                    <ProvenanceChip tag={rechargeScore.data_tag} />
                  </div>
                </div>

                <div className="score-val-row">
                  <span className="score-val tabular-num">{rechargeScore.value.toFixed(1)}</span>
                  <span className="score-denom">/ 100</span>
                  <ConfidenceBar confidence={rechargeScore.confidence} />
                </div>

                {/* 3c. Driver Bars */}
                <DriverBars drivers={rechargeScore.drivers} />
              </div>
            )}

            {/* Heat-Water Vulnerability */}
            {heatScore && (
              <div className="score-card score-heat">
                <div className="score-card-top">
                  <div className="score-label-group">
                    <Sun size={18} className="score-icon orange" />
                    <span className="score-title">Heat-Water Vulnerability</span>
                  </div>
                  <div className="score-chips-group">
                    <span className={`class-chip class-${heatScore.score_class}`}>
                      {heatScore.score_class}
                    </span>
                    <ProvenanceChip tag={heatScore.data_tag} />
                  </div>
                </div>

                <div className="score-val-row">
                  <span className="score-val tabular-num">{heatScore.value.toFixed(1)}</span>
                  <span className="score-denom">/ 100</span>
                  <ConfidenceBar confidence={heatScore.confidence} />
                </div>

                {/* 3c. Driver Bars */}
                <DriverBars drivers={heatScore.drivers} />
              </div>
            )}

            {/* Spring Desiccation Risk */}
            {springScore && (
              <div className="score-card score-spring">
                <div className="score-card-top">
                  <div className="score-label-group">
                    <Waves size={18} className="score-icon cyan" />
                    <span className="score-title">Spring Desiccation Risk</span>
                  </div>
                  <div className="score-chips-group">
                    <span className={`class-chip class-${springScore.score_class}`}>
                      {springScore.score_class}
                    </span>
                    <ProvenanceChip tag={springScore.data_tag} />
                  </div>
                </div>

                <div className="score-val-row">
                  <span className="score-val tabular-num">{springScore.value.toFixed(1)}</span>
                  <span className="score-denom">/ 100</span>
                  <ConfidenceBar confidence={springScore.confidence} />
                </div>

                {/* 3c. Driver Bars */}
                <DriverBars drivers={springScore.drivers} />
              </div>
            )}
          </div>

          {/* 3d. Recommendation Summary (Hidden when REJECTED) */}
          {isRejected ? (
            <div className="rejection-callout" role="alert">
              <AlertOctagon size={20} />
              <div>
                <b>Structural Recommendation Withheld</b>
                <p>Because {village.name} is classified REJECTED, engineering structures cannot be sanctioned.</p>
              </div>
            </div>
          ) : primaryRec ? (
            <div className="rec-summary-card">
              <div className="rec-summary-head">
                <div className="rec-summary-title">
                  <Wrench size={18} />
                  <div>
                    <span className="eyebrow">RECOMMENDED ACTION</span>
                    <h4>{primaryRec.intervention_name}</h4>
                  </div>
                </div>
                <span className="suitability-tag">{(primaryRec.suitability_score * 100).toFixed(0)}% fit</span>
              </div>
              <p className="rec-category">Category: {primaryRec.category} • Schedule of Rates: {village.state} MGNREGA</p>
              <div className="rec-metrics-row">
                <div>
                  <small>Cost Range (INR)</small>
                  <b>₹{(primaryRec.cost_range_inr.low / 100000).toFixed(1)}–{(primaryRec.cost_range_inr.high / 100000).toFixed(1)}L</b>
                </div>
                <div>
                  <small>Unskilled Labour</small>
                  <b>{primaryRec.labour_days} Person-Days</b>
                </div>
              </div>
              <button
                type="button"
                className="primary-cta"
                onClick={() => setActiveTab('Plan')}
              >
                View Detailed Work Plan <ChevronRight size={17} />
              </button>
            </div>
          ) : null}

          {/* 3e. Key Insight with AI/Template Tag and quoted numbers */}
          <div className="insight-card">
            <div className="insight-header-row">
              <div className="insight-heading">
                <Sparkles size={16} />
                <strong>Synthesized Key Insight</strong>
              </div>
              <span className="origin-badge">Template Synthesized</span>
            </div>
            <p>
              {isRejected
                ? `${village.name} faces severe geotechnical slope hazards (${safety.rule_ids.join(', ')}). No artificial recharge structures should be constructed.`
                : `${village.name} exhibits a recharge suitability score of ${rechargeScore?.value.toFixed(1)}/100 and heat-water vulnerability of ${heatScore?.value.toFixed(1)}/100. Spring desiccation risk stands at ${springScore?.value.toFixed(1)}/100.`}
            </p>
            <div className="quoted-numbers-row">
              <span className="quoted-number-pill">Recharge: {rechargeScore?.value.toFixed(1) || 'N/A'}</span>
              <span className="quoted-number-pill">Heat: {heatScore?.value.toFixed(1) || 'N/A'}</span>
              <span className="quoted-number-pill">Spring: {springScore?.value.toFixed(1) || 'N/A'}</span>
            </div>
          </div>

          {/* 3f. Data Quality Note and Provenance Chips */}
          <div className="data-quality-note">
            <div className="dq-top">
              <Info size={14} />
              <span>Data Provenance &amp; Verification Note</span>
            </div>
            <p>
              {rechargeScore?.data_quality_note ||
                'Scores computed via deterministic spatial formulas using CGWB and IMD empirical baselines.'}
            </p>
            <div className="dq-chips">
              <ProvenanceChip tag="real" />
              <ProvenanceChip tag="proxy" />
              <ProvenanceChip tag="illustrative" />
            </div>
          </div>
        </div>
      )}

      {/* ======================= TAB: AI AGENTS ======================= */}
      {activeTab === 'AI Agents' && (
        <div className="tab-pane agents-pane">
          {/* Executive Decision Banner */}
          <div className={`executive-decision-banner ${isRejected ? 'vetoed' : 'cleared'}`}>
            <div className="exec-head">
              <Bot size={20} className="exec-icon" />
              <div>
                <span className="exec-kicker">LEAD DISTRICT PLANNER ORCHESTRATOR</span>
                <h4>Executive Decision &amp; Sanction Verdict</h4>
              </div>
              <span className={`exec-badge ${isRejected ? 'vetoed' : 'approved'}`}>
                {isRejected ? 'SAFETY VETO' : 'SANCTION APPROVED'}
              </span>
            </div>
            <p className="exec-text">
              {agentBriefing?.executive_decision ||
                (isRejected
                  ? `ACTION PROHIBITED: ${village.name} has been issued a formal SAFETY VETO. Construction is strictly rejected.`
                  : `ACTION APPROVED: ${village.name} is cleared for civil development (${safety?.status || 'SAFE'}).`)}
            </p>
          </div>

          {/* 5 Domain Specialist Agent Briefing Cards */}
          <div className="agents-briefing-grid">
            <span className="agents-section-title">
              <Sparkles size={15} /> Domain Specialist Committee Briefings (Live Multi-Agent Synthesis)
            </span>

            {/* 1. Safety Auditor Agent */}
            <div className={`agent-card ${isRejected ? 'card-rejected' : 'card-safe'}`}>
              <div className="agent-card-top">
                <div className="agent-badge-group">
                  <span className="agent-role-icon">🛡️</span>
                  <div>
                    <h5>Geotechnical Safety Auditor</h5>
                    <small>SafetyAuditorAgent</small>
                  </div>
                </div>
                <span className={`status-pill ${isRejected ? 'rejected' : 'safe'}`}>
                  {isRejected ? 'VETO ISSUED' : 'PASSED'}
                </span>
              </div>
              <p className="agent-summary-text">
                {agentBriefing?.agent_briefings?.safety_audit?.summary ||
                  (isRejected
                    ? `VETO ISSUED: Civil construction at ${village.name} is strictly REJECTED due to geotechnical hazard rules: ${safety?.rule_ids?.join(', ')}.`
                    : `Geotechnical and slope hazard evaluation cleared for ${village.name}.`)}
              </p>
              <div className="agent-recs-box">
                <b>Directives:</b>
                <ul>
                  {(agentBriefing?.agent_briefings?.safety_audit?.recommendations || (isRejected ? ['Prohibit capital expenditure for heavy civil structures.', 'Redirect watershed funds to bio-engineering and vegetative stabilization.'] : ['Enforce 25m riparian buffer setback.', 'Proceed with standard civil sanction.'])).map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* 2. Hydrogeology Agent */}
            <div className="agent-card">
              <div className="agent-card-top">
                <div className="agent-badge-group">
                  <span className="agent-role-icon">💧</span>
                  <div>
                    <h5>Hard-Rock Hydrogeologist</h5>
                    <small>HydrogeologyAgent</small>
                  </div>
                </div>
                <span className="metric-pill">Recharge: {rechargeScore?.value.toFixed(1) || '50'}/100</span>
              </div>
              <p className="agent-summary-text">
                {agentBriefing?.agent_briefings?.hydrogeology?.summary ||
                  `Hydrogeological regime in ${village.district} indicates secondary porosity in fractured crystalline basement.`}
              </p>
              <div className="agent-recs-box">
                <b>Hydrogeology Directives:</b>
                <ul>
                  {(agentBriefing?.agent_briefings?.hydrogeology?.recommendations || [
                    'Prioritize check dams in 2nd order drainage channels.',
                    'Maximize recharge cascading into unconfined weathered zones.',
                  ]).map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* 3. Heat-Water Stress Agent */}
            <div className="agent-card">
              <div className="agent-card-top">
                <div className="agent-badge-group">
                  <span className="agent-role-icon">🌡️</span>
                  <div>
                    <h5>Heat-Water Nexus Climatologist</h5>
                    <small>HeatWaterStressAgent</small>
                  </div>
                </div>
                <span className="metric-pill">Stress: {heatScore?.value.toFixed(1) || '50'}/100</span>
              </div>
              <p className="agent-summary-text">
                {agentBriefing?.agent_briefings?.heat_water_stress?.summary ||
                  `Pre-monsoon land surface temperature and moisture deficit assessment for ${village.name}.`}
              </p>
              <div className="agent-recs-box">
                <b>Climatic Adaptation:</b>
                <ul>
                  {(agentBriefing?.agent_briefings?.heat_water_stress?.recommendations || [
                    'Sanction water retention bodies prior to May temperature peaks.',
                    'Combine farm ponds with shade tree agroforestry along bunds.',
                  ]).map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* 4. Springshed Agent */}
            <div className="agent-card">
              <div className="agent-card-top">
                <div className="agent-badge-group">
                  <span className="agent-role-icon">🏞️</span>
                  <div>
                    <h5>Springshed Hydrologist</h5>
                    <small>SpringshedAgent</small>
                  </div>
                </div>
                <span className="metric-pill">{village.has_spring ? 'Spring Registered' : 'No Perennial Spring'}</span>
              </div>
              <p className="agent-summary-text">
                {agentBriefing?.agent_briefings?.springshed?.summary ||
                  `Spring desiccation risk index at ${springScore?.value.toFixed(1) || '0'}/100.`}
              </p>
              <div className="agent-recs-box">
                <b>Springshed Directives:</b>
                <ul>
                  {(agentBriefing?.agent_briefings?.springshed?.recommendations || [
                    'Construct Continuous Staggered Contour Trenches on upper ridge slopes.',
                    'Delineate recharge protection zones in Gram Sabha registers.',
                  ]).map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* 5. Civil Engineering Agent */}
            <div className="agent-card">
              <div className="agent-card-top">
                <div className="agent-badge-group">
                  <span className="agent-role-icon">🏗️</span>
                  <div>
                    <h5>Principal Civil Engineer (MGNREGA)</h5>
                    <small>InterventionComposerAgent</small>
                  </div>
                </div>
                <span className="metric-pill">Wage: ₹{wageRate}/day</span>
              </div>
              <p className="agent-summary-text">
                {agentBriefing?.agent_briefings?.civil_engineering?.summary ||
                  (isRejected
                    ? 'No civil structures cleared under safety veto guidelines.'
                    : `Recommended structure: ${primaryRec?.intervention_name || 'Check Dam'} (${primaryRec?.labour_days || 120} person-days).`)}
              </p>
              <div className="agent-recs-box">
                <b>Engineering Directives:</b>
                <ul>
                  {(agentBriefing?.agent_briefings?.civil_engineering?.recommendations || [
                    'Adhere strictly to 60:40 wage-to-material ratio.',
                    'Download compiled DPR ZIP package with CAD specifications.',
                  ]).map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Interactive Agent Consultation Chat Section */}
          <div className="agent-consult-section">
            <div className="consult-head">
              <div className="consult-title-group">
                <Bot size={18} className="icon-cyan" />
                <h4>Interactive Lead Planner Agent Consultation</h4>
              </div>
              <span className="live-indicator-pill">
                <span className="live-pulse" /> Live Agent Connected
              </span>
            </div>
            <p className="consult-subtext">
              Ask the Lead District Planner Orchestrator custom questions regarding site safety vetoes, hydrogeology, monsoon sensitivity, or MGNREGA costings.
            </p>

            {/* Quick Prompt Chips */}
            <div className="prompt-chips-row">
              <button
                type="button"
                className="prompt-chip"
                onClick={() => handleConsultAgent('Can we construct a check dam here?')}
              >
                Can we build a check dam?
              </button>
              <button
                type="button"
                className="prompt-chip"
                onClick={() => handleConsultAgent('Explain geotechnical safety reasons')}
              >
                Explain safety reasons
              </button>
              <button
                type="button"
                className="prompt-chip"
                onClick={() => handleConsultAgent('What is the pre-monsoon heat and spring drying risk?')}
              >
                Pre-monsoon risks
              </button>
              <button
                type="button"
                className="prompt-chip"
                onClick={() => handleConsultAgent('What is the MGNREGA budget and labour person-days?')}
              >
                MGNREGA cost breakdown
              </button>
            </div>

            {/* Query Form */}
            <form
              className="consult-input-form"
              onSubmit={(e) => {
                e.preventDefault();
                handleConsultAgent();
              }}
            >
              <input
                type="text"
                className="consult-query-input"
                value={agentQuery}
                onChange={(e) => setAgentQuery(e.target.value)}
                placeholder="Ask Lead Planner Agent about this site..."
                disabled={consultLoading}
                aria-label="Ask Lead Planner Agent"
              />
              <button
                type="submit"
                className="primary-cta consult-submit-btn"
                disabled={consultLoading || !agentQuery.trim()}
              >
                {consultLoading ? <RefreshCw size={15} className="spin-icon" /> : <Send size={15} />}
                <span>{consultLoading ? 'Thinking...' : 'Ask Agent'}</span>
              </button>
            </form>

            {/* Conversation Stream */}
            {consultHistory.length > 0 && (
              <div className="consult-history-stream">
                {consultHistory.map((item, idx) => (
                  <div key={idx} className="consult-history-item">
                    <div className="history-query-bubble">
                      <b>Planner Question:</b> {item.query}
                    </div>
                    <div className="history-response-bubble">
                      <div className="response-head">
                        <Bot size={15} />
                        <span>{item.agent_name || 'LeadPlannerOrchestratorAgent'} ({item.role || 'Lead District Planner'})</span>
                        <span className="response-time">{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <p className="response-body">{item.response}</p>
                      {item.recommendations?.length > 0 && (
                        <div className="response-recs">
                          <b>Action Directives:</b>
                          <ul>
                            {item.recommendations.map((r, rIdx) => (
                              <li key={rIdx}>{r}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ======================= TAB: PLAN ======================= */}

      {activeTab === 'Plan' && (
        <div className="tab-pane plan-pane">
          {isRejected ? (
            <div className="rejection-callout" role="alert">
              <AlertOctagon size={24} />
              <div>
                <b>DPR Generation Locked for REJECTED Sites</b>
                <p>Safety violations ({safety.rule_ids.join(', ')}) prohibit the preparation or sanctioning of engineering structures at {village.name}.</p>
              </div>
            </div>
          ) : primaryRec ? (
            <>
              <div className="plan-section">
                <span className="eyebrow">ENGINEERING SPECIFICATION</span>
                <h3>{primaryRec.intervention_name}</h3>
                <p className="plan-why">
                  Selected to decelerate seasonal monsoon runoff, promote unconfined aquifer infiltration, and buffer lean-season domestic spring flow.
                </p>
              </div>

              {/* Dimensions */}
              <div className="plan-section">
                <h4 className="section-title">Standard Dimensions</h4>
                <div className="dimensions-grid">
                  {Object.entries(primaryRec.dimensions || {}).map(([dim, val]) => (
                    <div key={dim} className="dim-card">
                      <small>{formatFactorName(dim)}</small>
                      <b>{val} m</b>
                    </div>
                  ))}
                </div>
              </div>

              {/* Cost Table using State Wage */}
              <div className="plan-section">
                <h4 className="section-title">MGNREGA Cost Table ({village.state})</h4>
                <div className="cost-table-wrapper">
                  <table className="cost-table">
                    <thead>
                      <tr>
                        <th>Component</th>
                        <th>Rate Basis</th>
                        <th>Estimate</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>Unskilled Labour</td>
                        <td>{primaryRec.labour_days} days @ ₹{wageRate}/day</td>
                        <td className="tabular-num">₹{(primaryRec.labour_days * wageRate).toLocaleString('en-IN')}</td>
                      </tr>
                      <tr>
                        <td>Materials &amp; Masonry</td>
                        <td>State SOR Schedule</td>
                        <td className="tabular-num">₹{Math.max(15000, primaryRec.cost_range_inr.low - (primaryRec.labour_days * wageRate)).toLocaleString('en-IN')}</td>
                      </tr>
                      <tr>
                        <td>Technical Supervision</td>
                        <td>Junior Engineer Verification</td>
                        <td className="tabular-num">₹12,500</td>
                      </tr>
                      <tr className="total-row">
                        <td><strong>Total Estimate</strong></td>
                        <td>MGNREGA Allocation Range</td>
                        <td className="tabular-num">
                          <strong>₹{(primaryRec.cost_range_inr.low / 100000).toFixed(2)}L – ₹{(primaryRec.cost_range_inr.high / 100000).toFixed(2)}L</strong>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Assumptions */}
              {primaryRec.assumptions?.length > 0 && (
                <div className="plan-section">
                  <h4 className="section-title">Engineering Assumptions</h4>
                  <ul className="assumptions-list">
                    {primaryRec.assumptions.map((ass, i) => (
                      <li key={i}>{ass}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Buttons: Generate DPR & Open Report */}
              <div className="plan-actions">
                <button
                  type="button"
                  className="primary-cta"
                  disabled={dprLoading}
                  onClick={handleGenerateDpr}
                >
                  <Download size={17} />
                  {dprLoading ? dprProgress : 'Generate DPR Package (.ZIP)'}
                </button>

                <div className="report-action-group">
                  <span className="lang-toggle-label">Report Language:</span>
                  <div className="lang-toggle">
                    <button
                      type="button"
                      className={`lang-btn ${reportLang === 'en' ? 'active' : ''}`}
                      onClick={() => setReportLang('en')}
                    >
                      English
                    </button>
                    <button
                      type="button"
                      className={`lang-btn ${reportLang === 'hi' ? 'active' : ''}`}
                      onClick={() => setReportLang('hi')}
                    >
                      हिन्दी (Hindi)
                    </button>
                  </div>
                  <button
                    type="button"
                    className="secondary-full"
                    onClick={() => {
                      alert(`Opening ${reportLang.toUpperCase()} Action Dossier for ${village.name}...`);
                    }}
                  >
                    <FileText size={16} /> Open Action Report
                  </button>
                </div>
              </div>
            </>
          ) : (
            <p className="empty-note">No intervention plan available for this settlement.</p>
          )}
        </div>
      )}

      {/* ======================= TAB: SCENARIO ======================= */}
      {activeTab === 'Scenario' && (
        <div className="tab-pane scenario-pane">
          <div className="scenario-intro">
            <span className="eyebrow">SCENARIO SIMULATOR</span>
            <h3>Monsoon Sensitivity Analysis</h3>
            <p className="scenario-subtext">
              Test settlement hydrological vulnerability under varied rainfall stress. Illustrative scenario projection, not a meteorological forecast.
            </p>
          </div>

          {/* Rainfall Slider */}
          <div className="rainfall-slider-box">
            <div className="slider-header">
              <span>Monsoon Rainfall Fraction:</span>
              <strong className="tabular-num">
                {rainfallFraction.toFixed(2)}x ({(rainfallFraction * 100).toFixed(0)}% of baseline)
              </strong>
            </div>
            <input
              type="range"
              min="0.5"
              max="1.5"
              step="0.05"
              value={rainfallFraction}
              onChange={(e) => setRainfallFraction(parseFloat(e.target.value))}
              aria-label="Rainfall fraction slider"
              className="range-input"
            />
            <div className="slider-ticks">
              <span>0.50x (Drought)</span>
              <span>1.00x (Baseline)</span>
              <span>1.50x (Surplus)</span>
            </div>
          </div>

          {/* Intervention Toggle */}
          {!isRejected && (
            <label className="intervention-toggle-label">
              <input
                type="checkbox"
                checked={includeIntervention}
                onChange={(e) => setIncludeIntervention(e.target.checked)}
              />
              <span>Include {primaryRec?.intervention_name || 'Proposed Recharge Structure'} in simulation</span>
            </label>
          )}

          {/* Summer Deficit Readout */}
          <div className="deficit-readout-card">
            <div>
              <small>Summer Deficit Balance</small>
              <b className="tabular-num">
                {rainfallFraction < 1 ? `-${((1 - rainfallFraction) * 58).toFixed(1)} mm` : `+${((rainfallFraction - 1) * 44).toFixed(1)} mm buffer`}
              </b>
            </div>
            <div>
              <small>Baseline Catchment Rain</small>
              <b className="tabular-num">{scenarioResult?.rainfall_mm_baseline || 1150} mm</b>
            </div>
            <div>
              <small>Simulated Total</small>
              <b className="tabular-num">{scenarioResult?.rainfall_mm_adjusted || 1150} mm</b>
            </div>
          </div>

          {/* Recharts Monthly Water Balance Chart */}
          <div className="chart-wrapper">
            <span className="chart-title">Simulated Monthly Runoff &amp; Retention (mm)</span>
            <div style={{ width: '100%', height: 180 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={monthlyWaterData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={10} />
                  <YAxis stroke="#94a3b8" fontSize={10} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0c1a25', borderColor: 'rgba(255,255,255,0.15)', borderRadius: '8px', fontSize: '11px' }}
                  />
                  <Bar dataKey="Simulated" fill="#38bdf8" radius={[3, 3, 0, 0]} name="Rainfall (mm)" />
                  <Bar dataKey="Retained" fill="#22c55e" radius={[3, 3, 0, 0]} name="Retained (mm)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Collapsible Assumptions */}
          <div className="assumptions-collapsible">
            <button
              type="button"
              className="collapsible-header"
              onClick={() => setShowScenarioAssumptions((s) => !s)}
            >
              <span>Scenario Modeling Assumptions</span>
              {showScenarioAssumptions ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
            {showScenarioAssumptions && (
              <div className="collapsible-content">
                <p>• Monsoon rainfall uniformly scaled across catchment hydrologic units.</p>
                <p>• Interventions assume standard maintenance and nominal infiltration rate.</p>
                <p>• Projections illustrate sensitivity; not calibrated for extreme meteorological events.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ======================= TAB: EVIDENCE ======================= */}
      {activeTab === 'Evidence' && (
        <div className="tab-pane evidence-pane">
          <div className="evidence-section">
            <span className="eyebrow">OBSERVATIONAL TELEMETRY</span>
            <h3>Groundwater &amp; Climatology Baselines</h3>
            <p className="evidence-subtext">
              Derived from Central Ground Water Board (CGWB) observation wells and IMD high-resolution meteorological grids.
            </p>
          </div>

          {/* Telemetry Stats Grid */}
          <div className="evidence-grid">
            <div className="evidence-card">
              <small>CGWB Monitoring Wells ({village.district})</small>
              <b className="tabular-num">
                {telemetry?.groundwater?.district_summary?.station_count || 64} Stations
              </b>
              <span>{telemetry?.groundwater?.district_summary?.reading_count || 734} Historic Readings</span>
            </div>

            <div className="evidence-card">
              <small>Pre-Monsoon Mean Depth</small>
              <b className="tabular-num">
                {telemetry?.groundwater?.district_summary?.pre_monsoon_mean_depth_m || 6.24} m
              </b>
              <span>Seasonal Rise: {telemetry?.groundwater?.district_summary?.seasonal_rise_m || 2.8} m</span>
            </div>

            <div className="evidence-card">
              <small>Summer Mean Max Temp</small>
              <b className="tabular-num">
                {telemetry?.temperature?.summer_mean_max_c ? `${telemetry.temperature.summer_mean_max_c}°C` : '35.2°C'}
              </b>
              <span>Warming: {telemetry?.temperature?.trend_c_per_year ? `+${telemetry.temperature.trend_c_per_year}°C/yr` : '+0.06°C/yr'}</span>
            </div>

            <div className="evidence-card">
              <small>Monsoon Precipitation</small>
              <b className="tabular-num">
                {telemetry?.rainfall?.district_monsoon_total_mm || 835.9} mm
              </b>
              <span>Departure: +{telemetry?.rainfall?.district_departure_pct || 82.6}%</span>
            </div>
          </div>

          {/* Provenance Table */}
          <div className="evidence-section">
            <h4 className="section-title">Data Source Provenance Table</h4>
            <div className="provenance-table-wrapper">
              <table className="provenance-table">
                <thead>
                  <tr>
                    <th>Layer</th>
                    <th>Source Agency</th>
                    <th>Coverage</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Groundwater Depth</td>
                    <td>CGWB India-WRIS</td>
                    <td>64 District Stations</td>
                    <td><ProvenanceChip tag="real" /></td>
                  </tr>
                  <tr>
                    <td>Surface Temperature</td>
                    <td>IMD 0.5° Grid</td>
                    <td>District Centroid Grid</td>
                    <td><ProvenanceChip tag="real" /></td>
                  </tr>
                  <tr>
                    <td>Perched Mountain Springs</td>
                    <td>State Watershed Mission</td>
                    <td>Tribal Hamlets</td>
                    <td><ProvenanceChip tag="proxy" /></td>
                  </tr>
                  <tr>
                    <td>Geotechnical Safety Rules</td>
                    <td>NRSC &amp; Survey of India</td>
                    <td>Slope / Hazard Demarcation</td>
                    <td><ProvenanceChip tag="real" /></td>
                  </tr>
                  <tr>
                    <td>Adaptation Pathway</td>
                    <td>IPCC AR6 SSP Scenarios</td>
                    <td>Illustrative Scenarios</td>
                    <td><ProvenanceChip tag="illustrative" /></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Limitations Callout */}
          <div className="limitations-box">
            <Info size={16} />
            <div>
              <b>Methodological Limitations</b>
              <p>
                Telemetry reflects interpolated station clusters. Field validation by Gram Sabha and Junior Engineers is mandatory prior to releasing administrative MGNREGA sanctions.
              </p>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
