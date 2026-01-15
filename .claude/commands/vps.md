# VPS Operations Command

**Arguments:** [action] [service] [--project=name] [--env=staging|production]

**Success Criteria:** VPS operation completed successfully with status report

**Description:** Direct VPS operations via SSH MCP. Manage Docker containers, view logs, execute commands, and troubleshoot services on registered VPS servers.

---

## Quick Reference

```bash
/vps                           # Show container status for current project
/vps status                    # Detailed status + resource usage
/vps logs api                  # View API service logs (tail -100)
/vps logs api --follow         # Stream logs live
/vps exec 'docker ps'          # Execute arbitrary command on VPS
/vps restart api               # Restart specific container
/vps health                    # Run health checks on all services
/vps resources                 # Show CPU, memory, disk usage
/vps backup                    # Backup database to NAS
/vps ssh                       # Open interactive SSH session info
```

---

## Workflow

### Step 1: Load Project Configuration

```bash
# Read deployment registry
REGISTRY=".claude-toolkit/.claude/skills/infrastructure/deployments.registry.json"

# Detect current project
PROJECT=$(basename -s .git $(git remote get-url origin 2>/dev/null) | tr '[:upper:]' '[:lower:]')

# Load VPS config: host, user, sshKeyName
SSH_KEY="C:/Users/BerryLocal/.ssh/${SSH_KEY_NAME}"
```

### Step 2: Execute Requested Action

#### Status (default)

```bash
echo "=== Container Status ==="
ssh -i ${SSH_KEY} ${USER}@${HOST} "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
```

#### Logs

```bash
SERVICE="${2:-api}"
CONTAINER="${PROJECT}-${SERVICE}-${ENVIRONMENT}"

if [[ "${FOLLOW}" == "true" ]]; then
  ssh -i ${SSH_KEY} ${USER}@${HOST} "docker logs ${CONTAINER} --tail 50 --follow"
else
  ssh -i ${SSH_KEY} ${USER}@${HOST} "docker logs ${CONTAINER} --tail 100"
fi
```

#### Restart

```bash
SERVICE="${2}"
CONTAINER="${PROJECT}-${SERVICE}-${ENVIRONMENT}"

echo "Restarting ${CONTAINER}..."
ssh -i ${SSH_KEY} ${USER}@${HOST} "docker compose -f ${COMPOSE_PATH} restart ${SERVICE}"

# Verify restart
sleep 5
ssh -i ${SSH_KEY} ${USER}@${HOST} "docker ps | grep ${CONTAINER}"
```

#### Health

```bash
echo "=== Health Checks ==="

# API health
API_STATUS=$(curl -sf -w "%{http_code}" https://${API_DOMAIN}/health -o /dev/null)
echo "API: https://${API_DOMAIN}/health - ${API_STATUS}"

# Web health
WEB_STATUS=$(curl -sf -w "%{http_code}" https://${DOMAIN} -o /dev/null)
echo "Web: https://${DOMAIN} - ${WEB_STATUS}"

# Container health
ssh -i ${SSH_KEY} ${USER}@${HOST} << 'HEALTH'
  echo ""
  echo "=== Container Health ==="
  docker ps --format '{{.Names}}: {{.Status}}'

  echo ""
  echo "=== Recent Errors (last 5m) ==="
  docker logs ${API_CONTAINER} --since 5m 2>&1 | grep -i error | tail -10 || echo "No errors"
HEALTH
```

#### Resources

```bash
echo "=== System Resources ==="
ssh -i ${SSH_KEY} ${USER}@${HOST} << 'RESOURCES'
  echo "--- Memory ---"
  free -h

  echo ""
  echo "--- Disk ---"
  df -h | grep -E '^/dev|Filesystem'

  echo ""
  echo "--- Load ---"
  uptime

  echo ""
  echo "--- Docker Stats ---"
  docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'
RESOURCES
```

#### Backup

```bash
echo "=== Database Backup ==="

ssh -i ${SSH_KEY} ${USER}@${HOST} << 'BACKUP'
  BACKUP_FILE="/backup/${PROJECT}_$(date +%Y%m%d_%H%M%S).sql"
  echo "Creating backup: ${BACKUP_FILE}"
  docker exec ${DB_CONTAINER} pg_dump -U postgres ${DB_NAME} > ${BACKUP_FILE}
  ls -lh ${BACKUP_FILE}
  echo "Backup complete"
BACKUP

# Optionally copy to NAS
echo "Copying to NAS..."
NAS_KEY="C:/Users/BerryLocal/.ssh/home_nas"
scp -i ${NAS_KEY} ${USER}@${HOST}:/backup/${PROJECT}_*.sql berry@10.0.0.23:/volume1/backups/
```

#### Exec

```bash
COMMAND="${2}"
echo "Executing on VPS: ${COMMAND}"
ssh -i ${SSH_KEY} ${USER}@${HOST} "${COMMAND}"
```

---

## Output Format

```markdown
# VPS Status Report

**Project**: tribevibe
**VPS**: 148.230.71.1 (Hostinger)
**Environment**: staging

## Containers
| Name | Status | CPU | Memory |
|------|--------|-----|--------|
| tribevibe-api-staging | Up 2 hours | 5% | 256MB/512MB |
| tribevibe-web-staging | Up 2 hours | 2% | 128MB/256MB |
| tribevibe-postgres | Up 5 days | 1% | 512MB/1GB |

## System Resources
- **CPU**: 15% (4 cores)
- **Memory**: 2.1GB / 4GB (52%)
- **Disk**: 15GB / 50GB (30%)
- **Uptime**: 15 days

## Health Endpoints
- API: 200 OK (45ms)
- Web: 200 OK (120ms)
```

---

## Safety Rules

- NEVER run `pkill node` - will terminate Claude Code
- NEVER run destructive commands without confirmation
- Use `docker compose restart` instead of killing processes
- Always check container status after restart
- Be careful with `exec` - verify command before running
