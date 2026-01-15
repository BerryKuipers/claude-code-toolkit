# Deploy Command

**Arguments:** [environment] [--project=name] [--dry-run] [--skip-backup] [--rollback]

**Success Criteria:** Project deployed to target environment with all health checks passing

**Description:** Deploy registered projects to staging or production environments via SSH MCP and Docker. Reads configuration from `deployments.registry.json`.

---

## Quick Reference

```bash
/deploy                              # Interactive: select project + environment
/deploy staging                      # Deploy current project to staging
/deploy production                   # Deploy to production (requires staging verification)
/deploy status                       # Show deployment status across all projects
/deploy rollback                     # Rollback last deployment
/deploy --project=tribevibe staging  # Deploy specific project
/deploy --dry-run production         # Preview deployment without executing
```

---

## Prerequisites

Before deploying, ensure:
1. SSH MCP is configured for target VPS (passphrase-free keys)
2. Docker + docker-compose installed on VPS
3. Project registered in `deployments.registry.json`
4. GitHub Actions workflow exists (if using CI-based deployment)

---

## Workflow

### Step 1: Load Project Configuration

```bash
# Read deployment registry
REGISTRY=".claude-toolkit/.claude/skills/infrastructure/deployments.registry.json"

# Detect current project from git remote
PROJECT=$(basename -s .git $(git remote get-url origin 2>/dev/null) | tr '[:upper:]' '[:lower:]')

# Or use explicit --project argument
if [[ -n "${PROJECT_ARG}" ]]; then
  PROJECT="${PROJECT_ARG}"
fi

# Load project config from registry
# Extract: host, user, sshKeyName, dockerCompose, domain, services
```

### Step 2: Pre-Deployment Checks

```bash
# Verify VPS connectivity
SSH_KEY="C:/Users/BerryLocal/.ssh/${SSH_KEY_NAME}"
ssh -i ${SSH_KEY} -o ConnectTimeout=5 ${USER}@${HOST} "echo 'VPS accessible'" || exit 1

# Verify Docker running
ssh -i ${SSH_KEY} ${USER}@${HOST} "docker info > /dev/null 2>&1" || exit 1

# For production: verify staging was deployed successfully first
if [[ "${ENVIRONMENT}" == "production" ]]; then
  echo "Verifying staging health before production deploy..."
  curl -f https://${STAGING_API_DOMAIN}/health || {
    echo "ERROR: Staging health check failed. Deploy to staging first."
    exit 1
  }
fi
```

### Step 3: Backup Database (unless --skip-backup)

```bash
if [[ "${SKIP_BACKUP}" != "true" ]]; then
  echo "Creating database backup..."
  ssh -i ${SSH_KEY} ${USER}@${HOST} << 'BACKUP'
    BACKUP_FILE="/backup/${PROJECT}_$(date +%Y%m%d_%H%M%S).sql"
    docker exec ${DB_CONTAINER} pg_dump -U postgres ${DB_NAME} > ${BACKUP_FILE}
    echo "Backup created: ${BACKUP_FILE}"
BACKUP
fi
```

### Step 4: Deploy via Docker Compose

```bash
echo "Deploying ${PROJECT} to ${ENVIRONMENT}..."

if [[ "${DRY_RUN}" == "true" ]]; then
  echo "[DRY RUN] Would execute:"
  echo "  cd ${DOCKER_COMPOSE_PATH}"
  echo "  docker compose pull"
  echo "  docker compose up -d --remove-orphans"
  exit 0
fi

ssh -i ${SSH_KEY} ${USER}@${HOST} << DEPLOY
  cd ${DOCKER_COMPOSE_PATH}

  # Pull latest images
  docker compose pull

  # Deploy with rolling restart
  docker compose up -d --remove-orphans

  # Wait for containers to start
  sleep 10

  # Show status
  docker compose ps
DEPLOY
```

### Step 5: Post-Deployment Verification

```bash
echo "Verifying deployment..."

# Health check
API_HEALTH=$(curl -sf https://${API_DOMAIN}/health)
if [[ $? -ne 0 ]]; then
  echo "ERROR: Health check failed!"
  echo "Consider running: /deploy rollback"
  exit 1
fi

# Check container status
ssh -i ${SSH_KEY} ${USER}@${HOST} "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep ${PROJECT}"

# Check for errors in logs
ERRORS=$(ssh -i ${SSH_KEY} ${USER}@${HOST} "docker logs ${API_CONTAINER} --tail 50 2>&1 | grep -i error | wc -l")
if [[ ${ERRORS} -gt 0 ]]; then
  echo "WARNING: ${ERRORS} errors found in recent logs"
  ssh -i ${SSH_KEY} ${USER}@${HOST} "docker logs ${API_CONTAINER} --tail 50 2>&1 | grep -i error"
fi

echo ""
echo "Deployment successful!"
echo "API: https://${API_DOMAIN}"
echo "Web: https://${DOMAIN}"
```

### Step 6: Rollback (if requested)

```bash
if [[ "${ROLLBACK}" == "true" ]]; then
  echo "Rolling back deployment..."

  ssh -i ${SSH_KEY} ${USER}@${HOST} << 'ROLLBACK'
    cd ${DOCKER_COMPOSE_PATH}
    docker compose down

    # Restore from previous image (if tagged)
    # Or: docker tag ${PROJECT}-api:previous ${PROJECT}-api:latest

    docker compose up -d
ROLLBACK

  echo "Rollback complete. Verify health manually."
fi
```

---

## Output Format

```markdown
# Deployment Report

**Project**: tribevibe
**Environment**: staging
**Timestamp**: 2025-01-15T17:00:00Z
**Status**: SUCCESS

## Services
| Service | Container | Status | Health |
|---------|-----------|--------|--------|
| API     | tribevibe-api-staging | Up 2m | 200 OK |
| Web     | tribevibe-web-staging | Up 2m | 200 OK |
| DB      | tribevibe-postgres | Up 5h | Connected |

## Health Checks
- API: https://api-staging.tribevibe.events/health - 200 OK (45ms)
- Web: https://staging.tribevibe.events - 200 OK (120ms)

## Actions Taken
1. Pre-flight checks passed
2. Database backup created: tribevibe_20250115_170000.sql
3. Pulled latest Docker images
4. Deployed via docker compose up -d
5. Health checks verified

## Monitoring
- Seq Logs: https://seq.tribevibe.events
- Next: Monitor for 10-15 minutes, run smoke tests
```

---

## Safety Rules

- NEVER deploy to production without staging verification
- ALWAYS backup database before deployment (unless --skip-backup)
- ALWAYS verify health checks after deployment
- If health check fails, consider immediate rollback
- Monitor logs for 10-15 minutes post-deployment
