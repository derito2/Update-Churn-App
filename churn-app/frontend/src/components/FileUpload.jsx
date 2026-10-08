export default function FileUpload({ onFileSelected, loading }) {
  const handleChange = (e) => {
    const file = e.target.files[0];
    if (file) onFileSelected(file);
  };

  return (
    <div className="bg-surface border border-border rounded-card p-4 h-full flex flex-col">
      <h2 className="text-sm font-semibold text-ink mb-3 text-center">Cargar datos</h2>
      <label className="flex-1 flex flex-col items-center justify-center border border-dashed border-border rounded-card cursor-pointer hover:border-brand hover:bg-brand-50/40 transition-colors px-3">
        <span className="text-muted text-xs text-center">
          {loading ? "Procesando archivo..." : "Selecciona un archivo .csv"}
        </span>
        <input
          type="file"
          accept=".csv"
          onChange={handleChange}
          disabled={loading}
          className="hidden"
        />
      </label>
    </div>
  );
}