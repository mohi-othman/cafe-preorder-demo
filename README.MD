# Qahwati

A demo of pre-ordering and a smart menu for specialty cafés. A customer scans a QR code at the table, orders from the mobile browser (no app), pays through a stubbed payment page, and follows the order live. Baristas work orders on a tablet kitchen display (KDS) that updates in real time. A Super Admin manages cafés, menus, QR codes and daily reports. The UI is Arabic (right-to-left) by default and switches to English.

**Architecture:** one Next.js frontend (`src/web`), one FastAPI API (`src/api`), one Postgres database. Live updates use a WebSocket on the API.

```
src/
  api/                 FastAPI app (Python)
  web/                 Next.js app (TypeScript)
  tests/               pytest tests for the API
  deploy/              production stack for one VPS (compose, Caddyfile, cloud-init)
  docker-compose.yml   local Postgres
  .env.example         every setting, with placeholder values
.github/workflows/     test, build and deploy to the VPS
```

## Run locally on Windows

All commands are PowerShell, run from the repository root unless a step says otherwise.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Postgres), or a native Postgres 16 (see [Native Postgres](#native-postgres-instead-of-docker))
- Python 3.12
- Node.js 20.9 or newer (Next.js 16 requirement)

### 1. Start Postgres

```powershell
docker compose -f src/docker-compose.yml up -d
```

This starts Postgres 16 on `localhost:5432` with user `qahwati`, password `qahwati` and database `cafe`. Data is kept in a Docker volume.

### 2. Configure

```powershell
Copy-Item src\.env.example src\api\.env
"NEXT_PUBLIC_API_URL=http://localhost:8000" | Set-Content src\web\.env.local
```

Edit `src\api\.env`:

- `DATABASE_URL` and `TEST_DATABASE_URL` already point at the local Docker database (password `qahwati`, local use only).
- Set `ADMIN_PASSWORD`, `BARISTA_PASSWORD` and `JWT_SECRET` to values of your own. A random secret:
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`

Both files are gitignored. See [Environment variables](#environment-variables) for what each setting does.

### 3. Install and seed the API

```powershell
cd src\api
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m app.seed
```

The seed creates the tables, the café "Demo Roasters" (slug `demo-roasters`) with 12 products, and two logins: `admin` (password `ADMIN_PASSWORD`) and `barista` (password `BARISTA_PASSWORD`, café Demo Roasters). It is safe to run again, but a re-run resets those two passwords to the current values and resets seeded products (matched by English name) to their seed price, availability and text. A seeded product renamed in admin is added again as a new product.

`requirements-dev.txt` adds the test tools; `requirements.txt` is enough to only run the app.

### 4. Run the API

From `src\api`:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

The API listens on http://localhost:8000. Check http://localhost:8000/api/health (returns `{"ok":true}`); interactive docs are at http://localhost:8000/docs. The schema is created on startup.

### 5. Run the web app

In a second terminal, from `src\web`:

```powershell
npm ci
npm run dev
```

Open http://localhost:3000. For a production build instead of the dev server: `npm run build`, then `npm run start`. To use another port: `npm run dev -- -p 3001` (then add that origin to `WEB_ORIGIN`).

| Page | URL | Login |
|---|---|---|
| Customer menu | http://localhost:3000/c/demo-roasters?table=4 (`/` redirects here without a table) | none |
| Order tracking | `/o/<order id>`, opened after payment | none |
| KDS | http://localhost:3000/kds (tap "Start shift" to enable the chime) | `barista` |
| Admin | http://localhost:3000/admin | `admin` |

Logins last 12 hours. New cafés and their barista logins are created in Admin → Cafés.

### Tests

From `src`, with Postgres running:

```powershell
api\.venv\Scripts\python -m pytest
```

Tests use `TEST_DATABASE_URL` (from the environment or `src\api\.env`). They create that database if it is missing and **drop and recreate all its tables**, so never point it at a database you care about. Test passwords and secrets are set by the tests themselves.

Frontend checks, from `src\web`: `npm run lint` and `npm run build` (type check). There are no frontend unit tests.

### Native Postgres instead of Docker

Create an empty database, then point `DATABASE_URL` and `TEST_DATABASE_URL` in `src\api\.env` at your server, for example:

```powershell
psql -U postgres -c "CREATE DATABASE cafe"
```

```
DATABASE_URL=postgresql+psycopg://postgres:<your password>@localhost:5432/cafe
TEST_DATABASE_URL=postgresql+psycopg://postgres:<your password>@localhost:5432/cafe_test
```

The test user needs permission to create databases (the tests create `cafe_test` through the `postgres` maintenance database).

### Changing the schema

There are no migrations: tables are created with `create_all`, which never alters an existing table. After a model change, stop the API, recreate the database and seed again:

```powershell
docker compose -f src/docker-compose.yml down -v
docker compose -f src/docker-compose.yml up -d
```

(`down -v` deletes all local data.) With a native or hosted Postgres, drop and recreate the database instead.

## Environment variables

| Variable | Read by | Purpose | Example |
|---|---|---|---|
| `DATABASE_URL` | API, seed | Postgres connection. Must use the `postgresql+psycopg://` scheme. Default: the local Docker database. | `postgresql+psycopg://qahwati:qahwati@localhost:5432/cafe` |
| `TEST_DATABASE_URL` | tests only | Database the tests wipe and recreate. Required to run tests. | `postgresql+psycopg://qahwati:qahwati@localhost:5432/cafe_test` |
| `WEB_ORIGIN` | API | Allowed browser origins (CORS), comma-separated, no trailing slash. Default `http://localhost:3000`. | `https://qahwati.vercel.app` |
| `JWT_SECRET` | API | Signs login tokens. Required for logins; use a long random value. Changing it logs everyone out. | 48+ random characters |
| `ADMIN_PASSWORD` | seed only | Password the seed gives the `admin` login. | a strong password |
| `BARISTA_PASSWORD` | seed only | Password the seed gives the `barista` login (Demo Roasters). | a strong password |
| `NEXT_PUBLIC_API_URL` | web | Public base URL of the API, no trailing slash. The WebSocket URL is derived from it (`http` → `ws`, `https` → `wss`). Built into the browser bundle, so it must be set **before** `npm run build`. Default `http://localhost:8000`. | `https://qahwati-api.onrender.com` |
| `API_INTERNAL_URL` | web (server only) | Optional private API address for server-side fetches; the browser still uses `NEXT_PUBLIC_API_URL`. Read at run time. | `http://api:8000` |

Locally the API reads `src\api\.env`; real environment variables override it. The web app reads `src\web\.env.local`. In hosting, set them in the provider's dashboard; no `.env` file is deployed.

## Deploy: API and Postgres on Render, web on Vercel

Push the repository to GitHub first; both providers deploy from it. Deploy in this order, because each side needs the other's URL: database, API, web, then finish the API's `WEB_ORIGIN`.

### 1. Postgres on Render

1. Render Dashboard → **New** → **Postgres**. Pick a name, a region, Postgres 16 and a plan, then create it.
2. On the database's **Info** page, note the **Internal Database URL** (for the API, same region only) and the **External Database URL** (for seeding from your own computer).

Render shows these URLs as `postgres://…` or `postgresql://…`. The API uses SQLAlchemy with the psycopg 3 driver, which rejects `postgres://`, so always change the scheme to `postgresql+psycopg://` and keep the rest unchanged:

```
postgres://user:pass@dpg-xxxx-a/cafe   →   postgresql+psycopg://user:pass@dpg-xxxx-a/cafe
```

For the external URL, also add `?sslmode=require` at the end.

Free Render databases expire 30 days after creation; use a paid plan for anything that must last.

### 2. API on Render

Render Dashboard → **New** → **Web Service**, connect the repository, then set:

| Setting | Value |
|---|---|
| Language | Python 3 |
| Branch | `main` |
| Region | the database's region |
| Root Directory | `src/api` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/health` (under Advanced) |
| Instances | **1** (see [Limits](#limits)) |

Environment variables:

| Variable | Value |
|---|---|
| `PYTHON_VERSION` | `3.12.9` (Render needs a full version; without it Render uses its newer default) |
| `DATABASE_URL` | the Internal Database URL with the `postgresql+psycopg://` scheme |
| `JWT_SECRET` | a new random value: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `WEB_ORIGIN` | your Vercel URL once you have it (step 4); until then any placeholder such as `https://example.invalid` |

Render sets `$PORT` itself; do not hard-code a port. WebSockets work on Render web services with no extra settings; the browser connects with `wss://`. After the deploy, open `https://<your-api>.onrender.com/api/health`; it should return `{"ok":true}`. The tables are created on the first start.

A free Render web service sleeps after 15 minutes without traffic and takes about a minute to wake up; a KDS on the free plan will see that delay after idle periods.

### 3. Seed the new environment

Seed once per new database. Use new, strong passwords for every environment; they are only needed where the seed runs.

**From your computer** (works on every plan), from `src\api` after the local install in step 3 above:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://<user>:<pass>@<external host>/<db>?sslmode=require"
$env:ADMIN_PASSWORD = "<strong password>"
$env:BARISTA_PASSWORD = "<another strong password>"
.\.venv\Scripts\python -m app.seed
Remove-Item Env:DATABASE_URL, Env:ADMIN_PASSWORD, Env:BARISTA_PASSWORD
```

These variables override `src\api\.env` for that terminal only.

**From Render Shell** (paid plans only): add `ADMIN_PASSWORD` and `BARISTA_PASSWORD` to the API service's environment, open the service's **Shell** tab and run `python -m app.seed`. You can remove the two variables afterwards; the running API does not need them.

To change the `admin` or `barista` password later, set new values and run the seed again (this also resets seeded products, see step 3 of the local setup).

### 4. Web on Vercel

Vercel Dashboard → **Add New** → **Project**, import the repository, then set:

| Setting | Value |
|---|---|
| Framework Preset | Next.js (detected) |
| Root Directory | `src/web` |
| Build / Install / Output | defaults (`npm run build`, `npm install`, `.next`) |
| Environment variable | `NEXT_PUBLIC_API_URL` = `https://<your-api>.onrender.com` (no trailing slash), for Production (and Preview if you use previews) |

Set `NEXT_PUBLIC_API_URL` **before** the first deploy: it is built into the bundle, and Vercel applies changed variables only to new deployments, so redeploy after changing it.

### 5. Connect the API to the web app

Back on the Render API service, set `WEB_ORIGIN` to the Vercel production URL, for example `https://qahwati.vercel.app` (scheme included, no trailing slash). Add more origins comma-separated, for example a custom domain or a Preview URL. Saving the variable redeploys the API.

### 6. Check

- `https://<your-web>.vercel.app/c/demo-roasters?table=1` shows the menu.
- Log in at `/kds` as `barista` and at `/admin` as `admin`.
- Place an order and pay; it appears on the KDS without a reload, and the tracking page updates when the barista moves it.

QR codes use the address the admin page is open on. Open Admin → QR codes on the public web URL (not localhost or a Preview URL) before printing them.

### Adding keys to a new environment (summary)

| Where | Variables |
|---|---|
| Render API service | `PYTHON_VERSION`, `DATABASE_URL`, `JWT_SECRET`, `WEB_ORIGIN` |
| Wherever you run the seed | `DATABASE_URL`, `ADMIN_PASSWORD`, `BARISTA_PASSWORD` |
| Vercel project | `NEXT_PUBLIC_API_URL` |

Generate new secrets and passwords for each environment, and never commit them. `src/.env.example` holds placeholders only, apart from the local Docker database password.

## Deploy to a VPS with GitHub Actions

An alternative to Render and Vercel: everything on one small Ubuntu 24.04 server (1 vCPU / 1 GB RAM is enough), deployed by [.github/workflows/deploy.yml](.github/workflows/deploy.yml) on every push to `main`, or by hand with **Actions → Deploy → Run workflow**.

```
push to main → tests + lint → build api and web images → push to ghcr.io → ssh to the VPS → docker compose pull + up → health check
```

On the server, [src/deploy/docker-compose.yml](src/deploy/docker-compose.yml) runs Postgres, the API (one process), the web app and Caddy in `/opt/qahwati`. Only Caddy is reachable from outside: `/api/*` (REST and WebSockets) goes to the API, everything else to the web app. Images are built on GitHub, so the server never runs `npm run build`.

### 1. Make two SSH keys

In PowerShell on your computer, skipping the first command if you already have a personal key:

```powershell
ssh-keygen -t ed25519 -f $HOME\.ssh\id_ed25519
ssh-keygen -t ed25519 -C qahwati-deploy -f $HOME\.ssh\qahwati_deploy
```

Press Enter at the deploy key's passphrase prompts: it has no passphrase because GitHub Actions uses it unattended. Keep it only in GitHub secrets (step 3) and delete the local copy afterwards if you like.

### 2. Create the server

1. Copy [src/deploy/cloud-init.yaml](src/deploy/cloud-init.yaml) and replace the two `REPLACE-WITH-…` lines with the contents of `id_ed25519.pub` and `qahwati_deploy.pub`.
2. Create an Ubuntu 24.04 server. Under **Cloud-Init User-Data** (on Vultr: Additional Features → Cloud-Init User-Data), paste the edited file.
3. Wait about 3 minutes after it boots, then log in as `ssh deploy@<server ip>`. `cloud-init status` should say `done`. Root and password logins are off.

cloud-init sets up the firewall (22, 80, 443), 2 GB swap, Docker, automatic security updates, and `/opt/qahwati/db.env` and `/opt/qahwati/api.env` with newly generated database password, `JWT_SECRET`, `ADMIN_PASSWORD` and `BARISTA_PASSWORD`. Read the logins once and keep them in your password manager:

```powershell
ssh deploy@<server ip> cat /opt/qahwati/api.env
```

### 3. Add the GitHub settings

Repository → **Settings → Secrets and variables → Actions**, or with the GitHub CLI from the repository folder:

| Name | Kind | Value |
|---|---|---|
| `VPS_HOST` | secret | the server's IP |
| `VPS_SSH_KEY` | secret | the private deploy key (`qahwati_deploy`, not `.pub`) |
| `VPS_KNOWN_HOSTS` | secret | the server's host keys, so the workflow refuses an impostor server |
| `PUBLIC_URL` | variable | the address people open, no trailing slash, for example `http://203.0.113.10` |

```powershell
gh secret set VPS_HOST --body "<server ip>"
Get-Content -Raw $HOME\.ssh\qahwati_deploy | gh secret set VPS_SSH_KEY
ssh-keyscan <server ip> | gh secret set VPS_KNOWN_HOSTS
gh variable set PUBLIC_URL --body "http://<server ip>"
```

`ssh-keyscan` trusts whatever answers. Run it right after you have logged in once in step 2, and compare a fingerprint with `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the server if you want to be sure.

### 4. Deploy

Push to `main`, or run the workflow by hand. The first deploy also seeds the database (Demo Roasters and the two logins) and leaves `/opt/qahwati/.seeded` so later deploys don't reset admin edits. Then check the same things as in [6. Check](#6-check) on `PUBLIC_URL`.

**Roll back:** open an earlier successful run of the workflow and choose **Re-run all jobs**. Each run deploys the images tagged with its own commit. Images older than a week that are not in use are deleted from the server.

**Schema changes:** there are no migrations. After a deploy that changes the models, reset the database on the server (this deletes all data):

```powershell
ssh deploy@<server ip> "cd /opt/qahwati && docker compose down && docker volume rm qahwati_pgdata && rm .seeded"
```

Then run the workflow again.

**Logs:** `ssh deploy@<server ip> "cd /opt/qahwati && docker compose logs -f api"` (or `web`, `caddy`, `db`).

### Adding a domain and HTTPS later

Point an `A` record at the server, replace `:80` with the domain in [src/deploy/Caddyfile](src/deploy/Caddyfile), set `PUBLIC_URL` to `https://<domain>` and push. Caddy gets the certificate by itself. `PUBLIC_URL` is built into the web image, so changing it always needs a new run of the workflow.

### Adding keys to a new VPS (summary)

| Where | What |
|---|---|
| Server, `/opt/qahwati/db.env` and `api.env` | generated by cloud-init; never in git or GitHub |
| GitHub secrets | `VPS_HOST`, `VPS_SSH_KEY`, `VPS_KNOWN_HOSTS` |
| GitHub variable | `PUBLIC_URL` |

The workflow logs in to `ghcr.io` with its own short-lived `GITHUB_TOKEN`, so there is no registry password to manage.

## Limits

- **Run exactly one API instance.** Live updates go through an in-memory broadcaster inside the API process. With two or more instances (or `uvicorn --workers` above 1), an order handled by one instance would not reach KDS screens or tracking pages connected to another. Scaling out needs a shared pub/sub such as Postgres `LISTEN/NOTIFY` or Redis.
- **No migrations.** A schema change means recreating the database and seeding again.
- **Payments are a stub.** The Apple Pay and mada buttons always succeed; there is a "simulate failure" link for testing.
