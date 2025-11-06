import crypto from 'crypto';
import http from 'http';
import { URL } from 'url';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import type { OAuthConfig } from './config.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface OAuthTokens {
  access_token: string;
  token_type: string;
  expires_in?: number;
  refresh_token?: string;
  expires_at?: number;
}

interface OAuthServerMetadata {
  authorization_endpoint?: string;
  token_endpoint?: string;
  registration_endpoint?: string;
}

interface DynamicClientRegistration {
  client_id: string;
  client_secret?: string;
  client_id_issued_at?: number;
  client_secret_expires_at?: number;
}

const tokensCache = new Map<string, OAuthTokens>();
const TOKENS_DIR = join(__dirname, '..', '.oauth-tokens');

// Ensure tokens directory exists
function ensureTokensDir() {
  if (!existsSync(TOKENS_DIR)) {
    mkdirSync(TOKENS_DIR, { recursive: true });
  }
}

// Generate PKCE parameters
function generatePKCE(): { verifier: string; challenge: string } {
  const verifier = crypto.randomBytes(32).toString('base64url');
  const challenge = crypto.createHash('sha256').update(verifier).digest('base64url');
  return { verifier, challenge };
}

// Generate random state parameter
function generateState(): string {
  return crypto.randomBytes(16).toString('hex');
}

// Discover OAuth server metadata
async function discoverMetadata(baseUrl: string): Promise<OAuthServerMetadata | null> {
  try {
    const wellKnownUrl = new URL('/.well-known/oauth-authorization-server', baseUrl).href;
    const response = await fetch(wellKnownUrl);

    if (response.ok) {
      return await response.json();
    }
  } catch (error) {
    console.error(`Failed to discover OAuth metadata: ${error}`);
  }

  return null;
}

// Load client registration from disk
function loadClientRegistration(serverId: string): DynamicClientRegistration | null {
  ensureTokensDir();
  const clientPath = join(TOKENS_DIR, `${serverId}-client.json`);

  if (existsSync(clientPath)) {
    try {
      const data = readFileSync(clientPath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      console.error(`Failed to load client registration for ${serverId}: ${error}`);
    }
  }

  return null;
}

// Save client registration to disk
function saveClientRegistration(serverId: string, registration: DynamicClientRegistration): void {
  ensureTokensDir();
  const clientPath = join(TOKENS_DIR, `${serverId}-client.json`);

  try {
    writeFileSync(clientPath, JSON.stringify(registration, null, 2), 'utf-8');
  } catch (error) {
    console.error(`Failed to save client registration for ${serverId}: ${error}`);
  }
}

// Perform dynamic client registration (RFC 7591)
async function registerClient(
  registrationUrl: string,
  redirectUri: string
): Promise<DynamicClientRegistration> {
  const registrationRequest = {
    client_name: 'MCP Broker',
    redirect_uris: [redirectUri],
    grant_types: ['authorization_code', 'refresh_token'],
    response_types: ['code'],
    token_endpoint_auth_method: 'none', // Public client
  };

  const response = await fetch(registrationUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(registrationRequest),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Dynamic client registration failed: ${response.status} ${error}`);
  }

  return await response.json();
}

// Load tokens from disk
function loadTokensFromDisk(serverId: string): OAuthTokens | null {
  ensureTokensDir();
  const tokenPath = join(TOKENS_DIR, `${serverId}.json`);

  if (existsSync(tokenPath)) {
    try {
      const data = readFileSync(tokenPath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      console.error(`Failed to load tokens for ${serverId}: ${error}`);
    }
  }

  return null;
}

// Save tokens to disk
function saveTokensToDisk(serverId: string, tokens: OAuthTokens): void {
  ensureTokensDir();
  const tokenPath = join(TOKENS_DIR, `${serverId}.json`);

  try {
    writeFileSync(tokenPath, JSON.stringify(tokens, null, 2), 'utf-8');
  } catch (error) {
    console.error(`Failed to save tokens for ${serverId}: ${error}`);
  }
}

// Check if token is expired
function isTokenExpired(tokens: OAuthTokens): boolean {
  if (!tokens.expires_at) {
    return false; // No expiry info, assume valid
  }

  // Add 5 minute buffer
  return Date.now() + (5 * 60 * 1000) >= tokens.expires_at;
}

// Exchange authorization code for tokens
async function exchangeCodeForTokens(
  tokenUrl: string,
  code: string,
  redirectUri: string,
  codeVerifier: string,
  clientId?: string,
  clientSecret?: string
): Promise<OAuthTokens> {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: redirectUri,
    code_verifier: codeVerifier,
  });

  if (clientId) {
    body.append('client_id', clientId);
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/x-www-form-urlencoded',
  };

  // Add Basic Auth if client secret provided
  if (clientId && clientSecret) {
    const auth = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');
    headers['Authorization'] = `Basic ${auth}`;
  }

  const response = await fetch(tokenUrl, {
    method: 'POST',
    headers,
    body: body.toString(),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Token exchange failed: ${response.status} ${error}`);
  }

  const tokens: OAuthTokens = await response.json();

  // Calculate expiry timestamp
  if (tokens.expires_in) {
    tokens.expires_at = Date.now() + (tokens.expires_in * 1000);
  }

  return tokens;
}

