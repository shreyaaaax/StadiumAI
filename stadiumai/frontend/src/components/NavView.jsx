import React, { useState, useEffect } from "react";
import { getNavigation } from "../api";
import { getTranslationHelper } from "../translations";

export default function NavView({ venueId, language, demoScenario }) {
  const t = getTranslationHelper(language);
  const errMsg = t("nav.errors");
  const emptyMsg = t("nav.empty");

  const [fromLoc, setFromLoc] = useState("");
  const [toLoc, setToLoc] = useState("");
  const [accessible, setAccessible] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const [directions, setDirections] = useState(null);
  const [error, setError] = useState(false);

  // Monitor demoScenario triggers
  useEffect(() => {
    if (demoScenario && (demoScenario.expected_feature === "navigation" || demoScenario.expected_feature === "navigate")) {
      setFromLoc("Gate A");
      setToLoc("Restroom");
      setAccessible(true);
      handleRouteSearch("Gate A", "Restroom");
    }
  }, [demoScenario]);

  const handleRouteSearch = async (fromVal = fromLoc, toVal = toLoc) => {
    if (!fromVal.trim() || !toVal.trim()) return;

    setLoading(true);
    setError(false);
    setDirections(null);

    try {
      const res = await getNavigation(fromVal, toVal, venueId, language, accessible);
      setDirections(res);
    } catch (err) {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const onFormSubmit = (e) => {
    e.preventDefault();
    handleRouteSearch();
  };

  const handleSwap = () => {
    const tempVal = fromLoc;
    setFromLoc(toLoc);
    setToLoc(tempVal);
  };

  const applyPreset = (presetFrom, presetTo) => {
    setFromLoc(presetFrom);
    setToLoc(presetTo);
    handleRouteSearch(presetFrom, presetTo);
  };

  return (
    <div className="view-container">
      <div className="nav-grid">
        
        {/* Left Column: Form & Route Details */}
        <div className="nav-planner-card">
          <h3 className="section-title">🗺️ {t("nav.title")}</h3>
          <p className="subtitle">{t("nav.subtitle")}</p>

          <form onSubmit={onFormSubmit} style={{ display: "flex", flexDirection: "column" }}>
            
            {/* FROM Field with Swap button */}
            <div className="form-group" style={{ position: "relative" }}>
              <label className="field-label">{t("nav.from")}</label>
              <input 
                type="text" 
                className="styled-input" 
                placeholder={t("nav.placeholderFrom")}
                value={fromLoc}
                onChange={(e) => setFromLoc(e.target.value)}
                required
              />
              <button 
                type="button" 
                onClick={handleSwap} 
                className="nav-swap-btn"
                title="Swap Locations"
              >
                ↕️
              </button>
            </div>

            {/* TO Field */}
            <div className="form-group" style={{ marginTop: "8px" }}>
              <label className="field-label">{t("nav.to")}</label>
              <input 
                type="text" 
                className="styled-input" 
                placeholder={t("nav.placeholderTo")}
                value={toLoc}
                onChange={(e) => setToLoc(e.target.value)}
                required
              />
            </div>

            {/* Accessibility Checkbox Banner */}
            <div className="nav-accessibility-banner">
              <label className="toggle-label font-display" style={{ fontSize: "14px", fontWeight: "600" }}>
                <input 
                  type="checkbox" 
                  checked={accessible}
                  onChange={(e) => setAccessible(e.target.checked)}
                  style={{ width: "16px", height: "16px", accentColor: "#10B981" }}
                />
                ♿ {t("nav.accessibleOnly")}
              </label>
            </div>

            {/* Get Directions Submit Button */}
            <button type="submit" className="action-btn" style={{ width: "100%", padding: "14px" }} disabled={loading}>
              {loading ? `⚽ ${t("nav.fetchingDirections")}` : t("nav.getDirections")}
            </button>
          </form>

          {/* Preset common routes */}
          <div style={{ marginTop: "24px", paddingTop: "20px", borderTop: "1px solid var(--color-border)" }}>
            <h4 style={{ fontSize: "13px", color: "var(--color-text-primary)", marginBottom: "12px", fontWeight: "700" }}>⭐ {t("nav.commonRoutes")}</h4>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              <button 
                type="button" 
                className="chip-btn" 
                onClick={() => applyPreset("Gate A", "Section 112")}
                disabled={loading}
              >
                Gate A ➔ Section 112
              </button>
              <button 
                type="button" 
                className="chip-btn" 
                onClick={() => applyPreset("Parking Zone 3", "Food Court")}
                disabled={loading}
              >
                Parking Zone 3 ➔ Food Court
              </button>
              <button 
                type="button" 
                className="chip-btn" 
                onClick={() => applyPreset("Metro Exit", "Medical Center")}
                disabled={loading}
              >
                Metro Exit ➔ Medical Center
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="error-box animate-fade" style={{ display: "flex", flexDirection: "column", gap: "8px", background: "rgba(239, 68, 68, 0.08)", borderColor: "var(--color-error)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-error)", marginTop: "20px" }}>
              <p style={{ margin: 0, color: "var(--color-error)", fontSize: "13px" }}>⚠️ {errMsg}</p>
              <button 
                type="button" 
                className="action-btn" 
                style={{ padding: "6px 12px", fontSize: "12px", alignSelf: "flex-start", backgroundColor: "var(--color-error)", color: "#fff", minHeight: "36px" }} 
                onClick={() => handleRouteSearch(fromLoc, toLoc)}
              >
                {t("nav.retry")}
              </button>
            </div>
          )}

          {/* Empty State when no directions */}
          {!directions && !loading && !error && (
            <div className="card-panel text-center animate-fade" style={{ marginTop: "20px", padding: "24px", opacity: 0.85 }}>
              <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", margin: 0 }}>{emptyMsg}</p>
            </div>
          )}

          {/* Results section */}
          {directions && (
            <div className="route-results-section animate-fade">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <span className="route-time-badge">⏱️ ~{directions.estimated_minutes || 8} minutes walk</span>
                {directions.accessible_route && (
                  <span style={{ fontSize: "13px", fontWeight: "700", color: "#1D9E75" }}>♿ Accessible Route Priority</span>
                )}
              </div>

              <div className="steps-list">
                {directions.steps && directions.steps.map((step, idx) => (
                  <div key={idx} className="step-item animate-fade">
                    <span className="step-num-circle">{idx + 1}</span>
                    <p className="step-text-content">{step}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Route Preview Map Placeholder */}
        <div className="route-preview-card">
          <h3 style={{ fontSize: "14px", fontWeight: "600", marginBottom: "16px" }}>Route Preview</h3>
          <div className="map-placeholder-content">
            Interactive map would render here
          </div>
          
          <div className="map-info-box">
             ℹ️ Live venue paths are updated dynamically. Follow nearest physical signs and event stewards.
          </div>
        </div>

      </div>
    </div>
  );
}
