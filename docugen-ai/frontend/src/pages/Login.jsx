import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import Button from "../components/common/Button.jsx";
import Field from "../components/common/Field.jsx";
import LoadingSpinner from "../components/common/LoadingSpinner.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { useToast } from "../context/ToastContext.jsx";
import { getErrorMessage } from "../utils/errors.js";

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Login() {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  function validate() {
    const nextErrors = {};
    if (!emailPattern.test(form.email)) nextErrors.email = "Enter a valid email address.";
    if (!form.password) nextErrors.password = "Password is required.";
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setApiError("");
    if (!validate()) return;

    setLoading(true);
    try {
      await login({ email: form.email.trim(), password: form.password });
      showToast({ type: "success", title: "Logged in", message: "Welcome back to DocuGen AI." });
      navigate(location.state?.from?.pathname || "/app", { replace: true });
    } catch (error) {
      const message = getErrorMessage(error, "Unable to log in. Please try again.");
      setApiError(message);
      showToast({ type: "error", title: "Login failed", message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mx-auto mt-16 max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-2xl font-semibold">Login</h2>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Access your DocuGen AI workspace.</p>
      <form className="mt-6 space-y-4" onSubmit={handleSubmit} noValidate>
        <Field label="Email" error={errors.email}>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
            type="email"
            value={form.email}
            onChange={(event) => setForm({ ...form, email: event.target.value })}
          />
        </Field>
        <Field label="Password" error={errors.password}>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
            type="password"
            value={form.password}
            onChange={(event) => setForm({ ...form, password: event.target.value })}
          />
        </Field>
        {apiError ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-200">{apiError}</p> : null}
        <Button className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner label="Logging in" /> : "Login"}
        </Button>
      </form>
      <p className="mt-5 text-sm text-slate-600 dark:text-slate-400">
        New to DocuGen AI? <Link className="font-semibold text-blue-600" to="/register">Create an account</Link>
      </p>
    </section>
  );
}
