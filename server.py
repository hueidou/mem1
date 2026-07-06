from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import os, json, uuid, sqlite3
from pathlib import Path
from datetime import datetime

API_KEY = "Pa$$w0rd"
DB_PATH = os.path.expanduser("~/mem0-server/mem0.db")

AGENT_PROMPT = """# Mem1 - Agent Memory Service

Mem1 is a lightweight persistent memory service for AI agents. It uses simple SQLite + keyword matching.

**Base URL:** https://mem1.201609.xyz

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
Body: `{"user_id": "<who>", "agent_id": "<which agent>", "messages": "<content to remember>"}`

### POST /memory/search
Search memories by keyword.
Body: `{"user_id": "<who>", "agent_id": "<which agent>", "query": "<keywords>", "limit": 5}`

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
"""

app = FastAPI(title="Mem1")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
            agent_id TEXT DEFAULT 'default', content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user ON memories(user_id, agent_id)")
    conn.commit()
    conn.close()

init_db()

async def verify_auth(request: Request):
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

class MemRequest(BaseModel):
    user_id: str; agent_id: str = "default"; messages: str
class SearchRequest(BaseModel):
    user_id: str; agent_id: str = "default"; query: str; limit: int = 5

BASE_DIR = Path(__file__).parent

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "mem1",
        "version": "1.0.0",
        "agent_prompt": AGENT_PROMPT,
        "usage": "Read agent_prompt field for complete API documentation and agent instructions."
    }

@app.get("/ui")
@app.get("/ui/")
async def ui():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/memory/add")
async def add_memory(req: MemRequest, request: Request):
    await verify_auth(request)
    mid = str(uuid.uuid4()); ts = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO memories VALUES (?,?,?,?,?)",
        (mid, req.user_id, req.agent_id, req.messages, ts))
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM memories WHERE user_id=? AND agent_id=?",
        (req.user_id, req.agent_id)).fetchone()[0]
    conn.close()
    return {"status": "ok", "memory_id": mid, "count": count}

@app.post("/memory/search")
async def search_memory(req: SearchRequest, request: Request):
    await verify_auth(request)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT content FROM memories WHERE user_id=? AND agent_id=?",
        (req.user_id, req.agent_id)).fetchall()
    conn.close()
    query_words = req.query.lower().split()
    scored = []
    for (content,) in rows:
        score = sum(1 for w in query_words if w in content.lower())
        if score > 0: scored.append((score, content))
    scored.sort(key=lambda x: -x[0])
    return {"status": "ok", "result": [s[1] for s in scored[:req.limit]]}

@app.get("/memory/{user_id}")
async def get_memories(user_id: str, request: Request, agent_id: str = "default"):
    await verify_auth(request)
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT content FROM memories WHERE user_id=? AND agent_id=?",
        (user_id, agent_id)).fetchall()
    conn.close()
    return {"status": "ok", "count": len(rows), "memories": [r[0] for r in rows]}

@app.post("/memory/clear/{user_id}")
async def clear_memories(user_id: str, request: Request, agent_id: str = "default"):
    await verify_auth(request)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM memories WHERE user_id=? AND agent_id=?", (user_id, agent_id))
    conn.commit(); conn.close()
    return {"status": "ok", "message": f"Cleared memories for {user_id}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8012)
