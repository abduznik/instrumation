import { InstrumentCard } from './InstrumentCard';

/**
 * Responsive grid of InstrumentCard components, one per instrument_id
 * reported over the WebSocket stream. No instrument data is hardcoded --
 * cards appear/update purely from whatever the bridge relays.
 */
export function StatusGrid({ instruments }) {
  const list = Object.values(instruments).sort((a, b) => a.id.localeCompare(b.id));

  if (list.length === 0) {
    return (
      <div className="glass p-8 text-center text-dim">
        Waiting for instrument data...
      </div>
    );
  }

  return (
    <div className="status-grid">
      {list.map((instrument) => (
        <InstrumentCard key={instrument.id} instrument={instrument} />
      ))}
    </div>
  );
}

export default StatusGrid;
