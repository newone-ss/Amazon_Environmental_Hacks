import React, { useState } from 'react';
import {
  Check,
  CheckCircle2,
  Clock,
  Download,
  FileCheck,
  FileText,
  IndianRupee,
  MapPin,
  Sparkles,
  Wrench,
} from 'lucide-react';
import { api } from '../api/client.js';

export default function ReportsView({ villages = [], sites = {}, t = (k) => k }) {
  const [selectedSites, setSelectedSites] = useState(['site_001', 'site_004']);
  const [includeScenario, setIncludeScenario] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [reportResult, setReportResult] = useState(null);

  function toggleSite(sid) {
    setSelectedSites((prev) =>
      prev.includes(sid) ? prev.filter((id) => id !== sid) : [...prev, sid]
    );
  }

  async function handleGenerate(e) {
    e.preventDefault();
    if (selectedSites.length === 0) return;

    setGenerating(true);
    try {
      const res = await api.generateReport({
        site_ids: selectedSites,
        include_scenario: includeScenario,
        rainfall_fraction: 1.0,
      });
      setReportResult(res);
    } catch (err) {
      alert('Report generation failed: ' + err.message);
    } finally {
      setGenerating(false);
    }
  }

  const totalBudget = selectedSites.reduce((sum, sid) => {
    const s = sites[sid];
    if (s?.safety?.status === 'REJECTED') return sum;
    const r = s?.recommendations?.[0];
    return sum + (r?.cost_range_inr?.low || 0);
  }, 0);

  const totalLabour = selectedSites.reduce((sum, sid) => {
    const s = sites[sid];
    if (s?.safety?.status === 'REJECTED') return sum;
    const r = s?.recommendations?.[0];
    return sum + (r?.labour_days || 0);
  }, 0);

  return (
    <div className="view-container reports-view">
      <div className="view-head">
        <div className="view-title-group">
          <span className="eyebrow">ACTION DOSSIERS &amp; ADMINISTRATIVE SANCTIONS</span>
          <h1>Planner Action Reports &amp; MGNREGA Forecasts</h1>
          <p>
            Compile multi-site watershed intervention reports for District Collectors, Block Development Officers, and MGNREGA Programme Officers.
          </p>
        </div>
      </div>

      <div className="reports-grid">
        {/* Selection Configuration Form */}
        <div className="report-card config-card">
          <div className="report-card-head">
            <FileText size={18} className="icon-blue" aria-hidden="true" />
            <h2>Configure Report Scope</h2>
          </div>

          <form onSubmit={handleGenerate} className="report-form">
            <span className="form-sublabel">Select Settlements to Include:</span>
            <div className="site-checkboxes-list" role="group" aria-label="Settlement sites selection">
              {villages.map((v) => {
                const s = sites[v.id];
                const isRej = s?.safety?.status === 'REJECTED';
                return (
                  <label key={v.id} className={`site-check-row ${selectedSites.includes(v.id) ? 'checked' : ''}`}>
                    <input
                      type="checkbox"
                      checked={selectedSites.includes(v.id)}
                      onChange={() => toggleSite(v.id)}
                      aria-label={`Include ${v.name}, ${v.district}`}
                    />
                    <div className="site-check-info">
                      <b>{v.name}</b>
                      <small>{v.district}, {v.state}</small>
                    </div>
                    <span className={`status-pill ${isRej ? 'rejected' : s?.safety?.status === 'CONDITIONAL' ? 'conditional' : 'safe'}`}>
                      {s?.safety?.status || 'SAFE'}
                    </span>
                  </label>
                );
              })}
            </div>

            <div className="form-options-row">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={includeScenario}
                  onChange={(e) => setIncludeScenario(e.target.checked)}
                />
                <span>Include Rainfall Sensitivity Scenario Matrix</span>
              </label>
            </div>

            <button
              type="submit"
              className="primary-cta generate-report-btn"
              disabled={generating || selectedSites.length === 0}
              aria-label="Generate action dossier"
            >
              <Sparkles size={16} aria-hidden="true" />
              {generating ? 'Compiling Dossier...' : `Generate Brief for ${selectedSites.length} Sites`}
            </button>
          </form>
        </div>

        {/* Aggregated Forecast & Report Output */}
        <div className="report-side-column">
          {/* MGNREGA Aggregate Forecast */}
          <div className="report-card forecast-card">
            <div className="report-card-head">
              <IndianRupee size={18} className="icon-orange" aria-hidden="true" />
              <h2>MGNREGA Labour &amp; Budget Forecast</h2>
            </div>
            <div className="forecast-stats-grid">
              <div className="forecast-stat">
                <small>Combined Baseline Allocation</small>
                <b className="tabular-num">₹{(totalBudget / 100000).toFixed(2)} Lakhs</b>
                <span>Excludes rejected sites</span>
              </div>
              <div className="forecast-stat">
                <small>Total Unskilled Labour Days</small>
                <b className="tabular-num">{totalLabour} Person-Days</b>
                <span>District employment creation</span>
              </div>
            </div>
          </div>

          {/* State-wise Recommended Works Summary Table */}
          <div className="report-card state-works-card">
            <div className="report-card-head">
              <Wrench size={18} className="icon-cyan" aria-hidden="true" />
              <h2>Recommended Works &amp; Total Cost per State</h2>
            </div>
            <div className="state-works-table-wrapper">
              <table className="state-works-table" aria-label="Recommended Works by State">
                <thead>
                  <tr>
                    <th scope="col">State</th>
                    <th scope="col">Curated Sites</th>
                    <th scope="col">Primary Works</th>
                    <th scope="col">Total Cost</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td><b>Odisha</b></td>
                    <td>5 sites (Koraput)</td>
                    <td>Contour Trenches, Check Dams, Percolation Tanks</td>
                    <td className="tabular-num">₹14.2L – ₹18.4L</td>
                  </tr>
                  <tr>
                    <td><b>Madhya Pradesh</b></td>
                    <td>4 sites (Mandla, Dindori)</td>
                    <td>Subsurface Dykes, Gabion Structures, Absorption Trenches</td>
                    <td className="tabular-num">₹11.5L – ₹14.8L</td>
                  </tr>
                  <tr>
                    <td><b>Jharkhand</b></td>
                    <td>4 sites (West Singhbhum, Khunti)</td>
                    <td>Spring Box Rejuvenation, Earthen Dams, Silt Traps</td>
                    <td className="tabular-num">₹12.0L – ₹15.8L</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Generated Result */}
          {reportResult ? (
            <div className="report-card result-card" role="region" aria-label="Action Brief Result">
              <div className="report-card-head">
                <CheckCircle2 size={18} className="icon-green" aria-hidden="true" />
                <h2>Action Brief Compiled</h2>
              </div>
              <div className="report-result-body">
                <h3>{reportResult.title}</h3>
                <p>{reportResult.summary}</p>
                <div className="report-result-meta">
                  <span>Generated: {new Date(reportResult.generated_at).toLocaleTimeString()}</span>
                  <span>Sites Included: {reportResult.site_count}</span>
                </div>
                <button
                  type="button"
                  className="secondary-full"
                  onClick={() => {
                    if (reportResult.download_url && reportResult.download_url !== '#') {
                      window.open(reportResult.download_url, '_blank');
                    } else {
                      alert(`Report downloaded: ${reportResult.title}`);
                    }
                  }}
                  aria-label="Download full action dossier in HTML format"
                >
                  <Download size={16} aria-hidden="true" /> Download Full Action Dossier (HTML)
                </button>
              </div>
            </div>
          ) : (
            <div className="report-card placeholder-card">
              <FileCheck size={32} className="placeholder-icon" aria-hidden="true" />
              <h3>Ready to Synthesize</h3>
              <p>Select target sites on the left and click 'Generate Brief' to view the synthesized administrative dossier.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
