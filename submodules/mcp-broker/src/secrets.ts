import { config as loadDotenv } from 'dotenv';
import { existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { createVaultClient, VaultClient, VaultConfig } from './vault.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export interface SecretResolverConfig {
  vault: VaultConfig;
  dotenvPath?: string;
}

export class SecretResolver {
  private vaultClient: VaultClient;
  private envLoaded: boolean = false;

  constructor(config: SecretResolverConfig) {
    const dotenvPath = config.dotenvPath || join(__dirname, '..', '.env');
    if (existsSync(dotenvPath)) {
      loadDotenv({ path: dotenvPath });
      this.envLoaded = true;
    }

    this.vaultClient = createVaultClient(config.vault);

    if (this.vaultClient.isAvailable()) {
      console.log('[Secrets] Vault client initialized successfully');
    } else if (config.vault.enabled) {
      console.warn('[Secrets] Vault was enabled but is unavailable, falling back to env/.env only');
    }
  }

  async resolve(value: string): Promise<string> {
    const envMatches = [...value.matchAll(/\$\{env:([^}]+)\}/g)];
    const vaultMatches = [...value.matchAll(/\$\{vault:([^}]+)\}/g)];

    let result = value;

    for (const match of envMatches) {
      const key = match[1];
      const resolved = await this.resolveEnvKey(key);
      result = result.replace(match[0], resolved);
    }

    for (const match of vaultMatches) {
      const path = match[1];
      const resolved = await this.resolveVaultPath(path);
      result = result.replace(match[0], resolved);
    }

    return result;
  }

  private async resolveEnvKey(key: string): Promise<string> {
    return process.env[key] || '';
  }

  private async resolveVaultPath(path: string): Promise<string> {
    if (!this.vaultClient.isAvailable()) {
      return '';
    }

    const value = await this.vaultClient.read(path);
    return value || '';
  }

  async resolveObject(obj: any): Promise<any> {
    if (typeof obj === 'string') {
      return await this.resolve(obj);
    }
    if (Array.isArray(obj)) {
      return await Promise.all(obj.map((item) => this.resolveObject(item)));
    }
    if (obj && typeof obj === 'object') {
      const result: any = {};
      for (const [key, value] of Object.entries(obj)) {
        result[key] = await this.resolveObject(value);
      }
      return result;
    }
    return obj;
  }
}

export function createSecretResolver(): SecretResolver {
  const vaultConfig: VaultConfig = {
    enabled: process.env.VAULT_ENABLED === 'true',
    host: process.env.VAULT_HOST,
    port: process.env.VAULT_PORT ? parseInt(process.env.VAULT_PORT, 10) : 8200,
    token: process.env.VAULT_TOKEN,
    mountPath: process.env.VAULT_MOUNT_PATH || 'secret',
    namespace: process.env.VAULT_NAMESPACE,
    preferredCidr: process.env.VAULT_PREFERRED_CIDR,
    explicitHost: process.env.VAULT_EXPLICIT_HOST,
  };

  return new SecretResolver({ vault: vaultConfig });
}
