import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  ResponsiveContainer, CartesianGrid,
} from "recharts";
import axios from "axios";

const COLORES_SEXO = {
  H: "#2563EB",
  M: "#b443a3",
  Hombre: "#2563EB",
  Mujer: "#b443a3",
};

export default function ChurnByStateChart({ uploadId }) {
  const [datos, setDatos] = useState([]);
  const [sexos, setSexos] = useState([]);

  useEffect(() => {
    if (!uploadId) return;
    axios
      .get(`http://localhost:8000/churn-por-estado-sexo/${uploadId}`)
      .then(({ data }) => {
        setDatos(data.datos);
        setSexos(data.sexos);
      })
      .catch(console.error);
  }, [uploadId]);

  return (
    <div className="bg-surface border border-border rounded-card p-4 h-full flex flex-col">
      <h2 className="text-sm font-semibold text-ink text-center">Clientes en riesgo por estado</h2>
      <p className="text-xs text-muted mb-2 text-center">Top 5 estados · distribución por sexo</p>
      <div className="flex-1 min-h-0">
        {datos.length === 0 ? (
          <div className="h-full flex items-center justify-center text-muted text-xs">
            Sube un CSV para ver esta gráfica.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={datos} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E4E7EC" vertical={false} />
              <XAxis dataKey="estado" tick={{ fill: "#667085", fontSize: 11 }} axisLine={{ stroke: "#E4E7EC" }} tickLine={false} />
              <YAxis tick={{ fill: "#667085", fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: "#FFFFFF", border: "1px solid #E4E7EC", borderRadius: 8, fontSize: 12 }}
              />
              <Legend wrapperStyle={{ fontSize: 12, color: "#667085" }} />
              {sexos.map((s) => (
                <Bar key={s} dataKey={s} stackId="a" fill={COLORES_SEXO[s] || "#667085"} radius={[0, 0, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}