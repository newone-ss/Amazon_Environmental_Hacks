import React, { useEffect, useMemo, useState, useCallback } from 'react';
import {
  CircleHelp,
  ClipboardList,
  Database,
  FileText,
  Languages,
  MapPin,
  Search,
  X,
} from 'lucide-react';
import { api } from './api/client.js';
import { TRANSLATIONS } from './data/translations.js';
import MapStage from './components/MapStage.jsx';
import SettlementPanel from './components/SettlementPanel.jsx';
import FieldDataView from './components/FieldDataView.jsx';
import ReportsView from './components/ReportsView.jsx';
import AboutDataView from './components/AboutDataView.jsx';
import FirstRunGuideModal from './components/FirstRunGuideModal.jsx';

const navItems = [
  { id: 'Map', key: 'nav_map', icon: MapPin },
  { id: 'Field Data', key: 'nav_field_data', icon: ClipboardList },
  { id: 'Reports', key: 'nav_reports', icon: FileText },
  { id: 'About and Data', key: 'nav_about', icon: Database },
];

function BrandMark({ t }) {
  return (
    <div className="brand-lockup" aria-label="Bhujal home">
      <svg className="brand-symbol" viewBox="0 0 64 56" role="img" aria-label="mountain and water logo">
        <path d="M4 27 21 7l8 10L39 2l21 31H4Z" fill="#53d6ba" />
        <path d="m16 27 13-10 8 7L46 14l12 19H5Z" fill="#128c80" />
        <path d="m20 17 9 0-5 6Z" fill="#e6fff8" />
        <path d="M3 38c8-6 15-6 23 0s15 6 23 0" fill="none" stroke="#35c6f4" strokeWidth="4" strokeLinecap="round" />
        <path d="M7 46c7-4 13-4 20 0s13 4 20 0" fill="none" stroke="#168cc5" strokeWidth="3.5" strokeLinecap="round" />
      </svg>
      <div className="brand-copy">
        <div className="brand-name">Bhujal</div>
        <div className="brand-subtitle">{t('brand_subtitle')}</div>
      </div>
    </div>
  );
}

function Header({
  query,
  setQuery,
  stateFilter,
  setStateFilter,
  villages,
  onSelectVillage,
  lang,
  setLang,
  t,
}) {
  const [showSuggestions, setShowSuggestions] = useState(false);

  const suggestions = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase();
    return villages
      .filter((v) => v.name.toLowerCase().includes(q) || v.district.toLowerCase().includes(q))
      .slice(0, 5);
  }, [query, villages]);

  function submitSearch(e) {
    e.preventDefault();
    const match = suggestions[0] || villages.find((v) => v.name.toLowerCase() === query.trim().toLowerCase());
    if (match) {
      onSelectVillage(match);
      setQuery(match.name);
    }
    setShowSuggestions(false);
  }

  return (
    <header className="topbar" role="banner">
      <div className="topbar-branding-row">
        <BrandMark t={t} />

        <div className="topbar-actions-group">
          {/* Language Toggle */}
          <button
            type="button"
            className="lang-toggle-pill"
            onClick={() => setLang((l) => (l === 'en' ? 'hi' : 'en'))}
            aria-label={`Switch language to ${lang === 'en' ? 'Hindi' : 'English'}`}
            title="Toggle English / Hindi"
          >
            <Languages size={14} />
            <span>{lang === 'en' ? 'हिं (HI)' : 'EN'}</span>
          </button>
        </div>
      </div>

      <div className="topbar-search-row">
        <form className="search-wrap" onSubmit={submitSearch} role="search">
          <Search size={16} aria-hidden="true" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            placeholder={t('search_placeholder')}
            aria-label={t('search_placeholder')}
          />
          {query && (
            <button
              type="button"
              className="search-clear"
              onClick={() => setQuery('')}
              aria-label="Clear search"
            >
              <X size={14} />
            </button>
          )}
          {showSuggestions && suggestions.length > 0 && (
            <div className="suggestions" role="listbox">
              {suggestions.map((v) => (
                <button
                  type="button"
                  key={v.id}
                  onMouseDown={() => {
                    onSelectVillage(v);
                    setQuery(v.name);
                    setShowSuggestions(false);
                  }}
                >
                  <MapPin size={15} />
                  <span>
                    <b>{v.name}</b>
                    <small>{v.district}, {v.state}</small>
                  </span>
                </button>
              ))}
            </div>
          )}
        </form>

        {/* State Filter */}
        <label className="region-select">
          <MapPin size={14} fill="currentColor" aria-hidden="true" />
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            aria-label="Filter settlements by State"
          >
            <option value="All states">{t('all_states')}</option>
            <option value="Odisha">Odisha</option>
            <option value="Madhya Pradesh">Madhya Pradesh</option>
            <option value="Jharkhand">Jharkhand</option>
          </select>
        </label>
      </div>
    </header>
  );
}

