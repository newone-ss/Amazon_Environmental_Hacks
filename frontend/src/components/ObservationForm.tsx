import React, { useState } from 'react';

interface ObservationFormProps {
  siteData: any; // Site type
  onObservationSubmit: (observationData: any) => Promise<void>;
  observations: any[]; // LeaderboardEntry[]
  loading: boolean;
  error: string | null;
}

const ObservationForm: React.FC<ObservationFormProps> = ({
  siteData: _siteData,
  onObservationSubmit,
  observations,
  loading,
  error
}) => {
  const [text, setText] = useState<string>('');
  const [observerId, setObserverId] = useState<string>('');
  const [observerName, setObserverName] = useState<string>('');
  const [languageCode, setLanguageCode] = useState<string>('en-IN');
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);

  // Handle text observation submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || !observerId.trim()) return;

    setSubmitSuccess(false);

    try {
      // In a real app, we would upload photo to S3 via presigned URL first
      // For now, we'll just submit the text observation
      const observationData = {
        text: text.trim(),
        observer_id: observerId.trim(),
        observer_name: observerName.trim() || 'Anonymous',
        language_code: languageCode,
        photo_filename: photoFile ? photoFile.name : undefined
      };

      await onObservationSubmit(observationData);
      setSubmitSuccess(true);

      // Reset form
      setText('');
      setObserverId('');
      setObserverName('');
      setLanguageCode('en-IN');
      setPhotoFile(null);
      setPhotoPreview(null);
    } catch (err) {
      console.error('Observation submission failed:', err);
      // Error will be handled by parent component
    }
  };

  // Handle photo upload
  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (file) {
      setPhotoFile(file);
      // Create preview URL
      const previewUrl = URL.createObjectURL(file);
      setPhotoPreview(previewUrl);
    } else {
      setPhotoFile(null);
      setPhotoPreview(null);
    }
  };

  return (
    <div className="observation-panel">
      <div className="panel-header">
        <h2>Field Observation</h2>
        <p>Share your ground-level insights to improve community knowledge</p>
      </div>

      {/* Submission Status */}
      {submitSuccess && (
        <div className="submit-success">
          <p>✅ Observation submitted successfully!</p>
          <p>Thank you for contributing to community knowledge.</p>
        </div>
      )}

      {error && (
        <div className="submit-error" style={{ color: '#e53e3e', padding: '8px 0' }}>
          <p>⚠️ {error}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="observation-form">
        <div className="form-group">
          <label htmlFor="observation-text">Your Observation:</label>
          <textarea
            id="observation-text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g., Water level in the well is lower than last month..."
            rows={4}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="observer-id">Your ID (mobile number):</label>
          <input
            type="tel"
            id="observer-id"
            value={observerId}
            onChange={(e) => setObserverId(e.target.value)}
            placeholder="e.g., +91XXXXXXXXXX"
            pattern="[\\+]?[\\d]{10,13}"
            title="Please enter a valid mobile number"
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="observer-name">Your Name (optional):</label>
          <input
            type="text"
            id="observer-name"
            value={observerName}
            onChange={(e) => setObserverName(e.target.value)}
            placeholder="Your name"
          />
        </div>

        <div className="form-group">
          <label htmlFor="language-code">Language:</label>
          <select
            id="language-code"
            value={languageCode}
            onChange={(e) => setLanguageCode(e.target.value)}
          >
            <option value="en-IN">English (India)</option>
            <option value="hi-IN">Hindi</option>
            <option value="or-IN">Odia</option>
            <option value="san-IN">Santali</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="photo-upload">Photo (optional):</label>
          <input
            type="file"
            id="photo-upload"
            accept="image/*"
            onChange={handlePhotoChange}
          />
          {photoPreview && (
            <div className="photo-preview">
              <img src={photoPreview} alt="Preview" />
              <button type="button" onClick={() => {
                setPhotoFile(null);
                setPhotoPreview(null);
              }}>
                Remove
              </button>
            </div>
          )}
          <p className="help-text">Upload a photo to support your observation (JPG, PNG)</p>
        </div>

        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Observation'}
        </button>
      </form>

      {/* Leaderboard */}
      <div className="leaderboard-section">
        <h3>Top Contributors</h3>
        {observations.length === 0 ? (
          <p className="leaderboard-empty">No observations yet. Be the first to contribute!</p>
        ) : (
          <ol className="leaderboard-list">
            {observations.slice(0, 5).map((obs: any, index: number) => (
              <li key={obs.observer_id || index} className="leaderboard-item">
                <span className="rank">#{index + 1}</span>
                <span className="observer-name">
                  {obs.observer_name || 'Anonymous'}
                </span>
                <span className="observation-count">
                  ({obs.total_observations} contributions)
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
};

export default ObservationForm;