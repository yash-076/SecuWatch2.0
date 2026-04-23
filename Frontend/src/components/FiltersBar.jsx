export default function FiltersBar({ onFiltersChange }) {
  return (
    <div className="card-base flex flex-wrap gap-4 items-center p-3 md:p-4">
      <select className="input-soc w-full sm:w-auto">
        <option>All Severities</option>
        <option>High</option>
        <option>Medium</option>
        <option>Low</option>
      </select>

      <select className="input-soc w-full sm:w-auto">
        <option>All Sources</option>
        <option>Windows</option>
        <option>Apache</option>
        <option>Linux</option>
      </select>

      <select className="input-soc w-full sm:w-auto">
        <option>Last 24 Hours</option>
        <option>Last 7 Days</option>
        <option>Last 30 Days</option>
        <option>Custom Range</option>
      </select>

      <select className="input-soc w-full sm:w-auto">
        <option>All Statuses</option>
        <option>New</option>
        <option>Assigned</option>
        <option>Resolved</option>
      </select>

      <input
        type="text"
        placeholder="Search by IP, Rule, or Source..."
        className="input-soc flex-1 min-w-[200px]"
      />

      <button className="btn-primary px-6 py-2 w-full sm:w-auto">
        Filter
      </button>
    </div>
  )
}
