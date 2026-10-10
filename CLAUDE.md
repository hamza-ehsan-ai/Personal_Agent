# Personal Agent Workspace

## Project: OpenChat AI Chat Application

A full-stack AI chat application with local and cloud AI provider support.

### Directory Structure

```
Personal_Agent/
├── frontend/          # Next.js 16 + React 19 + TypeScript + Tailwind CSS 4
├── backend/           # FastAPI + Python 3.13 (uv)
└── skills/            # Reusable agent templates and utilities
```

## Stack Overview

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | Next.js 16, React 19, TypeScript 5 | Tailwind CSS 4, shadcn/ui |
| Backend | FastAPI, Python 3.13 | uv as package manager |
| Local AI | Ollama (localhost:11434) | gemma3:1b model |
| Cloud AI | OpenAI, Anthropic, Gemini, Grok, Meta | Fallback providers |

## Project Guidelines

**AGENTS.md** contains the full project rules and conventions. Key points:

* Never commit `.env`, secrets, or API keys
* Run tests after every change (`pytest` in backend)
* Keep changes minimal and focused
* Follow existing project patterns and conventions
* Prefer type-safe, clean, maintainable code
* Update tests when behavior changes
* Do not introduce dependencies without clear need

## Quick Start

### Prerequisites
- Node.js 24+ (frontend)
- Python 3.13 (backend)
- Ollama installed and running with `gemma3:1b` model

### Setup Commands

```bash
# Frontend setup
cd frontend
npm install
npm run dev

# Backend setup
cd backend
uv sync
uv run fastapi dev
```

## AI Provider Strategy

The application supports multiple AI providers via a pluggable architecture:

* **Local-first**: Ollama (gemma3:1b) - default for private, offline use
* **Cloud fallbacks**: OpenAI, Anthropic, Gemini, Grok, Meta Llama
* **Configurable**: Switch providers per request or globally via config

## Development Workflow

1. Make focused changes (one feature/focus per commit)
2. Run backend tests: `cd backend && pytest`
3. Frontend follows Next.js dev workflow (watch mode, hot reload)
4. Commit with conventional commits format
5. Push to main branch

## Key Files to Know

* `frontend/lib/api.ts` - API client configuration
* `backend/app/providers/registry.py` - AI provider interface
* `backend/app/core/config.py` - Environment and feature flags
* `frontend/app/page.tsx` - Main chat interface
* `backend/app/routes/chat.py` - Chat endpoint implementation

## Tools & Commands Reference

| Action | Command |
|--------|---------|
| Frontend install | `npm install <package>` |
| Backend install | `uv add <package>` |
| Run tests | `pytest` (backend only) |
| Linting | Ruff (backend), ESLint (frontend) |

## Memory Context

This workspace uses **CLAUDE.md** for local context (this file) and may use memory files in `.claude/projects/-Users-hamza-ehsan-Desktop-Personal-Agent/memory/` for persistent state across sessions.

---

🤖 Generated with Claude Code
