export default function StatCard({ icon: Icon, label, value, subtitle, trend }) {
  return (
    <div className="card-base hover-effect p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-soc-secondary text-sm font-medium mb-2">{label}</p>
          <p className="text-3xl font-bold text-soc-text mb-2">{value}</p>
           {subtitle && (
             <p className="text-xs text-soc-muted font-medium">{subtitle}</p>
           )}
        </div>
        <div className="p-3 bg-soc-info bg-opacity-10 rounded-lg">
          <Icon size={24} className="text-soc-info" />
        </div>
      </div>
      {trend && (
        <div className="mt-4 flex items-center gap-2">
          <span className={`text-sm font-medium ${trend > 0 ? 'text-soc-high' : 'text-soc-low'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
          <span className="text-xs text-soc-muted">vs last week</span>
        </div>
      )}
    </div>
  )
}
