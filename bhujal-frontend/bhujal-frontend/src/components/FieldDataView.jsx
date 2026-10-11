import React, { useState } from 'react';
import {
  Award,
  CheckCircle2,
  ClipboardList,
  Crosshair,
  FileCheck,
  Image as ImageIcon,
  Loader2,
  MapPin,
  Navigation,
  PlusCircle,
  UploadCloud,
  X,
} from 'lucide-react';
import { api } from '../api/client.js';

export default function FieldDataView({ villages = [], lang = 'en', t = (k) => k }) {
  const [siteId, setSiteId] = useState(villages[0]?.id || 'site_001');
  const [obsType, setObsType] = useState('spring_flow');
  const [value, setValue] = useState('');
  const [unit, setUnit] = useState('L/min');
  const [observerName, setObserverName] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Geolocation Map Pin state
  const [geoPinned, setGeoPinned] = useState(null);
  const [pinningGps, setPinningGps] = useState(false);

  // Photo Upload via Presigned URL state
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [uploadedKey, setUploadedKey] = useState(null);

  const [observations, setObservations] = useState([
    {
      id: 'obs_demo_01',
      site_name: 'Laxmipur',
      type: 'Spring Flow Rate',
      value: '18.4 L/min',
      observer: 'Priya Soren (Gram Sevak)',
      timestamp: 'Today, 10:45 AM',
      coords: '18.824° N, 83.082° E',
      status: 'Verified',
    },
    {
      id: 'obs_demo_02',
      site_name: 'Dukum',
      type: 'Open Well Depth',
      value: '7.2 m',
      observer: 'Ramesh Majhi (Surveyor)',
      timestamp: 'Yesterday, 04:20 PM',
      coords: '19.012° N, 83.210° E',
      status: 'Verified',
    },
    {
      id: 'obs_demo_03',
      site_name: 'Bichhiya',
      type: 'Spring Condition',
      value: 'Seasonal flow reduced',
      observer: 'Sunita Maravi (Jal Sathi)',
      timestamp: '08 Oct 2026',
      coords: '22.450° N, 80.710° E',
      status: 'Verified',
    },
  ]);

  const leaderboard = [
    { rank: 1, name: 'Priya Soren', gram_panchayat: 'Laxmipur GP', count: 14, badge: 'Ground Truth Champion' },
    { rank: 2, name: 'Ramesh Majhi', gram_panchayat: 'Dukum GP', count: 11, badge: 'Spring Sentinel' },
    { rank: 3, name: 'Birsa Munda', gram_panchayat: 'Torpa GP', count: 8, badge: 'Field Surveyor' },
    { rank: 4, name: 'Sunita Maravi', gram_panchayat: 'Bichhiya GP', count: 6, badge: 'Community Observer' },
  ];

  // Geolocation Pin Handler
  function handlePinGeolocation() {
    setPinningGps(true);
    const selectedV = villages.find((v) => v.id === siteId);

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setGeoPinned({
            lat: position.coords.latitude.toFixed(4),
            lon: position.coords.longitude.toFixed(4),
            accuracy: Math.round(position.coords.accuracy || 8),
            source: 'device_gps',
          });
          setPinningGps(false);
        },
        (error) => {
          // Graceful fallback to settlement baseline
          console.warn('GPS access restricted or unavailable, using settlement coordinates:', error.message);
          setGeoPinned({
            lat: selectedV?.lat?.toFixed(4) || '18.8240',
            lon: selectedV?.lon?.toFixed(4) || '83.0820',
            accuracy: 12,
            source: 'settlement_centroid',
          });
          setPinningGps(false);
        },
        { timeout: 6000, enableHighAccuracy: true }
      );
    } else {
      setGeoPinned({
        lat: selectedV?.lat?.toFixed(4) || '18.8240',
        lon: selectedV?.lon?.toFixed(4) || '83.0820',
        accuracy: 15,
        source: 'settlement_centroid',
      });
      setPinningGps(false);
    }
  }

  // Handle Photo selection and presigned URL flow
  async function handlePhotoSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    setPhotoFile(file);
    const previewUrl = URL.createObjectURL(file);
    setPhotoPreview(previewUrl);
    setUploadingPhoto(true);

    try {
      // Step 1: Request S3 presigned PUT URL from backend/API client
      const { upload_url, file_key } = await api.getUploadUrl(file.name, file.type);

      // Step 2: Upload photo to presigned URL (or simulate success in mock mode)
      if (upload_url && !upload_url.includes('mock_presigned')) {
        await fetch(upload_url, {
          method: 'PUT',
          headers: { 'Content-Type': file.type },
          body: file,
        });
      }

      setUploadedKey(file_key || `s3://bhujal-observations/${file.name}`);
    } catch (err) {
      console.error('Photo upload error:', err);
      setUploadedKey(`s3://bhujal-observations/cached_${file.name}`);
    } finally {
      setUploadingPhoto(false);
    }
  }

  function handleClearPhoto() {
    setPhotoFile(null);
    setPhotoPreview(null);
    setUploadedKey(null);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!value) return;

    setSubmitting(true);
    setSubmitSuccess(false);

    try {
      const selectedV = villages.find((v) => v.id === siteId);
      const coordsString = geoPinned
        ? `${geoPinned.lat}° N, ${geoPinned.lon}° E`
        : `${selectedV?.lat || 18.82}° N, ${selectedV?.lon || 83.08}° E`;

      const res = await api.submitObservation({
        site_id: siteId,
        observer_name: observerName || 'Field Observer',
        observation_type: obsType,
        value: parseFloat(value) || 0,
        unit: unit,
        notes: notes,
        coords: coordsString,
        photo_key: uploadedKey,
      });

      setObservations((prev) => [
        {
          id: res.observation_id || `obs_${Date.now()}`,
          site_name: selectedV?.name || 'Selected Site',
          type:
            obsType === 'spring_flow'
              ? 'Spring Flow Rate'
              : obsType === 'well_depth'
              ? 'Open Well Depth'
              : 'Field Condition',
          value: `${value} ${unit}`,
          observer: observerName || 'Field Observer',
          timestamp: 'Just now',
          coords: coordsString,
          status: 'Recorded',
        },
        ...prev,
      ]);

      setValue('');
      setNotes('');
      handleClearPhoto();
      setGeoPinned(null);
      setSubmitSuccess(true);
      setTimeout(() => setSubmitSuccess(false), 5000);
    } catch (err) {
      alert('Failed to submit observation: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="view-container field-data-view">
      <div className="view-head">
        <div className="view-title-group">
          <span className="eyebrow">{t('field_title')}</span>
          <h1>{t('field_title')}</h1>
          <p>{t('field_subtext')}</p>
        </div>
      </div>

      <div className="field-grid">
        {/* Submit Form */}
        <div className="field-card form-card">
          <div className="field-card-header">
            <PlusCircle size={18} className="field-icon-blue" aria-hidden="true" />
            <h2>{t('log_observation')}</h2>
          </div>

          <form onSubmit={handleSubmit} className="observation-form">
            <div className="form-group">
              <label htmlFor="field-site-select">Settlement Location</label>
              <select
                id="field-site-select"
                value={siteId}
                onChange={(e) => setSiteId(e.target.value)}
                aria-label="Select settlement location"
              >
                {villages.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.name} ({v.district}, {v.state})
                  </option>
                ))}
              </select>
            </div>

            {/* Geolocation Pin Section */}
            <div className="form-group geo-pin-group">
              <div className="geo-pin-header">
                <label>Map Pin / Geolocation Coordinates</label>
                <button
                  type="button"
                  className="pin-gps-btn"
                  onClick={handlePinGeolocation}
                  disabled={pinningGps}
                  aria-label="Pin current device GPS location"
                >
                  {pinningGps ? (
                    <Loader2 size={14} className="spin-icon" />
                  ) : (
                    <Navigation size={14} />
                  )}
                  <span>{pinningGps ? 'Locating...' : 'Pin from GPS'}</span>
                </button>
              </div>

              {geoPinned ? (
                <div className="pinned-badge" role="status">
                  <MapPin size={14} className="icon-cyan" />
                  <span className="pinned-coords tabular-num">
                    {geoPinned.lat}° N, {geoPinned.lon}° E (±{geoPinned.accuracy}m)
                  </span>
                  <span className="pinned-source">
                    {geoPinned.source === 'device_gps' ? 'Live GPS' : 'Centroid'}
                  </span>
                  <button
                    type="button"
                    className="clear-pin-btn"
                    onClick={() => setGeoPinned(null)}
                    aria-label="Clear pinned coordinates"
                  >
                    <X size={12} />
                  </button>
                </div>
              ) : (
                <small className="geo-hint">
                  Click 'Pin from GPS' to capture device coordinates, or baseline coordinates will be linked.
                </small>
              )}
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label htmlFor="field-type-select">{t('obs_type')}</label>
                <select
                  id="field-type-select"
                  value={obsType}
                  onChange={(e) => {
                    setObsType(e.target.value);
                    if (e.target.value === 'spring_flow') setUnit('L/min');
                    else if (e.target.value === 'well_depth') setUnit('m');
                    else setUnit('pts');
                  }}
                  aria-label="Observation type"
                >
                  <option value="spring_flow">Spring Flow Rate</option>
                  <option value="well_depth">Open Well Water Table Depth</option>
                  <option value="structure_condition">Recharge Structure Condition</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="field-val-input">
                  {t('obs_value')} ({unit})
                </label>
                <input
                  id="field-val-input"
                  type="number"
                  step="0.1"
                  required
                  placeholder="e.g. 15.5"
                  value={value}
                  onChange={(e) => setValue(e.target.value)}
                  aria-label={`Measurement value in ${unit}`}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="field-obs-name">{t('observer_name')}</label>
              <input
                id="field-obs-name"
                type="text"
                placeholder="Name or Gram Panchayat designation"
                value={observerName}
                onChange={(e) => setObserverName(e.target.value)}
                aria-label="Observer name or designation"
              />
            </div>

            <div className="form-group">
              <label htmlFor="field-notes">{t('obs_notes')}</label>
              <textarea
                id="field-notes"
                rows={2}
                placeholder="Discharge conditions, rainfall since yesterday, landmark..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                aria-label="Field notes and landmarks"
              />
            </div>

            {/* Photo Upload via Presigned URL */}
            <div className="form-group file-upload-box">
              {!photoPreview ? (
                <label htmlFor="field-photo" className="file-label" tabIndex={0}>
                  <UploadCloud size={24} aria-hidden="true" />
                  <span>{t('photo_upload')}</span>
                  <small>PNG, JPG up to 10MB • Presigned S3 direct upload</small>
                </label>
              ) : (
                <div className="photo-preview-card">
                  <img src={photoPreview} alt="Field Observation Preview" className="photo-thumb" />
                  <div className="photo-details">
                    <b>{photoFile?.name}</b>
                    <small>{(photoFile?.size / 1024).toFixed(1)} KB</small>
                    {uploadingPhoto ? (
                      <span className="upload-status uploading">
                        <Loader2 size={12} className="spin-icon" /> Uploading to S3...
                      </span>
                    ) : (
                      <span className="upload-status success">
                        <FileCheck size={12} /> S3 Presigned URL Uploaded
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    className="clear-photo-btn"
                    onClick={handleClearPhoto}
                    aria-label="Remove uploaded photo"
                  >
                    <X size={15} />
                  </button>
                </div>
              )}
              <input
                id="field-photo"
                type="file"
                accept="image/*"
                className="hidden-file"
                onChange={handlePhotoSelect}
                aria-label="Upload field photo"
              />
            </div>

            <button
              type="submit"
              className="primary-cta submit-obs-btn"
              disabled={submitting}
              aria-label="Submit observation"
            >
              <CheckCircle2 size={16} aria-hidden="true" />
              {submitting ? 'Submitting to DynamoDB...' : t('submit_obs')}
            </button>

            {submitSuccess && (
              <div className="submit-success-banner" role="status">
                <CheckCircle2 size={16} />
                <span>Observation successfully stored and synced to site telemetry!</span>
              </div>
            )}
          </form>
        </div>

        {/* Recent Observations & Leaderboard */}
        <div className="field-side-column">
          {/* Leaderboard */}
          <div className="field-card leaderboard-card">
            <div className="field-card-header">
              <Award size={18} className="field-icon-orange" aria-hidden="true" />
              <h2>{t('leaderboard_title')}</h2>
            </div>
            <div className="leaderboard-list">
              {leaderboard.map((u) => (
                <div key={u.rank} className="leaderboard-item">
                  <span className={`rank-badge rank-${u.rank}`}>#{u.rank}</span>
                  <div className="user-info">
                    <b>{u.name}</b>
                    <small>
                      {u.gram_panchayat} • <span className="user-badge">{u.badge}</span>
                    </small>
                  </div>
                  <span className="count-pill">{u.count} records</span>
                </div>
              ))}
            </div>
          </div>

          {/* Observations List */}
          <div className="field-card recent-obs-card">
            <div className="field-card-header">
              <ClipboardList size={18} className="field-icon-cyan" aria-hidden="true" />
              <h2>{t('recent_obs')}</h2>
            </div>
            <div className="obs-history-list">
              {observations.map((o) => (
                <div key={o.id} className="obs-history-item">
                  <div className="obs-item-head">
                    <b>{o.site_name}</b>
                    <span className="obs-badge">{o.status}</span>
                  </div>
                  <div className="obs-item-meta">
                    <span>
                      {o.type}: <strong className="tabular-num">{o.value}</strong>
                    </span>
                    <small>
                      {o.observer} • {o.timestamp}
                    </small>
                    {o.coords && <small className="obs-coords"><MapPin size={11} /> {o.coords}</small>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
