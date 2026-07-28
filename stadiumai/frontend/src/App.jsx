import React, { useState, useEffect } from "react";
import ChatView from "./components/ChatView";
import NavView from "./components/NavView";
import CrowdView from "./components/CrowdView";
import TransportView from "./components/TransportView";
import StaffView from "./components/StaffView";
import { subscribeToRateLimit } from "./api";

const VENUES = [
  { id: "metlife", name: "MetLife Stadium (NY)" },
  { id: "sofi", name: "SoFi Stadium (LA)" },
  { id: "azteca", name: "Estadio Azteca (MX)" }
];

const LANGUAGES = [
  { code: "en", label: "EN" },
  { code: "es", label: "ES" },
  { code: "fr", label: "FR" },
  { code: "zh", label: "ZH" }
];

export default function App() {
  const [language, setLanguage] = useState("en");
  const [venueId, setVenueId] = useState("metlife");
  const [activeTab, setActiveTab] = useState("chat");
  const [isRateLimited, setIsRateLimited] = useState(false);

  // Demo Mode state
  const [demoScenario, setDemoScenario] = useState(null);
  const [isRunningDemo, setIsRunningDemo] = useState(false);
  const [currentScenarioNum, setCurrentScenarioNum] = useState(null);

  useEffect(() => {
    const unsub = subscribeToRateLimit((val) => {
      setIsRateLimited(val);
    });
    return unsub;
  }, []);

  const runDemo = async () => {
    if (isRunningDemo) return;
    setIsRunningDemo(true);
    
    const scenarios = [
      {
        scenario_code: 1,
        title: "es-seat-search",
        language: "es",
        venue_id: "metlife",
        input_text: "¿Dónde está la sección 112 para mi asiento?",
        expected_feature: "chat"
      },
      {
        scenario_code: 2,
        title: "fr-accessible-restroom",
        language: "fr",
        venue_id: "metlife",
        input_text: "Où se trouve la toilette accessible la plus proche depuis Gate A?",
        expected_feature: "navigation"
      },
      {
        scenario_code: 3,
        title: "zh-transport-hotel",
        language: "zh",
        venue_id: "metlife",
        input_text: "比赛结束之后，有什么方式可以坐公交或者轻轨回市中心？",
        expected_feature: "transport"
      },
      {
        scenario_code: 4,
        title: "en-volunteer-incident",
        language: "en",
        venue_id: "metlife",
        input_text: "Medical incident: A fan has fainted near Gate C and requires immediate assistance.",
        expected_feature: "staff"
      },
      {
        scenario_code: 5,
        title: "en-manager-crowd",
        language: "en",
        venue_id: "metlife",
        input_text: "Which areas to avoid right now due to peak bottleneck prediction?",
        expected_feature: "crowd"
      }
    ];

    for (let idx = 0; idx < scenarios.length; idx++) {
      const scenario = scenarios[idx];
      setCurrentScenarioNum(scenario.scenario_code);
      setLanguage(scenario.language);
      setVenueId(scenario.venue_id);
      setActiveTab(scenario.expected_feature);
      setDemoScenario(scenario);
      await new Promise((resolve) => setTimeout(resolve, 4500));
    }

    setIsRunningDemo(false);
    setDemoScenario(null);
    setCurrentScenarioNum(null);
  };

  const showDemoButton = new URLSearchParams(window.location.search).get("demo") === "1" || window.location.href.includes("demo=1");

  const renderActiveView = () => {
    switch (activeTab) {
      case "chat":
        return <ChatView venueId={venueId} language={language} demoScenario={demoScenario} />;
      case "navigate":
      case "navigation":
        return <NavView venueId={venueId} language={language} demoScenario={demoScenario} />;
      case "crowd":
        return <CrowdView venueId={venueId} language={language} demoScenario={demoScenario} />;
      case "transport":
        return <TransportView venueId={venueId} language={language} demoScenario={demoScenario} />;
      case "staff":
        return <StaffView venueId={venueId} language={language} demoScenario={demoScenario} />;
      default:
        return <ChatView venueId={venueId} language={language} demoScenario={demoScenario} />;
    }
  };

  const handleTabClick = (tabKey) => {
    setActiveTab(tabKey);
  };

  return (
    <div className="desktop-app-layout">
      {/* Top Header */}
      <header className="top-header">
        <div className="header-left">
          <span className="logo-emoji">⚽</span>
          <span className="logo-title">StadiumAI</span>
        </div>
        <div className="header-center">
          <select
            className="venue-select"
            value={venueId}
            onChange={(e) => setVenueId(e.target.value)}
          >
            {VENUES.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
        </div>
        <div className="header-right">
          <div className="lang-switcher">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                className={`lang-btn ${language === lang.code ? "lang-btn-active" : ""}`}
                onClick={() => setLanguage(lang.code)}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>
      </header>

      {/* Left Sidebar */}
      <aside className="sidebar">
        <nav className="sidebar-nav">
          <button 
            className={`tab-btn-side ${activeTab === "chat" ? "active" : ""}`}
            onClick={() => handleTabClick("chat")}
          >
            💬 Chat
          </button>
          <button 
            className={`tab-btn-side ${activeTab === "navigate" || activeTab === "navigation" ? "active" : ""}`}
            onClick={() => handleTabClick("navigate")}
          >
            🗺️ Navigate
          </button>
          <button 
            className={`tab-btn-side ${activeTab === "crowd" ? "active" : ""}`}
            onClick={() => handleTabClick("crowd")}
          >
            👥 Crowd
          </button>
          <button 
            className={`tab-btn-side ${activeTab === "transport" ? "active" : ""}`}
            onClick={() => handleTabClick("transport")}
          >
            🚌 Transport
          </button>
          <button 
            className={`tab-btn-side ${activeTab === "staff" ? "active" : ""}`}
            onClick={() => handleTabClick("staff")}
          >
            👤 Staff
          </button>
        </nav>
        <div className="sidebar-footer">
          <a href="#support" className="support-link">ⓘ Support</a>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="content-area">
        {showDemoButton && (
          <div className="demo-banner-row font-display">
            <button 
              type="button"
              className="action-btn" 
              onClick={runDemo} 
              disabled={isRunningDemo}
              style={{ padding: "6px 12px", fontSize: "12px", backgroundColor: isRunningDemo ? "#555" : "var(--color-primary-pink)", border: "none" }}
            >
              {isRunningDemo ? `⏳ Playing: Scenario ${currentScenarioNum}/5...` : "🚀 Launch Demo Mode"}
            </button>
            {isRunningDemo && (
              <span style={{ fontSize: "12px", color: "var(--color-primary-pink)", fontWeight: 700 }} className="animate-pulse">
                {demoScenario?.title || ""}
              </span>
            )}
          </div>
        )}
        {isRateLimited && (
          <div className="rate-limit-banner">
            ⚠️ High demand right now — some features may be slow. Core navigation still works.
          </div>
        )}
        {renderActiveView()}
      </main>
    </div>
  );
}
