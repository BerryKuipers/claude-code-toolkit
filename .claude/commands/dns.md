# DNS & Cloudflare Command

**Arguments:** [action] [subdomain] [type] [value] [--domain=name] [--proxied]

**Success Criteria:** DNS operation completed with verification

**Description:** Manage Cloudflare DNS records, tunnels, Access policies, SSL certificates, and CDN caching for registered project domains.

---

## Quick Reference

```bash
/dns                           # Show DNS summary for current project
/dns list                      # List all DNS records for project domain
/dns add staging A 1.2.3.4     # Add A record
/dns add api CNAME target.com  # Add CNAME record
/dns update staging A 5.6.7.8  # Update existing record
/dns delete staging A          # Delete record
/dns ssl-status                # Check SSL certificate status
/dns purge                     # Purge Cloudflare cache for domain
/dns purge /api/v1/*           # Purge specific paths
/dns tunnel status             # Check Cloudflare Tunnel status
/dns access list               # List Access applications
```

---

## Prerequisites

- `wrangler` CLI installed and authenticated
- `cloudflared` CLI for tunnel management
- Cloudflare API token with DNS edit permissions
- Domain registered in `deployments.registry.json`

---

## Workflow

### Step 1: Load Domain Configuration

```bash
# Read deployment registry
REGISTRY=".claude-toolkit/.claude/skills/infrastructure/deployments.registry.json"

# Get domain from current project or --domain argument
PROJECT=$(basename -s .git $(git remote get-url origin 2>/dev/null))
DOMAIN=$(jq -r ".projects.${PROJECT}.environments.production.domain" ${REGISTRY})
```

### Step 2: Execute DNS Action

#### List Records

```bash
echo "=== DNS Records for ${DOMAIN} ==="
wrangler dns list ${DOMAIN}
```

#### Add Record

```bash
SUBDOMAIN="${2}"
TYPE="${3}"
VALUE="${4}"
PROXIED="${PROXIED:-true}"

echo "Adding ${TYPE} record: ${SUBDOMAIN}.${DOMAIN} -> ${VALUE}"

if [[ "${PROXIED}" == "true" ]]; then
  wrangler dns create ${DOMAIN} ${TYPE} ${SUBDOMAIN} --content ${VALUE} --proxied
else
  wrangler dns create ${DOMAIN} ${TYPE} ${SUBDOMAIN} --content ${VALUE}
fi

# Verify
echo "Verifying..."
dig +short ${SUBDOMAIN}.${DOMAIN}
```

#### Update Record

```bash
SUBDOMAIN="${2}"
TYPE="${3}"
VALUE="${4}"

echo "Updating ${TYPE} record: ${SUBDOMAIN}.${DOMAIN} -> ${VALUE}"
wrangler dns update ${DOMAIN} ${TYPE} ${SUBDOMAIN} --content ${VALUE}

# Verify
echo "Verifying..."
dig +short ${SUBDOMAIN}.${DOMAIN}
```

#### Delete Record

```bash
SUBDOMAIN="${2}"
TYPE="${3}"

echo "Deleting ${TYPE} record: ${SUBDOMAIN}.${DOMAIN}"
read -p "Are you sure? (y/N) " CONFIRM
if [[ "${CONFIRM}" == "y" ]]; then
  wrangler dns delete ${DOMAIN} ${TYPE} ${SUBDOMAIN}
  echo "Deleted"
else
  echo "Cancelled"
fi
```

#### SSL Status

```bash
echo "=== SSL Certificate Status ==="

for ENV in production staging; do
  DOMAIN=$(jq -r ".projects.${PROJECT}.environments.${ENV}.domain" ${REGISTRY})
  if [[ "${DOMAIN}" != "null" ]]; then
    echo ""
    echo "--- ${ENV}: ${DOMAIN} ---"
    echo | openssl s_client -servername ${DOMAIN} -connect ${DOMAIN}:443 2>/dev/null | \
      openssl x509 -noout -dates -issuer
  fi
done
```

#### Purge Cache

```bash
PATH_PATTERN="${2:-*}"

if [[ "${PATH_PATTERN}" == "*" ]]; then
  echo "Purging entire cache for ${DOMAIN}..."
  wrangler purge --everything
else
  echo "Purging cache for: https://${DOMAIN}${PATH_PATTERN}"
  wrangler purge "https://${DOMAIN}${PATH_PATTERN}"
fi

echo "Cache purged"
```

#### Tunnel Status

```bash
echo "=== Cloudflare Tunnel Status ==="

# List tunnels
cloudflared tunnel list

# Check tunnel service on VPS
echo ""
echo "--- Tunnel Service on VPS ---"
ssh -i ${SSH_KEY} ${USER}@${HOST} "sudo systemctl status cloudflared --no-pager | head -15"
```

#### Access List

```bash
echo "=== Cloudflare Access Applications ==="
wrangler access list-apps

echo ""
echo "To manage Access applications, use the Cloudflare dashboard:"
echo "https://dash.cloudflare.com/${CF_ACCOUNT_ID}/access/apps"
```

---

## Common Tasks

### Setup New Subdomain

```bash
# 1. Add DNS record
/dns add ${SUBDOMAIN} A ${VPS_IP} --proxied

# 2. Configure nginx on VPS
ssh ${USER}@${HOST} << EOF
cat > /etc/nginx/sites-available/${SUBDOMAIN}.conf << 'NGINX'
server {
    listen 443 ssl;
    server_name ${SUBDOMAIN}.${DOMAIN};

    location / {
        proxy_pass http://localhost:${PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX
ln -sf /etc/nginx/sites-available/${SUBDOMAIN}.conf /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
EOF

# 3. Verify
curl -I https://${SUBDOMAIN}.${DOMAIN}
```

### Add Zero-Trust Protection

```bash
# 1. Create Access application (via dashboard)
echo "Create Access app at: https://dash.cloudflare.com/access/apps"
echo "- Application name: ${SERVICE_NAME}"
echo "- Domain: ${SUBDOMAIN}.${DOMAIN}"
echo "- Session duration: 24h"
echo "- Add allowed emails/groups"

# 2. Update nginx for CORS (if needed)
# add_header Access-Control-Allow-Credentials "true" always;
```

---

## Output Format

```markdown
# DNS Report

**Domain**: tribevibe.events
**Cloudflare**: Proxied (Orange Cloud)

## DNS Records
| Type | Name | Value | Proxied | TTL |
|------|------|-------|---------|-----|
| A | @ | 148.230.71.1 | Yes | Auto |
| A | staging | 148.230.71.1 | Yes | Auto |
| CNAME | api | @ | Yes | Auto |
| CNAME | api-staging | staging | Yes | Auto |
| MX | @ | mail.example.com | No | 3600 |

## SSL Certificates
- tribevibe.events: Valid until 2025-06-15 (Cloudflare Universal)
- staging.tribevibe.events: Valid until 2025-06-15 (Cloudflare Universal)

## Access Applications
- Seq Logs (seq.tribevibe.events) - Email auth required
```

---

## Safety Rules

- NEVER delete production DNS records without backup plan
- ALWAYS verify DNS changes propagate (use `dig` or `nslookup`)
- DNS propagation can take up to 48 hours (usually minutes with Cloudflare)
- Keep Cloudflare proxy enabled for DDoS protection
- Document all DNS changes in project changelog
