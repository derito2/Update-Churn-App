import axios from "axios";

const API_URL = "http://localhost:8000";

export async function predecirChurn(file) {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await axios.post(`${API_URL}/predict`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return data; // { kpis, resultados }
}

export async function preguntarAlAgente(pregunta, uploadId) {
  const { data } = await axios.post(`${API_URL}/chat`, {
    pregunta,
    upload_id: uploadId,
  });
  return data.respuesta;
}