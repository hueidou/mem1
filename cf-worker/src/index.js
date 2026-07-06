// ── mem1 — Cloudflare Worker version ──────────────────────────────────────
// Uses Workers KV for persistent storage.
//
// Bindings (configure in wrangler.toml / Cloudflare Dashboard):
//   KV_NAMESPACE (KV namespace)
//   API_KEY      (secret env var)

// ── UI HTML (embedded for self-contained deployment) ──────────────────────
const UI_HTML = `<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>Mem1 UI</title>
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
<h2>Mem1 — Memory Service UI</h2>
<div class="section">
<h3>API Key</h3>
<input type="password" id="apiKey" placeholder="Enter API Key (Bearer token)" style="width:400px">
</div>
<div id="msgBox" class="msg"></div>

<div class="section">
<h3>🤖 Agent Skill Prompt</h3>
<p style="color:#666;font-size:13px;margin:4px 0 10px">Give this to any AI agent to let it use mem1. Fill in your details, then copy.</p>
<input type="text" id="skillUserId" placeholder="Your User ID" style="width:200px">
<button class="btn-primary" onclick="copySkillPrompt()" style="margin-top:6px">📋 Copy Prompt</button>
<pre id="skillPreview" style="margin-top:8px;background:#f0f4f8;padding:12px;border-radius:4px;font-size:13px;line-height:1.6">Loading...</pre>
</div>

<div class="section">
<h3>View User Memories</h3>
<div class="flex"><input type="text" id="viewUserId" placeholder="User ID" style="width:200px">
<button class="btn-primary" onclick="viewMemories()">View</button></div>
<button class="btn-small" onclick="toggleView()">Expand / Collapse</button>
<div id="viewResult" class="hidden"></div>
</div>

<div class="section">
<h3>Add Memory</h3>
<input type="text" id="addUserId" placeholder="User ID" style="width:200px">
<input type="text" id="addAgentId" placeholder='Agent ID (default: "default")' style="width:200px">
<textarea id="addContent" placeholder="Memory content"></textarea>
<button class="btn-primary" onclick="addMemory()">Add</button>
</div>

<div class="section">
<h3>Search Memories</h3>
<input type="text" id="searchUserId" placeholder="User ID" style="width:200px">
<input type="text" id="searchQuery" placeholder="Keywords" style="width:300px">
<label>Limit: <input type="number" id="searchLimit" value="5" style="width:80px"></label>
<button class="btn-primary" onclick="searchMemory()">Search</button>
<div id="searchResult"></div>
</div>

<div class="section">
<h3>Clear Memories</h3>
<div class="flex"><input type="text" id="clearUserId" placeholder="User ID" style="width:200px">
<button class="btn-danger" onclick="clearMemories()">Clear</button></div>
</div>

<script>
function getAuth(){const k=document.getElementById('apiKey').value;return k?'Bearer '+k:''}
function msg(t,c){const m=document.getElementById('msgBox');m.className='msg '+t;m.textContent=c;m.style.display='block';setTimeout(()=>m.style.display='none',5000)}
async function api(m,u,b){const h={'Authorization':getAuth()};if(b){h['Content-Type']='application/json'};const r=await fetch(u,{method:m,headers:h,body:b?JSON.stringify(b):undefined});if(!r.ok&&r.status>=500){const t=await r.text();msg('err',t)};return r}

function updateSkillPrompt(){
 const addr=window.location.origin;
 const key=document.getElementById('apiKey').value||'<your-api-key>';
 const uid=document.getElementById('skillUserId').value||'<your-user-id>';
 document.getElementById('skillPreview').textContent=
  'Hey, you can use the mem1 memory service.\\n'+
  'Address: '+addr+'\\nAuth: Bearer '+key+'\\nUser: '+uid+'\\n\\n'+
  "Hit the root endpoint first — it'll tell you everything you need.";
}
document.getElementById('apiKey').addEventListener('input',updateSkillPrompt);
document.getElementById('skillUserId').addEventListener('input',updateSkillPrompt);
updateSkillPrompt();

function copySkillPrompt(){
 navigator.clipboard.writeText(document.getElementById('skillPreview').textContent)
  .then(()=>msg('ok','Copied!')).catch(()=>msg('err','Copy failed'));
}

async function viewMemories(){
 const uid=document.getElementById('viewUserId').value;
 if(!uid){msg('err','Please enter User ID');return}
 const r=await api('GET','/memory/'+uid+'?agent_id=default');
 if(!r)return;const d=await r.json();
 if(!r.ok){msg('err',d.detail||'Error');return}
 const el=document.getElementById('viewResult');
 el.innerHTML='<p>Total: '+d.count+' memories</p>'+
  '<table><thead><tr><th>#</th><th>Content</th></tr></thead><tbody>'+
  d.memories.map((c,i)=>'<tr><td>'+(i+1)+'</td><td><pre>'+esc(c)+'</pre></td></tr>').join('')+
  '</tbody></table>';
 el.classList.remove('hidden');
 msg('ok','Success, '+d.count+' memories')
}
function toggleView(){document.getElementById('viewResult').classList.toggle('hidden')}

async function addMemory(){
 const uid=document.getElementById('addUserId').value;
 const content=document.getElementById('addContent').value;
 if(!uid||!content){msg('err','User ID and content cannot be empty');return}
 const aid=document.getElementById('addAgentId').value||'default';
 const r=await api('POST','/memory/add',{user_id:uid,agent_id:aid,messages:content});
 if(!r)return;const d=await r.json();
 if(!r.ok){msg('err',d.detail||'Error');return}
 msg('ok','Added. memory_id='+d.memory_id);document.getElementById('addContent').value=''
}

async function searchMemory(){
 const uid=document.getElementById('searchUserId').value;
 const q=document.getElementById('searchQuery').value;
 if(!uid||!q){msg('err','User ID and keyword cannot be empty');return}
 const limit=document.getElementById('searchLimit').value||5;
 const r=await api('POST','/memory/search',{user_id:uid,query:q,limit:parseInt(limit)});
 if(!r)return;const d=await r.json();
 if(!r.ok){msg('err',d.detail||'Error');return}
 const el=document.getElementById('searchResult');
 el.innerHTML='<p>Search results ('+d.result.length+'):</p>'+
  d.result.map((c,i)=>'<pre>'+(i+1)+'. '+esc(c)+'</pre>').join('')||'<p>No matching results</p>';
 msg('ok','Search complete')
}

async function clearMemories(){
 const uid=document.getElementById('clearUserId').value;
 if(!uid){msg('err','Please enter User ID');return}
 if(!confirm('Are you sure you want to clear all memories for '+uid+'?'))return;
 const r=await api('POST','/memory/clear/'+uid);
 if(!r)return;const d=await r.json();
 if(!r.ok){msg('err',d.detail||'Error');return}
 msg('ok',d.message)
}

function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}
</script></body></html>`;

