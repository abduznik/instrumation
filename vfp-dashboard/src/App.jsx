import { RefreshCw, Radio, Layers } from 'lucide-react';
import { useInstrumentData } from './hooks/useInstrumentData';
import { StatusGrid } from './components/StatusGrid';

const BRIDGE_URL = 'ws://127.0.0.1:8080';

function Dashboard() {
  const { instruments, isConnected, error } = useInstrumentData(BRIDGE_URL);
  const instrumentCount = Object.keys(instruments).length;

  return (
    <div className="flex-1 p-8 max-w-7xl mx-auto w-full flex flex-col gap-8">
      <header className="flex justify-between items-end mb-4">
        <div>
          <div className="flex items-center gap-2 text-accent mb-2">
            <Radio size={20} />
            <span className="font-bold tracking-widest uppercase text-xs">Instrumation HAL</span>
          </div>
          <h1 className="text-5xl font-bold tracking-tight m-0">Virtual Front Panel</h1>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-4">
            {isConnected ? (
              <div className="flex items-center">
                <span className="live-indicator"></span>
                <span className="text-success text-sm font-semibold">LIVE BRIDGE</span>
              </div>
            ) : (
              <div className="flex items-center text-error">
                <RefreshCw size={16} className="animate-spin mr-2" />
                <span className="text-sm font-semibold">
                  {error ? error.toUpperCase() : 'CONNECTING...'}
                </span>
              </div>
            )}
          </div>
          <div className="text-dim text-xs mono">
            {isConnected ? BRIDGE_URL : 'OFFLINE'}
          </div>
        </div>
      </header>

      <section className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <Layers className="text-accent" />
          <h2 className="text-2xl font-semibold m-0">Instruments</h2>
          <span className="text-dim text-sm mono">({instrumentCount})</span>
        </div>
        <StatusGrid instruments={instruments} />
      </section>

      <footer className="flex justify-between items-center text-dim text-xs mono mt-auto py-4 border-t border-border-color">
        <div>INSTRUMATION HAL ENGINE v0.10.0</div>
        <div>STATION: LOCALHOST</div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Dashboard />
    </div>
  );
}

export default App;
