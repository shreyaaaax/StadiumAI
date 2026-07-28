# ⚽ StadiumAI — FIFA World Cup 2026

GenAI-powered platform for stadium operations, fan navigation, crowd intelligence, transport advisory, and real-time decision support during the FIFA World Cup 2026.

## 🎯 Features

- **Multilingual Chat Assistant** (EN, ES, FR, ZH) — Answer fan questions about gates, food, restrooms, transport
- **Smart Navigation** — Natural language routing with accessibility support (wheelchair-friendly routes)
- **Live Crowd Intelligence** — Real-time crowd density heatmaps with AI predictions and re-routing recommendations
- **Transport Advisor** — Personalized departure time recommendations and transit options
- **Staff Copilot** — Volunteer assistance, incident reporting, escalation guidance
- **Sustainability Tracker** — Live energy, waste, and carbon monitoring with actionable insights

## 🛠 Tech Stack

**Backend:**
- FastAPI (Python) — REST API server
- Gemini 2.5 Flash (via Google AI Studio) — LLM for all AI features
- Uvicorn — ASGI server

**Frontend:**
- React (JavaScript) — Web UI
- CSS3 — Dark neon design (pink, purple, black)

**Data:**
- JSON venue knowledge base (RAG)
- In-memory caching for fast retrieval

**Infrastructure:**
- Desktop-first responsive design
- No database needed (hackathon scope)

## 🚀 Setup (5 minutes)

### Prerequisites
- Python 3.9+
- Node.js 14+
- Free Gemini API key (https://aistudio.google.com)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY
uvicorn main:app --reload
```

Backend runs on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs on `http://localhost:3000`

### Verify It Works

1. Open http://localhost:3000
2. Try asking the chatbot a question: "Where is Gate A?"
3. Switch languages (EN / ES / FR / 中文)
4. Test Navigation, Crowd, Transport, and Staff tabs

## 📖 API Endpoints

**Fan-facing:**
- `POST /chat` — Multilingual chatbot
- `POST /navigation` — Route planning with accessibility
- `GET /crowd/{venue_id}?phase=during_match` — Crowd density snapshot
- `POST /transport/recommend` — Transport advisor

**Staff-facing:**
- `POST /staff/query` — Volunteer copilot
- `POST /staff/incident_report` — Auto-draft incident reports
- `GET /sustainability/{venue_id}` — Sustainability metrics

**Admin:**
- `GET /health` — Health check
- `GET /venues` — List all loaded venues

## 🎨 Design

- **Colors:** Pink (#EC4899), Purple (#7C3AED), Black (#0F172A)
- **Layout:** Desktop-first with fixed sidebar navigation
- **Accessibility:** WCAG-compliant, built-in accessible route option
- **Responsiveness:** Optimized for 1024px+ screens

## 📝 Project Structure

```
stadiumai/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── routes/
│   │   ├── chat.py
│   │   ├── navigation.py
│   │   ├── crowd.py
│   │   ├── transport.py
│   │   └── staff.py
│   └── requirements.txt
├── ai_service/
│   ├── gemini_client.py        # Gemini API wrapper
│   ├── rag_loader.py           # Venue knowledge base
│   ├── detect_language.py      # Auto-detect language
│   └── response_formatter.py   # Clean output formatting
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── index.css           # Global dark neon styles
│   │   └── components/
│   │       ├── ChatView.js
│   │       ├── NavView.js
│   │       ├── CrowdView.js
│   │       ├── TransportView.js
│   │       └── StaffView.js
│   └── package.json
├── data/
│   ├── venue_metlife.json      # MetLife Stadium
│   ├── venue_sofi.json         # SoFi Stadium
│   └── venue_azteca.json       # Estadio Azteca
└── README.md
```

## 🔑 API Key Setup

Get a free Gemini API key:
1. Go to https://aistudio.google.com
2. Click "Get API Key"
3. Create a new key (no credit card required)
4. Copy the key into `.env` as `GEMINI_API_KEY=your_key_here`

**Free limits:** 10 requests per minute, 250 requests per day — sufficient for demo and testing.

## 🎓 Use Cases

**For Fans:**
- "How do I get to Section 112 from Gate A with wheelchair access?"
- "Where can I find vegetarian food?"
- "What's the best way to get back to downtown after the match?"

**For Staff:**
- "What's the evacuation procedure for a medical emergency?"
- "The North Concourse is at 95% capacity — what should I do?"
- "How much energy are we using right now?"

**For Organizers:**
- Real-time dashboard showing venue operations KPIs
- AI-powered crowd predictions 15 minutes ahead
- Automated incident reporting and escalation

## 🧪 Testing

All endpoints return clean JSON (no markdown):

```bash
# Chat in English
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Where is Gate A?","venue_id":"metlife","language":"en"}'

# Get crowd density
curl http://localhost:8000/crowd/metlife?phase=during_match

# Navigation
curl -X POST http://localhost:8000/navigation \
  -H "Content-Type: application/json" \
  -d '{"from_location":"Gate A","to_location":"Section 112","venue_id":"metlife","language":"en"}'
```

## 🚀 Deployment

This project is built for hackathons and demos. To deploy:

**Backend (Heroku, Railway, Render):**
```bash
git push heroku main  # If using Heroku
# Or upload to your preferred cloud platform
```

**Frontend (Vercel, Netlify):**
```bash
cd frontend && npm run build
# Deploy the `build/` folder to Vercel or Netlify
```

## 📄 License

MIT License — feel free to use and modify for your own FIFA stadium!

## 🤝 Contributing

Have ideas? Found a bug? Feel free to open an issue or submit a pull request.

## 👨‍💻 Author

Built for HackSkills Prompt Wars Challenge 4 — FIFA World Cup 2026 Operations

---

**Questions?** Check the API docs by visiting http://localhost:8000/docs (Swagger UI)