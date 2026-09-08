import React, { useState } from 'react';
import { Grid } from 'lucide-react';
import { CooccurrenceMatrixData } from './types';

interface CooccurrenceMatrixProps {
  data: CooccurrenceMatrixData;
  onSelectEntity?: (entityId: string) => void;
}

export const CooccurrenceMatrix: React.FC<CooccurrenceMatrixProps> = ({
  data,
  onSelectEntity
}) => {
  const [hoveredCell, setHoveredCell] = useState<{ row: number; col: number } | null>(null);

  if (!data || !data.labels || data.labels.length === 0) {
    return (
      <div className="flex items-center justify-center h-full p-8 text-xs text-zinc-500 font-mono">
        No interaction matrix data available.
      </div>
    );
  }

  const { labels, entity_ids, matrix } = data;

  const getCellBg = (val: number, isSelf: boolean) => {
    if (isSelf) return 'bg-zinc-800/80 border-zinc-700/60 text-zinc-500';
    if (val === 0) return 'bg-zinc-900/40 border-zinc-900 text-transparent';
    if (val > 0.75) return 'bg-rose-500 text-white font-bold border-rose-400';
    if (val > 0.5) return 'bg-amber-500 text-amber-950 font-bold border-amber-400';
    if (val > 0.25) return 'bg-purple-600 text-purple-100 border-purple-500';
    return 'bg-indigo-950 text-indigo-300 border-indigo-800/50';
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950 p-4 overflow-x-auto select-none">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Grid className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-sm font-bold text-zinc-100">
              Entity Co-Occurrence & Interaction Matrix
            </h3>
            <p className="text-xs text-zinc-400">
              High-density cross-entity interaction strength (calls + transactions + co-mentions).
            </p>
          </div>
        </div>

        {hoveredCell && (
          <div className="text-xs font-mono bg-zinc-900 px-3 py-1 rounded border border-zinc-700 text-zinc-200">
            <span className="text-indigo-400 font-bold">{labels[hoveredCell.row]}</span>
            <span className="text-zinc-500 mx-1.5">↔</span>
            <span className="text-purple-400 font-bold">{labels[hoveredCell.col]}</span>
            <span className="text-zinc-500 ml-2">Score:</span>{' '}
            <span className="text-emerald-400 font-bold">
              {matrix[hoveredCell.row]?.[hoveredCell.col]?.toFixed(2) || '0.00'}
            </span>
          </div>
        )}
      </div>

      {/* Matrix Table */}
      <div className="overflow-auto max-h-[400px]">
        <table className="border-collapse text-[11px] font-mono">
          <thead>
            <tr>
              <th className="p-1 text-left font-bold text-zinc-500 w-32 truncate">Entity</th>
              {labels.map((lbl, idx) => (
                <th
                  key={idx}
                  title={lbl}
                  className="p-1 text-center font-bold text-zinc-400 w-8 max-w-8 truncate"
                >
                  <div className="-rotate-45 origin-bottom-left w-6 overflow-hidden text-[9px]">
                    {lbl.split(' ')[0]}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {labels.map((rowLabel, rIdx) => (
              <tr key={rIdx}>
                <td
                  onClick={() => onSelectEntity && onSelectEntity(entity_ids[rIdx])}
                  className="p-1 font-semibold text-zinc-300 truncate cursor-pointer hover:text-indigo-400 hover:underline max-w-[120px]"
                  title={rowLabel}
                >
                  {rowLabel}
                </td>
                {labels.map((colLabel, cIdx) => {
                  const val = matrix[rIdx]?.[cIdx] || 0;
                  const isSelf = rIdx === cIdx;
                  const bgClass = getCellBg(val, isSelf);

                  return (
                    <td
                      key={cIdx}
                      onMouseEnter={() => setHoveredCell({ row: rIdx, col: cIdx })}
                      onMouseLeave={() => setHoveredCell(null)}
                      title={`${rowLabel} & ${colLabel}: ${val.toFixed(2)}`}
                      className={`w-7 h-7 text-center border p-0 transition-all ${bgClass} cursor-pointer hover:ring-2 hover:ring-white`}
                    >
                      {isSelf ? '—' : val > 0 ? val.toFixed(1) : ''}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

    </div>
  );
};
