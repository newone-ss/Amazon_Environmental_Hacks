import React from 'react';
import {
  AlertTriangle,
  Award,
  CheckCircle2,
  Database,
  ExternalLink,
  FileCheck,
  FileText,
  Info,
  Layers,
  Scale,
  ShieldCheck,
} from 'lucide-react';

export default function AboutDataView({ t = (k) => k }) {
  const datasets = [
    {
      name: 'CGWB India-WRIS Groundwater Telemetry',
      agency: 'Central Ground Water Board, Ministry of Jal Shakti',
      resolution: 'Point telemetry monitoring wells (seasonal & decadal)',
      license: 'Government Open Data License - India (GODL)',
      provenance: 'Real empirical measurements',
      link: 'https://indiawris.gov.in',
    },
    {
      name: 'IMD High-Resolution Daily Gridded Meteorological Data',
      agency: 'India Meteorological Department (IMD), MoES',
      resolution: '0.25° x 0.25° rainfall & 0.5° x 0.5° temperature climatology',
      license: 'IMD Data Dissemination Policy (Research & Government use)',
      provenance: 'Real empirical climatology',
      link: 'https://imdpune.gov.in',
    },
    {
      name: 'Landsat 8/9 & Sentinel-2 Surface Thermal & Vegetation Radiometry',
      agency: 'USGS / NASA & ESA Copernicus Programme',
      resolution: '30 m Land Surface Temperature (LST) & 10 m NDVI',
      license: 'Public Domain / Creative Commons (CC-BY 4.0)',
      provenance: 'Proxy radiometry',
      link: 'https://earthexplorer.usgs.gov',
    },
    {
      name: 'SRTM Digital Elevation Model (DEM) & Geotechnical Slopes',
      agency: 'NASA / NGA / Survey of India',
      resolution: '30 m topographic elevation & catchment flow accumulation',
      license: 'Public Domain (NASA Open Data)',
      provenance: 'Real topographic baseline',
      link: 'https://earthdata.nasa.gov',
    },
    {
      name: 'MGNREGA State Schedule of Rates (SOR)',
      agency: 'Ministry of Rural Development (MoRD)',
      resolution: 'State-calibrated daily unskilled wages & material schedules (2025-26)',
      license: 'Open Government Data',
      provenance: 'Real administrative rates',
      link: 'https://nrega.nic.in',
    },
  ];

  return (
    <div className="view-container about-view">
      <div className="view-head">
        <div className="view-title-group">
          <span className="eyebrow">METHODOLOGY &amp; OPEN DATA</span>
          <h1>About Bhujal &amp; Data Provenance</h1>
          <p>
            Bhujal is an AI-powered decision support system built on AWS for Amazon Environmental Hacks 2026. It enables transparent groundwater recharge and heat resilience planning across 13 priority tribal settlements in Odisha, Madhya Pradesh, and Jharkhand.
          </p>
        </div>
      </div>

      <div className="about-grid">
        {/* Core Principles */}
        <div className="about-card principles-card">
          <div className="card-top-icon">
            <ShieldCheck size={22} className="icon-cyan" />
            <h3>Core Engineering Principles</h3>
          </div>
          <div className="principles-list">
            <div className="principle-item">
              <CheckCircle2 size={16} />
              <div>
                <b>Deterministic Safety Override</b>
                <p>Engineering recommendations are strictly subordinated to geotechnical safety rules. A REJECTED site cannot be overridden by statistical scores or prompts.</p>
              </div>
            </div>
            <div className="principle-item">
              <CheckCircle2 size={16} />
              <div>
                <b>Honest Site-Level Data Binding</b>
                <p>We do not fabricate continuous high-resolution rasters where data does not exist. All points are real curated settlement locations with explicit confidence levels.</p>
              </div>
            </div>
            <div className="principle-item">
              <CheckCircle2 size={16} />
              <div>
                <b>No Dead Controls &amp; Zero Black-Box Decisions</b>
                <p>Every score includes a full driver decomposition ('Why?' breakdown) showing factor weights and contributions.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Validation & Limitations */}
        <div className="about-card limitations-card">
          <div className="card-top-icon">
            <AlertTriangle size={22} className="icon-amber" />
            <h3>Validation &amp; Limitations</h3>
          </div>
          <div className="limitations-body">
            <p>
              • <strong>Macro-to-Micro Interpolation:</strong> Well measurements from district stations (e.g. Koraput) reflect regional unconfined aquifers. Micro-catchment fractured basalt and khondalite aquifers require on-site junior engineer hydrogeological verification before civil construction.
            </p>
            <p>
              • <strong>Illustrative Scenarios:</strong> The Rainfall Simulator scales baseline precipitation to model sensitivity. It is designed for risk stress-testing, not micro-climate weather forecasting.
            </p>
            <p>
              • <strong>Administrative Sanctions:</strong> All MGNREGA cost ranges are indicative benchmarks based on 2025-26 state wage notifications and require Gram Sabha social sanction.
            </p>
          </div>
        </div>
      </div>

      {/* Dataset Inventory & Licences Table */}
      <div className="about-card datasets-card">
        <div className="card-top-icon">
          <Database size={22} className="icon-blue" />
          <h3>Curated Datasets, Provenance &amp; Licences</h3>
        </div>

        <div className="table-responsive">
          <table className="datasets-table">
            <thead>
              <tr>
                <th>Dataset Name</th>
                <th>Source Agency</th>
                <th>Spatial/Temporal Resolution</th>
                <th>Provenance Tag</th>
                <th>Licence</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((d) => (
                <tr key={d.name}>
                  <td>
                    <b>{d.name}</b>
                    <a href={d.link} target="_blank" rel="noreferrer" className="table-ext-link">
                      <ExternalLink size={11} /> Portal
                    </a>
                  </td>
                  <td>{d.agency}</td>
                  <td>{d.resolution}</td>
                  <td>
                    <span className={`provenance-chip chip-${d.provenance.includes('Real') ? 'real' : d.provenance.includes('Proxy') ? 'proxy' : 'illustrative'}`}>
                      {d.provenance.split(' ')[0]}
                    </span>
                  </td>
                  <td><span className="license-tag">{d.license}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
