import vault from 'node-vault';
import { shouldPreferNas } from './network.js';

export interface VaultConfig {
  enabled: boolean;
  host?: string;
  port?: number;
  token?: string;
  mountPath?: string;
  namespace?: string;
  preferredCidr?: string;
  explicitHost?: string;
}

export interface VaultClient {
  read(path: string): Promise<string | undefined>;
  isAvailable(): boolean;
}

class VaultClientImpl implements VaultClient {
  private client: any;
  private config: VaultConfig;
  private available: boolean;
  private cache: Map<string, string>;

  constructor(config: VaultConfig) {
    this.config = config;
    this.available = false;
    this.cache = new Map();

    if (!config.enabled) {
      return;
    }

    if (!shouldPreferNas({ preferredCidr: config.preferredCidr, explicitHost: config.explicitHost })) {
      console.warn('[Vault] Network check: not on preferred network, Vault disabled');
      return;
    }

    if (!config.host || !config.token) {
      console.warn('[Vault] Missing host or token, Vault disabled');
      return;
    }

    try {
      this.client = vault({
        apiVersion: 'v1',
        endpoint: `http://${config.host}:${config.port || 8200}`,
        token: config.token,
        namespace: config.namespace,
      });
      this.available = true;
    } catch (error) {
      console.warn('[Vault] Failed to initialize client:', (error as Error).message);
    }
  }

  async read(path: string): Promise<string | undefined> {
    if (!this.available || !this.client) {
      return undefined;
    }

    if (this.cache.has(path)) {
      return this.cache.get(path);
    }

    try {
      const mountPath = this.config.mountPath || 'secret';
      const fullPath = `${mountPath}/data/${path}`;

      const result = await this.client.read(fullPath);

      if (result?.data?.data) {
        const value = result.data.data.value || result.data.data[Object.keys(result.data.data)[0]];
        if (value) {
          this.cache.set(path, value);
          return value;
        }
      }
    } catch (error) {
      const err = error as any;
      if (err.response?.statusCode === 404) {
        return undefined;
      }
      console.warn(`[Vault] Failed to read ${path}:`, err.message);
    }

    return undefined;
  }

  isAvailable(): boolean {
    return this.available;
  }
}

class NoopVaultClient implements VaultClient {
  async read(_path: string): Promise<string | undefined> {
    return undefined;
  }

  isAvailable(): boolean {
    return false;
  }
}

export function createVaultClient(config: VaultConfig): VaultClient {
  if (!config.enabled) {
    return new NoopVaultClient();
  }

  try {
    return new VaultClientImpl(config);
  } catch (error) {
    console.warn('[Vault] Failed to create client, falling back to env only:', (error as Error).message);
    return new NoopVaultClient();
  }
}
