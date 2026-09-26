'use client';

import React, { useEffect, useState } from 'react';
import { api, formatTimeAgo, getRiskColor, getCategoryColor } from '@/lib/utils';

export default function HomePage() {
  const [health, setHealth] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [activeCalls, setActiveCalls] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [streamActive, setStreamActive] = useState(false);
  const [transcript, setTranscript] = useState<any[]>([]);
  const wsRef = React.useRef<WebSocket | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [healthData, alertsData, callsData] = await Promise.all([
        api.healthCheck(),
        api.getAlerts(true),
        api.getActiveCalls(),
      ]);
      setHealth(healthData);
      setAlerts(alertsData);
      setActiveCalls(callsData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  }

  function startStream() {
    try {
      const ws = api.connectStream();
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(JSON.stringify({ action: 'start_stream' }));
        setStreamActive(true);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'chunk') {
          setTranscript(prev => [{
            text: data.transcript,
            riskScore: data.classification?.risk_score || 0,
            riskCategory: data.classification?.risk_category || 'Safe',
            timestamp: new Date().toISOString(),
          }, ...prev.slice(0, 49)]);
        } else if (data.type === 'alert') {
          setAlerts(prev => [{
            alert_id: data.alert_id,
            title: data.message,
            severity: data.severity,
            risk_score: data.risk_score,
            created_at: data.timestamp,
            is_active: true,
          }, ...prev]);
        } else if (data.type === 'stream_complete') {
          setStreamActive(false);
        }
      };

      ws.onclose = () => {
        setStreamActive(false);
      };
    } catch (err) {
      console.error('WebSocket error:', err);
    }
  }

  function stopStream() {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setStreamActive(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header Section */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold">
            <span className="text-gradient">Command Center</span>
          </h2>
          <p className="text-xs text-gray-500 mt-1 tracking-wide">
            {health ? (
              <>
                <span className="inline-flex items-center gap-1.5">
                  <span className="status-dot active"></span>
                  System {health.status}
                </span>
                <span className="mx-2 text-gray-700">·</span>
                {health.modules?.length} intelligence modules active
              </>
            ) : 'Loading system status...'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            className="glass-btn px-4 py-2 text-xs text-gray-400 hover:text-gray-200"
          >
            <svg className="w-3.5 h-3.5 inline mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
          {!streamActive ? (
            <button
              onClick={startStream}
              className="glass-btn-primary px-5 py-2 text-xs tracking-wider"
            >
              <span className="flex items-center gap-2">
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
                Start Interception
              </span>
            </button>
          ) : (
            <button
              onClick={stopStream}
              className="glass-btn-danger px-5 py-2 text-xs tracking-wider animate-pulse"
            >
              <span className="flex items-center gap-2">
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 6h12v12H6z" />
                </svg>
                Stop Interception
              </span>
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Interceptor Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Live Transcript */}
          <div className="glass-card glass-card-blue p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-md bg-cyber-blue/10 flex items-center justify-center">
                  <svg className="w-3.5 h-3.5 text-cyber-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                </div>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Live Interceptor Monitor
                </h3>
              </div>
              {streamActive && (
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-cyber-red/10 border border-cyber-red/20">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyber-red opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-cyber-red"></span>
                  </span>
                  <span className="text-[10px] font-bold text-cyber-red tracking-widest uppercase">REC</span>
                </div>
              )}
            </div>

            {/* Waveform visualization */}
            <div className="flex items-end h-14 gap-[2px] mb-4 px-1">
              {Array.from({ length: 50 }).map((_, i) => {
                const h = streamActive ? Math.random() * 70 + 15 : 6;
                const delay = (Math.random() * 0.6).toFixed(2);
                return (
                  <div
                    key={i}
                    className="flex-1 rounded-t-sm transition-all duration-300"
                    style={{
                      height: `${h}%`,
                      background: streamActive
                        ? `linear-gradient(to top, rgba(59,130,246,0.4), rgba(147,197,253,0.6))`
                        : 'rgba(255,255,255,0.05)',
                      animation: streamActive ? `waveform ${0.4 + Math.random() * 0.4}s ease-in-out infinite` : 'none',
                      animationDelay: `${delay}s`,
                    }}
                  />
                );
              })}
            </div>

            {/* Transcript feed */}
            <div className="relative">
              <div className="space-y-1 max-h-80 overflow-y-auto pr-1">
                {transcript.length === 0 && !streamActive && (
                  <div className="flex flex-col items-center justify-center py-12 text-gray-600">
                    <svg className="w-10 h-10 mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                    </svg>
                    <p className="text-xs">Click <span className="text-cyber-blue font-medium">"Start Interception"</span> to begin monitoring</p>
                  </div>
                )}
                {transcript.map((item, i) => (
                  <div
                    key={i}
                    className="group flex items-start gap-3 p-3 rounded-xl hover:bg-white/[0.04] transition-all duration-200"
                  >
                    <div className="flex-shrink-0 mt-0.5">
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: getRiskColor(item.riskScore) }}
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-200 leading-relaxed font-light">{item.text}</p>
                      <div className="flex items-center gap-2 mt-1.5">
                        <span
                          className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-md"
                          style={{
                            backgroundColor: `${getCategoryColor(item.riskCategory)}15`,
                            color: getCategoryColor(item.riskCategory),
                            border: `1px solid ${getCategoryColor(item.riskCategory)}25`,
                          }}
                        >
                          <span
                            className="w-1.5 h-1.5 rounded-full"
                            style={{ backgroundColor: getCategoryColor(item.riskCategory) }}
                          />
                          {item.riskCategory} · {item.riskScore.toFixed(1)}
                        </span>
                        <span className="text-[10px] text-gray-600">{formatTimeAgo(item.timestamp)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Active Calls */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-md bg-cyber-green/10 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-cyber-green" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
              </div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Active Interceptions
              </h3>
              {activeCalls.length > 0 && (
                <span className="ml-auto text-[10px] font-mono text-cyber-green bg-cyber-green/10 px-2 py-0.5 rounded-md border border-cyber-green/20">
                  {activeCalls.length} active
                </span>
              )}
            </div>
            {activeCalls.length === 0 && (
              <div className="flex flex-col items-center py-6 text-gray-600">
                <p className="text-xs">No active calls being intercepted</p>
              </div>
            )}
            <div className="space-y-2">
              {activeCalls.map((call, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.05] transition-all border border-white/[0.04]">
                  <div className="flex items-center gap-3">
                    <span className={`status-dot ${call.is_scam ? 'critical' : 'active'}`}></span>
                    <div>
                      <span className="text-xs font-mono text-gray-300">{call.call_id}</span>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-gray-600">{call.progress}</span>
                        <span className="text-[10px] text-gray-600">·</span>
                        <span className="text-[10px] text-gray-600">{call.active_seconds}s</span>
                      </div>
                    </div>
                  </div>
                  {call.is_scam && (
                    <span className="text-[10px] font-bold text-cyber-red bg-cyber-red/10 px-2.5 py-1 rounded-md border border-cyber-red/20 tracking-wider">
                      SCAM DETECTED
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Alerts Panel */}
        <div className="space-y-6">
          <div className="glass-card glass-card-red p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-md bg-cyber-red/10 flex items-center justify-center">
                  <svg className="w-3.5 h-3.5 text-cyber-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  Active Alerts
                </h3>
              </div>
              {alerts.length > 0 && (
                <span className="text-[10px] font-bold text-cyber-red bg-cyber-red/10 px-2 py-0.5 rounded-md border border-cyber-red/20">
                  {alerts.length}
                </span>
              )}
            </div>
            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {alerts.length === 0 && (
                <div className="flex flex-col items-center py-8 text-gray-600">
                  <svg className="w-8 h-8 mb-2 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-xs">No active alerts</p>
                </div>
              )}
              {alerts.map((alert, i) => {
                const isCritical = alert.severity === 'CRITICAL' || alert.severity === 'Critical';
                const isHigh = alert.severity === 'HIGH' || alert.severity === 'High';
                return (
                  <div
                    key={alert.alert_id || i}
                    className={`p-3 rounded-xl transition-all duration-200 border ${
                      isCritical
                        ? 'bg-cyber-red/[0.04] border-cyber-red/15 hover:bg-cyber-red/[0.06]'
                        : isHigh
                        ? 'bg-yellow-500/[0.04] border-yellow-500/15 hover:bg-yellow-500/[0.06]'
                        : 'bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.05]'
                    }`}
                  >
                    <div className="flex items-start gap-2.5">
                      <span
                        className={`status-dot mt-1 ${
                          isCritical ? 'critical' : isHigh ? 'warning' : 'active'
                        }`}
                      ></span>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-gray-200 leading-relaxed">{alert.title || alert.message}</p>
                        <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                          <span
                            className={`text-[10px] font-medium px-2 py-0.5 rounded-md ${
                              isCritical
                                ? 'text-cyber-red bg-cyber-red/10 border border-cyber-red/20'
                                : isHigh
                                ? 'text-yellow-400 bg-yellow-500/10 border border-yellow-500/20'
                                : 'text-gray-400 bg-white/5 border border-white/10'
                            }`}
                          >
                            {alert.severity}
                          </span>
                          {alert.risk_score && (
                            <span className="text-[10px] font-mono text-cyber-blue">
                              RS: {alert.risk_score.toFixed(1)}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/[0.06]">
                          <span className="text-[10px] text-gray-600">{formatTimeAgo(alert.created_at)}</span>
                          <button
                            onClick={async () => {
                              try {
                                await api.resolveAlert(alert.alert_id);
                                loadData();
                              } catch (err) {}
                            }}
                            className="text-[10px] font-medium text-cyber-blue/70 hover:text-cyber-blue transition-colors"
                          >
                            Resolve
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="glass-card p-5">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">System Status</h3>
            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'API', active: true },
                { label: 'Database', active: true },
                { label: 'WebSocket', active: streamActive },
                { label: 'Classifier', active: true },
              ].map((s, i) => (
                <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-white/[0.02]">
                  <span className={`status-dot ${s.active ? 'active' : ''}`} style={!s.active ? { background: '#4b5563' } : {}}></span>
                  <span className="text-[10px] text-gray-500">{s.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}