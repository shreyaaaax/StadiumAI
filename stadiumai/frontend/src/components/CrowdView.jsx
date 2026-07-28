import React, { useState } from 'react';
import * as api from '../api';
import { getTranslationHelper } from '../translations';

function CrowdView({ language, venueId, t: propT, demoScenario }) {
  const [phase, setPhase] = useState('during_match');
  const [crowdData, setCrowdData] = useState(null);
  const [loading, setLoading] = useState(false);

  const localT = (key, lang) => {
    const helper = getTranslationHelper(lang);
    const map = {
      'crowdPre': 'crowd.preMatch',
      'crowdDuring': 'crowd.duringMatch',
      'crowdHalf': 'crowd.halfTime',
      'crowdPost': 'crowd.postMatch',
      'crowdStatus': 'crowd.title'
    };
    return helper(map[key] || key);
  };
  const t = propT || localT;

  const phases = [
    { key: 'pre_match', label: t('crowdPre', language) },
    { key: 'during_match', label: t('crowdDuring', language) },
    { key: 'half_time', label: t('crowdHalf', language) },
    { key: 'post_match', label: t('crowdPost', language) },
  ];

  const handlePhaseChange = async (newPhase) => {
    setPhase(newPhase);
    setLoading(true);
    
    try {
      const cleanId = venueId.replace("venue-", "");
      // Fetch crowd data for the new phase
      const response = await fetch(`http://localhost:8000/crowd/${cleanId}?phase=${newPhase}`);
      const data = await response.json();
      
      // Data should be: { phase: string, zones: [{id, name, location, type, density_percent}, ...] }
      setCrowdData(data);
    } catch (error) {
      console.error('Error fetching crowd data:', error);
      setCrowdData(null);
    }
    
    setLoading(false);
  };

  const getDensityColor = (density) => {
    if (density >= 80) return '#EF4444'; // Red
    if (density >= 60) return '#F59E0B'; // Amber
    if (density >= 40) return '#FBBF24'; // Light amber
    return '#10B981'; // Green
  };

  const getDensityStatus = (density) => {
    if (density >= 80) return 'critical';
    if (density >= 60) return 'high';
    if (density >= 40) return 'moderate';
    return 'low';
  };

  // Fetch initial crowd data on mount or when venueId changes
  React.useEffect(() => {
    handlePhaseChange(phase);
  }, [venueId]);

  // Handle demo scenario trigger
  React.useEffect(() => {
    if (demoScenario && demoScenario.expected_feature === 'crowd') {
      handlePhaseChange('half_time');
    }
  }, [demoScenario]);

  return (
    <div className="crowd-view">

      {/* Title */}
      <h2 className="crowd-title">👥 {t('crowdStatus', language) || 'Live Crowd Status'}</h2>

      {/* Phase selector */}
      <div className="phase-selector">
        {phases.map(p => (
          <button
            key={p.key}
            onClick={() => handlePhaseChange(p.key)}
            className={`phase-btn ${phase === p.key ? 'active' : ''}`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Loading state */}
      {loading && <div className="loading">Loading crowd data...</div>}

      {/* Zone cards grid */}
      {crowdData && crowdData.zones && crowdData.zones.length > 0 ? (
        <div className="zones-grid">
          {crowdData.zones.map(zone => (
            <div key={zone.id} className="zone-card">

              {/* Zone name */}
              <div className="zone-name">{zone.name}</div>

              {/* Zone location */}
              <div className="zone-location">{zone.location}</div>

              {/* Density bar */}
              <div className="density-bar-container">
                <div className="density-bar-bg">
                  <div 
                    className="density-bar-fill" 
                    style={{ 
                      width: `${zone.density_percent}%`,
                      backgroundColor: getDensityColor(zone.density_percent)
                    }} 
                  />
                </div>
              </div>

              {/* Density percentage + status */}
              <div className="density-info">
                <span className="density-percent">{zone.density_percent}%</span>
                <span className={`density-status ${getDensityStatus(zone.density_percent)}`}>
                  {getDensityStatus(zone.density_percent).toUpperCase()}
                </span>
              </div>

              {/* Zone type badge */}
              <div className="zone-type-badge">{zone.type}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="no-data">No crowd data available</div>
      )}
    </div>
  );
}

export default CrowdView;
