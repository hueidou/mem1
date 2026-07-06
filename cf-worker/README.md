# mem1 — Cloudflare Worker

Cloudflare Workers + KV implementation of the mem1 memory service.
Same API as the Python version, but runs at the edge with zero server management.

## Prerequisites

- [Node.js](https://nodejs.org/) 18+
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/): `npm install -g wrangler`
- A Cloudflare account with Workers paid plan (KV requires paid plan)

## Setup

```bash
# 1. Install dependencies (none required, but login to wrangler)
npx wrangler login

# 2. Create a KV namespace
npx wrangler kv:namespace create "KV_NAMESPACE"

# 3. Copy the namespace ID from the output and paste it into wrangler.toml

# 4. (Optional) Set your API key as a secret
npx wrangler secret put API_KEY
```

## Deploy

```bash
npx wrangler deploy
```

## Development

```bash
npx wrangler dev --remote
```

## API

Same endpoints as the [Python version](../README.md) — see the root README for full API reference.

## Differences from the Python version

| Aspect | Python | Worker |
|--------|--------|--------|
| Storage | SQLite (file) | Workers KV (distributed) |
| Search | SQL `LIKE` + scoring | In-memory scoring after KV list |
| Deployment | `python server.py` | `npx wrangler deploy` |
| Dependencies | FastAPI + uvicorn | None (edge runtime) |
| Scaling | Single process | Global edge network |
| Cost | Server cost | Per-request + KV ops |
