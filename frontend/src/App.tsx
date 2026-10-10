import { useState, useEffect } from 'react'
import './App.css'
import MapContainer from './components/MapContainer'
import SitePanel from './components/SitePanel'
import RecommendationPanel from './components/RecommendationPanel'
import ScenarioPanel from './components/ScenarioPanel'
import PathwaysPanel from './components/PathwaysPanel'
import ObservationForm from './components/ObservationForm'
import ReportViewer from './components/ReportViewer'
import ValidationPanel from './components/ValidationPanel'
import FirstRunGuide from './components/FirstRunGuide'
import DemoModeButton from './components/DemoModeButton'
import { bhujalAPI } from './services/api'

function App() {
  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null)
  const [siteData, setSiteData] = useState<any>(null)
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [scenarioResult, setScenarioResult] = useState<any>(null)
  const [pathwaysData, setPathwaysData] = useState<any>(null)
  const [observations, setObservations] = useState<any[]>([])
  const [reportData, setReportData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [firstRunComplete, setFirstRunComplete] = useState<boolean>(false)
  const [demoModeActive, setDemoModeActive] = useState<boolean>(false)

  // Check if this is the first run
  useEffect(() => {
    const completed = localStorage.getItem('bhujal_first_run_complete')
    setFirstRunComplete(completed === 'true')
  }, [])

  // Handle site selection
  const handleSiteSelect = async (siteId: string) => {
    setSelectedSiteId(siteId)
    setSiteData(null)
    setRecommendations([])
    setScenarioResult(null)
    setPathwaysData(null)
    setLoading(true)
    setError(null)

    try {
      // Fetch site data
      const siteResponse = await bhujalAPI.getSite(siteId)
      setSiteData(siteResponse.data)

      // Fetch recommendations
      const recResponse = await bhujalAPI.getRecommendations(siteId)
      setRecommendations(recResponse.data)
    } catch (err) {
      setError('Failed to load site data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Handle scenario run
  const handleRunScenario = async (rainfallFraction: number, includeIntervention: boolean) => {
    if (!selectedSiteId) return

    setLoading(true)
    setError(null)

    try {
      const response = await bhujalAPI.runScenario({
        site_id: selectedSiteId,
        rainfall_fraction: rainfallFraction,
        include_intervention: includeIntervention
      })
      setScenarioResult(response.data)
    } catch (err) {
      setError('Failed to run scenario')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Handle pathway generation
  const handleGeneratePathway = async (sspScenario: string, baseRainfallFraction: number) => {
    if (!selectedSiteId) return

    setLoading(true)
    setError(null)

    try {
      const response = await bhujalAPI.generatePathway({
        site_id: selectedSiteId,
        ssp_scenario: sspScenario,
        base_rainfall_fraction: baseRainfallFraction
      })
      setPathwaysData(response.data)
    } catch (err) {
      setError('Failed to generate pathway')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Handle observation submission
  const handleObservationSubmit = async (observationData: any) => {
    setLoading(true)
    setError(null)

    try {
      await bhujalAPI.submitTextObservation(observationData)
      // Refresh observations list
      const obsResponse = await bhujalAPI.getLeaderboard({ limit: 10 })
      setObservations(obsResponse.data)
    } catch (err) {
      setError('Failed to submit observation')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Handle report generation
  const handleGenerateReport = async (siteIds: string) => {
    setLoading(true)
    setError(null)

    try {
      const response = await bhujalAPI.generateReport({ site_ids: siteIds })
      setReportData(response.data)
    } catch (err) {
      setError('Failed to generate report')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Mark first run as complete
  const handleFirstRunComplete = () => {
    localStorage.setItem('bhujal_first_run_complete', 'true')
    setFirstRunComplete(true)
  }

  // Toggle demo mode
  const handleDemoModeToggle = () => {
    setDemoModeActive(!demoModeActive)
    if (demoModeActive) {
      setSelectedSiteId(null)
    }
  }

  if (!firstRunComplete) {
    return (
      <FirstRunGuide onComplete={handleFirstRunComplete} />
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Bhujal</h1>
        <p>Hydro-Climatic Decision Support System</p>
        <DemoModeButton
          active={demoModeActive}
          onToggle={handleDemoModeToggle}
        />
      </header>

      <div className="app-main">
        {/* Map Screen */}
        <MapContainer
          selectedSiteId={selectedSiteId}
          onSiteSelect={handleSiteSelect}
          demoModeActive={demoModeActive}
        />

        {/* Side Panels */}
        <div className="app-panels">
          {!siteData && !demoModeActive ? (
            <div className="placeholder">
              <p>Select a settlement from the map to view details</p>
            </div>
          ) : (
            <>
              <SitePanel
                siteData={siteData}
                loading={loading}
                error={error}
              />

              {siteData && (
                <RecommendationPanel
                  recommendations={recommendations}
                  siteData={siteData}
                  onGenerateDPR={async (siteIds: string, projectName: string, includePdf: boolean) => {
                    setLoading(true);
                    try {
                      const response = await bhujalAPI.generateDPR({ site_ids: siteIds, project_name: projectName, include_pdf: includePdf });
                      console.log('DPR generated:', response.data);
                    } catch (err) {
                      setError('Failed to generate DPR');
                      console.error(err);
                    } finally {
                      setLoading(false);
                    }
                  }}
                />
              )}

              <ScenarioPanel
                siteData={siteData}
                scenarioResult={scenarioResult}
                onRunScenario={handleRunScenario}
                loading={loading}
                error={error}
              />

              <PathwaysPanel
                siteData={siteData}
                pathwaysData={pathwaysData}
                onGeneratePathway={handleGeneratePathway}
                loading={loading}
                error={error}
              />

              <ObservationForm
                siteData={siteData}
                onObservationSubmit={handleObservationSubmit}
                observations={observations}
                loading={loading}
                error={error}
              />

              <ReportViewer
                siteData={siteData}
                onGenerateReport={handleGenerateReport}
                reportData={reportData}
                loading={loading}
                error={error}
              />

              <ValidationPanel
                siteData={siteData}
                loading={loading}
                error={error}
              />
            </>
          )}
        </div>
      </div>

      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} Bhujal - Amazon Environmental Hacks 2026</p>
      </footer>
    </div>
  )
}

export default App
