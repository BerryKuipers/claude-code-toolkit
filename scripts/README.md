# Wescobar Scripts

Development and deployment scripts for Wescobar Universe Storyteller.

---

## Infrastructure Plan

### Local Development
- **Frontend**: Vite dev server (port 5173)
- **Backend** (planned): Node.js API (port 3000)
- **Database** (planned): PostgreSQL via Docker
- **Cache** (optional): Redis via Docker

### Staging/Production
- **Host**: TribeVibe VPS (shared infrastructure)
- **Frontend**: Static build served via Nginx or Cloudflare Pages
- **Backend**: Node.js API behind reverse proxy
- **Database**: PostgreSQL on VPS
- **DNS**: TBD (future: wescobar.app or similar)

---

## Docker Containers (Planned)

### Local Development:
```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: wescobar_dev
      POSTGRES_USER: wescobar
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Production (VPS):
- Share PostgreSQL with TribeVibe (separate database)
- Optional: Dedicated Redis instance
- Reverse proxy: Nginx or Traefik

---

## Scripts

### Security & Secrets:
- **`load-secrets-from-vault.js`** - Load secrets from HashiCorp Vault on NAS
  - Fetches GEMINI_API_KEY from Vault and writes to .env.local
  - Usage: `VAULT_TOKEN=your_token npm run secrets:load`
  - Vault path: `secret/wescobar/gemini_api_key`

### Development (To Be Created):
- `dev.js` - Start frontend + backend + Docker services
- `setup.js` - Initial project setup and dependencies
- `seed-db.js` - Seed database with sample data

### Database (To Be Created):
- `migrate.js` - Run database migrations
- `db-reset.js` - Reset database to clean state

### Deployment (To Be Created):
- `build.js` - Build frontend and backend for production
- `deploy-staging.sh` - Deploy to VPS staging environment
- `deploy-prod.sh` - Deploy to VPS production environment

---

## Current Status

**Implemented:**
- ✅ Frontend development server (Vite)
- ✅ Basic component structure
- ✅ Story creation and management UI

**Planned:**
- ⏳ Backend API setup
- ⏳ PostgreSQL database schema
- ⏳ Docker Compose configuration
- ⏳ VPS deployment scripts
- ⏳ DNS configuration

---

## Usage

(Scripts will be added as the project grows)

```bash
# Development
npm run dev          # Start frontend only (current)

# Future:
# npm run dev:full    # Start frontend + backend + Docker
# npm run db:migrate  # Run migrations
# npm run db:seed     # Seed database
```
