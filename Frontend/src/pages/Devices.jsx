import { useEffect, useState } from 'react'
import { Check, Copy, Plus, Trash2, Settings } from 'lucide-react'
import { formatTimeAgo, getDevices, createDevice, deleteDevice, getDeviceConfig, updateDeviceConfig } from '../services/api'

const mapDeviceToUi = (device) => ({
  id: device.id,
  deviceId: `DEV-${String(device.id).padStart(3, '0')}`,
  name: device.device_name,
  apiKey: device.api_key || '',
  ip: device.ip_address || '-',
  status: String(device.status || 'offline').toLowerCase() === 'online' ? 'Online' : 'Offline',
  lastSeen: formatTimeAgo(device.last_seen),
  os: String(device.device_type || '-').toUpperCase(),
})

const maskApiKey = (apiKey) => {
  if (!apiKey) return 'Not available'
  const visible = apiKey.slice(0, 5)
  const hiddenLength = Math.max(apiKey.length - 5, 8)
  return `${visible}${'*'.repeat(hiddenLength)}`
}

export default function Devices() {
  const [devicesData, setDevicesData] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [copiedDeviceId, setCopiedDeviceId] = useState(null)
  const [hoveredDeviceId, setHoveredDeviceId] = useState(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [selectedDeviceForConfig, setSelectedDeviceForConfig] = useState(null)
  const [configForm, setConfigForm] = useState({
    heartbeat_interval: 30,
    log_min_interval: 5,
    log_max_interval: 10,
    local_detection: true,
    severity_threshold: 'MEDIUM',
  })
  const [newDevice, setNewDevice] = useState({
    device_name: '',
    device_type: '',
  })

  const handleAddDevice = () => {
    setShowAddModal(true)
  }

  const handleConfigureDevice = async (device) => {
    setError('')
    setSelectedDeviceForConfig(device)
    try {
      const config = await getDeviceConfig(device.id)
      let localDetection = true
      let severityThreshold = 'MEDIUM'

      if (config.alert_config) {
        try {
          const parsed = JSON.parse(config.alert_config)
          if (parsed.hasOwnProperty('local_detection')) {
            localDetection = parsed.local_detection
          }
          if (parsed.hasOwnProperty('severity_threshold')) {
            severityThreshold = parsed.severity_threshold
          }
        } catch (_err) {
          // ignore
        }
      }

      setConfigForm({
        heartbeat_interval: config.heartbeat_interval,
        log_min_interval: config.log_min_interval,
        log_max_interval: config.log_max_interval,
        local_detection: localDetection,
        severity_threshold: severityThreshold,
      })
      setShowConfigModal(true)
    } catch (err) {
      setError(err.message || 'Failed to fetch device configuration')
    }
  }

  const handleSubmitConfig = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const alertConfigString = JSON.stringify({
        local_detection: configForm.local_detection,
        severity_threshold: configForm.severity_threshold,
      })

      await updateDeviceConfig(selectedDeviceForConfig.id, {
        heartbeat_interval: configForm.heartbeat_interval,
        log_min_interval: configForm.log_min_interval,
        log_max_interval: configForm.log_max_interval,
        alert_config: alertConfigString,
      })

      const response = await getDevices()
      setDevicesData((response || []).map(mapDeviceToUi))
      setShowConfigModal(false)
    } catch (err) {
      setError(err.message || 'Failed to save configuration')
    }
  }

  const handleSubmitDevice = async (e) => {
    e.preventDefault()
    setError('')

    try {
      await createDevice({
        device_name: newDevice.device_name,
        device_type: newDevice.device_type,
      })
      // Reload devices after creating
      const response = await getDevices()
      setDevicesData((response || []).map(mapDeviceToUi))
      setNewDevice({ device_name: '', device_type: '' })
      setShowAddModal(false)
    } catch (err) {
      setError(err.message || 'Failed to add device')
    }
  }

  const handleRemoveDevice = async (deviceId) => {
    try {
      await deleteDevice(deviceId)
      // Reload devices after deleting
      const response = await getDevices()
      setDevicesData((response || []).map(mapDeviceToUi))
    } catch (err) {
      setError(err.message || 'Failed to remove device')
    }
  }

  const handleCopyApiKey = async (device) => {
    if (!device.apiKey) {
      setError('API key is not available for this device. Recreate device to get a new key.')
      return
    }

    try {
      await navigator.clipboard.writeText(device.apiKey)
      setCopiedDeviceId(device.id)
      window.setTimeout(() => {
        setCopiedDeviceId((current) => (current === device.id ? null : current))
      }, 2000)
    } catch (_err) {
      setError('Unable to copy API key. Please copy it manually.')
    }
  }

  useEffect(() => {
    let isMounted = true

    const loadDevices = async () => {
      setIsLoading(true)
      setError('')

      try {
        const response = await getDevices()
        if (isMounted) {
          setDevicesData((response || []).map(mapDeviceToUi))
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message || 'Failed to load devices')
          setDevicesData([])
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadDevices()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-soc-text mb-2">Devices</h1>
          <p className="text-section-subtitle">Monitor and manage all network devices</p>
        </div>
        <button
          onClick={handleAddDevice}
          className="flex items-center gap-2 btn-primary px-4 py-2 rounded-lg"
        >
          <Plus size={20} />
          Add Device
        </button>
      </div>

      {error && <p className="text-sm text-soc-critical">{error}</p>}

      {/* Devices Table */}
      <div className="card-base p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-soc-border bg-soc-bg">
                 <th className="table-cell-muted text-label">Device ID</th>
                 <th className="table-cell-muted text-label">Device Name</th>
                 <th className="table-cell-muted text-label">API Key</th>
                 <th className="table-cell-muted text-label">IP Address</th>
                 <th className="table-cell-muted text-label">Status</th>
                 <th className="table-cell-muted text-label">Last Seen</th>
                 <th className="table-cell-muted text-label">Operating System</th>
                 <th className="table-cell-muted text-label">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr>
                  <td className="table-cell text-soc-muted" colSpan={8}>Loading devices...</td>
                </tr>
              )}

              {!isLoading && devicesData.length === 0 && (
                <tr>
                  <td className="table-cell text-soc-muted" colSpan={8}>No devices found.</td>
                </tr>
              )}

              {devicesData.map((device) => (
                <tr
                  key={device.id}
                  onMouseEnter={() => setHoveredDeviceId(device.id)}
                  onMouseLeave={() => setHoveredDeviceId(null)}
                  className="border-b border-soc-border hover:bg-soc-bg transition-colors duration-200 cursor-pointer relative"
                >
                  <td className="table-cell font-mono text-xs">{device.deviceId}</td>
                  <td className="table-cell font-medium">{device.name}</td>
                  <td className="table-cell">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-soc-secondary">{maskApiKey(device.apiKey)}</span>
                      <button
                        onClick={() => handleCopyApiKey(device)}
                        className="p-1.5 rounded hover:bg-soc-bg transition-smooth text-soc-secondary hover:text-soc-text disabled:opacity-40"
                        title={device.apiKey ? 'Copy API key' : 'API key unavailable'}
                        disabled={!device.apiKey}
                      >
                        {copiedDeviceId === device.id ? <Check size={14} /> : <Copy size={14} />}
                      </button>
                    </div>
                  </td>
                  <td className="table-cell font-mono text-xs">{device.ip}</td>
                  <td className="table-cell">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          device.status === 'Online' ? 'bg-soc-low' : 'bg-soc-critical'
                        }`}
                      />
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${
                          device.status === 'Online'
                            ? 'bg-green-500 bg-opacity-10 text-soc-low'
                            : 'bg-red-500 bg-opacity-10 text-soc-critical'
                        }`}
                      >
                        {device.status}
                      </span>
                    </div>
                  </td>
                  <td className="table-cell-muted text-sm">{device.lastSeen}</td>
                  <td className="table-cell">{device.os}</td>
                  <td className="table-cell">
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleConfigureDevice(device)
                        }}
                        className="p-2 text-soc-secondary hover:text-soc-text hover:bg-soc-bg rounded transition-all duration-200"
                        title="Configure device"
                      >
                        <Settings size={18} />
                      </button>
                      {hoveredDeviceId === device.id && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleRemoveDevice(device.id)
                          }}
                          className="p-2 text-soc-critical hover:bg-red-500 hover:bg-opacity-10 rounded transition-all duration-200"
                          title="Delete device"
                        >
                          <Trash2 size={18} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Table Footer */}
        <div className="px-6 py-4 border-t border-soc-border bg-soc-bg flex items-center justify-between text-xs text-soc-secondary">
          <p>Showing {devicesData.length} devices</p>
          <div className="flex gap-2">
            <button className="px-3 py-2 hover:bg-soc-card rounded transition-all duration-200">Previous</button>
            <button className="px-3 py-2 bg-soc-accent text-white rounded transition-all duration-200">1</button>
            <button className="px-3 py-2 hover:bg-soc-card rounded transition-all duration-200">2</button>
            <button className="px-3 py-2 hover:bg-soc-card rounded transition-all duration-200">Next</button>
          </div>
        </div>
      </div>

      {/* Add Device Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-soc-card rounded-lg p-8 max-w-md w-full mx-4 space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-soc-text">Add New Device</h2>
              <p className="text-section-subtitle">Register a new device to monitor</p>
            </div>

            <form onSubmit={handleSubmitDevice} className="space-y-4">
              <div>
                <label className="block text-label mb-2">Device Name</label>
                <input
                  type="text"
                  value={newDevice.device_name}
                  onChange={(e) =>
                    setNewDevice((prev) => ({
                      ...prev,
                      device_name: e.target.value,
                    }))
                  }
                  className="input-soc w-full"
                  placeholder="e.g., Server-01"
                  required
                />
              </div>

              <div>
                <label className="block text-label mb-2">Device Type</label>
                <select
                  value={newDevice.device_type}
                  onChange={(e) =>
                    setNewDevice((prev) => ({
                      ...prev,
                      device_type: e.target.value,
                    }))
                  }
                  className="input-soc w-full"
                  required
                >
                  <option value="">Select device type</option>
                  <option value="windows">Windows</option>
                  <option value="linux">Linux</option>
                  <option value="web">Web</option>
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 border border-soc-border text-soc-text rounded-lg hover:bg-soc-bg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary py-2 rounded-lg"
                >
                  Add Device
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Configure Device Modal */}
      {showConfigModal && selectedDeviceForConfig && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-soc-card rounded-lg p-8 max-w-md w-full mx-4 space-y-6">
            <div>
              <h2 className="text-2xl font-bold text-soc-text">Configure Device</h2>
              <p className="text-section-subtitle">Adjust settings for {selectedDeviceForConfig.name}</p>
            </div>

            <form onSubmit={handleSubmitConfig} className="space-y-4">
              <div>
                <label className="block text-label mb-2">Heartbeat Interval (seconds)</label>
                <input
                  type="number"
                  min="5"
                  max="300"
                  value={configForm.heartbeat_interval}
                  onChange={(e) =>
                    setConfigForm((prev) => ({
                      ...prev,
                      heartbeat_interval: parseInt(e.target.value) || 30,
                    }))
                  }
                  className="input-soc w-full"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-label mb-2">Min Log Interval (s)</label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={configForm.log_min_interval}
                    onChange={(e) =>
                      setConfigForm((prev) => ({
                        ...prev,
                        log_min_interval: parseInt(e.target.value) || 5,
                      }))
                    }
                    className="input-soc w-full"
                    required
                  />
                </div>
                <div>
                  <label className="block text-label mb-2">Max Log Interval (s)</label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    value={configForm.log_max_interval}
                    onChange={(e) =>
                      setConfigForm((prev) => ({
                        ...prev,
                        log_max_interval: parseInt(e.target.value) || 10,
                      }))
                    }
                    className="input-soc w-full"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-label mb-2">Alert Severity Threshold</label>
                <select
                  value={configForm.severity_threshold}
                  onChange={(e) =>
                    setConfigForm((prev) => ({
                      ...prev,
                      severity_threshold: e.target.value,
                    }))
                  }
                  className="input-soc w-full"
                  required
                >
                  <option value="LOW">Low & Above</option>
                  <option value="MEDIUM">Medium & Above</option>
                  <option value="HIGH">High Only</option>
                </select>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <input
                  type="checkbox"
                  id="local_detection"
                  checked={configForm.local_detection}
                  onChange={(e) =>
                    setConfigForm((prev) => ({
                      ...prev,
                      local_detection: e.target.checked,
                    }))
                  }
                  className="rounded bg-soc-bg border-soc-border text-soc-info focus:ring-soc-info"
                />
                <label htmlFor="local_detection" className="text-soc-text font-medium select-none cursor-pointer">
                  Enable Local Threat Detection
                </label>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowConfigModal(false)}
                  className="flex-1 px-4 py-2 border border-soc-border text-soc-text rounded-lg hover:bg-soc-bg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary py-2 rounded-lg"
                >
                  Save Settings
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
