# Vault Integration Guide

The MCP Broker supports multi-layer secret resolution with optional HashiCorp Vault integration on your NAS.

## Secret Resolution Layers

Secrets are resolved in the following order:

1. **.env file** (workspace/local overrides)
2. **Process environment** (system-wide or session variables)
3. **Vault on NAS** (optional, requires configuration)

If Vault is unreachable or disabled, the broker continues gracefully using only env/.env.

## Configuration

### Enable Vault

Set these environment variables (in `.env` or process environment):

```bash
VAULT_ENABLED=true
VAULT_HOST=192.168.1.100
VAULT_PORT=8200
VAULT_TOKEN=your-vault-token
VAULT_MOUNT_PATH=secret
VAULT_NAMESPACE=
```

### Network Detection

The broker can automatically enable/disable Vault based on your network location:

```bash
# Enable Vault only when on home network
VAULT_PREFERRED_CIDR=192.168.1.0/24

# Or explicitly specify host (bypasses network check)
VAULT_EXPLICIT_HOST=vault.local
```

**How it works:**
- If `VAULT_EXPLICIT_HOST` is set, Vault is always used (if enabled)
- If `VAULT_PREFERRED_CIDR` is set, Vault is only used when your local IP is in that CIDR range
- If neither is set and `VAULT_ENABLED=true`, Vault will be attempted without network checks

## Secret Syntax

### Environment Variables

Use `${env:KEY}` to reference environment variables:

```json
{
  "env": {
    "DEBUG": "${env:DEBUG}",
    "BASE_URL": "${env:API_BASE_URL}"
  }
}
```

### Vault Secrets

Use `${vault:PATH}` to reference Vault secrets:

```json
{
  "env": {
    "GITHUB_TOKEN": "${vault:mcp/github/token}",
    "API_KEY": "${vault:mcp/api/key}"
  }
}
```

### Mixed Secrets

You can mix both types:

```json
{
  "env": {
    "API_KEY": "${vault:mcp/api/key}",
    "DEBUG": "${env:DEBUG}",
    "BASE_URL": "${env:BASE_URL}"
  }
}
```

## Vault Setup

### 1. Create Vault Secrets

```bash
# Using Vault CLI
vault kv put secret/mcp/github token=ghp_xxxxxxxxxxxx
vault kv put secret/mcp/api key=sk-xxxxxxxxxxxx

# Or via Vault UI
# Navigate to secret/mcp and create key-value pairs
```

### 2. Configure Broker

Create `.env` file:

```bash
VAULT_ENABLED=true
VAULT_HOST=192.168.1.100
VAULT_PORT=8200
VAULT_TOKEN=your-vault-token
VAULT_MOUNT_PATH=secret
VAULT_PREFERRED_CIDR=192.168.1.0/24
```

### 3. Update Server Config

In `servers.config.json`:

```json
{
  "servers": [
    {
      "id": "github",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${vault:mcp/github/token}"
      },
      "startMode": "lazy"
    }
  ]
}
```

## Vault Path Structure

The broker expects secrets at:

```
{VAULT_MOUNT_PATH}/data/{PATH}
```

For example, with default mount path `secret`:
- `${vault:mcp/github/token}` → `secret/data/mcp/github`
- `${vault:credentials/api}` → `secret/data/credentials/api`

## Behavior

### When Vault is Enabled and Available

- Secrets starting with `${vault:` are fetched from Vault
- Secrets starting with `${env:` are fetched from environment
- Results are cached for the session (no repeated network calls)
- Secret values are never logged

### When Vault is Unreachable

```
[Vault] Failed to read mcp/github/token: connection timeout
```

The broker logs a warning and continues with empty string for that secret.

### When Vault is Disabled

No Vault initialization occurs; only `${env:KEY}` expansion works.

## Security Notes

1. **Never commit `.env` with secrets** - It's in `.gitignore` by default
2. **Use Vault tokens with appropriate policies** - Limit access to only needed paths
3. **Rotate Vault tokens regularly** - Follow your security policy
4. **Monitor Vault access logs** - Track which services access which secrets
5. **Use network segmentation** - Keep Vault on a trusted network segment

## Testing

### Test Environment Resolution

```bash
# Set a test variable
export TEST_VAR=hello

# Create test config
echo '{"servers":[{"id":"test","transport":"stdio","command":"echo","args":["${env:TEST_VAR}"],"env":{},"startMode":"lazy"}]}' > servers.config.json

# Start broker and check logs
npm run start:stdio
```

### Test Vault Resolution

```bash
# Create a test secret in Vault
vault kv put secret/test/key value=secret-value

# Create test config
echo '{"servers":[{"id":"test","transport":"stdio","command":"echo","args":["${vault:test/key}"],"env":{},"startMode":"lazy"}]}' > servers.config.json

# Start broker with Vault enabled
VAULT_ENABLED=true VAULT_HOST=192.168.1.100 VAULT_TOKEN=your-token npm run start:stdio
```

## Troubleshooting

### Vault Not Initializing

Check these conditions:
1. `VAULT_ENABLED=true` is set
2. `VAULT_HOST` is set
3. `VAULT_TOKEN` is set
4. Network check passes (if `VAULT_PREFERRED_CIDR` is set)

### Secrets Not Resolving

1. Check Vault path: `{mount}/data/{path}`
2. Verify token has read permissions
3. Check broker logs for detailed error messages
4. Test Vault access directly: `vault kv get secret/mcp/github`

### Network Detection Not Working

1. Verify your local IP: `ifconfig` or `ip addr`
2. Check CIDR range includes your IP
3. Set `VAULT_EXPLICIT_HOST` to bypass network detection

## Example: Complete Setup

**Vault secrets:**
```bash
vault kv put secret/mcp/github token=ghp_xxxxxxxxxxxx
vault kv put secret/mcp/salesforce token=sf_xxxxxxxxxxxx
vault kv put secret/mcp/openai api_key=sk-xxxxxxxxxxxx
```

**.env file:**
```bash
VAULT_ENABLED=true
VAULT_HOST=192.168.1.100
VAULT_PORT=8200
VAULT_TOKEN=hvs.xxxxxxxxx
VAULT_MOUNT_PATH=secret
VAULT_PREFERRED_CIDR=192.168.1.0/24

DEBUG=false
LOG_LEVEL=info
```

**servers.config.json:**
```json
{
  "servers": [
    {
      "id": "github",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${vault:mcp/github/token}"
      },
      "startMode": "lazy"
    },
    {
      "id": "openai",
      "transport": "http",
      "url": "http://localhost:8080/mcp",
      "env": {
        "OPENAI_API_KEY": "${vault:mcp/openai/api_key}",
        "DEBUG": "${env:DEBUG}"
      },
      "startMode": "lazy"
    }
  ]
}
```

With this setup:
- `GITHUB_TOKEN` comes from Vault at `secret/data/mcp/github`
- `OPENAI_API_KEY` comes from Vault at `secret/data/mcp/openai`
- `DEBUG` comes from .env file
- Vault is only used when on the 192.168.1.0/24 network
- If Vault is unavailable, the broker continues with empty strings for vault secrets
