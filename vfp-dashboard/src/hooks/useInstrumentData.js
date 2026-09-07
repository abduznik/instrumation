import { useEffect, useRef, useState } from 'react';

const HISTORY_LENGTH = 20;
const RECONNECT_DELAY_MS = 3000;

/**
 * Connects to the VFP Bridge WebSocket and groups incoming measurement
 * packets by `metadata.instrument_id` (falling back to `metadata.driver`,
 * then a fixed "default" key for older packets that carry neither) so the
 * dashboard can render one card per physical instrument instead of a
 * single "last message" view.
 *
 * Each packet is the JSON produced by `MeasurementResult.to_dict()`.
 */
export function useInstrumentData(url = 'ws://127.0.0.1:8080') {
  const [instruments, setInstruments] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const ws = useRef(null);
  const reconnectTimer = useRef(null);

  useEffect(() => {
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      ws.current.onmessage = (event) => {
        let payload;
        try {
          payload = JSON.parse(event.data);
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
          return;
        }

        const metadata = payload.metadata || {};
        const instrumentId = metadata.instrument_id || metadata.driver || 'default';

        setInstruments((prev) => {
          const existing = prev[instrumentId] || { history: [] };
          const nextHistory =
            typeof payload.value === 'number'
              ? [
                  ...existing.history,
                  {
                    time: new Date(payload.timestamp || Date.now()).toLocaleTimeString([], {
                      hour12: false,
                      minute: '2-digit',
                      second: '2-digit',
                    }),
                    value: payload.value,
                  },
                ].slice(-HISTORY_LENGTH)
              : existing.history;

          return {
            ...prev,
            [instrumentId]: {
              id: instrumentId,
              driver: metadata.driver || 'GENERIC',
              lastMessage: payload,
              history: nextHistory,
              lastSeen: Date.now(),
            },
          };
        });
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        if (!cancelled) {
          reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
        }
      };

      ws.current.onerror = () => {
        setError('Bridge connection error');
        ws.current.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [url]);

  return { instruments, isConnected, error };
}
