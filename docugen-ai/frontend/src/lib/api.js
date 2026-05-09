import axios from "axios";
import { env } from "../config/env";

export const api = axios.create({
  baseURL: env.apiUrl,
  timeout: 30000
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      if (error.code === "ECONNABORTED") {
        error.message = "The request timed out. The backend may still be processing the file.";
      } else {
        error.message = `Cannot reach backend at ${env.apiUrl}. Check that FastAPI is running.`;
      }
    }
    return Promise.reject(error);
  }
);

export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
}
