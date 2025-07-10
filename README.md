# 🧳 TripSaathi — Multi-Agent RAG Travel Planner

A **Multi-Agent RAG-powered Travel Planner** built with LangChain, LangGraph, FastAPI, and React. Demonstrates modern GenAI engineering patterns including multi-agent orchestration, retrieval-augmented generation, and structured LLM outputs.

## 🏗️ Architecture

```
User Request
     │
     ▼
┌─────────────┐
│  FastAPI     │
│  Backend     │
└─────┬───────┘
      │
      ▼
┌─────────────────────────────────────────┐
│           LangGraph Workflow            │
│                                         │
│  ┌──────────────┐  ┌──────────────┐    │
│  │ Destination   │→│ Budget       │    │
│  │ Agent (RAG)   │  │ Agent        │    │
│  └──────────────┘  └──────┬───────┘    │
│                           │             │
│                    ┌──────▼───────┐     │
│                    │ Itinerary    │◄──┐ │
│                    │ Agent        │   │ │
│                    └──────┬───────┘   │ │
│                           │           │ │
│                    ┌──────▼───────┐   │ │
│                    │ Critic       │   │ │
│                    │ Agent        │───┘ │
│                    └──────────────┘     │
│                    (reject → revise)    │
└─────────────────────────────────────────┘
      │
      ▼
┌─────────────┐    ┌──────────────┐
│ PostgreSQL   │    │ ChromaDB     │
│ (Trips)      │    │ (RAG Vectors)│
└─────────────┘    └──────────────┘
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq (Llama 3.1 70B) |
| Orchestration | LangGraph |
| RAG | LangChain + ChromaDB + HuggingFace Embeddings |
| Backend | FastAPI + Pydantic |
| Database | PostgreSQL + SQLAlchemy |
| Frontend | React (Vite) |

## 📋 Key Concepts Demonstrated

- **Multi-Agent Systems**: 4 specialized agents with distinct responsibilities
- **RAG (Retrieval-Augmented Generation)**: Grounding LLM responses in factual travel data
- **LangGraph State Management**: Typed shared state flowing through agent nodes
- **Conditional Routing**: Critic agent can reject and trigger itinerary revision
- **Structured Outputs**: Pydantic models for agent responses (not raw strings)
- **LLM + Application Code**: LLM for reasoning, Python for arithmetic and validation

## 🚀 Quick Start

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GROQ_API_KEY
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
TripSaathi/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point
│   │   ├── config.py        # Pydantic Settings
│   │   ├── agents/          # Destination, Budget, Itinerary, Critic
│   │   ├── graph/           # LangGraph state & workflow
│   │   ├── rag/             # RAG pipeline (loader, embeddings, retriever)
│   │   ├── api/             # FastAPI routes & schemas
│   │   ├── db/              # SQLAlchemy models & CRUD
│   │   └── core/            # LLM client, logging
│   └── travel_data/         # RAG knowledge base (.md files)
├── frontend/
│   └── src/
│       ├── components/      # React components
│       └── api/             # API client
└── README.md
```

## 📝 License

MIT
