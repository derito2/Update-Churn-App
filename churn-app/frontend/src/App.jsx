import { useState } from "react";
import FileUpload from "./components/FileUpload";
import KpiCards from "./components/KpiCards";
import ResultsTable from "./components/ResultsTable";
import ChurnByStateChart from "./components/ChurnByStateChart";
import CorrelationChart from "./components/CorrelationChart";
import ChatWidget from "./components/ChatWidget";
import { predecirChurn } from "./services/api";

export default function App() {
  const [kpis, setKpis] = useState(null);
  const [resultados, setResultados] = useState(null);
  const [uploadId, setUploadId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFile = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const data = await predecirChurn(file);
      setKpis(data.kpis);
      setResultados(data.resultados);
      setUploadId(data.upload_id);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al procesar el archivo");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-bg flex flex-col overflow-hidden px-6 py-4 gap-4">
      <header className="flex-shrink-0 text-center">
        <h1 className="text-xl font-semibold text-ink tracking-tight">
          Churn Intelligence
        </h1>
        <p className="text-sm text-muted mt-0.5">
          Análisis de retención y riesgo de clientes
        </p>
        {error && (
          <div className="mt-2 bg-risk-50 border border-risk/30 text-risk rounded-btn px-3 py-1.5 text-xs inline-block">
            {error}
          </div>
        )}
      </header>

      <div className="flex-shrink-0" style={{ height: "84px" }}>
        <KpiCards kpis={kpis} />
      </div>

      <div className="flex-1 grid grid-cols-2 grid-rows-2 gap-4 min-h-0">
        <div className="min-h-0">
          <FileUpload onFileSelected={handleFile} loading={loading} />
        </div>
        <div className="min-h-0">
          <ResultsTable resultados={resultados} />
        </div>
        <div className="min-h-0">
          <ChurnByStateChart uploadId={uploadId} />
        </div>
        <div className="min-h-0">
          <CorrelationChart uploadId={uploadId} />
        </div>
      </div>

      <ChatWidget uploadId={uploadId} />
    </div>
  );
}