import React, { useMemo } from 'react';
import { Clock, AlertTriangle } from 'lucide-react';
import { TemporalHeatmapPoint } from './types';

interface TemporalHeatmapProps {
  data: TemporalHeatmapPoint[];
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export const TemporalHeatmap: React.FC<TemporalHeatmapProps> = ({ data }) => {
  // Build lookup map: (day, hour) -> count
  const { matrix, maxCount, oddHourCount } = useMemo(() => {
    const map: Record<string, number> = {};
    let max = 1;
    let oddHours = 0;

    data.forEach(pt => {
      const key = `${pt.day}_${pt.hour}`;
      map[key] = pt.count;
      if (pt.count > max) max = pt.count;
      if (pt.hour >= 1 && pt.hour <= 4 && pt.count > 0) {
        oddHours += pt.count;
      }
    });

    return { matrix: map, maxCount: max, oddHourCount: oddHours };
  }, [data]);

  // Color generator based on intensity
  const getCellColor = (count: number, hour: number) => {
    if (count === 0) return 'bg-zinc-900/60 border-zinc-800/40 text-transparent';
    const intensity = count / maxCount;

    // Highlight odd hours in glowing crimson/red
    if (hour >= 1 && hour <= 4) {
      if (intensity > 0.6) return 'bg-red-500 text-white font-bold shadow-sm shadow-red-500/50 border-red-400';
      if (intensity > 0.3) return 'bg-red-600/80 text-red-100 border-red-500';
      return 'bg-red-900/70 text-red-200 border-red-700/60';
    }

    // Standard hours in purple/indigo gradient
    if (intensity > 0.7) return 'bg-purple-500 text-white font-bold border-purple-400';
    if (intensity > 0.4) return 'bg-purple-700 text-purple-100 border-purple-600';
    if (intensity > 0.2) return 'bg-indigo-900/80 text-indigo-200 border-indigo-700';
    return 'bg-indigo-950/60 text-indigo-300 border-indigo-800/40';
  };

  return (
    <div className="flex flex-col h-full bg-zinc-950 p-4 overflow-x-auto">
      
      {/* Title & Anomaly Callout Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 pb-3 border-b border-zinc-800">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-sm font-bold text-zinc-100">
              Temporal Activity Heatmap (Day × Hour)
            </h3>
            <p className="text-xs text-zinc-400">
              Surfaces operational cadence across all monitored calls, transactions, and intercepts.
            </p>
          </div>
        </div>

        {oddHourCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-red-950/70 border border-red-600/70 text-red-200 text-xs shadow-md">
            <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse shrink-0" />
            <span>
              <b>Tactical Anomaly:</b> High activity ({oddHourCount} events) detected between <b>01:00 AM – 04:00 AM</b>
            </span>
          </div>
        )}
      </div>

      {/* Heatmap Grid */}
      <div className="min-w-[700px] select-none">
        
        {/* Hour Header */}
        <div className="flex items-center mb-1 text-[10px] font-mono text-zinc-400">
          <div className="w-24 shrink-0 font-bold uppercase">Day \ Hour</div>
          <div className="flex-1 grid grid-cols-24 gap-1">
            {HOURS.map(h => (
              <div
                key={h}
                className={`text-center py-0.5 rounded font-mono ${
                  h >= 1 && h <= 4 ? 'text-red-400 font-bold bg-red-950/30' : ''
                }`}
              >
                {h}h
              </div>
            ))}
          </div>
        </div>

        {/* Days Rows */}
        <div className="space-y-1.5">
          {DAYS.map(day => (
            <div key={day} className="flex items-center">
              <div className="w-24 shrink-0 text-xs font-medium text-zinc-300">
                {day}
              </div>
              <div className="flex-1 grid grid-cols-24 gap-1">
                {HOURS.map(hour => {
                  const count = matrix[`${day}_${hour}`] || 0;
                  const colorClass = getCellColor(count, hour);

                  return (
                    <div
                      key={hour}
                      title={`${day} at ${hour}:00 - ${count} event(s)`}
                      className={`h-7 rounded flex items-center justify-center text-[10px] border transition-transform hover:scale-110 cursor-pointer ${colorClass}`}
                    >
                      {count > 0 ? count : ''}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-zinc-900 text-xs text-zinc-400">
          <div className="flex items-center gap-2">
            <span>Low Activity</span>
            <div className="flex gap-1">
              <span className="w-4 h-4 rounded bg-zinc-900 border border-zinc-800" />
              <span className="w-4 h-4 rounded bg-indigo-950 border border-indigo-800" />
              <span className="w-4 h-4 rounded bg-indigo-800 border border-indigo-700" />
              <span className="w-4 h-4 rounded bg-purple-600 border border-purple-500" />
              <span className="w-4 h-4 rounded bg-purple-500 border border-purple-400" />
            </div>
            <span>High Activity</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="w-3.5 h-3.5 rounded bg-red-600 border border-red-400" />
            <span className="text-red-300 font-medium">01:00 AM – 04:00 AM Midnight Spike Band</span>
          </div>
        </div>

      </div>

    </div>
  );
};
