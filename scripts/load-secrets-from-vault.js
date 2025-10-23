#!/usr/bin/env node
/**
 * Load secrets from Vault and write to .env.local
 *
 * This script fetches the GEMINI_API_KEY from HashiCorp Vault running on the NAS
 * and writes it to .env.local for local development.
 *
 * Usage:
 *   node scripts/load-secrets-from-vault.js
 *
 * Environment variables:
 *   VAULT_ADDR - Vault server address (default: http://10.0.0.23:8200)
 *   VAULT_TOKEN - Vault authentication token (required)
 */

import { writeFileSync, readFileSync } from 'fs';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

// Vault configuration
const VAULT_ADDR = process.env.VAULT_ADDR || 'http://10.0.0.23:8200';
const VAULT_TOKEN = process.env.VAULT_TOKEN;

if (!VAULT_TOKEN) {
  console.error('❌ Error: VAULT_TOKEN environment variable is required');
  console.error('   Set it with: export VAULT_TOKEN=your_token_here');
  process.exit(1);
}

const fetchFromVault = async (path) => {
  const url = `${VAULT_ADDR}/v1/${path}`;

  try {
    const response = await fetch(url, {
      headers: {
        'X-Vault-Token': VAULT_TOKEN,
      },
    });

    if (!response.ok) {
      throw new Error(`Vault returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.data.data || data.data; // Handle both KV v1 and v2
  } catch (error) {
    throw new Error(`Failed to fetch from Vault: ${error.message}`);
  }
};

const updateEnvLocal = (secrets) => {
  const envPath = join(projectRoot, '.env.local');

  // Read existing .env.local if it exists
  let existing = {};
  try {
    const content = readFileSync(envPath, 'utf-8');
    content.split('\n').forEach(line => {
      const [key, ...valueParts] = line.split('=');
      if (key && valueParts.length > 0) {
        existing[key.trim()] = valueParts.join('=').trim();
      }
    });
  } catch (error) {
    // File doesn't exist, that's OK
  }

  // Merge with new secrets
  const merged = { ...existing, ...secrets };

  // Write back to .env.local
  const content = Object.entries(merged)
    .map(([key, value]) => `${key}=${value}`)
    .join('\n') + '\n';

  writeFileSync(envPath, content, 'utf-8');
  console.log(`✅ Updated ${envPath}`);
};

const main = async () => {
  console.log('🔐 Loading secrets from Vault...');
  console.log(`   Vault: ${VAULT_ADDR}`);

  try {
    // Fetch Gemini API key from Vault
    // Assuming the key is stored at: secret/wescobar/gemini_api_key
    // Adjust the path based on your Vault structure
    const geminiSecret = await fetchFromVault('secret/wescobar/gemini_api_key');

    if (!geminiSecret.api_key) {
      throw new Error('GEMINI_API_KEY not found in Vault secret');
    }

    const secrets = {
      GEMINI_API_KEY: geminiSecret.api_key,
    };

    updateEnvLocal(secrets);

    console.log('✅ Secrets loaded successfully!');
    console.log('   GEMINI_API_KEY: ****' + secrets.GEMINI_API_KEY.slice(-4));
    console.log('');
    console.log('You can now start the dev server with: npm run dev');

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error('');
    console.error('💡 Tips:');
    console.error('   1. Ensure Vault is running: http://10.0.0.23:8200');
    console.error('   2. Check your VAULT_TOKEN is valid');
    console.error('   3. Verify the secret exists at: secret/wescobar/gemini_api_key');
    console.error('   4. Create the secret with: vault kv put secret/wescobar/gemini_api_key api_key=YOUR_KEY');
    process.exit(1);
  }
};

main();
