import { api } from "../lib/api";

export async function listImages() {
  const { data } = await api.get("/reports/images");
  return data;
}

export async function uploadReportImage({ file, caption, sectionHeading }) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("caption", caption || "");
  if (sectionHeading) formData.append("section_heading", sectionHeading);
  const { data } = await api.post("/reports/images/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function generateDocx(payload) {
  try {
    const response = await api.post("/reports/generate-docx", payload, {
      responseType: "blob",
      timeout: 120000
    });
    return downloadBlob(response.data, filenameFromDisposition(response.headers["content-disposition"]) || "report.docx");
  } catch (error) {
    throw await normalizeBlobError(error);
  }
}

export async function generatePdf(payload) {
  try {
    const response = await api.post("/reports/generate-pdf", payload, {
      responseType: "blob",
      timeout: 180000
    });
    return downloadBlob(response.data, filenameFromDisposition(response.headers["content-disposition"]) || "report.pdf");
  } catch (error) {
    throw await normalizeBlobError(error);
  }
}

async function normalizeBlobError(error) {
  const data = error?.response?.data;
  if (data instanceof Blob) {
    try {
      const text = await data.text();
      const payload = JSON.parse(text);
      return new Error(payload.detail || "Export failed");
    } catch {
      return error;
    }
  }
  return error;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
  return filename;
}

function filenameFromDisposition(disposition = "") {
  const match = disposition.match(/filename="?([^"]+)"?/i);
  return match?.[1];
}
