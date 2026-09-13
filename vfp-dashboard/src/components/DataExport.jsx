import { useState } from 'react';
import { Download, ChevronDown } from 'lucide-react';

/**
 * Toolbar button that downloads current instrument readings from the
 * dashboard.py REST API (`/api/readings`) as CSV or JSON.
 */
export function DataExport({ apiBase = '' }) {
  const [open, setOpen] = useState(false);

  const download = async (format) => {
    setOpen(false);
    const url = `${apiBase}/api/readings${format === 'csv' ? '?format=csv' : ''}`;
    const res = await fetch(url);
    const blob = await res.blob();

    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = format === 'csv' ? 'readings.csv' : 'readings.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);
  };

  return (
    <div className="relative">
      <button
        className="flex items-center gap-2 px-3 py-2 rounded glass text-sm font-semibold"
        onClick={() => setOpen((v) => !v)}
      >
        <Download size={16} />
        Export
        <ChevronDown size={14} />
      </button>
      {open && (
        <div className="absolute right-0 mt-2 glass rounded overflow-hidden z-10 min-w-[140px]">
          <button
            className="block w-full text-left px-4 py-2 text-sm hover:bg-white/10"
            onClick={() => download('csv')}
          >
            Export as CSV
          </button>
          <button
            className="block w-full text-left px-4 py-2 text-sm hover:bg-white/10"
            onClick={() => download('json')}
          >
            Export as JSON
          </button>
        </div>
      )}
    </div>
  );
}

export default DataExport;
