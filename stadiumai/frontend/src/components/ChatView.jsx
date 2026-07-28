import React, { useState, useEffect, useRef } from "react";
import { sendChat, getAccessibilityAssist } from "../api";
import { getTranslationHelper } from "../translations";

const VENUE_METRICS = {
  metlife: { name: "MetLife Stadium", capacity: "82,500", city: "East Rutherford, NJ" },
  sofi: { name: "SoFi Stadium", capacity: "70,240", city: "Inglewood, CA" },
  azteca: { name: "Estadio Azteca", capacity: "87,523", city: "Mexico City, MX" }
};

export default function ChatView({ venueId, language, demoScenario }) {
  const t = getTranslationHelper(language);
  const errMsg = t("chat.errors");
  const emptyMsg = t("chat.empty");

  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState("");
  const [loading, setLoading] = useState(false);
  const [assistMode, setAssistMode] = useState(false);
  const [needCategory, setNeedCategory] = useState("mobility");
  const [features, setFeatures] = useState([]);
  const [errorState, setErrorState] = useState(false);
  const [lastQuery, setLastQuery] = useState("");

  const chatEndRef = useRef(null);

  // Monitor language switches to re-set the greeting message
  useEffect(() => {
    const greetingMsg = t("chat.greeting");
    setMessages([
      { sender: "bot", text: greetingMsg, timestamp: getCurrentTimeStr() }
    ]);
    setFeatures([]);
    setErrorState(false);
  }, [language]);

  // Monitor demoScenario triggers
  useEffect(() => {
    if (demoScenario && demoScenario.expected_feature === "chat") {
      queryApi(demoScenario.input_text);
    }
  }, [demoScenario]);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, errorState]);

  const getCurrentTimeStr = () => {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const queryApi = async (queryText) => {
    setLoading(true);
    setErrorState(false);
    setLastQuery(queryText);
    setMessages((prev) => [...prev, { sender: "user", text: queryText, timestamp: getCurrentTimeStr() }]);

    try {
      if (assistMode) {
        const res = await getAccessibilityAssist(queryText, venueId, language, needCategory);
        setMessages((prev) => [...prev, { sender: "bot", text: res.response, timestamp: getCurrentTimeStr() }]);
        if (res.accessible_features_nearby && res.accessible_features_nearby.length > 0) {
          setFeatures(res.accessible_features_nearby);
        }
      } else {
        const res = await sendChat(queryText, venueId, language);
        setMessages((prev) => [...prev, { sender: "bot", text: res.reply, timestamp: getCurrentTimeStr() }]);
        setFeatures([]);
      }
    } catch (err) {
      setErrorState(true);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    if (lastQuery) {
      queryApi(lastQuery);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputVal.trim() || loading) return;
    const text = inputVal;
    setInputVal("");
    queryApi(text);
  };

  const handleChipClick = (chipLabel) => {
    if (loading) return;
    queryApi(chipLabel);
  };

  const venueInfo = VENUE_METRICS[venueId] || { name: venueId, capacity: "N/A", city: "N/A" };

  return (
    <div className="view-container">
      <div className="chat-grid">
        
        {/* Left Column - Chat Area */}
        <div className="chat-main-area">
          
          {/* Accessibility Assist toggle at the top */}
          <div className="chat-accessibility-settings">
            <label className="toggle-label font-display" style={{ fontSize: "14px", fontWeight: "600" }}>
              <input 
                type="checkbox" 
                checked={assistMode}
                onChange={(e) => setAssistMode(e.target.checked)}
                style={{ width: "16px", height: "16px", accentColor: "var(--color-primary-pink)" }}
              />
              ♿ {t("chat.enableAssist")}
            </label>
            
            {assistMode && (
              <select 
                className="styled-select animate-fade"
                style={{ width: "auto", padding: "6px 12px", minHeight: "36px" }}
                value={needCategory} 
                onChange={(e) => setNeedCategory(e.target.value)}
              >
                <option value="mobility">{t("chat.mobilityHelp")}</option>
                <option value="visual">{t("chat.visualAssistance")}</option>
                <option value="hearing">{t("chat.hearingAssist")}</option>
                <option value="general">{t("chat.generalSupport")}</option>
              </select>
            )}
          </div>

          {/* Near accessible features toast */}
          {features.length > 0 && (
            <div className="features-toast animate-fade">
              <h4 style={{ fontSize: "13px", color: "var(--color-primary-pink)", marginBottom: "4px", fontWeight: "700" }}>♿ {t("chat.resolvedFeatures")}</h4>
              <ul style={{ paddingLeft: "16px", margin: 0, fontSize: "12px", color: "var(--color-text-secondary)" }}>
                {features.map((f, idx) => (
                  <li key={idx} style={{ marginBottom: "2px" }}>{f}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Messages block */}
          <div className="chat-messages-container">
            {messages.length === 0 && (
              <div className="card-panel text-center animate-fade" style={{ margin: "auto", opacity: 0.85 }}>
                <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", margin: 0 }}>{emptyMsg}</p>
              </div>
            )}

            {messages.map((m, idx) => (
              <div key={idx} className={`chat-bubble-wrapper ${m.sender === "bot" ? "bot" : "user"}`}>
                <div className="message-bubble">
                  {m.text}
                </div>
                {/* AI / Bot messages have a timestamp */}
                {m.sender === "bot" && (
                  <span className="message-timestamp">{m.timestamp}</span>
                )}
              </div>
            ))}

            {loading && (
              <div className="chat-bubble-wrapper bot">
                <div className="message-bubble typing-indicator">
                  <span style={{ marginRight: "4px" }}>{t("chat.typing")}</span>
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                  <div className="typing-dot" />
                </div>
              </div>
            )}

            {errorState && (
              <div className="error-box animate-fade" style={{ display: "flex", flexDirection: "column", gap: "8px", background: "rgba(239, 68, 68, 0.08)", borderColor: "var(--color-error)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-error)", margin: "8px 0" }}>
                <p style={{ margin: 0, fontSize: "13px", color: "var(--color-error)" }}>⚠️ {errMsg}</p>
                <button 
                  type="button" 
                  className="action-btn" 
                  style={{ padding: "6px 12px", fontSize: "12px", alignSelf: "flex-start", backgroundColor: "var(--color-error)", color: "#fff", minHeight: "36px" }} 
                  onClick={handleRetry}
                >
                  {t("chat.retry")}
                </button>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Quick replies chips row */}
          <div className="quick-chips-row" style={{ marginTop: "12px" }}>
            {t("chat.chips").map((chip, idx) => (
              <button
                key={idx}
                type="button"
                className="chip-btn"
                onClick={() => handleChipClick(chip.label)}
                disabled={loading}
              >
                {chip.label}
              </button>
            ))}
          </div>

          {/* Sticky input area */}
          <form onSubmit={handleSubmit} className="chat-input-area">
            <input
              type="text"
              className="chat-input-field"
              placeholder={t("chat.placeholder")}
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="chat-send-btn" disabled={loading}>
              {t("chat.send")}
            </button>
          </form>

        </div>

        {/* Right Column - Sidebar Info Panel */}
        <div className="chat-info-sidebar">
          <h3 className="chat-info-title">Quick Info</h3>
          
          <div className="info-venue-box">
            <div style={{ fontSize: "13px", fontWeight: "700", marginBottom: "4px" }}>{venueInfo.name}</div>
            <div style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>Capacity: {venueInfo.capacity}</div>
            <div style={{ fontSize: "12px", color: "var(--color-text-secondary)" }}>City: {venueInfo.city}</div>
          </div>

          <div className="info-lang-badge">
            Language: {language.toUpperCase()}
          </div>

          <h4 style={{ fontSize: "13px", fontWeight: "600", marginTop: "16px", marginBottom: "8px" }}>Suggested Questions</h4>
          <ul style={{ padding: 0, margin: 0 }}>
            <li className="suggestion-question-item" onClick={() => handleChipClick("Where is Gate A?")}>
              Where is Gate A?
            </li>
            <li className="suggestion-question-item" onClick={() => handleChipClick("Food options?")}>
              Food options?
            </li>
            <li className="suggestion-question-item" onClick={() => handleChipClick("How do I exit?")}>
              How do I exit?
            </li>
          </ul>
        </div>

      </div>
    </div>
  );
}
