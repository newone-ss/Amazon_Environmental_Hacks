import React from 'react';

interface DemoModeButtonProps {
  active: boolean;
  onToggle: () => void;
}

const DemoModeButton: React.FC<DemoModeButtonProps> = ({ active, onToggle }) => {
  return (
    <button
      className={`demo-mode-button ${active ? 'active' : ''}`}
      onClick={onToggle}
    >
      {active ? 'Demo Mode: ON' : 'Demo Mode: OFF'}
    </button>
  );
};

export default DemoModeButton;