// Refresh access token
async function refreshAccessToken(
  tokenUrl: string,
  refreshToken: string,
  clientId?: string,
  clientSecret?: string
): Promise<OAuthTokens> {
  const body = new URLSearchParams({
    grant_type: 'refresh_token',
    refresh_token: refreshToken,
  });

  if (clientId) {
    body.append('client_id', clientId);
  }

  const headers: HeadersInit = {
    'Content-Type': 'application/x-www-form-urlencoded',
  };

  if (clientId && clientSecret) {
    const auth = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');
    headers['Authorization'] = `Basic ${auth}`;
  }

  const response = await fetch(tokenUrl, {
    method: 'POST',
    headers,
    body: body.toString(),
  });

  if (!response.ok) {
    throw new Error(`Token refresh failed: ${response.status}`);
  }

  const tokens: OAuthTokens = await response.json();

  if (tokens.expires_in) {
    tokens.expires_at = Date.now() + (tokens.expires_in * 1000);
  }

  return tokens;
}

// Start callback server and wait for authorization code
async function waitForCallback(
  redirectUri: string,
  state: string
): Promise<string> {
  return new Promise((resolve, reject) => {
    const url = new URL(redirectUri);
    const port = parseInt(url.port) || 45454;

    const server = http.createServer((req, res) => {
      if (!req.url) {
        return;
      }

      const reqUrl = new URL(req.url, `http://localhost:${port}`);

      if (reqUrl.pathname === url.pathname) {
        const code = reqUrl.searchParams.get('code');
        const returnedState = reqUrl.searchParams.get('state');
        const error = reqUrl.searchParams.get('error');

        if (error) {
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end('<html><body><h1>Authorization Failed</h1><p>You can close this window.</p></body></html>');
          server.close();
          reject(new Error(`OAuth error: ${error}`));
          return;
        }

        if (!code || returnedState !== state) {
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end('<html><body><h1>Invalid Request</h1><p>You can close this window.</p></body></html>');
          server.close();
          reject(new Error('Invalid authorization response'));
          return;
        }

        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end('<html><body><h1>Authorization Successful!</h1><p>You can close this window and return to Claude Code.</p></body></html>');
        server.close();
        resolve(code);
      }
    });

    server.listen(port, () => {
      console.log(`OAuth callback server listening on ${redirectUri}`);
    });

    // Timeout after 5 minutes
    setTimeout(() => {
      server.close();
      reject(new Error('OAuth authorization timeout'));
    }, 5 * 60 * 1000);
  });
}

