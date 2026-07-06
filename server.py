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

UI_HTML = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>Mem1 UI</title>
<style>
*{box-sizing:border-box}
body{font-family:sans-serif;margin:20px;max-width:1000px}
h2{color:#333}
.section{border:1px solid #ddd;border-radius:6px;padding:16px;margin:12px 0}
.section h3{margin-top:0}
label{display:block;margin:6px 0}
input,textarea,select{width:100%;padding:8px;border:1px solid #ccc;border-radius:4px;font-size:14px}
textarea{font-family:monospace;min-height:60px}
button{padding:8px 20px;border:none;border-radius:4px;cursor:pointer;font-size:14px}
.btn-primary{background:#4CAF50;color:white}
.btn-danger{background:#f44336;color:white}
.btn-small{padding:4px 10px;font-size:12px}
table{border-collapse:collapse;width:100%;margin-top:8px;font-size:13px}
th,td{border:1px solid #ddd;padding:6px;text-align:left}
th{background:#4CAF50;color:white;position:sticky;top:0}
tr:nth-child(even){background:#f9f9f9}
pre{background:#f5f5f5;padding:8px;border-radius:4px;overflow-x:auto;font-size:12px}
.msg{padding:8px 12px;border-radius:4px;margin:6px 0;display:none}
.msg.info{background:#e3f2fd;border:1px solid #90caf9;display:block}
.msg.err{background:#ffebee;border:1px solid #ef9a9a;display:block}
.msg.ok{background:#e8f5e9;border:1px solid #a5d6a7;display:block}
.hidden{display:none}
.flex{display:flex;gap:8px;align-items:center}
</style></head>
<body>
<h2>Mem1 - Memory Service UI</h2>
<div class="section">
<h3>API Key</h3>
<input type="password" id="apiKey" placeholder="输入 API Key (Bearer token)" style="width:400px">
</div>
<div id="msgBox" class="msg"></div>

<div class="section">
<h3>查看用户记忆</h3>
<div class="flex"><input type="text" id="viewUserId" placeholder="User ID" style="width:200px">
<button class="btn-primary" onclick="viewMemories()">查询</button></div>
<button class="btn-small" onclick="toggleView()">展开/收起</button>
<div id="viewResult" class="hidden"></div>
</div>

<div class="section">
<h3>添加记忆</h3>
<input type="text" id="addUserId" placeholder="User ID" style="width:200px">
<input type="text" id="addAgentId" placeholder="Agent ID (默认 default)" style="width:200px">
<textarea id="addContent" placeholder="记忆内容"></textarea>
<button class="btn-primary" onclick="addMemory()">添加</button>
</div>

<div class="section">
<h3>搜索记忆</h3>
<input type="text" id="searchUserId" placeholder="User ID" style="width:200px">
<input type="text" id="searchQuery" placeholder="关键词" style="width:300px">
<label>limit: <input type="number" id="searchLimit" value="5" style="width:80px"></label>
<button class="btn-primary" onclick="searchMemory()">搜索</button>
<div id="searchResult"></div>
</div>

<div class="section">
<h3>清除记忆</h3>
<div class="flex"><input type="text" id="clearUserId" placeholder="User ID" style="width:200px">
<button class="btn-danger" onclick="clearMemories()">清除</button></div>
</div>

<script>
function getAuth(){const k=document.getElementById('apiKey').value;return k?'Bearer '+k:''}
function msg(t,c){const m=document.getElementById('msgBox');m.className='msg '+t;m.textContent=c;m.style.display='block';setTimeout(()=>m.style.display='none',5000)}
async function api(m,u,b){const h={'Authorization':getAuth()};if(b){h['Content-Type']='application/json'};return fetch(u,{method:m,headers:h,body:b?JSON.stringify(b):undefined})}

async function viewMemories(){
 const uid=document.getElementById('viewUserId').value;
 if(!uid){msg('err','请输入 User ID');return}
 const r=await api('GET','/memory/'+uid+'?agent_id=default');
 const d=await r.json();
 if(!r.ok){msg('err',d.detail||'Error');return}
 const el=document.getElementById('viewResult');
 el.innerHTML='<p>共 '+d.count+' 条记忆</p>'+
  '<table><thead><tr><th>#</th><th>Content</th></tr></thead><tbody>'+
  d.memories.map((c,i)=>'<tr><td>'+(i+1)+'</td><td><pre>'+esc(c)+'</pre></td></tr>').join('')+
  '</tbody></table>';
 el.classList.remove('hidden');
 msg('ok','查询成功，共 '+d.count+' 条')
}
function toggleView(){const el=document.getElementById('viewResult');el.classList.toggle('hidden')}

async function addMemory(){
 const uid=document.getElementById('addUserId').value;
 const content=document.getElementById('addContent').value;
 if(!uid||!content){msg('err','User ID 和内容不能为空');return}
 const aid=document.getElementById('addAgentId').value||'default';
 const r=await api('POST','/memory/add',{user_id:uid,agent_id:aid,messages:content});
 const d=await r.json();
 if(!r.ok){msg('err',d.detail||'Error');return}
 msg('ok','已添加，memory_id='+d.memory_id);document.getElementById('addContent').value=''
}

async function searchMemory(){
 const uid=document.getElementById('searchUserId').value;
 const q=document.getElementById('searchQuery').value;
 if(!uid||!q){msg('err','User ID 和关键词不能为空');return}
 const limit=document.getElementById('searchLimit').value||5;
 const r=await api('POST','/memory/search',{user_id:uid,query:q,limit:parseInt(limit)});
 const d=await r.json();
 if(!r.ok){msg('err',d.detail||'Error');return}
 const el=document.getElementById('searchResult');
 el.innerHTML='<p>搜索结果 ('+d.result.length+'):</p>'+
  d.result.map((c,i)=>'<pre>'+(i+1)+'. '+esc(c)+'</pre>').join('')||'<p>无匹配结果</p>';
 msg('ok','搜索完成')
}

async function clearMemories(){
 const uid=document.getElementById('clearUserId').value;
 if(!uid){msg('err','请输入 User ID');return}
 if(!confirm('确定清除 '+uid+' 的所有记忆？'))return;
 const r=await api('POST','/memory/clear/'+uid);
 const d=await r.json();
 if(!r.ok){msg('err',d.detail||'Error');return}
 msg('ok',d.message)
}

function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}
</script></body></html>"""

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
    return HTMLResponse(UI_HTML)

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
