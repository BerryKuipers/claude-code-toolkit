import { mkdir, readFile, writeFile, rename } from 'node:fs/promises';
import { dirname } from 'node:path';
import { randomUUID } from 'node:crypto';

export interface SecretCipher {
  available(): boolean;
  encrypt(value: string): Buffer | Promise<Buffer>;
  decrypt(value: Buffer): string | Promise<string>;
}

export class SecretStore {
  private readonly session = new Map<string, string>();
  private stored: Record<string, string> = {};
  private queue: Promise<void> = Promise.resolve();

  constructor(
    private readonly path: string,
    private readonly cipher: SecretCipher,
  ) {}

  async init(): Promise<void> {
    try {
      const data: unknown = JSON.parse(await readFile(this.path, 'utf8'));
      if (
        !data ||
        typeof data !== 'object' ||
        Array.isArray(data) ||
        Object.values(data).some((value) => typeof value !== 'string')
      )
        throw new Error('Credential store is malformed. Restore it from a local backup.');
      this.stored = Object.assign(Object.create(null), data);
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    }
  }

  available(): boolean {
    return this.cipher.available();
  }

  has(id: string): boolean {
    return this.session.has(id) || Boolean(this.stored[id]);
  }

  async get(id: string): Promise<string | undefined> {
    if (this.session.has(id)) return this.session.get(id);
    if (!this.stored[id]) return undefined;
    if (!this.available())
      throw new Error(
        'The operating-system credential store is locked or unavailable. Unlock it or enter a session-only key.',
      );
    try {
      return await this.cipher.decrypt(Buffer.from(this.stored[id], 'base64'));
    } catch {
      throw new Error(
        'The saved key could not be decrypted by this operating-system account. Enter the key again.',
      );
    }
  }

  async set(id: string, secret: string, persist: boolean): Promise<void> {
    if (!/^[A-Za-z0-9_-]{1,120}$/.test(id)) throw new Error('Invalid profile identifier.');
    if (!secret.trim() || secret.length > 16384 || /[\0\r\n]/.test(secret))
      throw new Error('Enter a valid API key on one line.');
    if (persist) {
      if (!this.available())
        throw new Error(
          'Secure operating-system storage is unavailable. Choose session-only storage.',
        );
      this.stored[id] = (await this.cipher.encrypt(secret.trim())).toString('base64');
      await this.persist();
      this.session.delete(id);
    } else {
      this.session.set(id, secret.trim());
      if (this.stored[id]) {
        delete this.stored[id];
        await this.persist();
      }
    }
  }

  async delete(id: string): Promise<void> {
    this.session.delete(id);
    delete this.stored[id];
    await this.persist();
  }

  private async persist(): Promise<void> {
    const snapshot = JSON.stringify(this.stored);
    const next = this.queue
      .catch(() => undefined)
      .then(async () => {
        await mkdir(dirname(this.path), { recursive: true, mode: 0o700 });
        const temporary = `${this.path}.${randomUUID()}.tmp`;
        await writeFile(temporary, snapshot, { mode: 0o600, flag: 'wx' });
        await rename(temporary, this.path);
      });
    this.queue = next;
    await next;
  }
}
