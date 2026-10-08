function BadgeChurn({ valor }) {
  const esRiesgo = valor === "Sí";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        esRiesgo ? "bg-risk-50 text-risk" : "bg-teal-50 text-teal"
      }`}
    >
      {esRiesgo ? "En riesgo" : "Bajo riesgo"}
    </span>
  );
}

export default function ResultsTable({ resultados }) {
  if (!resultados || resultados.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-card p-4 h-full flex items-center justify-center">
        <p className="text-muted text-sm">Sube un CSV para ver los resultados aquí.</p>
      </div>
    );
  }

  const columnas = Object.keys(resultados[0]);

  return (
    <div className="bg-surface border border-border rounded-card p-4 h-full flex flex-col">
      <div className="mb-2 text-center">
        <h2 className="text-sm font-semibold text-ink">Resultados de predicción</h2>
        <span className="text-xs text-muted">{resultados.length} usuarios</span>
        </div>

      <div
        className="flex-1 overflow-auto rounded-card border border-border"
        style={{ overscrollBehavior: "contain" }}
      >
        <table className="min-w-full text-sm">
          <thead className="sticky top-0 bg-bg z-10">
            <tr className="text-muted border-b border-border">
              {columnas.map((col) => (
                <th key={col} className="text-left font-medium py-2 px-3 whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {resultados.map((fila, i) => (
              <tr key={i} className="border-b border-border hover:bg-bg/60">
                {columnas.map((col) => (
                  <td key={col} className="py-2 px-3 whitespace-nowrap text-ink">
                    {col === "prediccion_churn" ? (
                      <BadgeChurn valor={fila[col]} />
                    ) : col === "probabilidad_churn" ? (
                      <span className="text-muted">{fila[col]}%</span>
                    ) : (
                      String(fila[col])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}