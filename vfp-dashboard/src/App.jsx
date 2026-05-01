import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, Cpu, Gauge, Zap, AlertCircle, RefreshCw, Layers, Radio } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const Dashboard = () => {
  const [data, setData] = useState([]);
  const [lastMessage, setLastMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket('ws://127.0.0.1:8080');

      ws.current.onopen = () => {
        setIsConnected(true);
        setError(null);
        console.log('Connected to VFP Bridge');
      };

      ws.current.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          setLastMessage(payload);
          
          // If value is a number, add to history
          if (typeof payload.value === 'number') {
            setData(prev => {
              const newData = [...prev, {
                time: new Date().toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' }),
                value: payload.value,
                unit: payload.unit
              }].slice(-20); // Keep last 20 points
              return newData;
            });
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };

      ws.current.onclose = () => {
        setIsConnected(false);
        console.log('Disconnected from VFP Bridge. Retrying in 3s...');
        setTimeout(connect, 3000);
      };

      ws.current.onerror = (err) => {
        setError('Bridge connection error');
        ws.current.close();
      };
    };

    connect();
    return () => ws.current?.close();
  }, []);

  const StatCard = ({ icon: Icon, title, value, unit, status }) => (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass p-6 flex flex-col gap-2"
    >
      <div className="flex justify-between items-center text-dim">
        <div className="flex items-center gap-2">
          <Icon size={18} className="text-accent" />
          <span className="text-sm font-semibold uppercase tracking-wider">{title}</span>
        </div>
        <span className={`status-badge ${status === 'OK' ? 'status-ok' : 'status-error'}`}>
          {status || 'IDLE'}
        </span>
      </div>
      <div className="flex items-baseline gap-2 mt-2">
        <span className="text-4xl font-bold glow-text">{value ?? '---'}</span>
        <span className="text-lg text-dim font-medium">{unit}</span>
      </div>
    </motion.div>
  );

  return (
    <div className="flex-1 p-8 max-w-7xl mx-auto w-full flex flex-col gap-8">
      {/* Header */}
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
                  <span className="text-sm font-semibold">CONNECTING...</span>
                </div>
             )}
          </div>
          <div className="text-dim text-xs mono">
            {isConnected ? 'ws://127.0.0.1:8080' : 'OFFLINE'}
          </div>
        </div>
      </header>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          icon={Gauge} 
          title="Current Measurement" 
          value={lastMessage?.value} 
          unit={lastMessage?.unit}
          status={lastMessage?.status}
        />
        <StatCard 
          icon={Activity} 
          title="Signal Frequency" 
          value={lastMessage?.metadata?.frequency} 
          unit="Hz"
          status={lastMessage?.status}
        />
        <StatCard 
          icon={Zap} 
          title="Channel Info" 
          value={lastMessage?.channel ?? 'MAIN'} 
          unit=""
          status={lastMessage?.status}
        />
      </div>

      {/* Main Chart Section */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass p-8 flex-1 flex flex-col gap-6"
      >
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Layers className="text-accent" />
            <h2 className="text-2xl font-semibold m-0">Real-time Trace</h2>
          </div>
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
               <div className="w-3 h-3 rounded-full bg-accent"></div>
               <span className="text-xs text-dim uppercase font-bold tracking-tighter">Main Trace</span>
            </div>
          </div>
        </div>
        
        <div className="flex-1 min-h-[400px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorVal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#2e303a" vertical={false} />
              <XAxis 
                dataKey="time" 
                stroke="#4b5563" 
                fontSize={12} 
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="#4b5563" 
                fontSize={12} 
                tickLine={false}
                axisLine={false}
                domain={['auto', 'auto']}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1f2028', 
                  border: '1px solid #2e303a',
                  borderRadius: '8px',
                  color: '#f3f4f6'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#8b5cf6" 
                strokeWidth={3}
                fillOpacity={1} 
                fill="url(#colorVal)" 
                animationDuration={300}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Footer Info */}
      <footer className="flex justify-between items-center text-dim text-xs mono mt-auto py-4 border-t border-border-color">
        <div>INSTRUMATION HAL ENGINE v0.1.6</div>
        <div>STATION: LOCALHOST | DRIVER: {lastMessage?.metadata?.driver || 'GENERIC'}</div>
      </footer>
    </div>
  );
};

function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Dashboard />
    </div>
  );
}

export default App;
