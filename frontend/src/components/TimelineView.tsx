import React, { useState } from 'react';
import { Clock, Phone, CreditCard, Shield, FileText, ExternalLink } from 'lucide-react';
import { TimelineEvent } from './types';

interface TimelineViewProps {
  events: TimelineEvent[];
  onSelectEvidence?: (ref: string, entityIds: string[]) => void;
}

export const TimelineView: React.FC<TimelineViewProps> = ({
  events,
  onSelectEvidence
}) => {
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterText, setFilterText] = useState<string>('');

  const filteredEvents = events.filter(e => {
    if (filterType !== 'ALL' && e.type !== filterType) return false;
    if (filterText) {
      const q = filterText.toLowerCase();
      const match = e.title.toLowerCase().includes(q) ||
                    e.description.toLowerCase().includes(q) ||
                    e.evidence_ref.toLowerCase().includes(q);
      if (!match) return false;
    }
    return true;
  });

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'Call':
        return <Phone className="w-3.5 h-3.5 text-cyan-400" />;
      case 'Transaction':
        return <CreditCard className="w-3.5 h-3.5 text-emerald-400" />;
      case 'FIR':
        return <Shield className="w-3.5 h-3.5 text-red-400" />;
      default:
        return <FileText className="w-3.5 h-3.5 text-indigo-400" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950 p-4 overflow-hidden">
      
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-sm font-bold text-zinc-100">
              Chronological Intelligence Timeline
            </h3>
            <p className="text-xs text-zinc-400">
              Temporal sequence of verified FIR actions, telecommunication calls, and financial flows.
            </p>
          </div>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            placeholder="Filter events..."
            className="px-2.5 py-1 text-xs bg-zinc-900 border border-zinc-700 rounded text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-2 py-1 text-xs bg-zinc-900 border border-zinc-700 rounded text-zinc-200 focus:outline-none"
          >
            <option value="ALL">All Types</option>
            <option value="Call">Calls</option>
            <option value="Transaction">Transactions</option>
            <option value="FIR">FIRs</option>
          </select>
        </div>
      </div>

      {/* Timeline Stream */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {filteredEvents.length === 0 ? (
          <div className="text-center py-10 text-xs text-zinc-500 font-mono">
            No events match the selected criteria.
          </div>
        ) : (
          filteredEvents.map((evt, idx) => (
            <div
              key={evt.id || idx}
              className="relative flex items-start gap-3 pl-4 border-l-2 border-zinc-800 hover:border-indigo-500 transition-colors group"
            >
              {/* Bullet Node */}
              <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full bg-zinc-900 border-2 border-zinc-700 flex items-center justify-center group-hover:border-indigo-400">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              </div>

              {/* Event Card */}
              <div className="flex-1 p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 hover:border-zinc-700 transition-all text-xs">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <div className="flex items-center gap-2">
                    {getEventIcon(evt.type)}
                    <span className="font-bold text-zinc-100">{evt.title}</span>
                  </div>
                  <span className="font-mono text-[10px] text-zinc-400">
                    {evt.timestamp}
                  </span>
                </div>

                <p className="text-zinc-300 text-xs mb-2">
                  {evt.description}
                </p>

                <div className="flex items-center justify-between pt-2 border-t border-zinc-800/60 text-[10px] font-mono text-zinc-400">
                  <button
                    onClick={() => onSelectEvidence && onSelectEvidence(evt.evidence_ref, evt.entity_ids)}
                    className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 font-semibold"
                  >
                    <span>Anchor: {evt.evidence_ref}</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                  {evt.location && <span>Loc: {evt.location}</span>}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
};
