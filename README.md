
# ⚡ Flashpoint: Real-Time Geopolitical Intelligence Platform

> **"While other AI models tell you what happened yesterday, Flashpoint tells you what is happening right now."**

### 🎥 [Watch the Demo Video Here] (Link needed)

---

## 🚨 The Problem: The "Knowledge Cutoff" in Crisis

Decision-makers (Governments, NGOs, Logistics) face a critical gap during rapidly evolving crises:

1. **News Lags:** Mainstream media takes 30-60 minutes to verify and publish.
2. **AI Hallucinates:** Standard LLMs (GPT-4) have a knowledge cutoff or rely on slow browsing tools.
3. **Noise Overload:** Human analysts cannot manually filter 10,000 Telegram messages per minute.

## 🛡️ The Solution: Flashpoint

**Flashpoint** is a **Live RAG (Retrieval Augmented Generation)** engine that listens to the raw pulse of the world—Telegram channels, Reddit threads, and News Wires—in real-time.

It uses **Pathway** to ingest, embed, and index streaming data instantly, allowing an AI Commander to answer strategic questions based on events that happened **seconds ago**.

### ✨ Key Features

* **📡 Multi-Source Intel:** Aggregates data from **Telegram** (Raw speed), **Reddit** (Human intel), and **GNews** (Verified reports).
* **⚖️ Narrative Divergence:** Unique "Bias Detection" engine that contrasts Western (CNN/Reuters) vs. Eastern (TASS/Xinhua) reporting on the same event.
* **📍 Live Conflict Map:** Auto-extracts geolocation from text streams to pin "Active Threats" on a tactical map.
* **⚡ Zero-DB Architecture:** No vector database to manage. Pathway handles streaming updates in-memory.

---

### Tech Stack

* **Engine:** [Pathway](https://pathway.com/) (Python ETL + RAG)
* **LLM:** OpenAI GPT-4o + `text-embedding-3-small`
* **Connectors:** `Telethon` (Telegram MTProto), `PRAW` (Reddit), `feedparser` (RSS)
* **Frontend:** Streamlit + Folium (Mapping)
* **Deployment:** Docker Compose

---

## 🚀 Getting Started

### Prerequisites

* Docker & Docker Compose
* OpenAI API Key
* Telegram API ID/Hash (Get from my.telegram.org)
* Reddit Client ID/Secret

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/flashpoint.git
cd flashpoint
```


2. **Configure Environment**
Run the following command:
- Linux/MacOS:
```bash
cp .env.example .env
```
- Windows:
```bash
copy .env.example .env
```
and configure all the api keys


3. **Launch the System**
Run the entire stack (Backend + Frontend) with one command:
```bash
docker-compose up --build
```


4. **Access the Dashboard**
* **UI:** Open [http://localhost:8501](https://www.google.com/search?q=http://localhost:8501)
* **Backend API:** [http://localhost:8000](https://www.google.com/search?q=http://localhost:8000)



---

## 🕹️ Demo Scenarios

### Scenario 1: The "Live" Test

1. Open the Dashboard.
2. Watch the **"Incoming Stream"** panel on the left.
3. Wait for a live update from `@insider_paper` or `r/worldnews`.
4. **Action:** Ask the AI: *"What just happened in [Region]?"*
5. **Result:** The AI answers using the message that arrived 5 seconds ago.

### Scenario 2: The Simulation

*To demonstrate capability when news is slow:*

1. Click **"Inject Simulation"** in the sidebar.
2. This feeds a pre-set scenario: *"BREAKING: 10:45 AM - Dam failure reported in Region X."*
3. Observe the **Threat Map** immediately drop a **Red Pin** on the location.
4. The **Defcon Gauge** escalates to "CRITICAL".

---

## 📂 Project Structure

```text
flashpoint/
├── backend/               # Pathway RAG Engine
│   ├── connectors/        # Custom Python Connectors (Telegram/Reddit)
│   ├── main.py            # Pipeline Logic
│   └── Dockerfile
├── frontend/              # Streamlit Dashboard
│   ├── dashboard.py       # UI Logic
│   └── Dockerfile
├── docker-compose.yaml    # Orchestration
└── README.md

```

## 👥 Team

* **[Your Name]** - Backend & Pathway Architecture
* **[Teammate Name]** - Frontend & Design
* **[Teammate Name]** - Data Strategy & Research
---

*Built with ❤️ using Pathway.*