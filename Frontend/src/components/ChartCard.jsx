export default function ChartCard({ title, children }) {
  return (
    <div className="card-base p-6">
      <h3 className="text-card-title">{title}</h3>
      {children}
    </div>
  )
}
