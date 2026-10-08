import { useState } from "react";
import axios from "axios";

export default function StrategyReport({ uploadId }) {
  const [reporte, setReporte] = useState(null);
  const [loading, setLoading] = useState(false);

  const generar = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`http://localhost:8000/estrategia/${uploadId}`);
      setReporte(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-navy-900 border border-navy-700 rounded-2xl p-6 shadow-xl mt-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gold-400">
          Reporte de estrategia de retención
        </h2>
        <button
          onClick={generar}
          disabled={loading}
          className="bg-gold-500 text-navy-950 font-semibold px-4 py-2 rounded-lg text-sm hover:bg-gold-400 disabled:opacity-50"
        >
          {loading ? "Generando..." : "Generar análisis"}
        </button>
      </div>

      {reporte && (
        <div className="space-y-6">
          <div className="bg-navy-950 rounded-xl p-4 border border-navy-700">
            <p className="text-slate-300">{reporte.resumen_ejecutivo}</p>
            <p className="text-gold-400 font-bold mt-2">
              Ingreso mensual en riesgo: ${reporte.ingreso_total_en_riesgo?.toLocaleString()} MXN
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reporte.segmentos?.map((seg, i) => (
              <div key={i} className="bg-navy-950 rounded-xl p-4 border border-navy-700">
                <h3 className="font-semibold text-white">{seg.nombre}</h3>
                <p className="text-sm text-slate-400 mt-1">{seg.num_usuarios} usuarios</p>
                <p className="text-sm text-slate-300 mt-2">{seg.descripcion}</p>
                <p className="text-sm text-emerald-400 mt-2">→ {seg.recomendacion}</p>
              </div>
            ))}
          </div>

          <div className="bg-navy-950 rounded-xl p-4 border border-gold-500/30">
            <h3 className="font-semibold text-gold-400 mb-2">Top 3 acciones prioritarias</h3>
            <ol className="list-decimal list-inside text-sm text-slate-300 space-y-1">
              {reporte.top_3_acciones_prioritarias?.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}