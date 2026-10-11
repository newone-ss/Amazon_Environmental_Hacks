import React, { useState } from 'react';
import {
  AlertOctagon,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  FileText,
  SlidersHorizontal,
  Sparkles,
  X,
} from 'lucide-react';

export default function FirstRunGuideModal({ open, onClose, t = (k) => k }) {
  const [step, setStep] = useState(1);

  React.useEffect(() => {
    if (!open) return;
    function handleKeyDown(e) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  const steps = [
    {
      step: 1,
      badge: 'Step 1 of 3',
      title: t('guide_step1_title'),
      desc: t('guide_step1_desc'),
      icon: AlertOctagon,
      iconColor: 'icon-red',
      takeaway: 'Rule: The safety verdict overrides all statistical scoring. Never build on a REJECTED site.',
    },
    {
      step: 2,
      badge: 'Step 2 of 3',
      title: t('guide_step2_title'),
      desc: t('guide_step2_desc'),
      icon: SlidersHorizontal,
      iconColor: 'icon-cyan',
      takeaway: 'Insight: Driver bars decompose the "Why?". Use the Scenario tab to stress-test monsoon drought.',
    },
    {
      step: 3,
      badge: 'Step 3 of 3',
      title: t('guide_step3_title'),
      desc: t('guide_step3_desc'),
      icon: FileText,
      iconColor: 'icon-green',
      takeaway: 'Action: State-calibrated wage rates feed directly into the downloadable DPR ZIP package.',
    },
  ];

  const current = steps[step - 1];
  const Icon = current.icon;

  return (
    <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="detail-modal guide-modal" role="dialog" aria-modal="true" aria-labelledby="guide-title">
        <button className="modal-close" onClick={onClose} aria-label="Close guide">
          <X size={20} />
        </button>

        <span className="modal-kicker">DECISION WORKFLOW GUIDE</span>
        <h2 id="guide-title">{t('guide_title')}</h2>

        <div className="guide-step-card">
          <div className="step-header">
            <div className={`step-icon ${current.iconColor}`}>
              <Icon size={24} />
            </div>
            <div>
              <span className="step-badge">{current.badge}</span>
              <h3>{current.title}</h3>
            </div>
          </div>
          <p className="step-description">{current.desc}</p>
          <div className="step-takeaway">
            <b>Key Takeaway:</b> <span>{current.takeaway}</span>
          </div>
        </div>

        {/* Step dots */}
        <div className="step-indicators">
          {steps.map((s) => (
            <button
              key={s.step}
              type="button"
              className={`step-dot ${step === s.step ? 'active' : ''}`}
              onClick={() => setStep(s.step)}
              aria-label={`Go to step ${s.step}`}
            />
          ))}
        </div>

        {/* Navigation Buttons */}
        <div className="guide-actions">
          {step > 1 && (
            <button
              type="button"
              className="secondary-full guide-prev"
              onClick={() => setStep((s) => s - 1)}
            >
              {t('prev')}
            </button>
          )}

          {step < 3 ? (
            <button
              type="button"
              className="primary-cta guide-next"
              onClick={() => setStep((s) => s + 1)}
            >
              {t('next')} <ArrowRight size={16} />
            </button>
          ) : (
            <button
              type="button"
              className="primary-cta guide-finish"
              onClick={onClose}
            >
              <CheckCircle2 size={16} /> {t('got_it')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