// Perform full OAuth flow
export async function performOAuthFlow(
  serverId: string,
  serverUrl: string,
  config: OAuthConfig
): Promise<OAuthTokens> {
  console.log(`Starting OAuth flow for server: ${serverId}`);

  // Try to discover endpoints first
  const metadata = await discoverMetadata(serverUrl);

  const authorizationUrl = config.authorizationUrl || metadata?.authorization_endpoint;
  const tokenUrl = config.tokenUrl || metadata?.token_endpoint;

  if (!authorizationUrl || !tokenUrl) {
    throw new Error(`OAuth endpoints not configured and discovery failed for ${serverId}`);
  }

  const redirectUri = config.redirectUri || 'http://localhost:45454/oauth/callback';

  // Get or register client_id
  let clientId = config.clientId;
  let clientSecret = config.clientSecret;

  if (!clientId) {
    // Try to load saved client registration
    let registration = loadClientRegistration(serverId);

    if (!registration && metadata?.registration_endpoint) {
      // Attempt dynamic client registration
      console.log(`Performing dynamic client registration for ${serverId}...`);
      try {
        registration = await registerClient(metadata.registration_endpoint, redirectUri);
        saveClientRegistration(serverId, registration);
        console.log(`✓ Dynamic client registration successful for ${serverId}`);
      } catch (error) {
        console.error(`Dynamic client registration failed: ${error}`);
        throw new Error(`OAuth requires client_id but dynamic registration failed for ${serverId}`);
      }
    }

    if (registration) {
      clientId = registration.client_id;
      clientSecret = registration.client_secret;
    } else {
      throw new Error(`OAuth requires client_id but none configured and dynamic registration not available for ${serverId}`);
    }
  }

  // Generate PKCE and state
  const { verifier, challenge } = generatePKCE();
  const state = generateState();

  // Build authorization URL
  const authUrl = new URL(authorizationUrl);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('code_challenge', challenge);
  authUrl.searchParams.set('code_challenge_method', 'S256');
  authUrl.searchParams.set('state', state);
  authUrl.searchParams.set('redirect_uri', redirectUri);
  authUrl.searchParams.set('client_id', clientId);

  if (config.scopes && config.scopes.length > 0) {
    authUrl.searchParams.set('scope', config.scopes.join(' '));
  }

  console.log(`\n🔐 Please authorize in your browser:\n${authUrl.href}\n`);

  // Try to open browser (platform-specific)
  const open = (await import('open')).default;
  await open(authUrl.href);

  // Wait for callback
  const code = await waitForCallback(redirectUri, state);

  // Exchange code for tokens
  const tokens = await exchangeCodeForTokens(
    tokenUrl,
    code,
    redirectUri,
    verifier,
    clientId,
    clientSecret
  );

  // Save tokens
  saveTokensToDisk(serverId, tokens);
  tokensCache.set(serverId, tokens);

  console.log(`✓ OAuth authorization successful for ${serverId}`);

  return tokens;
}

// Get or refresh OAuth token
export async function getOAuthToken(
  serverId: string,
  serverUrl: string,
  config: OAuthConfig
): Promise<string> {
  // Check memory cache first
  let tokens = tokensCache.get(serverId);

  // Load from disk if not in cache
  if (!tokens) {
    const loadedTokens = loadTokensFromDisk(serverId);
    if (loadedTokens) {
      tokens = loadedTokens;
      tokensCache.set(serverId, tokens);
    }
  }

  // If no tokens or expired, start OAuth flow
  if (!tokens || isTokenExpired(tokens)) {
    if (tokens?.refresh_token && config.tokenUrl) {
      try {
        tokens = await refreshAccessToken(
          config.tokenUrl,
          tokens.refresh_token,
          config.clientId,
          config.clientSecret
        );
        saveTokensToDisk(serverId, tokens);
        tokensCache.set(serverId, tokens);
      } catch (error) {
        console.error(`Token refresh failed, starting new OAuth flow: ${error}`);
        tokens = await performOAuthFlow(serverId, serverUrl, config);
      }
    } else {
      tokens = await performOAuthFlow(serverId, serverUrl, config);
    }
  }

  return tokens.access_token;
}
