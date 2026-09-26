'use client';

import React, { useEffect, useState } from 'react';
import { api, formatTimeAgo } from '@/lib/utils';

export default function CurrencyPage() {
  const [scans, setScans] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [scanResult, setScanResult] = useState<any>(null);
  const [denomination, setDenomination] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [scanData, statsData] = await Promise.all([
        api.getRecentScans(),
        api.getSentinelStats(),
      ]);
      setScans(scanData);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to load currency data:', err);
    } finally {
      setLoading(false);
    }
  }

  async function runScan() {
    try {
      const placeholderImg = btoa(JSON.stringify({
        type: 'currency_note',
        denomination: denomination || 'random',
        timestamp: new Date().toISOString(),
      }));
      const result = await api.scanCurrency(placeholderImg, denomination || undefined);
      setScanResult(result);
      loadData();
    } catch (err) {
      console.error('Scan error:', err);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold">
            <span className="text-gradient">Currency Sentinel</span>
          </h2>
          <p className="text-xs text-gray-500 mt-1 tracking-wide">
            {stats ? (
              <>
                <span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-cyber-cyan"></span> {stats.total_scans} scans</span>
                <span className="mx-2 text-gray-700">·</span>
                <span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-cyber-red"></span> {stats.counterfeit_rate}% counterfeit rate</span>
              </>
            ) : 'Loading...'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Scan Interface */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass-card glass-card-cyan p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-md bg-cyber-cyan/10 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-cyber-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Forensic Scanner
              </h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-[10px] text-gray-500 block mb-1.5 tracking-wide">Denomination (optional)</label>
                <select
                  value={denomination}
                  onChange={(e) => setDenomination(e.target.value)}
                  className="glass-input w-full px-3 py-2.5 text-xs"
                >
                  <option value="">Auto-detect</option>
                  <option value="₹10">₹10</option>
                  <option value="₹20">₹20</option>
                  <option value="₹50">₹50</option>
                  <option value="₹100">₹100</option>
                  <option value="₹200">₹200</option>
                  <option value="₹500">₹500</option>
                  <option value="₹2000">₹2000</option>
                </select>
              </div>
              <button
                onClick={runScan}
                className="glass-btn-primary w-full px-4 py-2.5 text-xs tracking-wider"
              >
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Run Forensic Scan
                </span>
              </button>
            </div>
          </div>

          {/* Stats */}
          {stats && (
            <div className="glass-card p-5">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Statistics</h3>
              <div className="space-y-3">
                {[
                  { label: 'Total Scans', value: stats.total_scans, color: 'text-white' },
                  { label: 'Authentic', value: stats.authentic, color: 'text-threat-safe' },
                  { label: 'Counterfeit', value: stats.counterfeit, color: 'text-threat-critical' },
                  { label: 'Counterfeit Rate', value: `${stats.counterfeit_rate}%`, color: 'text-threat-critical' },
                  { label: 'Avg Confidence', value: `${stats.avg_confidence}%`, color: 'text-cyber-blue' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-white/[0.02]">
                    <span className="text-[10px] text-gray-500">{item.label}</span>
                    <span className={`text-[10px] font-mono font-medium ${item.color}`}>{item.value}</span>
                  </div>
                ))}
              </div>
              {stats.denomination_breakdown && Object.keys(stats.denomination_breakdown).length > 0 && (
                <div className="mt-4 pt-4 border-t border-white/[0.06]">
                  <p className="text-[10px] text-gray-500 mb-2">By Denomination</p>
                  <div className="space-y-1">
                    {Object.entries(stats.denomination_breakdown).map(([denom, count]: [string, any]) => (
                      <div key={denom} className="flex items-center justify-between text-[10px]">
                        <span className="text-gray-500">{denom}</span>
                        <span className="font-mono text-gray-400">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Scan Results */}
        <div className="lg:col-span-3 space-y-6">
          {/* Latest Scan */}
          {scanResult && (
            <div className="glass-card glass-card-blue p-5 animate-slide-up">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className={`w-6 h-6 rounded-md flex items-center justify-center ${
                    scanResult.is_authentic ? 'bg-cyber-green/10' : 'bg-cyber-red/10'
                  }`}>
                    <svg className={`w-3.5 h-3.5 ${
                      scanResult.is_authentic ? 'text-cyber-green' : 'text-cyber-red'
                    }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      {scanResult.is_authentic ? (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      )}
                    </svg>
                  </div>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Latest Scan Result
                  </h3>
                </div>
                <span className="text-[10px] font-mono text-gray-500 bg-white/[0.04] px-2 py-1 rounded-md">{scanResult.scan_id}</span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                  <p className="text-[10px] text-gray-500 mb-1">Denomination</p>
                  <p className="text-sm font-bold text-white">{scanResult.denomination}</p>
                </div>
                <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                  <p className="text-[10px] text-gray-500 mb-1">Status</p>
                  <p className={`text-sm font-bold ${scanResult.is_authentic ? 'text-cyber-green' : 'text-cyber-red'}`}>
                    {scanResult.is_authentic ? 'AUTHENTIC' : 'COUNTERFEIT'}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                  <p className="text-[10px] text-gray-500 mb-1">Confidence</p>
                  <p className="text-sm font-bold text-cyber-blue">{scanResult.confidence_score.toFixed(1)}%</p>
                </div>
                <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                  <p className="text-[10px] text-gray-500 mb-1">Serial Number</p>
                  <p className="text-sm font-mono text-gray-300 truncate">{scanResult.serial_number}</p>
                </div>
              </div>

              {/* Forensic checks */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                {[
                  { label: 'Serial Valid', value: scanResult.serial_valid },
                  { label: 'Security Thread', value: scanResult.security_thread_detected },
                  { label: 'UV Fibers', value: scanResult.uv_fibers_detected },
                  { label: 'Watermark', value: scanResult.watermark_detected },
                  { label: 'Micro-printing', value: scanResult.micro_printing_valid },
                ].map((check, i) => (
                  <div key={i} className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] text-center">
                    <p className="text-[10px] text-gray-500 mb-2">{check.label}</p>
                    <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-md ${
                      check.value
                        ? 'text-cyber-green bg-cyber-green/10 border border-cyber-green/20'
                        : 'text-cyber-red bg-cyber-red/10 border border-cyber-red/20'
                    }`}>
                      {check.value ? '✓ PASS' : '✗ FAIL'}
                    </span>
                  </div>
                ))}
              </div>

              {/* Anomaly details */}
              {Object.keys(scanResult.anomaly_details || {}).length > 0 && (
                <div className="mt-4 p-4 rounded-xl bg-cyber-red/[0.06] border border-cyber-red/20">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-3.5 h-3.5 text-cyber-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <p className="text-[10px] font-bold text-cyber-red tracking-wider">ANOMALIES DETECTED</p>
                  </div>
                  <ul className="space-y-1">
                    {Object.values(scanResult.anomaly_details).map((anomaly: any, i: number) => (
                      <li key={i} className="text-[10px] text-gray-400 flex items-start gap-2">
                        <span className="text-cyber-red mt-0.5">•</span>
                        {Array.isArray(anomaly) ? anomaly.join(', ') : String(anomaly)}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Recent Scans */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-md bg-gray-500/10 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Recent Scans
              </h3>
              <span className="ml-auto text-[10px] font-mono text-gray-500">{scans.length} records</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs glass-table">
                <thead>
                  <tr className="text-gray-500">
                    <th className="text-left py-2.5 px-3 font-medium">Scan ID</th>
                    <th className="text-left py-2.5 px-3 font-medium">Denom</th>
                    <th className="text-left py-2.5 px-3 font-medium">Status</th>
                    <th className="text-left py-2.5 px-3 font-medium">Confidence</th>
                    <th className="text-left py-2.5 px-3 font-medium">Serial</th>
                    <th className="text-left py-2.5 px-3 font-medium">Thread</th>
                    <th className="text-left py-2.5 px-3 font-medium">UV</th>
                  </tr>
                </thead>
                <tbody>
                  {scans.map((scan, i) => (
                    <tr key={i} className="transition-colors">
                      <td className="py-3 px-3 font-mono text-gray-400">{scan.scan_id?.slice(-8)}</td>
                      <td className="py-3 px-3 text-white font-medium">{scan.denomination}</td>
                      <td className="py-3 px-3">
                        <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-md ${
                          scan.is_authentic
                            ? 'text-cyber-green bg-cyber-green/10 border border-cyber-green/20'
                            : 'text-cyber-red bg-cyber-red/10 border border-cyber-red/20'
                        }`}>
                          {scan.is_authentic ? '✓ AUTH' : '✗ FAKE'}
                        </span>
                      </td>
                      <td className="py-3 px-3 font-mono text-cyber-blue">{scan.confidence_score?.toFixed(1)}%</td>
                      <td className="py-3 px-3 font-mono text-gray-400">{scan.serial_number?.slice(-6)}</td>
                      <td className="py-3 px-3">
                        <span className={scan.security_thread_detected ? 'text-cyber-green' : 'text-cyber-red'}>
                          {scan.security_thread_detected ? '✓' : '✗'}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span className={scan.uv_fibers_detected ? 'text-cyber-green' : 'text-cyber-red'}>
                          {scan.uv_fibers_detected ? '✓' : '✗'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {scans.length === 0 && (
                <div className="flex flex-col items-center py-10 text-gray-600">
                  <svg className="w-8 h-8 mb-2 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <p className="text-xs">No scan records yet</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}