import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { preguntarAlAgente } from "../services/api";

export default function ChatWidget({ uploadId }) {
  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const enviar = async () => {
    if (!input.trim() || loading) return;
    const pregunta = input;
    setMensajes((prev) => [...prev, { rol: "usuario", texto: pregunta }]);
    setInput("");
    setLoading(true);

    try {
      const respuesta = await preguntarAlAgente(pregunta, uploadId);
      setMensajes((prev) => [...prev, { rol: "agente", texto: respuesta }]);
    } catch (err) {
      setMensajes((prev) => [
        ...prev,
        { rol: "agente", texto: "El asistente está muy solicitado, intenta de nuevo en unos segundos." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (!abierto) {
    return (
      <button
        onClick={() => setAbierto(true)}
        className="fixed bottom-6 right-6 z-50 bg-brand hover:bg-brand-700 text-white rounded-full w-12 h-12 shadow-md flex items-center justify-center transition-colors"
        aria-label="Abrir Churn Copilot"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
        </svg>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 h-[28rem] bg-surface border border-border rounded-card shadow-lg flex flex-col overflow-hidden">
      <div className="flex justify-between items-start px-4 py-3 border-b border-border">
        <div>
          <h2 className="text-sm font-semibold text-ink">Churn Agent</h2>
          <p className="text-xs text-muted mt-0.5">
            Consulta el riesgo, comportamiento y segmentos de tus clientes.
          </p>
        </div>
        <button
          onClick={() => setAbierto(false)}
          className="text-muted hover:text-ink text-base leading-none"
          aria-label="Minimizar"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {mensajes.length === 0 && (
          <p className="text-muted text-xs text-center mt-6">
            Pregúntale al Churn Agent sobre tus clientes.
          </p>
        )}
        {mensajes.map((m, i) => (
          <div
            key={i}
            className={`max-w-[88%] px-3 py-2 rounded text-xs leading-relaxed ${
              m.rol === "usuario"
                ? "bg-brand-50 text-ink ml-auto"
                : "bg-bg text-ink"
            }`}
          >
            {m.rol === "agente" ? (
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                  strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
                  ul: ({ children }) => <ul className="list-disc list-inside space-y-0.5 mb-1">{children}</ul>,
                }}
              >
                {m.texto}
              </ReactMarkdown>
            ) : (
              m.texto
            )}
          </div>
        ))}
        {loading && <div className="text-muted text-xs">Analizando...</div>}
      </div>

      <div className="flex gap-2 p-3 border-t border-border">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && enviar()}
          placeholder="Escribe tu pregunta..."
          className="flex-1 bg-bg border border-border rounded-btn px-2.5 py-1.5 text-xs text-ink focus:outline-none focus:border-brand"
          disabled={loading || !uploadId}
        />
        <button
          onClick={enviar}
          disabled={loading || !uploadId}
          className="bg-brand hover:bg-brand-700 text-white px-3 py-1.5 rounded-btn text-xs font-medium disabled:opacity-40 transition-colors"
        >
          Enviar
        </button>
      </div>

      {!uploadId && (
        <p className="text-xs text-muted text-center px-3 pb-2">
          Sube un CSV primero para activar el Churn Copilot.
        </p>
      )}
    </div>
  );
}