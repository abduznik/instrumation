import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';
import { Gauge } from 'lucide-react';

const STALE_MS = 5000;

/**
 * Derives the card's status from the last packet's `status` field and how
 * recently it arrived: ERROR/OVERLOAD -> red, no packet in STALE_MS -> gray
 * (offline/idle), OK -> green, anything else reported by the driver -> amber.
 */
function deriveStatus(lastMessage, lastSeen) {
  if (!lastMessage) return { label: 'IDLE', className: 'status-idle' };
  if (Date.now() - lastSeen > STALE_MS) return { label: 'OFFLINE', className: 'status-idle' };

  const raw = (lastMessage.status || 'OK').toUpperCase();
  if (raw === 'OK') return { label: 'CONNECTED', className: 'status-ok' };
  if (raw === 'ERROR' || raw === 'OVERLOAD') return { label: raw, className: 'status-error' };
  return { label: raw, className: 'status-warning' };
}

export function InstrumentCard({ instrument }) {
  const { id, driver, lastMessage, history, lastSeen } = instrument;
  const status = deriveStatus(lastMessage, lastSeen);

  return (
    <div className="glass instrument-card p-6 flex flex-col gap-3">
      <div className="flex justify-between items-center text-dim">
        <div className="flex items-center gap-2 min-w-0">
          <Gauge size={18} className="text-accent shrink-0" />
          <span className="text-sm font-semibold uppercase tracking-wider truncate" title={id}>
            {driver}
          </span>
        </div>
        <span className={`status-badge ${status.className}`}>{status.label}</span>
      </div>

      <div className="text-dim text-xs mono truncate" title={id}>
        {id}
      </div>

      <div className="flex items-baseline gap-2 mt-1">
        <span className="text-3xl font-bold glow-text">
          {lastMessage ? lastMessage.value : '---'}
        </span>
        <span className="text-lg text-dim font-medium">{lastMessage?.unit ?? ''}</span>
        {lastMessage?.channel != null && (
          <span className="text-xs text-dim mono ml-auto">CH {lastMessage.channel}</span>
        )}
      </div>

      {history.length > 1 && (
        <div className="h-16 -mx-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history}>
              <YAxis hide domain={['auto', 'auto']} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#8b5cf6"
                strokeWidth={2}
                fillOpacity={0.15}
                fill="#8b5cf6"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default InstrumentCard;
