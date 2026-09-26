/**
 * ThreatPro - Frontend Utility Functions
 * API helpers, data formatters, and shared utilities.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// API Client
// ============================================================================

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }

    return response.json();
  }

  // Interceptor Module
  async getActiveCalls(): Promise<any[]> {
    return this.request('/api/v1/interceptor/calls/active');
  }

  async startInterception(): Promise<any> {
    return this.request('/api/v1/interceptor/calls/start', { method: 'POST' });
  }

  async stopInterception(callId: string): Promise<any> {
    return this.request(`/api/v1/interceptor/calls/${callId}/stop`, { method: 'POST' });
  }

  async getCallSummary(callId: string): Promise<any> {
    return this.request(`/api/v1/interceptor/calls/${callId}/summary`);
  }

  async getAlerts(activeOnly: boolean = false): Promise<any[]> {
    return this.request(`/api/v1/interceptor/alerts?active_only=${activeOnly}`);
  }

  async resolveAlert(alertId: string): Promise<any> {
    return this.request(`/api/v1/interceptor/alerts/${alertId}/resolve`, { method: 'POST' });
  }

  // WebSocket Stream
  connectStream(): WebSocket {
    return new WebSocket(`${this.baseUrl.replace('http', 'ws')}/api/v1/interceptor/ws/stream`);
  }

  // Sentinel Module
  async scanCurrency(imageB64: string, denominationHint?: string): Promise<any> {
    return this.request('/api/v1/sentinel/scan', {
      method: 'POST',
      body: JSON.stringify({ image_b64: imageB64, denomination_hint: denominationHint }),
    });
  }

  async getRecentScans(): Promise<any[]> {
    return this.request('/api/v1/sentinel/scans');
  }

  async getSentinelStats(): Promise<any> {
    return this.request('/api/v1/sentinel/stats');
  }

  // Graph Intelligence
  async getGraphSnapshot(maxNodes: number = 100): Promise<any> {
    return this.request(`/api/v1/graph/snapshot?max_nodes=${maxNodes}`);
  }

  async getGeospatialLocations(): Promise<any[]> {
    return this.request('/api/v1/geospatial/locations?skip=0&limit=100');
  }

  async getTransactions(suspiciousOnly: boolean = false): Promise<any[]> {
    return this.request(`/api/v1/graph/transactions?suspicious_only=${suspiciousOnly}&limit=200`);
  }

  async detectMuleNetworks(): Promise<any[]> {
    return this.request('/api/v1/graph/mule-networks');
  }

  async generateDossier(caseSummary?: string): Promise<any> {
    return this.request('/api/v1/graph/dossier/generate', {
      method: 'POST',
      body: JSON.stringify({ case_summary: caseSummary || 'Digital Arrest Investigation Case' }),
    });
  }

  // Geospatial
  async seedGeodata(count: number = 30): Promise<any> {
    return this.request(`/api/v1/geospatial/seed?count=${count}`, { method: 'POST' });
  }

  async runClustering(): Promise<any> {
    return this.request('/api/v1/geospatial/cluster', { method: 'POST' });
  }

  async getHotspots(): Promise<any> {
    return this.request('/api/v1/geospatial/hotspots');
  }

  async optimizePatrolRoute(): Promise<any> {
    return this.request('/api/v1/geospatial/patrol-optimize', { method: 'POST' });
  }

  // Health
  async healthCheck(): Promise<any> {
    return this.request('/health');
  }
}

export const api = new ApiClient();

// ============================================================================
// Data Formatters
// ============================================================================

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatTimestamp(ts: string): string {
  const date = new Date(ts);
  return date.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
}

export function formatDate(ts: string): string {
  const date = new Date(ts);
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function formatTimeAgo(ts: string): string {
  const now = new Date();
  const date = new Date(ts);
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHour < 24) return `${diffHour}h ago`;
  return `${diffDay}d ago`;
}

export function truncate(str: string, len: number = 50): string {
  if (str.length <= len) return str;
  return str.substring(0, len) + '...';
}

export function maskAccount(account: string): string {
  if (account.length <= 8) return account;
  return '****' + account.slice(-4);
}

// ============================================================================
// Risk Color Helpers
// ============================================================================

export function getRiskColor(score: number): string {
  if (score >= 70) return '#ef4444'; // Red - Critical
  if (score >= 40) return '#f97316'; // Orange - High
  if (score >= 15) return '#eab308'; // Yellow - Suspicious
  return '#22c55e'; // Green - Safe
}

export function getRiskLabel(score: number): string {
  if (score >= 70) return 'Active Scam';
  if (score >= 40) return 'High Risk';
  if (score >= 15) return 'Suspicious';
  return 'Safe';
}

export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    'Safe': '#22c55e',
    'Suspicious': '#eab308',
    'High Risk': '#f97316',
    'Active Scam': '#ef4444',
  };
  return colors[category] || '#6b7280';
}

export function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    'Low': '#22c55e',
    'Medium': '#eab308',
    'High': '#f97316',
    'Critical': '#ef4444',
  };
  return colors[severity] || '#6b7280';
}