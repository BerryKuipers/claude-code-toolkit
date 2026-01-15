# Verify Deploy Command

**Arguments:** [environment] [--project=name] [--fix] [--strict]

**Success Criteria:** All pre-deployment checks pass with detailed report

**Description:** Pre-flight validation for staging/production deployments. Catches configuration mismatches, missing env vars, port conflicts, and security issues before deployment to avoid runtime failures.

---

## Quick Reference

```bash
/verify-deploy                     # Verify current project for staging
/verify-deploy production          # Verify for production deployment
/verify-deploy --fix               # Auto-fix common issues where possible
/verify-deploy --strict            # Fail on warnings (not just errors)
/verify-deploy --project=tribevibe # Verify specific project
```

---

## Validation Categories

### 1. Docker & Container Setup
### 2. Environment Variables
### 3. Frontend Build Config (Vite)
### 4. Backend Config
### 5. Port & Network Mappings
### 6. Directory Structure & Paths
### 7. DNS & Cloudflare Prep
### 8. Security & Access

---

## Workflow

### Phase 1: Docker & Container Validation

```bash
echo "=== Docker Configuration ==="

# Check docker-compose exists
COMPOSE_FILE="docker-compose.yml"
if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "ERROR: ${COMPOSE_FILE} not found"
  ERRORS+=("Missing docker-compose.yml")
fi

# Validate docker-compose syntax
docker compose -f ${COMPOSE_FILE} config > /dev/null 2>&1 || {
  echo "ERROR: Invalid docker-compose.yml syntax"
  ERRORS+=("Invalid docker-compose syntax")
}

# Check required services defined
REQUIRED_SERVICES=("api" "web" "postgres")
for svc in "${REQUIRED_SERVICES[@]}"; do
  if ! grep -q "^\s*${svc}:" ${COMPOSE_FILE}; then
    echo "WARNING: Service '${svc}' not found in compose file"
    WARNINGS+=("Missing service: ${svc}")
  fi
done

# Check for environment-specific compose files
if [[ "${ENVIRONMENT}" == "production" ]]; then
  if [[ ! -f "docker-compose.prod.yml" ]] && [[ ! -f "docker/docker-compose.prod.yml" ]]; then
    echo "WARNING: No production compose override found"
    WARNINGS+=("Consider docker-compose.prod.yml for production overrides")
  fi
fi

# Check healthchecks defined
if ! grep -q "healthcheck:" ${COMPOSE_FILE}; then
  echo "WARNING: No healthchecks defined in compose file"
  WARNINGS+=("Add healthchecks for reliable deployments")
fi
```

### Phase 2: Environment Variables

```bash
echo "=== Environment Variables ==="

# Check .env files exist
ENV_FILES=(".env" ".env.local" ".env.${ENVIRONMENT}")
for envfile in "${ENV_FILES[@]}"; do
  if [[ -f "${envfile}" ]]; then
    echo "Found: ${envfile}"
  fi
done

# Required variables per environment
REQUIRED_VARS_STAGING=(
  "DATABASE_URL"
  "VITE_API_URL"
  "JWT_SECRET"
  "NODE_ENV"
)

REQUIRED_VARS_PRODUCTION=(
  "${REQUIRED_VARS_STAGING[@]}"
  "SENTRY_DSN"
  "CLOUDFLARE_API_TOKEN"
)

# Check each required var
for var in "${REQUIRED_VARS[@]}"; do
  if ! grep -qE "^${var}=" .env* 2>/dev/null; then
    echo "ERROR: Missing required variable: ${var}"
    ERRORS+=("Missing env var: ${var}")
  fi
done

# Check for localhost in production configs
if [[ "${ENVIRONMENT}" == "production" ]]; then
  if grep -rE "localhost|127\.0\.0\.1" .env.production 2>/dev/null; then
    echo "ERROR: localhost found in production env file"
    ERRORS+=("Remove localhost from production config")
  fi
fi

# Check for secrets in git
if git ls-files | xargs grep -l "sk-\|secret_\|password=" 2>/dev/null | grep -v ".example"; then
  echo "ERROR: Possible secrets found in tracked files"
  ERRORS+=("Secrets may be committed to git")
fi

# Validate no .env in git (should be in .gitignore)
if git ls-files | grep -E "^\.env$|^\.env\.local$"; then
  echo "ERROR: .env files tracked in git"
  ERRORS+=(".env files should be in .gitignore")
fi
```

