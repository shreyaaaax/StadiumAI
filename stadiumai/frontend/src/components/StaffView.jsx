import React, { useState, useEffect } from "react";
import { 
  staffQuery, 
  staffIncidentReport, 
  getSustainability, 
  getSustainabilityFanScore, 
  postSustainabilityInsight 
} from "../api";
import { getTranslationHelper } from "../translations";

export default function StaffView({ venueId, language, demoScenario }) {
  const t = getTranslationHelper(language);
  const errMsg = t("staff.errors");
  const [subTab, setSubTab] = useState("copilot"); // copilot | incident | sustainability

  // Subtab 1: Copilot
  const [role, setRole] = useState("volunteer");
  const [copilotQuestion, setCopilotQuestion] = useState("");
  const [copilotAnswer, setCopilotAnswer] = useState("");
  const [loadingCopilot, setLoadingCopilot] = useState(false);
  const [errorCopilot, setErrorCopilot] = useState(false);

  // Subtab 2: Incident Report
  const [incidentDesc, setIncidentDesc] = useState("");
  const [incidentLoc, setIncidentLoc] = useState("");
  const [incidentSev, setIncidentSev] = useState("3");
  const [draftedReport, setDraftedReport] = useState("");
  const [loadingIncident, setLoadingIncident] = useState(false);
  const [copied, setCopied] = useState(false);
  const [errorIncident, setErrorIncident] = useState(false);

  // Subtab 3: Sustainability
  const [ecoMetrics, setEcoMetrics] = useState(null);
  const [fanScoreMsg, setFanScoreMsg] = useState("");
  const [sustainabilityQuestion, setSustainabilityQuestion] = useState("");
  const [sustainabilityAnswer, setSustainabilityAnswer] = useState("");
  const [loadingEco, setLoadingEco] = useState(false);
  const [loadingEcoQuery, setLoadingEcoQuery] = useState(false);
  const [errorEco, setErrorEco] = useState(false);

  // Monitor demoScenario triggers
  useEffect(() => {
    if (demoScenario && demoScenario.expected_feature === "staff") {
      setSubTab("incident");
      setIncidentDesc(demoScenario.input_text);
      setIncidentLoc("Gate C");
      setIncidentSev("4");
      const triggerIncidentForDemo = async () => {
        setLoadingIncident(true);
        setDraftedReport("");
        setErrorIncident(false);
        try {
          const res = await staffIncidentReport(demoScenario.input_text, "Gate C", "4");
          setDraftedReport(res.draft_report);
        } catch (err) {
          setErrorIncident(true);
        } finally {
          setLoadingIncident(false);
        }
      };
      triggerIncidentForDemo();
    }
  }, [demoScenario]);

  // Fetch Sustainability Tab metrics when subTab switches to "sustainability"
  useEffect(() => {
    if (subTab === "sustainability") {
      fetchSustainabilityMetrics();
    }
  }, [subTab, venueId]);

  const fetchSustainabilityMetrics = async () => {
    setLoadingEco(true);
    setErrorEco(false);
    try {
      const [resMetrics, resFan] = await Promise.all([
        getSustainability(venueId, "during"),
        getSustainabilityFanScore(venueId).catch(() => ({ message: "Eco portal online." }))
      ]);
      setEcoMetrics(resMetrics);
      setFanScoreMsg(resFan.message || resFan.eco_message || "");
    } catch (err) {
      setErrorEco(true);
    } finally {
      setLoadingEco(false);
    }
  };

  const handleCopilotAsk = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!copilotQuestion.trim()) return;

    setLoadingCopilot(true);
    setCopilotAnswer("");
    setErrorCopilot(false);
    try {
      const res = await staffQuery(copilotQuestion, role, venueId);
      setCopilotAnswer(res.answer);
    } catch (err) {
      setErrorCopilot(true);
    } finally {
      setLoadingCopilot(false);
    }
  };

  const handleIncidentSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!incidentDesc.trim() || !incidentLoc.trim()) return;

    setLoadingIncident(true);
    setDraftedReport("");
    setCopied(false);
    setErrorIncident(false);
    try {
      const res = await staffIncidentReport(incidentDesc, incidentLoc, incidentSev);
      setDraftedReport(res.draft_report);
    } catch (err) {
      setErrorIncident(true);
    } finally {
      setLoadingIncident(false);
    }
  };

  const handleSustainabilityAsk = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (!sustainabilityQuestion.trim()) return;

    setLoadingEcoQuery(true);
    setSustainabilityAnswer("");
    try {
      const res = await postSustainabilityInsight(venueId, sustainabilityQuestion, "during");
      setSustainabilityAnswer(res.insight);
    } catch (err) {
      setSustainabilityAnswer(`Query failed: ${err.message}`);
    } finally {
      setLoadingEcoQuery(false);
    }
  };

  const handleCopyReport = () => {
    if (!draftedReport) return;
    navigator.clipboard.writeText(draftedReport);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getScoreClassStr = (score) => {
    if (score >= 60) return "green";
    if (score >= 40) return "amber";
    return "red";
  };

  return (
    <div className="view-container" style={{ maxWidth: "1200px" }}>
      <h3 className="section-title">👤 Staff Operations Center</h3>

      {/* Horizontal Sub-tabs Tab Bar */}
      <div className="staff-tab-bar">
        <button
          className={`staff-tab-btn ${subTab === "copilot" ? "active" : ""}`}
          onClick={() => setSubTab("copilot")}
        >
          {t("staff.copilotTab")}
        </button>
        <button
          className={`staff-tab-btn ${subTab === "incident" ? "active" : ""}`}
          onClick={() => setSubTab("incident")}
        >
          {t("staff.incidentTab")}
        </button>
        <button
          className={`staff-tab-btn ${subTab === "sustainability" ? "active" : ""}`}
          onClick={() => setSubTab("sustainability")}
        >
          {t("staff.sustainabilityTab")}
        </button>
      </div>

      {/* TAB 1: copilot */}
      {subTab === "copilot" && (
        <div className="staff-copilot-grid animate-fade">
          
          {/* Left Panel: Form */}
          <div className="card-panel">
            <h4 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>{t("staff.copilotTitle")}</h4>
            <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", marginBottom: "20px" }}>{t("staff.copilotSubtitle")}</p>
            
            <form onSubmit={handleCopilotAsk}>
              <div className="form-group">
                <label className="field-label">{t("staff.roleCategory")}</label>
                <select 
                  className="styled-select"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="volunteer">{t("staff.volunteerRole")}</option>
                  <option value="security">{t("staff.securityPatrol")}</option>
                  <option value="medic">{t("staff.medicStaff")}</option>
                  <option value="supervisor">{t("staff.supervisorRole")}</option>
                </select>
              </div>

              <div className="form-group" style={{ marginTop: "12px" }}>
                <label className="field-label">{t("staff.question")}</label>
                <textarea
                  className="styled-input styled-textarea"
                  placeholder={t("staff.copilotPlaceholder")}
                  value={copilotQuestion}
                  onChange={(e) => setCopilotQuestion(e.target.value)}
                  rows={3}
                  required
                />
              </div>

              <button 
                type="submit" 
                className="action-btn" 
                style={{ width: "100%", marginTop: "12px" }}
                disabled={loadingCopilot}
              >
                {loadingCopilot ? t("staff.consultingOps") : t("staff.askCopilot")}
              </button>
            </form>

            {errorCopilot && (
              <div className="error-box animate-fade" style={{ display: "flex", flexDirection: "column", gap: "8px", background: "rgba(239, 68, 68, 0.08)", borderColor: "var(--color-error)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-error)", marginTop: "16px" }}>
                <p style={{ margin: 0, color: "var(--color-error)", fontSize: "13px" }}>⚠️ {errMsg}</p>
                <button 
                  type="button" 
                  className="action-btn" 
                  style={{ padding: "6px 12px", fontSize: "12px", alignSelf: "flex-start", backgroundColor: "var(--color-error)", color: "#fff", minHeight: "36px" }} 
                  onClick={handleCopilotAsk}
                >
                  {t("staff.retry")}
                </button>
              </div>
            )}
          </div>

          {/* Right Panel: Guidance Output Card */}
          <div className="staff-copilot-answer-card">
            <h4 style={{ fontSize: "14px", fontWeight: "700", color: "var(--color-primary-pink)", marginBottom: "12px" }}>🤖 {t("staff.guidanceHeader")}</h4>
            
            {loadingCopilot && (
              <span className="spinner animate-pulse">⏳ Querying event operations instructions database...</span>
            )}
            
            {!copilotAnswer && !loadingCopilot && (
              <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", margin: 0 }}>
                {t("staff.askInstructions")}
              </p>
            )}

            {copilotAnswer && !loadingCopilot && (
              <p style={{ fontSize: "14px", lineHeight: "1.6", color: "var(--color-text-primary)", whiteSpace: "pre-wrap", margin: 0 }}>
                {copilotAnswer}
              </p>
            )}
          </div>

        </div>
      )}

      {/* TAB 2: Incident Logger */}
      {subTab === "incident" && (
        <div className="staff-incident-grid animate-fade">
          
          {/* Left Column: Form */}
          <div className="card-panel">
            <h4 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "8px" }}>📝 {t("staff.incidentTitle")}</h4>
            <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", marginBottom: "20px" }}>{t("staff.incidentSubtitle")}</p>
            
            <form onSubmit={handleIncidentSubmit} className="incident-form">
              <div className="form-group">
                <label className="field-label">{t("staff.incidentDescLabel")}</label>
                <textarea
                  placeholder={t("staff.incidentPlaceholder")}
                  value={incidentDesc}
                  onChange={(e) => setIncidentDesc(e.target.value)}
                  style={{ width: "100%", height: "140px", padding: "12px 16px", border: "2px solid var(--color-border)", borderRadius: "var(--radius-sm)" }}
                  required
                />
              </div>

              <div className="form-group" style={{ margin: "16px 0" }}>
                <label className="field-label">{t("staff.locationLabel")}</label>
                <input
                  type="text"
                  className="styled-input"
                  placeholder={t("staff.locationPlaceholder")}
                  value={incidentLoc}
                  onChange={(e) => setIncidentLoc(e.target.value)}
                  style={{ width: "100%" }}
                  required
                />
              </div>

              <div className="form-group" style={{ margin: "16px 0" }}>
                <label className="field-label" style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{t("staff.severityLevel")}</span>
                  <span style={{ color: "var(--color-warning)", fontWeight: 800 }}>{incidentSev}/5</span>
                </label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  className="range-slider-style"
                  value={incidentSev}
                  onChange={(e) => setIncidentSev(e.target.value)}
                  style={{ width: "100%" }}
                />
              </div>

              <button 
                type="submit" 
                className="btn-warning"
                disabled={loadingIncident}
                style={{ width: "100%", color: "white", padding: "12px", borderRadius: "var(--radius-sm)", fontSize: "14px", fontWeight: "600", cursor: "pointer" }}
              >
                {loadingIncident ? t("staff.formulatingDraft") : t("staff.autoDraftReport")}
              </button>
            </form>

            {errorIncident && (
              <div className="error-box animate-fade" style={{ display: "flex", flexDirection: "column", gap: "8px", background: "rgba(239, 68, 68, 0.08)", borderColor: "var(--color-error)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-error)", marginTop: "16px" }}>
                <p style={{ margin: 0, color: "var(--color-error)", fontSize: "13px" }}>⚠️ {t("staff.incidentFailed")}</p>
                <button 
                  type="button" 
                  className="action-btn" 
                  style={{ padding: "6px 12px", fontSize: "12px", alignSelf: "flex-start", backgroundColor: "var(--color-error)", color: "#fff", minHeight: "36px" }} 
                  onClick={handleIncidentSubmit}
                >
                  {t("staff.retry")}
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Draft output report */}
          <div className="staff-report-output-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <h5 style={{ fontSize: "13px", color: "var(--color-warning)", margin: 0, fontWeight: "700" }}>📋 Draft Report Output</h5>
              {draftedReport && (
                <button type="button" className="copy-btn" onClick={handleCopyReport}>
                  {copied ? t("staff.copied") : t("staff.copyClipboard")}
                </button>
              )}
            </div>

            {loadingIncident && (
              <div className="animate-pulse" style={{ color: "var(--color-text-secondary)" }}>
                ⏳ Formulating incident log description drafts...
              </div>
            )}

            {!draftedReport && !loadingIncident && (
              <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", margin: 0, fontFamily: "sans-serif" }}>
                {t("staff.incidentInstructions")}
              </p>
            )}

            {draftedReport && !loadingIncident && (
              <pre style={{ margin: 0, fontFamily: "monospace", fontSize: "12px", whiteSpace: "pre-wrap" }}>
                {draftedReport}
              </pre>
            )}
          </div>

        </div>
      )}

      {/* TAB 3: Sustainability */}
      {subTab === "sustainability" && (
        <div className="animate-fade">
          {errorEco && (
            <div className="error-box animate-fade" style={{ display: "flex", flexDirection: "column", gap: "8px", background: "rgba(239, 68, 68, 0.08)", borderColor: "var(--color-error)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-error)", marginBottom: "20px" }}>
              <p style={{ margin: 0, color: "var(--color-error)", fontSize: "13px" }}>⚠️ {t("staff.ecoPortalFailed")}</p>
              <button 
                type="button" 
                className="action-btn" 
                style={{ padding: "6px 12px", fontSize: "12px", alignSelf: "flex-start", backgroundColor: "var(--color-error)", color: "#fff", minHeight: "36px" }} 
                onClick={fetchSustainabilityMetrics}
              >
                {t("staff.retry")}
              </button>
            </div>
          )}

          {loadingEco && (
            <div className="card-panel text-center">
              <span className="spinner animate-pulse">⚽ {t("staff.queryingEcoDb")}</span>
            </div>
          )}

          {!ecoMetrics && !loadingEco && !errorEco && (
            <div className="card-panel text-center" style={{ padding: "24px", opacity: 0.85 }}>
              <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", margin: 0 }}>{t("staff.ecoPortalEmpty")}</p>
            </div>
          )}

          {ecoMetrics && !loadingEco && (
            <>
              {/* Sustainability Metric Card Grid - 4 Columns */}
              <div className="staff-sustain-grid">
                <div className="sustain-metric-card">
                  <div className="sustain-metric-value">
                    {(ecoMetrics.metrics?.energy_kwh ?? ecoMetrics.energy_kwh ?? 0).toLocaleString()}
                  </div>
                  <div className="sustain-metric-label">{t("staff.energyConsumedLabel")} (kWh)</div>
                </div>

                <div className="sustain-metric-card">
                  <div className="sustain-metric-value">
                    {(ecoMetrics.metrics?.waste_kg ?? ecoMetrics.waste_kg ?? 0).toLocaleString()}
                  </div>
                  <div className="sustain-metric-label">{t("staff.solidWasteLabel")} (kg)</div>
                </div>

                <div className="sustain-metric-card">
                  <div className="sustain-metric-value">
                    {ecoMetrics.metrics?.recycled_pct ?? ecoMetrics.recycled_pct ?? 0}%
                  </div>
                  <div className="sustain-metric-label">{t("staff.recyclingRatioLabel")}</div>
                </div>

                <div className="sustain-metric-card">
                  <div className="sustain-metric-value">
                    {(ecoMetrics.metrics?.water_liters ?? ecoMetrics.water_liters ?? 0).toLocaleString()}
                  </div>
                  <div className="sustain-metric-label">{t("staff.waterUsageLabel")} (L)</div>
                </div>
              </div>

              {/* Eco score circle 80x80px below metrics */}
              <div className="eco-score-circle-outer">
                <div className={`eco-score-circle ${getScoreClassStr(ecoMetrics.eco_score)}`}>
                  {ecoMetrics.eco_score}
                </div>
                <div className="eco-score-caption">
                  {t("staff.pointsLabel")}
                </div>
              </div>

              {/* AI analysis box at the bottom */}
              <div className="sustain-ai-analysis-box">
                <h4 style={{ fontSize: "14px", fontWeight: "600", marginBottom: "16px" }}>🌱 {t("staff.askEcoAnalystTitle")}</h4>
                
                <form onSubmit={handleSustainabilityAsk} style={{ display: "flex", gap: "12px", marginBottom: "16px" }}>
                  <input
                    type="text"
                    className="styled-input"
                    placeholder={t("staff.ecoPlaceholder")}
                    value={sustainabilityQuestion}
                    onChange={(e) => setSustainabilityQuestion(e.target.value)}
                    required
                    style={{ flex: 1 }}
                  />
                  <button 
                    type="submit" 
                    className="action-btn"
                    style={{ minWidth: "120px", padding: "12px" }}
                    disabled={loadingEcoQuery}
                  >
                    {loadingEcoQuery ? t("staff.analyzing") : t("staff.askAIAnalyst")}
                  </button>
                </form>

                {loadingEcoQuery && (
                  <div className="animate-pulse" style={{ fontSize: "13px", color: "var(--color-text-secondary)" }}>
                    ⏳ Querying sustainability model recommendations...
                  </div>
                )}

                {sustainabilityAnswer && !loadingEcoQuery && (
                  <div className="response-box animate-fade" style={{ background: "var(--color-light)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-border)", marginTop: "16px" }}>
                    <h5 style={{ fontSize: "13px", color: "var(--color-primary-pink)", marginBottom: "8px", fontWeight: "700" }}>📝 {t("staff.insightsHeader")}</h5>
                    <p style={{ fontSize: "13.5px", lineHeight: "1.6", color: "var(--color-text-primary)", whiteSpace: "pre-line", margin: 0 }}>
                      {sustainabilityAnswer}
                    </p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

    </div>
  );
}
