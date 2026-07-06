# mem1 — Agent Memory Service

**mem1** is a lightweight, self-hosted persistent memory service for AI agents.
It stores structured memories in SQLite and retrieves them via simple keyword matching — no vector databases, no external dependencies, no complexity.

> Built for agent teams that need a **simple memory backend** without running a full vector DB. Perfect for prototyping, personal projects, or small agent fleets.

## ✨ Features

- **Simple CRUD API** — add, search, list, and clear memories via HTTP
- **Multi-tenant** — memories are scoped by `user_id` + `agent_id`
- **Keyword search** — lightweight relevance scoring without vector embeddings
- **Browser UI** — built-in web interface for manual operations
- **Single file** — everything in one Python file
- **SQLite backend** — no database server needed

## Quick Start

### Prerequisites

- Python 3.10+
- `pip install fastapi uvicorn`

### Run

```bash
python server.py
```

Then visit:
- **API docs**: http://127.0.0.1:8012/
- **Web UI**: http://127.0.0.1:8012/ui/

## API Reference

All requests (except `/` and `/health`) require authentication:

```
Authorization: Bearer Pa$$w0rd
```

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API documentation (agent prompt) |
| `GET` | `/health` | Health check |
| `GET` | `/ui/` | Browser-based management UI |
| `POST` | `/memory/add` | Save a memory |
| `POST` | `/memory/search` | Search memories by keyword |
| `GET` | `/memory/{user_id}` | Get all memories for a user |
| `POST` | `/memory/clear/{user_id}` | Clear memories for a user |

### Add a memory

```bash
curl -X POST http://127.0.0.1:8012/memory/add \
  -H "Authorization: Bearer Pa$$w0rd" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "messages": "User prefers dark mode and keyboard shortcuts."}'
```

### Search memories

```bash
curl -X POST http://127.0.0.1:8012/memory/search \
  -H "Authorization: Bearer Pa$$w0rd" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "query": "keyboard shortcuts", "limit": 5}'
```

## Project Structure

```
mem1/
├── server.py      # FastAPI application (~150 lines)
├── index.html     # Browser-based management UI
├── mem0.db        # SQLite database (auto-created)
└── README.md      # This file
```

## Deployment

The service typically runs behind a reverse proxy or tunnel (e.g. [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)). Start it with:

```bash
nohup python3 server.py &
```

## Agent Prompt

When an AI agent calls `GET /`, it receives the following usage guide embedded in the JSON response. This tells the agent how to use mem1:

```
# Mem1 - Agent Memory Service

Mem1 is a lightweight persistent memory service for AI agents. It uses simple SQLite + keyword matching.

**Base URL:** `{base_url}`

## Authentication
All requests require header: `Authorization: Bearer Pa$$w0rd`

## Endpoints

### GET /
Returns this usage guide. Read this first when you encounter a Mem1 server.

### GET /health
Health check.

### GET /ui or /ui/
Browser-based UI for all API operations (requires API key input in browser).

### POST /memory/add
Save a memory.
Body: {"user_id": "<who>", "agent_id": "<which agent>", "messages": "<content to remember>"}

### POST /memory/search
Search memories by keyword.
Body: {"user_id": "<who>", "agent_id": "<which agent>", "query": "<keywords>", "limit": 5}

### GET /memory/{user_id}
Get all memories for a user.
Query param: `agent_id` (default: "default")

### POST /memory/clear/{user_id}
Clear all memories for a user.

## Best Practices
1. Save important info immediately after learning it.
2. Use short, structured content (plain text, JSON, or markdown).
3. Search before asking the user for information already stored.
4. user_id is typically the human's name; agent_id identifies which agent saved it.
```

## Customization

To change the API key, edit the `API_KEY` variable at the top of `server.py`. The database path is configured via `DB_PATH`.

## License

MIT
