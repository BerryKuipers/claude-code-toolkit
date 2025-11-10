#!/usr/bin/env node
/**
 * Get Test Auth Tokens
 *
 * Helper script for agents to automatically login and get fresh auth tokens
 * for testing. Saves tokens to .test-tokens.json for agents to consume.
 *
 * Credentials are read from .env.local:
 *   TEST_USER_EMAIL=tester@wescobar.org
 *   TEST_USER_PASSWORD=xs2Testerwescobar99
 *
 * Usage:
 *   node scripts/get-test-tokens.cjs
 *   node scripts/get-test-tokens.cjs --output json  (for machine-readable output)
 */

import http from 'http';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load environment variables from .env.local
const envPath = join(__dirname, '..', '.env.local');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach((line) => {
    const match = line.match(/^([^=:#]+)=(.*)$/);
    if (match) {
      const key = match[1].trim();
      const value = match[2].trim().replace(/^['"]|['"]$/g, '');
      process.env[key] = value;
    }
  });
}

const BASE_URL = process.env.VITE_API_URL || 'http://localhost:3000';
const TEST_EMAIL = process.env.TEST_USER_EMAIL;
const TEST_PASSWORD = process.env.TEST_USER_PASSWORD;
const OUTPUT_FILE = '.test-tokens.json';

// Validate required env vars
if (!TEST_EMAIL || !TEST_PASSWORD) {
  console.error('❌ Error: Missing required environment variables');
  console.error('   Please add to .env.local:');
  console.error('   TEST_USER_EMAIL=tester@wescobar.org');
  console.error('   TEST_USER_PASSWORD=your_password_here');
  process.exit(1);
}

const args = process.argv.slice(2);
const outputJson = args.includes('--output') && args[args.indexOf('--output') + 1] === 'json';

/**
 * Make HTTP POST request
 */
function post(url, data) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const postData = JSON.stringify(data);

    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData),
      },
    };

    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => {
        body += chunk;
      });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(body);
          // Extract Set-Cookie header
          const cookies = res.headers['set-cookie'] || [];
          resolve({ data: parsed, cookies, status: res.statusCode });
        } catch (e) {
          reject(new Error(`Failed to parse response: ${body}`));
        }
      });
    });

    req.on('error', reject);
    req.write(postData);
    req.end();
  });
}

/**
 * Login and get tokens
 */
async function getTokens() {
  try {
    // Step 1: Login
    if (!outputJson) {
      console.log('🔐 Logging in as test user...');
      console.log(`   Email: ${TEST_EMAIL}`);
    }

    const loginResponse = await post(`${BASE_URL}/api/auth/login`, {
      email: TEST_EMAIL,
      password: TEST_PASSWORD,
    });

    if (loginResponse.status !== 200) {
      throw new Error(`Login failed (${loginResponse.status}): ${JSON.stringify(loginResponse.data)}`);
    }

    const { accessToken, refreshToken, user } = loginResponse.data;
    // CSRF token is in cookies, not response body
    const csrfCookie = loginResponse.cookies.find((c) => c.startsWith('csrf='));
    const csrfToken = csrfCookie ? csrfCookie.split('=')[1].split(';')[0] : null;

    if (!accessToken) {
      throw new Error(
        `Missing accessToken in login response. Got: ${JSON.stringify(loginResponse.data).substring(0, 500)}`
      );
    }

    // Extract auth cookie
    const authCookie = loginResponse.cookies.find((c) => c.startsWith('auth='));

    // Step 2: Save tokens to file
    const tokens = {
      accessToken,
      refreshToken,
      csrfToken,
      authCookie: authCookie ? authCookie.split(';')[0] : null,
      csrfCookie: csrfCookie ? csrfCookie.split(';')[0] : null,
      userId: user.id,
      email: user.email,
      timestamp: new Date().toISOString(),
      expiresAt: new Date(Date.now() + 15 * 60 * 1000).toISOString(), // 15 min from now
    };

    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(tokens, null, 2));

    if (outputJson) {
      // Machine-readable output
      console.log(JSON.stringify(tokens));
    } else {
      // Human-readable output
      console.log('✅ Login successful!\n');
      console.log('📋 Tokens saved to:', OUTPUT_FILE);
      console.log('\n🎫 Auth Tokens:');
      console.log('   Access Token:', accessToken.substring(0, 50) + '...');
      if (refreshToken) {
        console.log('   Refresh Token:', refreshToken.substring(0, 50) + '...');
      }
      if (csrfToken) {
        console.log('   CSRF Token:', csrfToken.substring(0, 50) + '...');
      }
      console.log('\n👤 User Info:');
      console.log('   User ID:', user.id);
      console.log('   Email:', user.email);
      console.log('\n⏰ Valid until:', tokens.expiresAt);
      console.log('\n💡 Usage Examples:');
      console.log('   curl -H "Authorization: Bearer ' + accessToken + '" \\');
      console.log('        -H "x-csrf-token: ' + csrfToken + '" \\');
      console.log('        http://localhost:3000/api/...');
    }

    process.exit(0);
  } catch (error) {
    if (outputJson) {
      console.error(JSON.stringify({ error: error.message }));
    } else {
      console.error('❌ Error:', error.message);
    }
    process.exit(1);
  }
}

// Run
getTokens();