### Phase 3: Frontend Build Config (Vite)

```bash
echo "=== Frontend Build Configuration ==="

# Check vite.config.ts exists
if [[ ! -f "vite.config.ts" ]] && [[ ! -f "vite.config.js" ]]; then
  echo "ERROR: No vite.config found"
  ERRORS+=("Missing vite.config.ts")
fi

# Check VITE_API_URL is set correctly per environment
VITE_API_URL=$(grep "VITE_API_URL" .env.${ENVIRONMENT} 2>/dev/null | cut -d= -f2)
if [[ -z "${VITE_API_URL}" ]]; then
  echo "ERROR: VITE_API_URL not set for ${ENVIRONMENT}"
  ERRORS+=("Set VITE_API_URL in .env.${ENVIRONMENT}")
else
  echo "VITE_API_URL: ${VITE_API_URL}"

  # Verify it's not localhost for production
  if [[ "${ENVIRONMENT}" == "production" ]] && [[ "${VITE_API_URL}" == *"localhost"* ]]; then
    echo "ERROR: VITE_API_URL contains localhost for production"
    ERRORS+=("VITE_API_URL must use production domain")
  fi
fi

# Check base path configuration
if grep -q "base:" vite.config.*; then
  BASE_PATH=$(grep "base:" vite.config.* | head -1)
  echo "Base path: ${BASE_PATH}"
fi

# Check build output directory
BUILD_DIR=$(grep -oP "outDir:\s*['\"]?\K[^'\"]*" vite.config.* 2>/dev/null || echo "dist")
echo "Build output: ${BUILD_DIR}"

# Verify production build works
echo "Testing production build..."
npm run build --dry-run 2>/dev/null || {
  echo "WARNING: Could not verify build command"
  WARNINGS+=("Verify 'npm run build' works")
}
```

### Phase 4: Backend Configuration

```bash
echo "=== Backend Configuration ==="

# Check backend entry point
BACKEND_ENTRY=$(find backend/src -name "server.ts" -o -name "main.ts" -o -name "index.ts" | head -1)
if [[ -z "${BACKEND_ENTRY}" ]]; then
  echo "WARNING: Could not identify backend entry point"
  WARNINGS+=("Verify backend entry point")
fi

# Check DATABASE_URL format
DB_URL=$(grep "DATABASE_URL" .env.${ENVIRONMENT} 2>/dev/null | cut -d= -f2)
if [[ -n "${DB_URL}" ]]; then
  if [[ "${DB_URL}" == *"localhost"* ]] && [[ "${ENVIRONMENT}" == "production" ]]; then
    echo "ERROR: DATABASE_URL uses localhost for production"
    ERRORS+=("DATABASE_URL must use production DB host")
  fi

  # Check if it's using docker service name for staging
  if [[ "${ENVIRONMENT}" == "staging" ]] && [[ "${DB_URL}" != *"postgres"* ]] && [[ "${DB_URL}" != *"db"* ]]; then
    echo "WARNING: DATABASE_URL may need docker service name"
    WARNINGS+=("Use docker service name (e.g., 'postgres') for DATABASE_URL in compose")
  fi
fi

# Check CORS configuration
if grep -rq "cors" backend/src; then
  CORS_ORIGINS=$(grep -r "origin" backend/src | grep -oP "origin:\s*['\"]?\K[^'\"]*" | head -3)
  echo "CORS origins found: ${CORS_ORIGINS}"

  if [[ "${ENVIRONMENT}" == "production" ]] && echo "${CORS_ORIGINS}" | grep -q "localhost"; then
    echo "WARNING: CORS allows localhost in production"
    WARNINGS+=("Review CORS origins for production")
  fi
fi

# Check port configuration
BACKEND_PORT=$(grep -E "PORT|port" .env 2>/dev/null | grep -oP "\d{4}" | head -1 || echo "3000")
echo "Backend port: ${BACKEND_PORT}"
```

