import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Button from "../components/common/Button.jsx";
import Field from "../components/common/Field.jsx";
import LoadingSpinner from "../components/common/LoadingSpinner.jsx";
import { useToast } from "../context/ToastContext.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { getErrorMessage } from "../utils/errors.js";

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export default function Register() {
  const { register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirmPassword: "" });
  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  function validate() {
    const nextErrors = {};
    if (form.full_name.trim().length < 2) nextErrors.full_name = "Full name must be at least 2 characters.";
    if (!emailPattern.test(form.email)) nextErrors.email = "Enter a valid email address.";
    if (form.password.length < 8) nextErrors.password = "Password must be at least 8 characters.";
    if (form.password !== form.confirmPassword) nextErrors.confirmPassword = "Passwords do not match.";
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setApiError("");
    if (!validate()) return;

    setLoading(true);
    try {
      await register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password
      });
      showToast({ type: "success", title: "Account created", message: "Your workspace is ready." });
      navigate("/app", { replace: true });
    } catch (error) {
      const message = getErrorMessage(error, "Unable to create account. Please try again.");
      setApiError(message);
      showToast({ type: "error", title: "Registration failed", message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="mx-auto mt-16 max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-2xl font-semibold">Register</h2>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Create your report automation workspace.</p>
      <form className="mt-6 space-y-4" onSubmit={handleSubmit} noValidate>
        <Field label="Full name" error={errors.full_name}>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
            value={form.full_name}
            onChange={(event) => setForm({ ...form, full_name: event.target.value })}
          />
        </Field>
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
        <Field label="Confirm password" error={errors.confirmPassword}>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
            type="password"
            value={form.confirmPassword}
            onChange={(event) => setForm({ ...form, confirmPassword: event.target.value })}
          />
        </Field>
        {apiError ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-200">{apiError}</p> : null}
        <Button className="w-full" disabled={loading}>
          {loading ? <LoadingSpinner label="Creating account" /> : "Create account"}
        </Button>
      </form>
      <p className="mt-5 text-sm text-slate-600 dark:text-slate-400">
        Already registered? <Link className="font-semibold text-blue-600" to="/login">Login</Link>
      </p>
    </section>
  );
}
