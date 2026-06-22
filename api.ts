/**
 * TeleManager API Client - Ultra Advanced Edition
 * Supports fingerprinting and proxy management
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiResponse<T = unknown> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

interface FingerprintInfo {
  device: string;
  system: string;
  app: string;
  app_version: string;
  language: string;
  device_hash: string;
}

interface ProxyInfo {
  id: string;
  host: string;
  port: number;
  type: string;
  username?: string;
  validated: boolean;
  latency_ms?: number;
  country?: string;
  city?: string;
  isp?: string;
  used: boolean;
  state?: string;
  quality?: string;
  quality_score?: number;
  is_anonymous?: boolean;
  usage_result?: string;
}

interface SendCodeData {
  phone_code_hash?: string;
  code_type?: string;
  already_authorized?: boolean;
  account?: TelegramAccountApi;
  fingerprint?: FingerprintInfo;
  proxy?: ProxyInfo;
}

interface VerifyCodeData {
  needs_2fa?: boolean;
  account?: TelegramAccountApi;
  fingerprint?: FingerprintInfo;
}

interface TelegramAccountApi {
  id: string;
  phone: string;
  firstName: string;
  lastName: string;
  username: string;
  apiId: string;
  apiHash: string;
  status: 'online' | 'offline' | 'recently';
  loginDate: string;
  deviceModel?: string;
  appName?: string;
}

interface ProxyStats {
  total: number;
  available: number;
  used: number;
  dead: number;
  validated: number;
}

interface AddProxiesResult {
  added: number;
  failed: number;
  duplicates: number;
  errors: string[];
  stats: ProxyStats;
}

class TeleManagerApi {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API Error:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error. Is the backend running?',
      };
    }
  }

  // ========== Health Check ==========

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  async getInfo(): Promise<{ apps: string[]; proxy_stats: ProxyStats } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/info`);
      return await response.json();
    } catch {
      return null;
    }
  }

  // ========== Authentication ==========

  async sendCode(
    phone: string,
    apiId: string,
    apiHash: string,
    useProxy: boolean = true
  ): Promise<ApiResponse<SendCodeData>> {
    return this.request<SendCodeData>('/api/auth/send-code', {
      method: 'POST',
      body: JSON.stringify({ phone, api_id: apiId, api_hash: apiHash, use_proxy: useProxy }),
    });
  }

  async verifyCode(phone: string, code: string): Promise<ApiResponse<VerifyCodeData>> {
    return this.request<VerifyCodeData>('/api/auth/verify-code', {
      method: 'POST',
      body: JSON.stringify({ phone, code }),
    });
  }

  async verify2FA(phone: string, password: string): Promise<ApiResponse<{ account: TelegramAccountApi }>> {
    return this.request('/api/auth/verify-2fa', {
      method: 'POST',
      body: JSON.stringify({ phone, password }),
    });
  }

  // ========== Accounts ==========

  async getAccounts(): Promise<{ success: boolean; accounts: TelegramAccountApi[]; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/accounts`);
      const data = await response.json();
      return { success: true, accounts: data.accounts || [] };
    } catch {
      return { success: false, accounts: [], error: 'Failed to fetch accounts' };
    }
  }

  async deleteAccount(accountId: string): Promise<ApiResponse> {
    return this.request(`/api/accounts/${accountId}`, {
      method: 'DELETE',
    });
  }

  // ========== Proxies ==========

  async getProxies(): Promise<{ success: boolean; proxies: ProxyInfo[]; stats: ProxyStats }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/proxies`);
      const data = await response.json();
      return { success: true, proxies: data.proxies || [], stats: data.stats };
    } catch {
      return { success: false, proxies: [], stats: { total: 0, available: 0, used: 0, dead: 0, validated: 0 } };
    }
  }

  async addProxies(proxies: string[], validate: boolean = true): Promise<AddProxiesResult> {
    try {
      const response = await fetch(`${this.baseUrl}/api/proxies`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ proxies, validate }),
      });
      return await response.json();
    } catch {
      return { added: 0, failed: proxies.length, duplicates: 0, errors: ['Network error'], stats: { total: 0, available: 0, used: 0, dead: 0, validated: 0 } };
    }
  }

  async removeUsedProxies(): Promise<ApiResponse> {
    return this.request('/api/proxies/used', { method: 'DELETE' });
  }

  async removeDeadProxies(): Promise<ApiResponse> {
    return this.request('/api/proxies/dead', { method: 'DELETE' });
  }

  async clearAllProxies(): Promise<ApiResponse> {
    return this.request('/api/proxies/all', { method: 'DELETE' });
  }

  // ========== Fingerprint ==========

  async previewFingerprint(): Promise<{ fingerprint: FingerprintInfo; full_details: Record<string, string> } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/fingerprint/preview`);
      const data = await response.json();
      return data;
    } catch {
      return null;
    }
  }

  async getAvailableDevices(): Promise<{ android: Record<string, string[]>; ios: string[] } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/fingerprint/devices`);
      return await response.json();
    } catch {
      return null;
    }
  }

  async getAvailableApps(): Promise<{ apps: { key: string; name: string; layer: number }[] } | null> {
    try {
      const response = await fetch(`${this.baseUrl}/api/fingerprint/apps`);
      return await response.json();
    } catch {
      return null;
    }
  }
}

// Export singleton instance
export const api = new TeleManagerApi();
export type { TelegramAccountApi, ApiResponse, FingerprintInfo, ProxyInfo, ProxyStats };