// ── Helpers ──────────────────────────────────────────────────────────────

function uuid() {
  return crypto.randomUUID();
}

function now() {
  return new Date().toISOString();
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  });
}

function html(body, status = 200) {
  return new Response(body, {
    status,
    headers: { 'content-type': 'text/html; charset=utf-8' },
  });
}

// ── KV key helpers ──────────────────────────────────────────────────────
// Key format: mem:{user_id}:{agent_id}:{uuid}
// Index key:  memidx:{user_id}:{agent_id} -> comma-separated list of memory IDs

function memKey(user_id, agent_id, id) {
  return `mem:${user_id}:${agent_id}:${id}`;
}

function idxKey(user_id, agent_id) {
  return `memidx:${user_id}:${agent_id}`;
}

async function verifyAuth(request, env) {
  const auth = request.headers.get('Authorization') || '';
  const expected = `Bearer ${env.API_KEY || 'Pa$$w0rd'}`;
  if (auth !== expected) {
    throw new Error('Unauthorized');
  }
}

function makeAgentPrompt(baseUrl) {
  const key = API_KEY_PLACEHOLDER;
  return `# Mem1 - Agent Memory Service

Mem1 is a lightweight persistent memory service for AI agents. It uses simple SQLite + keyword matching.

**Base URL:** \`${baseUrl}\`

## Authentication
All requests require header: \`Authorization: Bearer ${key}\`

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
Query param: \`agent_id\` (default: "default")

### POST /memory/clear/{user_id}
Clear all memories for a user.

## Best Practices
1. Save important info immediately after learning it.
2. Use short, structured content (plain text, JSON, or markdown).
3. Search before asking the user for information already stored.
4. user_id is typically the human's name; agent_id identifies which agent saved it.`;
}

let API_KEY_PLACEHOLDER = '<your-api-key>';

