'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

const GeoMap = dynamic(() => import('./GeoMap'), {
  ssr: false,
});
import { api, formatCurrency, formatTimeAgo, maskAccount, getRiskColor, getCategoryColor, getSeverityColor } from '@/lib/utils';

export default function DashboardPage() {
  const [txns, setTxns] = useState<any[]>([]);
  const [muleNetworks, setMuleNetworks] = useState<any[]>([]);
  const [snapshot, setSnapshot] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [dossier, setDossier] = useState<any>(null);
  const [locations, setLocations] = useState<any[]>([]);

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      const [txData, muleData, graphData, locationData] = await Promise.all([
        api.getTransactions(true),
        api.detectMuleNetworks(),
        api.getGraphSnapshot(50),
        api.getGeospatialLocations(),
      ]);
      setTxns(txData);
      setMuleNetworks(muleData);
      setSnapshot(graphData);
      setLocations(locationData);
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  }

  async function generateDossier() {
    try {
      const result = await api.generateDossier('Digital Arrest / Financial Fraud Investigation - Case #ET2026');
      setDossier(result);
    } catch (err) {
      console.error('Dossier generation error:', err);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-xl font-bold">
            <span className="text-gradient">Fraud Intelligence Dashboard</span>
          </h2>
          <p className="text-xs text-gray-500 mt-1 tracking-wide">
            {snapshot ? (
              <>
                <span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-cyber-blue"></span> {snapshot.nodes?.length || 0} graph nodes</span>
                <span className="mx-2 text-gray-700">·</span>
                <span className="inline-flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-cyber-red"></span> {txns.length} suspicious transactions</span>
              </>
            ) : 'Loading...'}
          </p>
        </div>
        <button
          onClick={generateDossier}
          className="glass-btn-primary px-5 py-2 text-xs tracking-wider"
        >
          <span className="flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Generate Legal Dossier
          </span>
        </button>
      </div>

      {/* Dossier Result */}
      {dossier && (
        <div className="glass-border-animated p-5 mb-6 animate-slide-up">
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-md bg-cyber-purple/10 flex items-center justify-center">
                  <svg className="w-3.5 h-3.5 text-cyber-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <span className="text-xs font-semibold text-cyber-purple">Section 65B Legal Dossier Generated</span>
              </div>
              <span className="text-[10px] font-mono text-gray-500 bg-white/[0.04] px-2 py-1 rounded-md">{dossier.dossier_id}</span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
              <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                <p className="text-[10px] text-gray-500">Evidence Items</p>
                <p className="text-lg font-bold text-gradient">{dossier.evidence_count}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                <p className="text-[10px] text-gray-500">Graph Nodes</p>
                <p className="text-lg font-bold text-cyber-blue">{dossier.graph_snapshot?.nodes?.length || 0}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                <p className="text-[10px] text-gray-500">Graph Edges</p>
                <p className="text-lg font-bold text-cyber-cyan">{dossier.graph_snapshot?.edges?.length || 0}</p>
              </div>
              <div className="p-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
                <p className="text-[10px] text-gray-500">SHA-256 Hash</p>
                <p className="text-[10px] font-mono text-cyber-purple truncate">{dossier.sha256_hash?.substring(0, 24)}...</p>
              </div>
            </div>
            <pre className="text-[10px] text-gray-500 bg-black/40 p-3 rounded-xl border border-white/[0.06] overflow-x-auto max-h-16 leading-relaxed">
              {dossier.case_summary}
            </pre>
          </div>
        </div>
      )}

      <div className="glass-card glass-card-blue p-5 mb-6">
        <div className="flex items-center gap-2 mb-4">
         <div className="w-6 h-6 rounded-md bg-cyber-cyan/10 flex items-center justify-center">
          <span className="text-cyber-cyan text-xs">●</span>
        </div>
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
          Geospatial Intelligence
        </h3>
        <span className="ml-auto text-[10px] font-mono text-gray-500">
          {locations.length} locations
        </span>
       </div>

       <GeoMap locations={locations} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Graph Visualization Panel */}
        <div className="lg:col-span-3 glass-card glass-card-blue p-5">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-6 h-6 rounded-md bg-cyber-blue/10 flex items-center justify-center">
              <svg className="w-3.5 h-3.5 text-cyber-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Fraud Network Graph
            </h3>
            <span className="ml-auto text-[10px] font-mono text-gray-500">
              {snapshot?.nodes?.length || 0} nodes · {snapshot?.edges?.length || 0} edges
            </span>
          </div>

          {/* Network visualization */}
          <div className="relative bg-black/40 rounded-xl p-4 min-h-[420px] overflow-hidden border border-white/[0.06]">
            <svg className="w-full h-full" viewBox="0 0 600 400">
              <defs>
                <radialGradient id="nodeGlow">
                  <stop offset="0%" stopColor="rgba(59,130,246,0.3)" />
                  <stop offset="100%" stopColor="rgba(59,130,246,0)" />
                </radialGradient>
              </defs>
              {/* Edges */}
              {snapshot?.edges?.slice(0, 100).map((edge: any, i: number) => {
                const sourceNode = snapshot.nodes.find((n: any) => n.id === edge.source);
                const targetNode = snapshot.nodes.find((n: any) => n.id === edge.target);
                if (!sourceNode || !targetNode) return null;
                const sx = parseInt(sourceNode.id.charCodeAt(sourceNode.id.length - 1) + '') * 40 + 50;
                const sy = parseInt(sourceNode.id.charCodeAt(0) + '') % 4 * 80 + 40;
                const tx = parseInt(targetNode.id.charCodeAt(targetNode.id.length - 1) + '') * 40 + 50;
                const ty = parseInt(targetNode.id.charCodeAt(0) + '') % 4 * 80 + 40;
                return (
                  <line
                    key={i}
                    x1={sx % 550}
                    y1={sy % 360}
                    x2={tx % 550}
                    y2={ty % 360}
                    stroke="rgba(59, 130, 246, 0.15)"
                    strokeWidth={Math.max(0.5, (edge.weight || 0.5) * 2.5)}
                    strokeLinecap="round"
                  />
                );
              })}
              {/* Nodes */}
              {snapshot?.nodes?.slice(0, 35).map((node: any, i: number) => {
                const x = parseInt(node.id.charCodeAt(node.id.length - 1) + '') * 40 + 50;
                const y = parseInt(node.id.charCodeAt(0) + '') % 4 * 80 + 40;
                const colors: Record<string, string> = {
                  Account: '#3b82f6',
                  Phone: '#22c55e',
                  Device: '#eab308',
                  IP_Address: '#8b5cf6',
                  Location: '#06b6d4',
                  Victim: '#ef4444',
                };
                const color = colors[node.node_type] || '#6b7280';
                return (
                  <g key={i}>
                    <circle cx={x % 550} cy={y % 360} r={8} fill={color} opacity={0.15} />
                    <circle cx={x % 550} cy={y % 360} r={5} fill={color} opacity={0.9} />
                    <text x={x % 550 + 12} y={y % 360 + 3} fill="rgba(255,255,255,0.7)" fontSize="8" fontFamily="'JetBrains Mono', monospace">
                      {node.label}
                    </text>
                  </g>
                );
              })}
            </svg>
            {(!snapshot || snapshot.nodes?.length === 0) && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <svg className="w-10 h-10 mx-auto mb-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                  <p className="text-xs text-gray-600">No graph data available</p>
                </div>
              </div>
            )}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-3 mt-4 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            {[
              { type: 'Account', color: '#3b82f6' },
              { type: 'Phone', color: '#22c55e' },
              { type: 'Device', color: '#eab308' },
              { type: 'IP_Address', color: '#8b5cf6' },
              { type: 'Location', color: '#06b6d4' },
              { type: 'Victim', color: '#ef4444' },
            ].map(item => (
              <div key={item.type} className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color, boxShadow: `0 0 6px ${item.color}60` }} />
                <span className="text-[10px] text-gray-500">{item.type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Mule Networks & Transactions */}
        <div className="lg:col-span-2 space-y-6">
          {/* Mule Networks */}
          <div className="glass-card glass-card-red p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-md bg-cyber-red/10 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-cyber-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.072 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Mule Networks
              </h3>
              {muleNetworks.length > 0 && (
                <span className="ml-auto text-[10px] font-mono text-cyber-red bg-cyber-red/10 px-2 py-0.5 rounded-md border border-cyber-red/20">
                  {muleNetworks.length} detected
                </span>
              )}
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
              {muleNetworks.length === 0 && (
                <div className="flex flex-col items-center py-6 text-gray-600">
                  <p className="text-xs">No mule networks detected</p>
                </div>
              )}
              {muleNetworks.map((network, i) => (
                <div key={i} className="p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.05] transition-all border border-white/[0.04]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono text-cyber-red">{maskAccount(network.sink_account)}</span>
                    <div className="flex items-center gap-2">
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded-md"
                        style={{
                          backgroundColor: `${getRiskColor(network.risk_score)}18`,
                          color: getRiskColor(network.risk_score),
                          border: `1px solid ${getRiskColor(network.risk_score)}25`,
                        }}
                      >
                        RS: {network.risk_score.toFixed(0)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-gray-500">
                    <span className="font-mono">{formatCurrency(network.total_inflow)}</span>
                    <span>{network.transaction_count} txns</span>
                    <span>{network.source_accounts.length} sources</span>
                  </div>
                  <div className="mt-2 flex gap-1">
                    {network.devices_involved?.slice(0, 3).map((d: string, j: number) => (
                      <span key={j} className="text-[9px] font-mono text-gray-600 bg-white/[0.03] px-1.5 py-0.5 rounded">{d.slice(-6)}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Suspicious Transactions */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-md bg-yellow-500/10 flex items-center justify-center">
                <svg className="w-3.5 h-3.5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Suspicious Transactions
              </h3>
              <span className="ml-auto text-[10px] font-mono text-yellow-400 bg-yellow-500/10 px-2 py-0.5 rounded-md border border-yellow-500/20">
                {txns.length}
              </span>
            </div>
            <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
              {txns.slice(0, 25).map((tx, i) => (
                <div key={i} className="flex items-center justify-between p-2.5 rounded-xl hover:bg-white/[0.03] transition-all border border-transparent hover:border-white/[0.06]">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-1.5 h-1.5 rounded-full bg-cyber-red/60 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-[10px] font-mono text-gray-400 truncate leading-relaxed">
                        <span className="text-gray-300">{maskAccount(tx.source_account)}</span>
                        <span className="text-gray-600 mx-1">→</span>
                        <span className="text-gray-300">{maskAccount(tx.target_account)}</span>
                      </p>
                      <p className="text-[10px] text-gray-600">{tx.transaction_type} · {formatTimeAgo(tx.timestamp)}</p>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0 ml-3">
                    <span className="text-[10px] font-mono text-cyber-red">{formatCurrency(tx.amount)}</span>
                    {tx.fraud_score > 0 && (
                      <p className="text-[9px] text-gray-600">FS: {tx.fraud_score.toFixed(0)}</p>
                    )}
                  </div>
                </div>
              ))}
              {txns.length === 0 && (
                <div className="flex flex-col items-center py-6 text-gray-600">
                  <p className="text-xs">No suspicious transactions found</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}