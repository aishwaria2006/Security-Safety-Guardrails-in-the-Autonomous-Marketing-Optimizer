# 🚀 Marketing AI Hub — Twin Innovators

> An AI-powered, multi-module marketing intelligence platform that unifies analytics, CRM intelligence, campaign automation, strategic AI reasoning, and creative generation into one practical workspace.

---

## 📌 What This Project Is

Marketing teams today are overwhelmed. Customer data lives in five different tools. Lead prioritization is manual. Campaign creation takes days. Competitor awareness is delayed. Design and analytics teams don't talk to each other.

**Marketing AI Hub** solves this by bringing everything together — sentiment tracking, lead scoring, personalized content, campaign management, strategic AI decisions, operations monitoring, and poster generation — all under one dashboard, powered by AI at every layer.

---

## 🏗️ Architecture Overview

This is **not** a single monolithic app. It's a **federated hub-and-modules** platform:

```
┌─────────────────────────────────────────────────────────────┐
│                      login.html                             │
│                    (Entry Point)                            │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   dashboard.html                            │
│              (Central Launcher Hub)                         │
│                                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │ Module 1 │  │ Module 2 │  │ Module 3 │  │ Module 4 │  │
│   │ :5000    │  │ :5002    │  │ :5004    │  │ :5005    │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │ Module 5 │  │ Module 6 │  │ Module 7 │  │ Module 8 │  │
│   │ :5006    │  │ :5010    │  │ :9000    │  │ Chatbot  │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

Each module runs independently on its own port. The dashboard links them via browser navigation — no shared API gateway, no single point of failure.

---

## 📦 Modules — What Each Does & What It Uses

---

### 1️⃣ Social Media Sentiment Tracker
| | |
|---|---|
| **File** | `last.py` |
| **Port** | `5000` |
| **What It Does** | Analyzes social media content for brand sentiment. Upload CSVs, enter text, or fetch Twitter data. Generates word clouds, trending keywords, polarity breakdown, engagement metrics, and exportable insight summaries. |
| **Tech Used** | Flask, Flask-CORS, Pandas, NumPy, TextBlob (NLP sentiment), Tweepy (Twitter API), WordCloud, Matplotlib, HuggingFace BART (zero-shot classification via API) |
| **AI Technique** | Sentiment analysis (TextBlob polarity + optional HuggingFace BART zero-shot classifier) |
| **Data** | CSV uploads, Twitter API fetches, or generated sample data |

**🗣️ Speech Point:** *"This module is our brand listening engine. It tells us what the market thinks about us in real time — positive, negative, or neutral — across every social platform."*

---

### 2️⃣ Smart Lead Scorer (CRM Intelligence Dashboard)
| | |
|---|---|
| **File** | `final.py` |
| **Port** | `5002` |
| **What It Does** | Trains an XGBoost ML model on behavioral CRM data to predict lead conversion probability. Batch-scores all leads, classifies them as HOT/WARM/COOL/COLD, and exposes a full dashboard with KPI cards, score distributions, regional analysis, industry analysis, and a searchable lead table. |
| **Tech Used** | Flask, Pandas, NumPy, scikit-learn (StandardScaler, LabelEncoder, train/test split), XGBoost (XGBClassifier), Pickle (model persistence), Groq LLM (optional AI explanations) |
| **AI Technique** | Supervised ML classification (XGBoost) with engineered features like `Engagement_x_Recency`, `Session_Quality`, `Product_Interest_Score`, `Email_Engagement` |
| **Data** | `crm_leads_behavioral_tracking.csv` — 40+ behavioral/CRM features per lead |

**🗣️ Speech Point:** *"This is our revenue intelligence engine. It takes raw CRM data, trains a machine learning model, and tells sales teams exactly which leads to call first — backed by data, not gut feeling."*

---

### 3️⃣ Marketing Insights Chatbot
| | |
|---|---|
| **File** | `chatbotfinal.html` |
| **Port** | Static HTML page |
| **What It Does** | A conversational navigation experience that routes users to the platform's specialized modules. Also links to side analytics modules (competitive analysis, demand-supply forecasting, inflation tracking). |
| **Tech Used** | Vanilla HTML, CSS, JavaScript |

**🗣️ Speech Point:** *"The chatbot is our smart navigation layer — it guides users to the right tool for their question, making the platform feel intuitive even with 8+ modules."*

---

### 4️⃣ Content Recommendation Engine (AI Financial Assistant)
| | |
|---|---|
| **File** | `main.py` (also `preet.py` variant) |
| **Port** | `5004` |
| **What It Does** | Generates personalized, domain-specific educational content using LLM AI. User selects a topic (Investing, Crypto, Budgeting, etc.), the system generates a comprehensive email with AI, formats it in beautiful HTML, and sends it to the user via Gmail SMTP. |
| **Tech Used** | Flask, Flask-CORS, Groq API (LLama 3.3 70B model), Gmail SMTP (email delivery), HTML email templates |
| **AI Technique** | LLM content generation (Groq — LLama 3.3 70B Versatile) with structured prompt engineering |
| **Data** | AI-generated on demand; fallback content for 5 financial domains |

**🗣️ Speech Point:** *"This module is our AI content delivery service. Tell it a topic, and it generates a personalized, beautifully formatted email with actionable recommendations — then sends it directly to the user. All powered by LLM intelligence."*

---

### 5️⃣ Personalized Campaign Generator (Agentic Campaign System)
| | |
|---|---|
| **File** | `mailingcampaign.py` |
| **Port** | `5005` |
| **What It Does** | The most feature-rich module. A full campaign management platform with: customer upload/segmentation, AI-powered campaign creation (A/B testing), ROI prediction, real campaign sending via email/SMS, real-time analytics via WebSocket, and Excel report export. |
| **Tech Used** | Flask, Flask-SocketIO, Flask-CORS, SQLAlchemy + SQLite, CrewAI (multi-agent orchestration), LangChain-Groq, LangChain-Google-GenAI, Gmail SMTP, Twilio (SMS), Pandas, OpenPyXL, Eventlet |
| **AI Technique** | Multi-agent AI system (CrewAI) — Data Analyst agent + Content Creator agent + Strategy Advisor agent. Each agent uses LLM (Groq or Gemini) to analyze, create, and optimize. Falls back to rule-based logic if LLM fails. |
| **Data** | SQLite database (`campaign_system.db`) — Customers, Campaigns, Analytics, A/B Tests, Agent Activity logs |

**🗣️ Speech Point:** *"This is our campaign operations engine. It doesn't just create campaigns — it uses three AI agents working together: one to segment customers, one to write content with A/B variants, and one to predict ROI. Then it actually sends real emails and SMS, tracks results in real time, and exports reports."*

---

### 6️⃣ Digital Twin Dashboard
| | |
|---|---|
| **File** | `digital.py` (also `twin.py` variant) |
| **Port** | `5006` |
| **What It Does** | Simulates project/operations states using a digital twin model. Maintains in-memory hackathon projects with steps, issues, team members, budgets, and deadlines. Generates alerts, tracks progress, simulates random events in real time, and displays everything in a cyberpunk-themed dashboard. |
| **Tech Used** | Flask, Flask-CORS, Python dataclasses, threading (background simulation), API key authentication system, Vanilla JS frontend with cyberpunk CSS |
| **AI Technique** | Simulation-based digital twin (rule-based event generation, state tracking, alert classification) |
| **Data** | In-memory simulation — 5 projects with steps, issues, team members, budgets |

**🗣️ Speech Point:** *"The Digital Twin dashboard gives us a live simulation of our entire operation. It monitors project progress, flags risks, and generates alerts — like having a virtual control room for your business."*

---

### 7️⃣ Strategic Certainty Engine (Multi-Agent Decision Layer)
| | |
|---|---|
| **File** | `meta.py` |
| **Port** | `5010` |
| **What It Does** | The most architecturally ambitious module. Models strategic marketing decisions as a **multi-agent huddle** led by a Central Strategy Agent (CSA). Submit a business question, and 11 specialized AI agents analyze it from their domain (leads, campaigns, sentiment, competitors, macro trends), debate, and the CSA synthesizes a final verdict: **GO**, **STOP**, or **ADJUST** — with execution orders. |
| **Tech Used** | Flask, Flask-SocketIO, Flask-CORS, Groq API (LLama 3.1 70B), scikit-learn, XGBoost, Pandas, NumPy, WebSocket (real-time huddle updates) |
| **AI Technique** | Multi-agent orchestration with 11 specialized agents + Central Strategy Agent. Each agent runs domain-specific analysis (lead scoring, value prediction, sentiment, competitor intel) and presents arguments. CSA synthesizes with weighted priorities (growth/risk/efficiency). |
| **Data** | Dynamic scenario data built from query + business context. Decision history persisted in memory. |

**🎯 The 11 Agents:**
1. Smart Lead Scorer
2. Lead Enrichment Agent
3. Lead Value Predictor
4. Personalized Campaign Generator
5. Content Recommendation Engine
6. Creative Optimizer
7. Performance Monitor
8. Sentiment Tracker
9. Competitor Intelligence
10. Macro Trend Analyzer
11. Central Strategy Agent (Orchestrator)

**🗣️ Speech Point:** *"This is our AI Chief Marketing Officer. Ask it any strategic question — 'Should we increase our LinkedIn budget by 50%?' — and 11 specialized AI agents analyze it from every angle: leads, performance, sentiment, competitors, macro trends. They debate in a strategic huddle, and the Central Strategy Agent delivers a final verdict with execution orders. It's like having an entire board of directors powered by AI."*

---

### 8️⃣ Poster Creator
| | |
|---|---|
| **File** | `postergen.py` |
| **Port** | `9000` |
| **What It Does** | Generates professional social media poster images with 3D elements, gradients, glassmorphism effects, and matching captions + hashtags. Supports multiple platforms (Instagram, Facebook, Twitter, LinkedIn), industries, tones, and design styles. |
| **Tech Used** | Gradio (web UI framework), Pillow/PIL (image creation, manipulation, filters, 3D sphere/cube rendering, gradient generation) |
| **AI Technique** | Procedural image generation with 3D rendering, glassmorphism, adaptive color schemes by industry. Template-based caption + hashtag generation. |
| **Data** | Generated on demand — no external data needed |

**🗣️ Speech Point:** *"The Poster Creator generates ready-to-publish social media visuals — complete with 3D elements, industry-specific color schemes, captions, and hashtags. Your design team gets professional output in seconds."*

---

### 📊 Side Analytics Modules (Linked from Chatbot)

| Module | File | Port | What It Does | Tech |
|---|---|---|---|---|
| **Competitive Market Predictor** | `competative_market.py` | `4000` | Predicts market share and revenue using fintech company data | Flask, Pandas, scikit-learn (RandomForestRegressor), LabelEncoder |
| **Demand-Supply Forecaster** | `demand_supply.py` | `8000` | Forecasts B2B demand vs. inventory, identifies shortages/overstocks | Flask, Pandas, scikit-learn (RandomForestRegressor), Matplotlib |
| **Inflation Tracker** | `inflasion.py` | `3000` | Predicts inflation rates and trends for fintech apps | Flask, Pandas, scikit-learn (LinearRegression), Matplotlib |

---

## 🧠 AI/ML Techniques Summary

| Technique | Where Used |
|---|---|
| **XGBoost Classification** | Lead Scoring (final.py) |
| **Random Forest Regression** | Market Prediction, Demand Forecasting |
| **Linear Regression** | Inflation Prediction |
| **LLM Content Generation** | Content Engine (Groq — LLama 3.3 70B) |
| **Multi-Agent Orchestration** | Campaign Generator (CrewAI), Strategic Engine (custom) |
| **Sentiment Analysis** | TextBlob polarity, HuggingFace BART zero-shot |
| **Real-time Simulation** | Digital Twin (threaded event generation) |
| **Procedural Image Generation** | Poster Creator (PIL 3D rendering) |

---

## 🔌 External Integrations

| Service | Purpose |
|---|---|
| **Groq API** | LLM inference (LLama 3.x models) — ultra-fast content generation |
| **Google Gemini** | Alternative LLM (via LangChain wrapper) |
| **Gmail SMTP** | Sending campaign and content emails |
| **Twilio** | SMS campaign delivery |
| **Twitter/Tweepy** | Social media data fetching |
| **HuggingFace** | BART model for zero-shot sentiment classification |

---

## 📂 Data Layer

| Data Source | Used By |
|---|---|
| `crm_leads_behavioral_tracking.csv` | Smart Lead Scorer — 40+ behavioral CRM features |
| `B2B_Supply_Demand_Dataset.csv` | Demand-Supply Forecaster |
| `synthetic_fintech_200rows.csv` | Competitive Market Predictor |
| `fintech_app_usage_dataset_inflation.csv` | Inflation Tracker |
| `campaign_system.db` (SQLite) | Campaign Generator — customers, campaigns, analytics, A/B tests |
| `models/` directory | Persisted ML model artifacts (pickle files) |
| `dashboard_data/` directory | Exported KPI summaries and reports |

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install flask flask-cors flask-socketio sqlalchemy pandas numpy scikit-learn xgboost groq langchain-groq langchain-google-genai crewai tweepy textblob wordcloud matplotlib Pillow gradio openpyxl twilio requests eventlet
```

