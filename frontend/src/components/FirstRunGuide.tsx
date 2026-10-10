import React, { useState } from 'react';

interface FirstRunGuideProps {
  onComplete: () => void;
}

const FirstRunGuide: React.FC<FirstRunGuideProps> = ({ onComplete }) => {
  const [step, setStep] = useState<number>(1);

  const nextStep = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      onComplete();
    }
  };

  const prevStep = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  return (
    <div className="first-run-guide">
      <div className="guide-header">
        <h1>Welcome to Bhujal</h1>
        <p>Your hydro-climatic decision support system</p>
      </div>

      <div className="guide-steps">
        {/* Step 1: Overview */}
        {step === 1 && (
          <div className="guide-step">
            <h2>What is Bhujal?</h2>
            <p>
              Bhujal is a decision-support platform designed to help identify optimal
              groundwater recharge sites, assess climate vulnerabilities, and plan
              appropriate interventions in hard-rock terrains.
            </p>
            <div className="guide-illustration">
              <div className="illustration-icon">💧</div>
              <p>Focuses on mountainous and tribal watersheds in Odisha, Madhya Pradesh, and Jharkhand</p>
            </div>
          </div>
        )}

        {/* Step 2: How it works */}
        {step === 2 && (
          <div className="guide-step">
            <h2>How Bhujal Works</h2>
            <div className="guide-process">
              <div className="process-step">
                <h3>1. Site Assessment</h3>
                <p>Analyzes hydrogeological data to score sites for recharge suitability,
                heat-water stress, and spring desiccation risk</p>
              </div>
              <div className="process-step">
                <h3>2. Safety Evaluation</h3>
                <p>Applies geotechnical and regulatory veto rules to ensure structural safety</p>
              </div>
              <div className="process-step">
                <h3>3. Recommendations</h3>
                <p>Suggests appropriate interventions with cost estimates using local wage rates</p>
              </div>
              <div className="process-step">
                <h3>4. Planning Support</h3>
                <p>Generates reports, scenarios, and pathways for long-term resilience planning</p>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Getting Started */}
        {step === 3 && (
          <div className="guide-step">
            <h2>Ready to Explore?</h2>
            <p>
              Use the map to explore settlements across the three priority states.
              Click on any site to see detailed assessments and recommendations.
            </p>
            <div className="guide-tips">
              <h3>Tips for Getting Started:</h3>
              <ul>
                <li>🎯 Try the demo mode to see priority sites automatically</li>
                <li>📊 Check the site panels for scores, recommendations, and scenarios</li>
                <li>📝 Share your field observations to improve community knowledge</li>
                <li>📄 Generate reports for planning and approval processes</li>
              </ul>
            </div>
          </div>
        )}
      </div>

      <div className="guide-navigation">
        <button
          className="nav-button prev"
          onClick={prevStep}
          disabled={step === 1}
        >
          {step > 1 ? 'Previous' : ''}
        </button>

        <span className="step-indicator">
          Step {step} of 3
        </span>

        <button
          className="nav-button next"
          onClick={nextStep}
        >
          {step === 3 ? 'Get Started' : 'Next'}
        </button>
      </div>

      <div className="guide-footer">
        <p>
          <em>Bhujal combines deterministic hydrogeology with contextual AI to provide
          transparent, actionable insights for groundwater recharge planning.</em>
        </p>
      </div>
    </div>
  );
};

export default FirstRunGuide;