export default function FiltersBar({
  filters,
  devices = [],
  isLoadingDevices = false,
  onChange,
  onApply,
  onReset,
}) {
  const handleFieldChange = (field) => (event) => {
    onChange?.({ ...filters, [field]: event.target.value })
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    onApply?.()
  }

  return (
    <form onSubmit={handleSubmit} className="card-base flex flex-wrap gap-4 items-center p-3 md:p-4">
      <select
        className="input-soc w-full sm:w-auto"
        value={filters.severity}
        onChange={handleFieldChange('severity')}
      >
        <option value="">All Severities</option>
        <option value="CRITICAL">Critical</option>
        <option value="HIGH">High</option>
        <option value="MEDIUM">Medium</option>
        <option value="LOW">Low</option>
      </select>

      <select
        className="input-soc w-full sm:w-auto"
        value={filters.deviceId}
        onChange={handleFieldChange('deviceId')}
      >
        <option value="">All Devices</option>
        {devices.map((device) => (
          <option key={device.id} value={device.id}>
            {device.device_name}
          </option>
        ))}
        {!devices.length && isLoadingDevices && <option value="">Loading devices...</option>}
      </select>

      <select
        className="input-soc w-full sm:w-auto"
        value={filters.timeRange}
        onChange={handleFieldChange('timeRange')}
      >
        <option value="">All Time</option>
        <option value="24h">Last 24 Hours</option>
        <option value="7d">Last 7 Days</option>
        <option value="30d">Last 30 Days</option>
      </select>

      <input
        type="text"
        value={filters.search}
        onChange={handleFieldChange('search')}
        placeholder="Search by description..."
        className="input-soc flex-1 min-w-[200px]"
      />

      <button type="submit" className="btn-primary px-6 py-2 w-full sm:w-auto">
        Filter
      </button>

      <button type="button" onClick={onReset} className="btn-primary px-6 py-2 w-full sm:w-auto">
        Reset
      </button>
    </form>
  )
}
