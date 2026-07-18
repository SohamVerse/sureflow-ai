# 🔧 Troubleshooting

Real failures hit while building and running SureFlow OS, with the fixes that actually worked.

---

## Contents

- [Docker build fails: `invalid file request Dockerfile`](#-docker-build-fails-invalid-file-request-dockerfile)
- [Port already in use](#-port-already-in-use)
- [Login redirect loop between /login and /industrial](#-login-redirect-loop-between-login-and-industrial)
- [Login returns 401](#-login-returns-401)
- [Dashboards are empty](#-dashboards-are-empty)
- [Agents fail or return nothing](#-agents-fail-or-return-nothing)
- [Document upload fails](#-document-upload-fails)
- [Neo4j connection refused](#-neo4j-connection-refused)
- [Next.js picks the wrong workspace root](#-nextjs-picks-the-wrong-workspace-root)

---

## 🐳 Docker build fails: `invalid file request Dockerfile`

**Symptom**

```
#2 [internal] load build definition from Dockerfile
#2 transferring dockerfile: 31B
#2 ERROR: invalid file request Dockerfile
failed to solve: failed to read dockerfile: invalid file request Dockerfile
```

The giveaway is the byte count — `31B` when the real Dockerfile is ~640B. Docker isn't reading your
file at all.

**Cause**

The project is inside a **OneDrive**-synced folder. OneDrive Files On-Demand converts files into
dehydrated placeholders carrying the `ReparsePoint` attribute, and Docker BuildKit refuses to read
any file with a reparse point.

**Confirm it**

```powershell
Get-Item .\backend\Dockerfile | Select-Object Name, Length, Attributes
# ReparsePoint in the output → this is your problem
```

**What does *not* work**

`attrib +P` ("Always keep on this device") hydrates the content but **leaves the reparse point tag in
place** — attributes stay `0x80420` and the build fails identically. This is the advice you'll find
everywhere and it does not fix this.

**The fix** — rewrite each affected file as a genuine local file:

```powershell
$root = "path\to\sureflow-ai"
$venv = [System.IO.Path]::Combine($root, "backend", ".venv")

$targets = @()
$targets += Get-ChildItem $root -File -Force -ErrorAction SilentlyContinue
$targets += Get-ChildItem ([System.IO.Path]::Combine($root,"backend")) -Recurse -File -Force `
            -ErrorAction SilentlyContinue | Where-Object { -not $_.FullName.StartsWith($venv) }
$targets = $targets | Where-Object { ([int]$_.Attributes -band 0x400) -ne 0 }

foreach ($f in $targets) {
  $src = $f.FullName; $tmp = "$src.hyd"
  $bytes = [System.IO.File]::ReadAllBytes($src)
  [System.IO.File]::WriteAllBytes($tmp, $bytes)
  [System.IO.File]::Delete($src)
  [System.IO.File]::Move($tmp, $src)
}
```

Attributes should drop to `32` (Archive only). The build then succeeds.

> 💡 **The durable fix is moving the repository outside OneDrive.** OneDrive can re-dehydrate files at
> any time, so this will recur otherwise.

---

## 🔌 Port already in use

SureFlow claims a lot of ports. Find the offender:

```powershell
netstat -ano | findstr :8000        # Windows
lsof -i :8000                       # macOS / Linux
```

| Port | Service | Frequent conflict |
|---|---|---|
| 3000 | Frontend | Another Next.js/React app |
| 8000 | Backend | **A local backend and the Docker backend both running** |
| 5433 | Postgres | Deliberately not 5432, to dodge a local Postgres |
| 7474 / 7687 | Neo4j | A local Neo4j install |
| 3001 | Grafana | Mapped off 3000 because the frontend owns it |

The most common case by far is running Path A and Path B at once. Pick one:

```bash
docker compose stop backend temporal-worker   # then run uvicorn locally
```

---

## 🔁 Login redirect loop between `/login` and `/industrial`

**Symptom** — the browser flickers rapidly between the two routes and never settles.

**Cause** — a desynced session in `localStorage`: `sureflow_user` present but `sureflow_token`
missing. The route guard and the login page then each redirect to the other forever.

**Fix** — a hard refresh (`Ctrl+Shift+R`). The auth layer now treats a session as valid only when
*both* keys exist and clears a half-session automatically, so it self-heals to the login page.

If it somehow persists, clear the keys manually in DevTools → Console:

```js
localStorage.removeItem('sureflow_token');
localStorage.removeItem('sureflow_user');
localStorage.removeItem('sureflow_target_plant');
location.href = '/login';
```

---

## 🔑 Login returns 401

**Check the password.** Older docs circulated `admin123` / `plant123`; those are **wrong** and return
401. The working credentials:

| Email | Password |
|---|---|
| `cto@sureflow.ai` | `Sureflow_CTO_2026!` |
| `karnataka@sureflow.ai` | `Sureflow_Plant_2026!` |
| `delhi@sureflow.ai` | `Sureflow_Plant_2026!` |

`backend/scripts/seed_users.py` is the source of truth — check there if these ever drift.

**If the password is right,** the users probably aren't seeded:

```bash
docker compose exec backend python scripts/seed_users.py
```

**If you were logged in and suddenly get 401s,** your JWT expired — tokens last **24 hours**. Log in
again.

---

## 📭 Dashboards are empty

Almost always missing seed data. Run all three seed scripts
([details](./GETTING_STARTED.md#seeding-the-demo-data)):

```bash
docker compose exec backend python scripts/seed_industrial_data.py
docker compose exec backend python scripts/seed_users.py
docker compose exec backend python scripts/seed_kpi_snapshots.py
```

Verify the graph actually has nodes — at [localhost:7474](http://localhost:7474):

```cypher
MATCH (e:Equipment) RETURN count(e)
```

If that returns `0`, `seed_industrial_data.py` didn't complete — check its output for errors.

**If data exists but a specific plant looks empty,** that's the isolation model working as intended:
a plant manager only ever sees their own plant. Log in as the CTO to see everything.

---

## 🤖 Agents fail or return nothing

**1. Is `GEMINI_API_KEY` set?** The single most common cause.

```bash
docker compose exec backend printenv | grep GEMINI
```

Empty means `backend/.env` is missing or the key isn't in it. Note that editing `.env` requires a
restart: `docker compose restart backend`.

**2. Quota exhausted.** The free tier has daily limits; a `429` in the logs means you've hit them.
The Model Broker falls back to local Ollama automatically — but only if Ollama is actually running:

```bash
ollama list        # should show nomic-embed-text and llama3.2
```

**3. Malformed JSON from the LLM.** Handled — `core/json_utils.py` uses `json-repair` to recover
broken model output. If you see parse errors despite that, they'll be logged with the raw response.

**4. Watch it happen:**

```bash
docker compose logs -f backend
```

---

## 📄 Document upload fails

**In Docker** — Tesseract and Poppler are installed in the image, so OCR should just work. If uploads
fail, check the logs for the actual exception.

**Running locally on Windows** — the OCR binaries aren't present. Install both and set them in `.env`:

```env
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\poppler\Library\bin
```

- Tesseract → https://github.com/UB-Mannheim/tesseract/wiki
- Poppler → https://github.com/oschwartz10612/poppler-windows/releases

**Scanned PDFs with no text layer** fall back to OCR, which is slower — allow time before assuming
it hung. The upload endpoint streams SSE progress, so the UI shows which stage it's on.

---

## 🕸 Neo4j connection refused

**Wrong hostname for your setup.** Inside Docker the host is `neo4j`; from your machine it's
`localhost`:

```env
NEO4J_URI=bolt://neo4j:7687        # backend running in Docker
NEO4J_URI=bolt://localhost:7687    # backend running on the host
```

`docker-compose.yml` sets the Docker value automatically — you only need to change this for Path B.

**Neo4j is slow to start.** It accepts Bolt connections several seconds after the container reports
as running. Check readiness:

```bash
docker compose logs neo4j | grep -i started
```

**Credentials** are `neo4j` / `sureflow_password`, set via `NEO4J_AUTH` in compose. Changing that
after the volume is created won't take effect — you'd need `docker compose down -v` (which erases
all data).

---

## ⚠️ Next.js picks the wrong workspace root

**Symptom**

```
⚠ Warning: Next.js inferred your workspace root, but it may not be correct.
 We detected multiple lockfiles and selected the directory of C:\Users\...\Desktop\package-lock.json
```

Next.js found several `package-lock.json` files and picked one outside the project. Harmless, but it
can cause odd module resolution.

**Fix** — delete the stray lockfiles, keeping `frontend/package-lock.json`. Or pin the root
explicitly in `next.config.ts`:

```ts
const nextConfig = {
  turbopack: { root: __dirname },
};
```
