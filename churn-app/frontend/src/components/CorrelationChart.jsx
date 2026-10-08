import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Cell, ReferenceLine,
} from "recharts";
import axios from "axios";

export default function CorrelationChart({ uploadId }) {
  const [datos, setDatos] = useState([]);

  useEffect(() => {
    if (!uploadId) return;
    axios
      .get(`http://localhost:8000/correlaciones/${uploadId}`)
      .then(({ data }) => setDatos(data.correlaciones))
      .catch(console.error);
  }, [uploadId]);

  return (
    <div className="bg-surface border border-border rounded-card p-4 h-full flex flex-col">
      <h2 className="text-sm font-semibold text-ink mb-2 text-center">Variables más relevantes para el churn</h2>
      <div className="flex-1 min-h-0">
        {datos.length === 0 ? (
          <div className="h-full flex items-center justify-center text-muted text-xs">
            Sube un CSV para ver esta gráfica.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={datos} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E4E7EC" horizontal={false} />
              <XAxis type="number" domain={[-1, 1]} tick={{ fill: "#667085", fontSize: 11 }} axisLine={{ stroke: "#E4E7EC" }} tickLine={false} />
              <YAxis type="category" dataKey="variable" width={130} tick={{ fill: "#667085", fontSize: 11 }} axisLine={false} tickLine={false} />
              <ReferenceLine x={0} stroke="#E4E7EC" />
              <Tooltip
                contentStyle={{ backgroundColor: "#FFFFFF", border: "1px solid #E4E7EC", borderRadius: 8, fontSize: 12 }}
                formatter={(value) => [value, "Correlación"]}
              />
              <Bar dataKey="correlacion" radius={[0, 4, 4, 0]}>
                {datos.map((d, i) => (
                  <Cell key={i} fill={d.correlacion >= 0 ? "#E45756" : "#0F9D8A"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}