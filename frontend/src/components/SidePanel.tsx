import React from 'react';
import { X, ArrowUpRight, ArrowDownLeft } from 'lucide-react';
import { NodeSchema, EdgeSchema } from './types';
import { TYPE_COLORS, EDGE_COLORS } from './GraphView';

interface SidePanelProps {
  node: NodeSchema | null;
  edges: EdgeSchema[];
  allNodes: NodeSchema[];
  onClose: () => void;
  onSelectNeighbor: (node: NodeSchema) => void;
}

export const SidePanel: React.FC<SidePanelProps> = ({
  node,
  edges,
  allNodes,
  onClose,
  onSelectNeighbor
}) => {
  if (!node) return null;

  // Filter edges connected to this node
  const connectedEdges = edges.filter(e => {
    const s = typeof e.source === 'object' ? e.source.id : e.source;
    const t = typeof e.target === 'object' ? e.target.id : e.target;
    return s === node.id || t === node.id;
  });

  const nodeMap = new Map(allNodes.map(n => [n.id, n]));
  const typeColor = TYPE_COLORS[node.type] || '#818cf8';

  // Calculate connected transaction sum
  let totalTxnAmount = 0;
  let totalCalls = 0;
  connectedEdges.forEach(e => {
    if (e.type === 'Transaction') totalTxnAmount += Number(e.attributes.amount || 0);
    if (e.type === 'Call') totalCalls += 1;
  });

  return (
    <div className="flex flex-col h-full bg-zinc-950/95 border-l border-zinc-800 shadow-2xl overflow-hidden w-80 sm:w-96 text-zinc-100 z-30">
      
      {/* Drawer Header */}
      <div className="flex items-center justify-between p-4 bg-zinc-900/90 border-b border-zinc-800">
        <div className="flex items-center gap-2.5 min-w-0">
          <div
            className="w-3.5 h-3.5 rounded-full shrink-0 shadow-sm"
            style={{ backgroundColor: typeColor }}
          />
          <div className="min-w-0">
            <h3 className="font-bold text-sm text-zinc-100 truncate">{node.label}</h3>
            <span
              className="text-[10px] font-semibold uppercase tracking-wider font-mono"
              style={{ color: typeColor }}
            >
              {node.type} · Cell #{node.community_id}
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1 rounded-md text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-3 gap-2 p-3 bg-zinc-900/40 border-b border-zinc-800/80 text-center text-xs font-mono">
        <div className="p-2 bg-zinc-900/60 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-400">Centrality</div>
          <div className="font-bold text-purple-400 mt-0.5">
            {node.centrality_score ? node.centrality_score.toFixed(3) : '0.000'}
          </div>
        </div>
        <div className="p-2 bg-zinc-900/60 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-400">Calls</div>
          <div className="font-bold text-cyan-400 mt-0.5">{totalCalls}</div>
        </div>
        <div className="p-2 bg-zinc-900/60 rounded border border-zinc-800">
          <div className="text-[10px] text-zinc-400">Transfers</div>
          <div className="font-bold text-emerald-400 mt-0.5">
            {totalTxnAmount > 0 ? `₹${(totalTxnAmount / 1000).toFixed(0)}k` : '0'}
          </div>
        </div>
      </div>

      {/* Content Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        
        {/* Node Specific Attributes */}
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 mb-2 font-mono">
            Profile Attributes
          </div>
          <div className="bg-zinc-900/60 p-2.5 rounded-lg border border-zinc-800/80 space-y-1.5 font-mono text-[11px]">
            <div><span className="text-zinc-500">ID:</span> <span className="text-zinc-300">{node.id}</span></div>
            {Object.entries(node.attributes || {}).map(([k, v]) => {
              if (typeof v === 'object') return null;
              return (
                <div key={k} className="flex items-start gap-1">
                  <span className="text-zinc-500 capitalize shrink-0">{k.replace(/_/g, ' ')}:</span>
                  <span className="text-zinc-300 break-words">{String(v)}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Connected Relationships */}
        <div>
          <div className="flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-zinc-400 mb-2 font-mono">
            <span>Direct Connections</span>
            <span className="text-zinc-500">({connectedEdges.length})</span>
          </div>

          <div className="space-y-1.5">
            {connectedEdges.length === 0 ? (
              <div className="text-zinc-500 text-center py-4 font-mono">No direct links recorded</div>
            ) : (
              connectedEdges.map((e, idx) => {
                const s = typeof e.source === 'object' ? e.source.id : e.source;
                const t = typeof e.target === 'object' ? e.target.id : e.target;
                const isOutgoing = s === node.id;
                const neighborId = isOutgoing ? t : s;
                const neighborNode = nodeMap.get(neighborId);
                const neighborLabel = neighborNode ? neighborNode.label : neighborId;
                const edgeCol = EDGE_COLORS[e.type] || '#71717a';

                return (
                  <div
                    key={e.id || idx}
                    onClick={() => neighborNode && onSelectNeighbor(neighborNode)}
                    className="p-2.5 rounded bg-zinc-900/60 hover:bg-zinc-800/80 border border-zinc-800/70 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <div className="flex items-center gap-1.5 min-w-0">
                        {isOutgoing ? (
                          <ArrowUpRight className="w-3 h-3 text-emerald-400 shrink-0" />
                        ) : (
                          <ArrowDownLeft className="w-3 h-3 text-cyan-400 shrink-0" />
                        )}
                        <span className="font-semibold text-zinc-200 group-hover:text-indigo-300 truncate">
                          {neighborLabel}
                        </span>
                      </div>

                      <span
                        className="px-1.5 py-0.5 rounded text-[9px] font-mono uppercase font-bold"
                        style={{ color: edgeCol, backgroundColor: `${edgeCol}15` }}
                      >
                        {e.type}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400">
                      <span>{e.evidence_ref || 'Direct Edge'}</span>
                      {e.attributes?.amount && (
                        <span className="text-emerald-400 font-bold">₹{Number(e.attributes.amount).toLocaleString()}</span>
                      )}
                      {e.attributes?.duration_sec && (
                        <span className="text-cyan-400">{e.attributes.duration_sec}s</span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

      </div>

    </div>
  );
};