### Phase 5: Port & Network Mappings

```bash
echo "=== Port & Network Configuration ==="

# Extract ports from docker-compose
echo "Docker port mappings:"
grep -E "^\s*-\s*\"\d+:\d+\"" docker-compose.yml | while read line; do
  echo "  ${line}"
done

# Check for port conflicts
PORTS_USED=$(grep -oP "\d+(?=:)" docker-compose.yml | sort -u)
for port in ${PORTS_USED}; do
  if [[ $(echo "${PORTS_USED}" | grep -c "^${port}$") -gt 1 ]]; then
    echo "ERROR: Port ${port} used multiple times"
    ERRORS+=("Port conflict: ${port}")
  fi
done

# Verify frontend can reach backend
FRONTEND_API_URL=$(grep "VITE_API_URL" .env.${ENVIRONMENT} 2>/dev/null | cut -d= -f2)
BACKEND_EXPOSED_PORT=$(grep -A5 "api:" docker-compose.yml | grep -oP "\d+(?=:\d+)" | head -1)

echo "Frontend expects API at: ${FRONTEND_API_URL}"
echo "Backend exposes port: ${BACKEND_EXPOSED_PORT}"

# Check nginx proxy configuration (if exists)
if [[ -f "nginx.conf" ]] || [[ -f "docker/nginx.conf" ]]; then
  NGINX_CONF=$(find . -name "nginx.conf" | head -1)
  echo "Nginx config found: ${NGINX_CONF}"

  # Check proxy_pass matches backend port
  PROXY_PASS=$(grep "proxy_pass" ${NGINX_CONF} | head -1)
  echo "Nginx proxy: ${PROXY_PASS}"
fi

# Check internal vs external communication
echo ""
echo "Network topology check:"
echo "  - Frontend (browser) -> API: via ${FRONTEND_API_URL}"
echo "  - API -> Database: via docker network (service name)"
echo "  - Nginx -> API: via docker network (service name)"
```

### Phase 6: Directory Structure & Paths

```bash
echo "=== Directory Structure ==="

# Check required directories exist or will be created
REQUIRED_DIRS=(
  "backend/dist"
  "dist"
  "docker"
)

for dir in "${REQUIRED_DIRS[@]}"; do
  if [[ -d "${dir}" ]] || grep -q "mkdir.*${dir}" Dockerfile* 2>/dev/null; then
    echo "OK: ${dir}"
  else
    echo "WARNING: ${dir} may need to be created"
    WARNINGS+=("Verify ${dir} exists or is created during build")
  fi
done

# Check volume mount paths (VPS side)
echo ""
echo "Volume mounts in compose:"
grep -E "volumes:" -A 10 docker-compose.yml | grep -E "^\s*-\s*" | head -10

# Check for absolute paths that may differ between dev/prod
if grep -rE "/home/|/Users/|C:\\\\" docker-compose.yml .env* 2>/dev/null; then
  echo "WARNING: Absolute local paths found in config"
  WARNINGS+=("Use relative paths or environment variables for portability")
fi

# Persistence directories
echo ""
echo "Persistent data directories:"
grep -E "\.\/data|\.\/postgres|\.\/uploads" docker-compose.yml || echo "  (none found - verify persistence setup)"
```

### Phase 7: DNS & Cloudflare Preparation

