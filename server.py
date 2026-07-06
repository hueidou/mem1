from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os, json, uuid, sqlite3
from datetime import datetime

API_KEY = "Pa$$w0rd"
DB_PATH = os.path.expanduser("~/mem0-server/mem0.db")

AGENT_PROMPT = """# Mem1 - Agent Memory Service

Mem1 is a lightweight persistent memory service for AI agents. It uses simple SQLite + keyword matching.

## Authentication
All requests require header: `Authorization: Bearer Pa$$w0rd`

## Endpoints

### GET /
Returns this usage guide. Read this first when you encounter a Mem1 server.

### GET /health
Health check.

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

HTML_CSS = """body{font-family:sans-serif;margin:20px;max-width:1200px}
table{border-collapse:collapse;width:100%;margin-top:10px}
th,td{border:1px solid #ddd;padding:6px;text-align:left;font-size:13px}
th{background:#4CAF50;color:white;position:sticky;top:0}
tr:nth-child(even){background:#f2f2f2}
pre{background:#f5f5f5;padding:10px;border-radius:4px;overflow-x:auto}
input,button{padding:6px 12px;margin:2px;font-size:14px}
.error{color:red}"""

@app.get("/")
async def root(request: Request, user_id: str = "", api_key: str = ""):
    rows = []
    error = ""
    if user_id and api_key:
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute(
                "SELECT id, agent_id, content, timestamp FROM memories WHERE user_id=? ORDER BY timestamp DESC",
                (user_id,)
            ).fetchall()
        except Exception as e:
            error = str(e)
        conn.close()
    trs = "".join(
        f"<tr><td>{r[0][:8]}</td><td>{r[2]}</td><td>{r[1]}</td><td>{r[3][:19]}</td></tr>"
        for r in rows
    ) if rows else "<tr><td colspan='4' style='text-align:center;color:#999'>No memories found</td></tr>"
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>Mem1</title><style>{HTML_CSS}</style></head>
<body>
<h2>Mem1 - Agent Memory Service</h2>
<div style="display:flex;gap:20px;flex-wrap:wrap">
<div style="flex:1;min-width:300px">
<h3>使用说明</h3>
<pre>{AGENT_PROMPT}</pre>
</div>
<div style="flex:1;min-width:400px">
<h3>查询记忆</h3>
<form method="get" action="/">
<label>User ID: <input type="text" name="user_id" value="{user_id}" required></label><br>
<label>API Key: <input type="password" name="api_key" value="{api_key}" required></label><br>
<button type="submit">查询</button>
</form>
{('<p class="error">' + error + '</p>') if error else ''}
<h3>记忆列表 ({len(rows)})</h3>
<div style="max-height:600px;overflow-y:auto">
<table><thead><tr><th>ID</th><th>Content</th><th>Agent</th><th>Time</th></tr></thead>
<tbody>{trs}</tbody></table></div>
</div></div></body></html>""")

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