// ── Router ───────────────────────────────────────────────────────────────

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const method = request.method;
    const baseUrl = url.origin;

    // Set placeholder from env for root prompt
    API_KEY_PLACEHOLDER = env.API_KEY || 'Pa$$w0rd';

    try {
      // ── GET / ──────────────────────────────────────────────────────
      if (method === 'GET' && path === '/') {
        return json({
          status: 'ok',
          service: 'mem1',
          version: '1.0.0',
          agent_prompt: makeAgentPrompt(baseUrl),
          usage: 'Read agent_prompt field for complete API documentation and agent instructions.',
        });
      }

      // ── GET /health ─────────────────────────────────────────────────
      if (method === 'GET' && path === '/health') {
        return json({ status: 'healthy' });
      }

      // ── GET /ui ─────────────────────────────────────────────────────
      if (method === 'GET' && (path === '/ui' || path === '/ui/')) {
        return html(UI_HTML);
      }

      // ── POST /memory/add ────────────────────────────────────────────
      if (method === 'POST' && path === '/memory/add') {
        await verifyAuth(request, env);
        const { user_id, agent_id = 'default', messages } = await request.json();
        if (!user_id || !messages) {
          return json({ detail: 'user_id and messages are required' }, 400);
        }
        const id = uuid();
        const ts = now();
        await env.KV_NAMESPACE.put(memKey(user_id, agent_id, id), messages, {
          metadata: { user_id, agent_id, id, timestamp: ts },
        });

        // Update index
        const idx = (await env.KV_NAMESPACE.get(idxKey(user_id, agent_id))) || '';
        const updatedIdx = idx ? `${idx},${id}` : id;
        // Only keep last 1000 IDs to avoid hitting KV 512KB limit
        const trimmed = updatedIdx.split(',').slice(-1000).join(',');
        await env.KV_NAMESPACE.put(idxKey(user_id, agent_id), trimmed);

        // Count
        const count = trimmed.split(',').filter(Boolean).length;
        return json({ status: 'ok', memory_id: id, count });
      }

      // ── POST /memory/search ─────────────────────────────────────────
      if (method === 'POST' && path === '/memory/search') {
        await verifyAuth(request, env);
        const { user_id, agent_id = 'default', query, limit = 5 } = await request.json();
        if (!user_id || !query) {
          return json({ detail: 'user_id and query are required' }, 400);
        }
        const idx = (await env.KV_NAMESPACE.get(idxKey(user_id, agent_id))) || '';
        const ids = idx.split(',').filter(Boolean);
        const queryWords = query.toLowerCase().split(/\s+/);

        // Fetch all memory entries for this user+agent
        const entries = [];
        // Process in batches to avoid too many KV reads
        const batchSize = 100;
        for (let i = 0; i < ids.length; i += batchSize) {
          const batch = ids.slice(i, i + batchSize);
          const results = await Promise.all(
            batch.map(id => env.KV_NAMESPACE.getWithMetadata(memKey(user_id, agent_id, id)))
          );
          for (const r of results) {
            if (r.value) {
              entries.push({ id: r.metadata?.id, content: r.value });
            }
          }
        }

        // Score by keyword match
        const scored = entries
          .map(e => {
            const score = queryWords.reduce((s, w) => s + (e.content.toLowerCase().includes(w) ? 1 : 0), 0);
            return { score, content: e.content };
          })
          .filter(e => e.score > 0)
          .sort((a, b) => b.score - a.score)
          .slice(0, limit);

        return json({ status: 'ok', result: scored.map(s => s.content) });
      }

      // ── GET /memory/{user_id} ───────────────────────────────────────
      const listMatch = path.match(/^\/memory\/([^/]+)$/);
      if (method === 'GET' && listMatch) {
        await verifyAuth(request, env);
        const user_id = listMatch[1];
        const agent_id = url.searchParams.get('agent_id') || 'default';
        const idx = (await env.KV_NAMESPACE.get(idxKey(user_id, agent_id))) || '';
        const ids = idx.split(',').filter(Boolean);

        const entries = await Promise.all(
          ids.map(id => env.KV_NAMESPACE.get(memKey(user_id, agent_id, id)))
        );
        const memories = entries.filter(Boolean);
        return json({ status: 'ok', count: memories.length, memories });
      }

      // ── POST /memory/clear/{user_id} ────────────────────────────────
      const clearMatch = path.match(/^\/memory\/clear\/([^/]+)$/);
      if (method === 'POST' && clearMatch) {
        await verifyAuth(request, env);
        const user_id = clearMatch[1];
        const agent_id = url.searchParams.get('agent_id') || 'default';
        const idx = (await env.KV_NAMESPACE.get(idxKey(user_id, agent_id))) || '';
        const ids = idx.split(',').filter(Boolean);

        // Delete all memory entries
        await Promise.all(ids.map(id => env.KV_NAMESPACE.delete(memKey(user_id, agent_id, id))));
        // Clear index
        await env.KV_NAMESPACE.delete(idxKey(user_id, agent_id));

        return json({ status: 'ok', message: `Cleared memories for ${user_id} (agent: ${agent_id})` });
      }

      // ── 404 ─────────────────────────────────────────────────────────
      return json({ detail: 'Not Found' }, 404);

    } catch (e) {
      if (e.message === 'Unauthorized') {
        return json({ detail: 'Unauthorized' }, 401);
      }
      return json({ detail: e.message || 'Internal Server Error' }, 500);
    }
  },
};