```bash
echo "=== DNS & Cloudflare ==="

# Load domain from registry
REGISTRY=".claude-toolkit/.claude/skills/infrastructure/deployments.registry.json"
if [[ -f "${REGISTRY}" ]]; then
  DOMAIN=$(jq -r ".projects.${PROJECT}.environments.${ENVIRONMENT}.domain" ${REGISTRY})
  API_DOMAIN=$(jq -r ".projects.${PROJECT}.environments.${ENVIRONMENT}.apiDomain" ${REGISTRY})
  echo "Target domain: ${DOMAIN}"
  echo "API domain: ${API_DOMAIN}"
fi

# Check DNS records exist
if command -v dig &> /dev/null; then
  echo ""
  echo "DNS resolution check:"
  for domain in "${DOMAIN}" "${API_DOMAIN}"; do
    if [[ -n "${domain}" ]] && [[ "${domain}" != "null" ]]; then
      IP=$(dig +short ${domain} 2>/dev/null | head -1)
      if [[ -n "${IP}" ]]; then
        echo "  ${domain} -> ${IP}"
      else
        echo "  ${domain} -> NOT RESOLVED"
        WARNINGS+=("DNS not configured for ${domain}")
      fi
    fi
  done
fi

# Check SSL readiness (for production)
if [[ "${ENVIRONMENT}" == "production" ]] && [[ -n "${DOMAIN}" ]]; then
  echo ""
  echo "SSL certificate check:"
  SSL_EXPIRY=$(echo | openssl s_client -servername ${DOMAIN} -connect ${DOMAIN}:443 2>/dev/null | \
    openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
  if [[ -n "${SSL_EXPIRY}" ]]; then
    echo "  SSL expires: ${SSL_EXPIRY}"
  else
    echo "  SSL not configured or domain not accessible"
    WARNINGS+=("Verify SSL is configured for ${DOMAIN}")
  fi
fi

# Check Cloudflare Access (if applicable)
if jq -e ".projects.${PROJECT}.monitoring.seq" ${REGISTRY} &>/dev/null; then
  SEQ_DOMAIN=$(jq -r ".projects.${PROJECT}.monitoring.seq" ${REGISTRY})
  echo ""
  echo "Protected services (require Cloudflare Access):"
  echo "  - Seq: ${SEQ_DOMAIN}"
fi
```

### Phase 8: Security Validation

```bash
echo "=== Security Checks ==="

# Check for hardcoded secrets
echo "Scanning for hardcoded secrets..."
SECRET_PATTERNS=(
  "sk-[a-zA-Z0-9]{20,}"
  "ghp_[a-zA-Z0-9]{36}"
  "password\s*=\s*['\"][^'\"]+['\"]"
  "secret\s*=\s*['\"][^'\"]+['\"]"
  "api_key\s*=\s*['\"][^'\"]+['\"]"
)

for pattern in "${SECRET_PATTERNS[@]}"; do
  MATCHES=$(grep -rE "${pattern}" --include="*.ts" --include="*.tsx" --include="*.js" \
    --exclude-dir=node_modules --exclude-dir=dist 2>/dev/null | grep -v ".example" | head -3)
  if [[ -n "${MATCHES}" ]]; then
    echo "WARNING: Possible secret found:"
    echo "${MATCHES}"
    WARNINGS+=("Review possible hardcoded secrets")
  fi
done

# Check .gitignore
GITIGNORE_REQUIRED=(".env" ".env.local" ".env.production" "*.pem" "*.key")
for item in "${GITIGNORE_REQUIRED[@]}"; do
  if ! grep -q "${item}" .gitignore 2>/dev/null; then
    echo "WARNING: ${item} not in .gitignore"
    WARNINGS+=("Add ${item} to .gitignore")
  fi
done

# Check authentication middleware
if grep -rq "authenticate\|requireAuth\|isAuthenticated" backend/src; then
  echo "OK: Authentication middleware found"
else
  echo "WARNING: No authentication middleware detected"
  WARNINGS+=("Verify authentication is properly implemented")
fi

# Check HTTPS enforcement
if [[ "${ENVIRONMENT}" == "production" ]]; then
  if grep -rq "http://" .env.production 2>/dev/null | grep -v "localhost"; then
    echo "ERROR: HTTP (not HTTPS) URLs in production config"
    ERRORS+=("Use HTTPS for all production URLs")
  fi
fi

# Check admin routes protection
if grep -rq "/admin" backend/src/routes; then
  if grep -rq "requireAdmin\|isAdmin\|role.*admin" backend/src; then
    echo "OK: Admin routes appear protected"
  else
    echo "WARNING: Admin routes may lack role protection"
    WARNINGS+=("Verify admin routes require admin role")
  fi
fi
```

