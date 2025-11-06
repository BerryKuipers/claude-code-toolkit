import { networkInterfaces } from 'os';

export interface NetworkConfig {
  preferredCidr?: string;
  explicitHost?: string;
}

function parseIp(ip: string): number[] {
  return ip.split('.').map((octet) => parseInt(octet, 10));
}

function ipToNumber(octets: number[]): number {
  return (
    (octets[0] << 24) |
    (octets[1] << 16) |
    (octets[2] << 8) |
    octets[3]
  );
}

function isInCidr(ip: string, cidr: string): boolean {
  const [network, prefixLen] = cidr.split('/');
  const prefix = parseInt(prefixLen, 10);

  const ipNum = ipToNumber(parseIp(ip));
  const networkNum = ipToNumber(parseIp(network));
  const mask = -1 << (32 - prefix);

  return (ipNum & mask) === (networkNum & mask);
}

export function getLocalIpAddresses(): string[] {
  const addresses: string[] = [];
  const interfaces = networkInterfaces();

  for (const [name, nets] of Object.entries(interfaces)) {
    if (!nets) continue;

    for (const net of nets) {
      if (net.family === 'IPv4' && !net.internal) {
        addresses.push(net.address);
      }
    }
  }

  return addresses;
}

export function shouldPreferNas(config: NetworkConfig): boolean {
  if (config.explicitHost) {
    return true;
  }

  if (!config.preferredCidr) {
    return false;
  }

  const localIps = getLocalIpAddresses();

  for (const ip of localIps) {
    if (isInCidr(ip, config.preferredCidr)) {
      return true;
    }
  }

  return false;
}