function Sidebar({ active, setActive, onOpenGuide, t }) {
  return (
    <aside className="sidebar" aria-label="Main navigation">
      <nav className="sidebar-nav">
        {navItems.map(({ id, key, icon: Icon }) => (
          <button
            key={id}
            className={`nav-item ${active === id ? 'active' : ''}`}
            onClick={() => setActive(id)}
            aria-current={active === id ? 'page' : undefined}
          >
            <Icon size={20} strokeWidth={2} />
            <span>{t(key)}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <button
          type="button"
          className="nav-item guide-nav-item"
          onClick={onOpenGuide}
          aria-label="Open 3-step decision guide"
        >
          <CircleHelp size={19} />
          <span>{t('nav_help')}</span>
        </button>
        <div className="sidebar-version">
          Bhujal <span>•</span> AWS Hackathon 2026
        </div>
      </div>
    </aside>
  );
}

export default function App() {
  const [lang, setLang] = useState('en');
  const [active, setActive] = useState('Map');
  const [stateFilter, setStateFilter] = useState('All states');
  const [query, setQuery] = useState('');
  const [villages, setVillages] = useState([]);
  const [sites, setSites] = useState({});
  const [selectedVillage, setSelectedVillage] = useState(null);
  const [selectedSite, setSelectedSite] = useState(null);
  const [siteLoading, setSiteLoading] = useState(false);
  const [siteError, setSiteError] = useState(null);
  const [activeTab, setActiveTab] = useState('Overview');
  const [showPanel, setShowPanel] = useState(true);
  const [layerMode, setLayerMode] = useState('Recharge Potential');
  const [showSafetyRings, setShowSafetyRings] = useState(true);
  const [showSprings, setShowSprings] = useState(true);
  const [guideOpen, setGuideOpen] = useState(false);

  // Mobile Bottom Sheet state: 'peek' | 'half' | 'full'
  const [sheetState, setSheetState] = useState('half');

  // Translation lookup helper
  const t = useMemo(() => {
    return (key) => TRANSLATIONS[lang]?.[key] || key;
  }, [lang]);

  // Load settlements based on state filter
  useEffect(() => {
    const controller = new AbortController();
    let isMounted = true;
    async function loadVillages() {
      try {
        const list = await api.getVillages(stateFilter, { signal: controller.signal });
        if (!isMounted) return;
        setVillages(list);
        if (list.length > 0) {
          const currentExists = selectedVillage && list.some((v) => v.id === selectedVillage.id);
          if (!currentExists) {
            setSelectedVillage(list[0]);
          }
        }
      } catch (e) {
        if (e.name === 'AbortError' || e.name === 'CancellationError') return;
        console.error('Failed to load villages', e);
      }
    }
    loadVillages();
    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [stateFilter]);

  // Load site detail for selected village
  useEffect(() => {
    const controller = new AbortController();
    let isMounted = true;
    async function loadSite() {
      if (!selectedVillage?.id) return;
      setSiteLoading(true);
      setSiteError(null);
      try {
        const site = await api.getSite(selectedVillage.id, { signal: controller.signal });
        if (isMounted) {
          setSelectedSite(site);
          setSites((prev) => ({ ...prev, [selectedVillage.id]: site }));
        }
      } catch (e) {
        if (e.name === 'AbortError' || e.name === 'CancellationError') return;
        if (isMounted) {
          setSiteError(e.message || 'Could not load site evaluation');
        }
      } finally {
        if (isMounted) setSiteLoading(false);
      }
    }
    loadSite();
    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [selectedVillage?.id]);

  function handleSelectVillage(v) {
    setSelectedVillage(v);
    setShowPanel(true);
    setActiveTab('Overview');
    setActive('Map');
    // On mobile, expand bottom sheet to half view
    setSheetState('half');
  }

  function handleSelectVillageById(id) {
    const v = villages.find((item) => item.id === id);
    if (v) handleSelectVillage(v);
  }

  const handleRetry = useCallback(() => {
    if (selectedVillage?.id) {
      // Trigger the loadSite effect by temporarily clearing and re-setting selectedVillage
      setSelectedSite(null);
      setSiteError(null);
      setSiteLoading(true);
      api.getSite(selectedVillage.id).then(setSelectedSite).catch(console.error).finally(() => {
        setSiteLoading(false);
      });
    }
  }, [selectedVillage?.id]);

  function cycleSheetState() {
    setSheetState((curr) => (curr === 'peek' ? 'half' : curr === 'half' ? 'full' : 'peek'));
  }

  return (
    <div className="app-shell" lang={lang}>
      <Header
        query={query}
        setQuery={setQuery}
        stateFilter={stateFilter}
        setStateFilter={setStateFilter}
        villages={villages}
        onSelectVillage={handleSelectVillage}
        lang={lang}
        setLang={setLang}
        t={t}
      />

      <Sidebar
        active={active}
        setActive={setActive}
        onOpenGuide={() => setGuideOpen(true)}
        t={t}
      />

      <main className="main-shell" role="main">
        {active === 'Field Data' ? (
          <FieldDataView villages={villages} lang={lang} t={t} />
        ) : active === 'Reports' ? (
          <ReportsView villages={villages} sites={sites} t={t} />
        ) : active === 'About and Data' ? (
          <AboutDataView t={t} />
        ) : (
          /* MAP VIEW */
          <div className={`map-layout ${showPanel ? '' : 'panel-hidden'}`}>
            <MapStage
              villages={villages}
              sites={sites}
              selectedVillage={selectedVillage}
              onSelectVillage={handleSelectVillage}
              stateFilter={stateFilter}
              layerMode={layerMode}
              setLayerMode={setLayerMode}
              showSafetyRings={showSafetyRings}
              setShowSafetyRings={setShowSafetyRings}
              showSprings={showSprings}
              setShowSprings={setShowSprings}
            />

            {showPanel && selectedVillage && (
              <div className={`settlement-panel-wrapper sheet-${sheetState}`}>
                <div
                  className="sheet-handle-bar"
                  onClick={cycleSheetState}
                  role="button"
                  tabIndex={0}
                  aria-label={`Toggle mobile bottom sheet height: current state ${sheetState}`}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') cycleSheetState(); }}
                >
                  <span className="sheet-pill" />
                </div>

                <SettlementPanel
                  village={selectedVillage}
                  site={selectedSite}
                  activeTab={activeTab}
                  setActiveTab={setActiveTab}
                  onClose={() => setShowPanel(false)}
                  onSelectVillageById={handleSelectVillageById}
                  loading={siteLoading}
                  error={siteError}
                  onRetry={handleRetry}
                />
              </div>
            )}

            {!showPanel && (
              <button
                type="button"
                className="reopen-panel"
                onClick={() => setShowPanel(true)}
                aria-label="Reopen settlement detail panel"
              >
                <MapPin size={16} /> Settlement Details
              </button>
            )}
          </div>
        )}
      </main>

      {/* Mobile Bottom Navigation Bar (< 768px) */}
      <nav className="mobile-bottom-bar" aria-label="Mobile navigation">
        {navItems.map(({ id, key, icon: Icon }) => (
          <button
            key={id}
            type="button"
            className={`mobile-tab-btn ${active === id ? 'active' : ''}`}
            onClick={() => setActive(id)}
            aria-label={t(key)}
          >
            <Icon size={19} />
            <span>{t(key)}</span>
          </button>
        ))}
        <button
          type="button"
          className="mobile-tab-btn"
          onClick={() => setGuideOpen(true)}
          aria-label={t('nav_help')}
        >
          <CircleHelp size={19} />
          <span>{t('nav_help')}</span>
        </button>
      </nav>

      {/* First-Run Decision Workflow Guide Modal */}
      <FirstRunGuideModal
        open={guideOpen}
        onClose={() => setGuideOpen(false)}
        t={t}
      />
    </div>
  );
}
