import { api } from "../lib/api";

export async function listTemplates() {
  const { data } = await api.get("/templates");
  return data;
}

export async function uploadTemplate(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/templates/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}
