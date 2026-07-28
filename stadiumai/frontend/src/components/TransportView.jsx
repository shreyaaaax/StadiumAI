import React, { useState, useEffect } from "react";
import { getTransport } from "../api";
import { getTranslationHelper } from "../translations";

export default function TransportView({ venueId, language, demoScenario }) {
  const t = getTranslationHelper(language);
  const errMsg = t("transport.errors");
  const emptyMsg = t("transport.empty");
  const [origin, setOrigin] = useState("");
  const [matchTime, setMatchTime] = useState("20:00");
  const [currentTime, setCurrentTime] = useState("18:30");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(false);

  // Auto-fill current browser time in 24h format
  useEffect(() => {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    setCurrentTime(`${hours}:${minutes}`);
  }, []);

  // Monitor demoScenario triggers
  useEffect(() => {
    if (demoScenario && demoScenario.expected_feature === "transport") {
      setOrigin("Downtown Hotel");
      setMatchTime("20:00");
      setCurrentTime("22:15");
      const triggerSearchForDemo = async () => {
        setLoading(true);
        setError(false);
        setResult(null);
        try {
          const res = await getTransport(venueId, "20:00", "22:15", "Downtown Hotel", language);
          setResult(res);
        } catch (err) {
          setError(true);
        } finally {
          setLoading(false);
        }
      };
      triggerSearchForDemo();
    }
  }, [demoScenario]);

  const triggerSearch = async () => {
    if (!origin.trim()) return;

    setLoading(true);
    setError(false);
    setResult(null);

    try {
      const res = await getTransport(venueId, matchTime, currentTime, origin, language);
      setResult(res);
    } catch (err) {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    triggerSearch();
  };

  return (
    <div className="view-container">
      <div className="transport-grid">
        
        {/* Left Column: Form & General Travel parameters */}
        <div className="transport-form-card">
          <h3 className="section-title">🚌 {t("transport.title")}</h3>
          <p className="subtitle">{t("transport.subtitle")}</p>

          <form onSubmit={handleSearch}>
            
            {/* Where are you? input */}
            <div className="form-group">
              <label className="field-label">{t("transport.whereNow")}</label>
              <input
                type="text"
                className="styled-input"
                placeholder={t("transport.placeholderWhere")}
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                required
                style={{ width: "100%", padding: "12px 16px", marginBottom: "20px" }}
              />
            </div>

            {/* Match start & current clock row */}
            <div className="time-inputs-row">
              <div className="form-group">
                <label className="field-label">{t("transport.matchStartTime")}</label>
                <input
                  type="text"
                  className="styled-input"
                  placeholder="20:00"
                  value={matchTime}
                  onChange={(e) => setMatchTime(e.target.value)}
                  required
                />
              </div>
              
              <div className="form-group">
                <label className="field-label">{t("transport.currentClockTime")}</label>
                <input
                  type="text"
                  className="styled-input"
                  placeholder="18:30"
                  value={currentTime}
                  onChange={(e) => setCurrentTime(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Recommendation Submit button */}
            <button 
              type="submit" 
              className="action-btn" 
              style={{ width: "100%", padding: "14px", fontWeight: "600" }} 
              disabled={loading}
            >
              {loading ? t("transport.analyzingTransit") : t("transport.getRecommendation")}
            </button>
          </form>

          {error && (
            <div className="error-box animate-fade" style={{ display: "flex", flexDirection: "column", gap: "8px", background: "rgba(239, 68, 68, 0.08)", borderColor: "var(--color-error)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-error)", marginTop: "20px" }}>
              <p style={{ margin: 0, color: "var(--color-error)", fontSize: "13px" }}>⚠️ {errMsg}</p>
              <button 
                type="button" 
                className="action-btn" 
                style={{ padding: "6px 12px", fontSize: "12px", alignSelf: "flex-start", backgroundColor: "var(--color-error)", color: "#fff", minHeight: "36px" }} 
                onClick={triggerSearch}
              >
                {t("transport.retry")}
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Transport Options panel */}
        <div className="transport-info-card">
          <h3 className="transport-info-title">Transport Options</h3>
          
          {loading && (
            <div className="animate-pulse" style={{ fontSize: "14px", color: "var(--color-text-secondary)" }}>
              ⏳ Querying public transport routes, road traffic delays, and shuttle status...
            </div>
          )}

          {!result && !loading && (
            <div style={{ fontSize: "13px", color: "var(--color-text-secondary)", lineHeight: "1.6" }}>
              {emptyMsg}
            </div>
          )}

          {result && !loading && (
            <div className="animate-fade">
              {/* Suggested departure badge */}
              {result.suggested_departure && (
                <div className="suggested-departure-badge">
                  🚀 Depart: {result.suggested_departure}
                </div>
              )}

              {/* Recommendation text description */}
              <p className="transport-recommendation-text">
                {result.recommendation}
              </p>

              {/* Transit alternatives cards */}
              {result.options && result.options.length > 0 && (
                <div className="transport-options-list">
                  <h4 style={{ fontSize: "12px", fontWeight: "600", textTransform: "uppercase", color: "var(--color-text-secondary)", marginBottom: "12px" }}>Alternative Options</h4>
                  {result.options.map((option, idx) => (
                    <div key={idx} className="transport-option-card animate-fade">
                      {option}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
