import { X } from 'lucide-react'

const getSeverityColor = (severity) => {
  const colors = {
    Critical: '#ef4444',
    High: '#f97316',
    Medium: '#f59e0b',
    Low: '#22c55e',
    Info: '#3b82f6',
  }
  return colors[severity] || '#e2e8f0'
}

export default function AlertDrawer({ alert, onClose }) {
  if (!alert) return null

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-200"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-96 bg-soc-card border-l border-soc-border shadow-2xl overflow-y-auto z-50 transform transition-transform duration-300">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-soc-border sticky top-0 bg-soc-card">
          <h2 className="text-xl font-bold text-soc-text">Alert Details</h2>
           <button
             onClick={onClose}
             className="p-2 hover:bg-soc-bg rounded-lg transition-smooth text-soc-secondary hover:text-soc-text"
           >
             <X size={20} />
           </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Severity Badge */}
          <div>
            <p className="text-soc-secondary text-sm font-medium mb-2">Severity</p>
            <span
              className="inline-block px-4 py-2 rounded-lg font-bold text-white"
              style={{ backgroundColor: getSeverityColor(alert.severity) }}
            >
              {alert.severity}
            </span>
          </div>
         {/* Details Grid */}
         <div className="space-y-4 mt-6">
            {[
              { label: 'Alert ID', value: `#ALT-${alert.id}` },
              { label: 'Timestamp', value: alert.timestamp },
              { label: 'Source', value: alert.source },
              { label: 'Source IP', value: alert.ip },
              { label: 'Destination IP', value: alert.destIp },
              { label: 'Rule Name', value: alert.rule },
              { label: 'Rule Category', value: alert.category },
              { label: 'Protocol', value: alert.protocol },
              { label: 'Port', value: alert.port },
            ].map((item, idx) => (
              <div key={idx} className="pb-4 border-b border-soc-border">
                <p className="text-soc-secondary text-xs font-medium uppercase mb-1">{item.label}</p>
                <p className="text-soc-text font-mono text-sm break-all">{item.value}</p>
              </div>
            ))}
          </div>

          {/* Full Payload */}
          <div>
            <p className="text-soc-secondary text-sm font-medium mb-3">Alert Payload</p>
            <div className="bg-soc-bg p-4 rounded-lg border border-soc-border overflow-x-auto">
              <pre className="text-soc-muted text-xs font-mono whitespace-pre-wrap break-words leading-relaxed">
                {JSON.stringify(alert, null, 2)}
              </pre>
            </div>
          </div>

          {/* Actions */}
          <div className="space-y-3 pt-4 border-t border-soc-border">
            <select className="input-soc w-full">
              <option>Assign to...</option>
              <option>John Doe</option>
              <option>Jane Smith</option>
              <option>Mike Johnson</option>
            </select>

            <select className="input-soc w-full">
              <option>Change Status</option>
              <option>Open</option>
              <option>Acknowledged</option>
              <option>Investigating</option>
              <option>Resolved</option>
              <option>False Positive</option>
            </select>

            <button className="btn-danger w-full">
              Delete Alert
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
