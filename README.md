# 🤖 Enterprise AI Platform

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)

**A complete, production-ready AI platform running 100% locally with zero API costs.**

Local-first AI platform: LLM chat + RAG, image generation, and chart building. No API costs. FastAPI + Streamlit + Ollama.

[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Documentation](#-documentation)

</div>

---

## 📖 Overview

Enterprise AI Platform is a full-featured AI application suite that runs entirely on your local machine. It combines powerful LLM chat capabilities, AI image generation, and data visualization tools in a professional, production-ready architecture.

### Why Choose This Platform?

- 🆓 **100% Free** - No API keys, no usage limits, no hidden costs
- 🔒 **Private** - All data stays on your machine
- 🏗️ **Production-Ready** - Clean Architecture, CQRS, comprehensive testing
- 🚀 **Feature-Rich** - Chat, RAG, image generation, charts, and more
- 📦 **Easy Deployment** - Docker Compose or systemd deployment

---

## ✨ Features

### 💬 AI Chat
- Multi-model support (DeepSeek, Llama, Qwen, Mistral, CodeLlama)
- Streaming responses with Server-Sent Events
- Conversation memory and RAG (Retrieval Augmented Generation)
- Document Q&A with local embeddings
- Prompt templates and system prompts
- Chat history and search

### 🎨 Image Generation
- Multiple models (Z-Image Turbo, Flux.2 Klein)
- Style presets (photorealistic, anime, oil painting, cyberpunk)
- Negative prompts and seed control
- Batch generation
- Gallery management with favorites

### 📊 Chart Builder
- Interactive chart creation from CSV/Excel data
- Multiple chart types (line, bar, scatter, area, pie, heatmap)
- AI-assisted chart generation from natural language
- Real-time data streaming via WebSocket
- Export to PNG, SVG, PDF, CSV

### 🔐 Security & Administration
- JWT authentication with refresh tokens
- RBAC (Admin, Power User, User, Viewer)
- API key management
- Rate limiting (token bucket)
- Comprehensive audit logging
- Data encryption at rest

### 🏗️ Architecture Highlights
- **Clean Architecture** with Domain-Driven Design
- **CQRS** pattern for command/query separation
- **Repository Pattern** for data access abstraction
- **Dependency Injection** for loose coupling
- **WebSocket** support for real-time features
- **Full test coverage** (unit, integration, e2e)

---

## 📋 Requirements

| Component | Minimum | Recommended |
|-----------|---------|--------------|
| Python | 3.10 | 3.11+ |
| RAM | 8 GB | 16 GB+ |
| Storage | 20 GB | 50 GB+ |
| GPU | Optional | NVIDIA 8GB+ VRAM |
| OS | Linux/macOS/Windows | Ubuntu 22.04+ |

---

## 🚀 Installation

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/srinuk9570/enterprise-ai-platform.git
cd enterprise-ai-platform

# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d

# Access the application
# Frontend: http://localhost:8501
# API Docs: http://localhost:8000/api/docs
```

### Option 2: Local Development

```bash
# Clone repository
git clone https://github.com/srinuk9570/enterprise-ai-platform.git
cd enterprise-ai-platform

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
make install-dev

# Install Ollama (required for LLM)
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull deepseek-r1:7b
ollama pull llama3.2:7b
ollama pull x/z-image-turbo

# Initialize project
make init

# Run development server
make run
```

---

## 🎯 Quick Start

1. **Start the platform**

   ```bash
   make run
   ```

2. **Access the web interface**

   Open [http://localhost:8501](http://localhost:8501)

3. **Register a new account**

4. **Start chatting!**

5. **Try the API**

   ```bash
   # Login
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"yourpassword"}'

   # Chat
   curl -X POST http://localhost:8000/api/llm/chat \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"message":"Hello, AI!"}'
   ```

---

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [User Guide](docs/user-guide.md)
- [Development Guide](docs/development-guide.md)
- [Deployment Guide](docs/deployment-guide.md)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Uvicorn |
| Frontend | Streamlit |
| Database | SQLite, SQLAlchemy, Alembic |
| Vector Store | ChromaDB, Sentence Transformers |
| Cache | Redis |
| LLM | Ollama (DeepSeek, Llama, Qwen, Mistral) |
| Charts | Matplotlib, Plotly, Pandas |
| Auth | JWT, Bcrypt |
| Testing | Pytest, Coverage |
| Container | Docker, Docker Compose |
| Monitoring | Prometheus, Grafana |

---

## 📁 Project Structure

```
ai_platform/
│
├── backend/
│   ├── main.py               # FastAPI: Manages LLM, Image Gen, and Chart Data
│   ├── chart_engine.py       # Logic for generating Matplotlib charts FAST
│   ├── database.py           # SQLite connection for saving chat history
│   └── requirements.txt      # Python packages
│
├── frontend/
│   ├── app.py                # Streamlit UI (The "Strong Build" interface)
│   └── styles.css            # (Optional) Custom look
│
├── models/                    # Empty folder where Ollama stores LLMs locally
│
├── generated_images/          # Where AI-generated images are saved
│
├── docker-compose.yml         # (Professional Touch) Starts everything with one command
└── .env.example                # Template for secrets (even if empty, shows good practice)
```