import React from 'react';

interface ReportViewerProps {
  siteData: any; // Site type
  onGenerateReport: (siteIds: string) => Promise<void>;
  reportData: any | null;
  loading: boolean;
  error: string | null;
}

const ReportViewer: React.FC<ReportViewerProps> = ({
  siteData,
  onGenerateReport,
  reportData,
  loading,
  error
}) => {
  const [selectedSites, setSelectedSites] = React.useState<string>('');
  const [language, setLanguage] = React.useState<string>('en'); // en or hi


  const handleGenerateReport = async () => {
    if (!selectedSites.trim()) return;
    await onGenerateReport(selectedSites);
  };

  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'hi' : 'en');
  };

  if (!siteData) {
    return (
      <div className="report-panel">
        <div className="panel-placeholder">Select a settlement to generate reports</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="report-panel">
        <div className="panel-loading">Generating report...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="report-panel">
        <div className="panel-error">{error}</div>
      </div>
    );
  }

  return (
    <div className="report-panel">
      <div className="panel-header">
        <h2>Action Report Generation</h2>
        <p>Create comprehensive reports for planning and approvals</p>
        <div className="language-toggle">
          <button onClick={toggleLanguage}>
            {language === 'en' ? 'हिंदी' : 'English'}
          </button>
        </div>
      </div>

      <div className="report-controls">
        <div className="form-group">
          <label htmlFor="site-ids">Site IDs (comma-separated):</label>
          <input
            type="text"
            id="site-ids"
            value={selectedSites}
            onChange={(e) => setSelectedSites(e.target.value)}
            placeholder="e.g., site_001,site_mp_001,site_jh_004"
          />
          <p className="help-text">Enter one or more site IDs to include in the report</p>
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={false} // includeScenario - simplified for now
            />
            Include climate scenario analysis
          </label>
        </div>

        <button className="generate-report-btn" onClick={handleGenerateReport}>
          Generate Report
        </button>
      </div>

      {reportData ? (
        <div className="report-results">
          <div className="report-info">
            <h3>Report: {reportData.title}</h3>
            <p>Generated: {new Date(reportData.generated_at).toLocaleDateString()}</p>
            <p>Sites included: {reportData.sites.length}</p>
          </div>

          <div className="report-summary">
            <h4>Executive Summary</h4>
            <p>{language === 'en' ? reportData.narrative : '[Hindi translation would be displayed here]'}</p>
          </div>

          <div className="report-sites">
            <h4>Sites Included</h4>
            <ul>
              {reportData.sites.map((site: any, index: number) => (
                <li key={site.site_id || index}>
                  <strong>{site.site_id}</strong>: {site.name}
                  ({site.safety_verdict})
                </li>
              ))}
            </ul>
          </div>

          <div className="report-actions">
            <button className="btn-primary" onClick={() => {
              // In a real app, this would open the report in a new tab
              window.open(`${reportData.report_id}`, '_blank');
            }}>
              View Full Report
            </button>
            <button className="btn-secondary" onClick={() => {
              // In a real app, this would trigger print-friendly view
              window.print();
            }}>
              Print View
            </button>
          </div>
        </div>
      ) : (
        <div className="report-placeholder">
          <p>Select sites and click "Generate Report" to create a comprehensive action dossier</p>
          <p>The report will include:</p>
          <ul>
            <li>Site assessments and recommendations</li>
            <li>Cost estimates and implementation timelines</li>
            <li>Climate resilience analysis (if selected)</li>
            <li>Community observation summaries</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default ReportViewer;