function Card({ label, value, suffix = "" }) {
  return (
    <div className="bg-surface border border-border rounded-card px-4 py-3 flex flex-col items-center justify-center text-center h-full">
      <span className="text-xs font-medium text-muted">{label}</span>
      <span className="text-2xl font-bold text-ink leading-tight mt-0.5">
        {value ?? "—"}
        {suffix}
      </span>
    </div>
  );
}

export default function KpiCards({ kpis }) {
  return (
    <div className="grid grid-cols-4 gap-4 h-full">
      <Card label="Usuarios analizados" value={kpis?.total_usuarios} />
      <Card label="Tasa de churn predicha" value={kpis?.tasa_churn_predicha} suffix="%" />
      <Card label="Satisfacción promedio" value={kpis?.satisfaccion_promedio} suffix="/10" />
      <Card label="Ingreso mensual promedio" value={kpis?.ingreso_promedio} suffix=" MXN" />
    </div>
  );
}