---

## Summary Report

```bash
echo ""
echo "=============================================="
echo "        DEPLOYMENT VERIFICATION REPORT        "
echo "=============================================="
echo ""
echo "Project: ${PROJECT}"
echo "Environment: ${ENVIRONMENT}"
echo "Timestamp: $(date -Iseconds)"
echo ""

# Count issues
ERROR_COUNT=${#ERRORS[@]}
WARNING_COUNT=${#WARNINGS[@]}

if [[ ${ERROR_COUNT} -eq 0 ]] && [[ ${WARNING_COUNT} -eq 0 ]]; then
  echo "✅ ALL CHECKS PASSED"
  echo ""
  echo "Ready to deploy with: /deploy ${ENVIRONMENT}"
  exit 0
fi

if [[ ${ERROR_COUNT} -gt 0 ]]; then
  echo "❌ ERRORS (${ERROR_COUNT}) - Must fix before deployment:"
  for err in "${ERRORS[@]}"; do
    echo "  - ${err}"
  done
  echo ""
fi

if [[ ${WARNING_COUNT} -gt 0 ]]; then
  echo "⚠️  WARNINGS (${WARNING_COUNT}) - Review recommended:"
  for warn in "${WARNINGS[@]}"; do
    echo "  - ${warn}"
  done
  echo ""
fi

if [[ ${ERROR_COUNT} -gt 0 ]]; then
  echo "RESULT: ❌ NOT READY FOR DEPLOYMENT"
  echo "Fix errors above before running /deploy"
  exit 1
else
  echo "RESULT: ⚠️  READY WITH WARNINGS"
  echo "Review warnings, then deploy with: /deploy ${ENVIRONMENT}"
  exit 0
fi
```

---

## Auto-Fix Mode (--fix)

When `--fix` is specified, attempt to fix common issues:

```bash
if [[ "${FIX_MODE}" == "true" ]]; then
  echo "=== Auto-Fix Mode ==="

  # Add missing items to .gitignore
  for item in ".env" ".env.local" ".env.production"; do
    if ! grep -q "^${item}$" .gitignore 2>/dev/null; then
      echo "${item}" >> .gitignore
      echo "Fixed: Added ${item} to .gitignore"
    fi
  done

  # Create missing .env files from examples
  if [[ ! -f ".env.${ENVIRONMENT}" ]] && [[ -f ".env.example" ]]; then
    cp .env.example .env.${ENVIRONMENT}
    echo "Fixed: Created .env.${ENVIRONMENT} from .env.example"
    echo "ACTION REQUIRED: Edit .env.${ENVIRONMENT} with correct values"
  fi

  # Create missing directories
  for dir in "backend/dist" "dist"; do
    if [[ ! -d "${dir}" ]]; then
      mkdir -p "${dir}"
      echo "Fixed: Created ${dir}/"
    fi
  done
fi
```

---

## Checklist Output

For manual review, generate a checklist:

```markdown
# Pre-Deployment Checklist: ${PROJECT} -> ${ENVIRONMENT}

## Docker
- [ ] docker-compose.yml valid
- [ ] All required services defined
- [ ] Healthchecks configured
- [ ] Volume mounts correct

## Environment
- [ ] .env.${ENVIRONMENT} exists
- [ ] All required vars set
- [ ] No localhost in production
- [ ] Secrets not in git

## Frontend
- [ ] VITE_API_URL correct for ${ENVIRONMENT}
- [ ] Build succeeds
- [ ] Base path configured

## Backend
- [ ] DATABASE_URL correct
- [ ] CORS configured properly
- [ ] Port bindings match

## Network
- [ ] No port conflicts
- [ ] Frontend -> Backend path clear
- [ ] Nginx proxy configured

## DNS/SSL
- [ ] DNS records exist
- [ ] SSL certificate valid
- [ ] Cloudflare Access configured

## Security
- [ ] No hardcoded secrets
- [ ] .gitignore complete
- [ ] Auth middleware in place
- [ ] Admin routes protected
```