### 2. Start Individual Modules
```bash
# Core modules (run each in a separate terminal)
python last.py           # Sentiment Tracker      → http://localhost:5000
python final.py          # Smart Lead Scorer       → http://localhost:5002
python main.py           # Content Engine          → http://localhost:5004
python mailingcampaign.py # Campaign Generator     → http://localhost:5005
python digital.py        # Digital Twin            → http://localhost:5006
python meta.py           # Strategic Engine        → http://localhost:5010
python postergen.py      # Poster Creator          → http://localhost:9000

# Side modules
python competative_market.py  # Market Predictor   → http://localhost:4000
python inflasion.py           # Inflation Tracker  → http://localhost:3000
python demand_supply.py       # Demand Forecaster  → http://localhost:8000
```

### 3. Open the Dashboard
Open `login.html` in your browser → log in → the dashboard links to all modules.

---

## 🎤 30-Second Pitch

> *"Marketing teams are drowning in fragmented tools. Our platform brings everything together — AI-powered sentiment analysis, machine learning lead scoring, multi-agent campaign automation, and strategic decision-making — all in one hub. We use 11 specialized AI agents that debate in real-time huddles to make strategic decisions. We don't just analyze data — we act on it: sending real emails, real SMS, real campaigns. It's like having an AI-powered marketing department in a box."*

---

## 👥 Team

**Twin Innovators**

---

*Built with ❤️ and AI for AI Hackathon Minds 2025*
