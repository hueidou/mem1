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

## Customization

To change the API key, edit the `API_KEY` variable at the top of `server.py`. The database path is configured via `DB_PATH`.

## License

MIT
