# Agent Testing Templates

**Autonomous authentication token management for QA and UI testing agents.**

## Overview

This folder contains templates that enable **fully autonomous agent testing** without manual token management. Agents (qa-triage, ui-frontend-agent) can discover and use these tools automatically.

## Files

### 1. `get-test-tokens.mjs`

**Autonomous token generation script** that:
- Logs in using test credentials from `.env.local`
- Gets fresh auth tokens (accessToken, CSRF, cookies)
- Saves to `.test-tokens.json` for agents to consume
- Supports both human-readable and machine-readable output

**Features**:
- ✅ ES Module (import statements)
- ✅ Reads credentials from `.env.local` (security)
- ✅ Validates required env vars
- ✅ Saves tokens with expiry timestamp
- ✅ Works with any backend API

### 2. `env.local.example`

**Environment template** showing required variables:
```
TEST_USER_EMAIL=your_test_user@example.com
TEST_USER_PASSWORD=your_password_here
```

## Installation (For New Projects)

### Step 1: Copy Templates

```bash
# From your project root
cp .claude-toolkit/templates/testing/get-test-tokens.mjs scripts/
cp .claude-toolkit/templates/testing/env.local.example .env.local.example
```

### Step 2: Configure Environment

```bash
# Copy and fill in your test credentials
cp .env.local.example .env.local

# Edit .env.local with your test user:
# TEST_USER_EMAIL=tester@yourapp.com
# TEST_USER_PASSWORD=your_test_password
```

### Step 3: Add npm Script

Add to your `package.json`:
```json
{
  "scripts": {
    "get-tokens": "node scripts/get-test-tokens.mjs"
  }
}
```

### Step 4: Update .gitignore

Ensure these are git-ignored:
```
# .gitignore
.env.local
.test-tokens.json
```

### Step 5: Customize API URL (Optional)

Edit `scripts/get-test-tokens.mjs` if your API uses a different:
- Port (default: 3000)
- Login endpoint (default: `/api/auth/login`)
- Response structure

## Usage

### For Developers

```bash
# Get fresh tokens
npm run get-tokens

# Tokens saved to .test-tokens.json
cat .test-tokens.json
```

### For Agents (Automatic Discovery)

Agents will automatically:
1. Detect `"get-tokens"` script in `package.json`
2. Run `npm run get-tokens`
3. Read tokens from `.test-tokens.json`
4. Use them for authenticated API calls

**No manual intervention needed!**

## Token Structure

`.test-tokens.json`:
```json
{
  "accessToken": "eyJhbGci...",
  "refreshToken": "eyJhbGci...",
  "csrfToken": "Lxg6TmRJ...",
  "userId": "019a5d59...",
  "email": "tester@example.com",
  "timestamp": "2025-11-10T07:00:00.000Z",
  "expiresAt": "2025-11-10T07:15:00.000Z"
}
```

## Agent Integration

### QA Triage Agent

```bash
# Agent automatically runs:
npm run get-tokens

# Then reads tokens:
ACCESS_TOKEN=$(jq -r '.accessToken' .test-tokens.json)
CSRF_TOKEN=$(jq -r '.csrfToken' .test-tokens.json)

# Uses in API calls:
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
     -H "x-csrf-token: $CSRF_TOKEN" \
     http://localhost:3000/api/...
```

### UI Frontend Agent

```javascript
// Agent reads tokens
const tokens = JSON.parse(fs.readFileSync('.test-tokens.json', 'utf8'));

// Sets auth in browser
await page.evaluate((tokens) => {
  localStorage.setItem('accessToken', tokens.accessToken);
  localStorage.setItem('refreshToken', tokens.refreshToken);
}, tokens);

// Adds cookies
await page.context().addCookies([
  { name: 'auth', value: tokens.accessToken, domain: 'localhost', path: '/' },
  { name: 'csrf', value: tokens.csrfToken, domain: 'localhost', path: '/' },
]);
```

## Security

- ✅ Credentials in `.env.local` (git-ignored)
- ✅ Tokens in `.test-tokens.json` (git-ignored)
- ✅ `.env.local.example` safe to commit (no secrets)
- ✅ Script validates env vars before running
- ❌ Never commit `.env.local` or `.test-tokens.json`

## Customization

### Different API URL

```javascript
// In get-test-tokens.mjs, change:
const BASE_URL = process.env.VITE_API_URL || 'http://localhost:3000';
```

### Different Login Endpoint

```javascript
// Change the endpoint:
const loginResponse = await post(`${BASE_URL}/api/auth/login`, {
  // ...
});
```

### Different Response Format

```javascript
// Customize token extraction:
const { accessToken, refreshToken, user, csrfToken } = loginResponse.data;
```

## Troubleshooting

**Script fails: "Missing required environment variables"**
→ Add `TEST_USER_EMAIL` and `TEST_USER_PASSWORD` to `.env.local`

**Login returns 401**
→ Check test user credentials are correct in `.env.local`

**Tokens expire quickly**
→ Token expiry is set in backend (default: 15 minutes)
→ Agents should call `npm run get-tokens` before each test session

**Can't find jq command**
→ Install jq: `winget install jqlang.jq` (Windows) or `brew install jq` (Mac)

## Examples

See [AGENT_TESTING_GUIDE.md](../../docs/AGENT_TESTING_GUIDE.md) for complete agent testing workflows.

---

**This template enables fully autonomous agent testing across all projects!**
