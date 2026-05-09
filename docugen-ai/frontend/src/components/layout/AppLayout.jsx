import { FileText, Home, LogOut, Menu, Moon, Plus, Sun, Upload, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import Button from "../common/Button.jsx";
import { useToast } from "../../context/ToastContext.jsx";
import { useAuth } from "../../hooks/useAuth.js";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("docugen_theme") === "dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("docugen_theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  async function handleLogout() {
    await logout();
    showToast({ type: "info", title: "Logged out", message: "Your session was ended securely." });
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50">
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-72 border-r border-slate-200 bg-white px-4 py-5 dark:border-slate-800 dark:bg-slate-900 lg:block">
        <SidebarContent onNavigate={() => setSidebarOpen(false)} />
      </aside>

      <AnimatePresence>
        {sidebarOpen ? (
        <motion.div className="fixed inset-0 z-50 lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          <button className="absolute inset-0 bg-slate-950/50" aria-label="Close menu" onClick={() => setSidebarOpen(false)} />
          <motion.aside
            initial={{ x: -288 }}
            animate={{ x: 0 }}
            exit={{ x: -288 }}
            transition={{ type: "spring", stiffness: 320, damping: 32 }}
            className="relative h-full w-72 border-r border-slate-200 bg-white px-4 py-5 shadow-xl dark:border-slate-800 dark:bg-slate-900"
          >
            <button className="absolute right-4 top-4 rounded-md p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => setSidebarOpen(false)} aria-label="Close sidebar">
              <X size={20} />
            </button>
            <SidebarContent onNavigate={() => setSidebarOpen(false)} />
          </motion.aside>
        </motion.div>
        ) : null}
      </AnimatePresence>

      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white/90 px-4 py-3 backdrop-blur dark:border-slate-800 dark:bg-slate-900/90 lg:ml-72 lg:px-6">
        <div className="flex items-center gap-3">
          <button className="rounded-md p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 lg:hidden" onClick={() => setSidebarOpen(true)} aria-label="Open sidebar">
            <Menu size={22} />
          </button>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Workspace</p>
            <h1 className="text-base font-semibold sm:text-lg">{user?.full_name || "DocuGen User"}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" className="h-10 w-10 px-0" onClick={() => setDarkMode((value) => !value)} aria-label="Toggle theme">
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </Button>
          <Button variant="secondary" className="hidden sm:inline-flex" onClick={handleLogout}>
            <LogOut size={17} /> Logout
          </Button>
        </div>
      </header>

      <main className="px-4 py-6 sm:px-6 lg:ml-72 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}

function SidebarContent({ onNavigate }) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 px-2">
        <div className="grid h-10 w-10 place-items-center rounded-md bg-blue-600 text-white">
          <FileText size={22} />
        </div>
        <div>
          <p className="text-lg font-bold">DocuGen AI</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">Document automation</p>
        </div>
      </div>
      <nav className="mt-8 space-y-1">
        <SidebarLink to="/app" icon={<Home size={18} />} label="Dashboard" onClick={onNavigate} end />
        <SidebarLink to="/app/reports/new" icon={<Plus size={18} />} label="Create report" onClick={onNavigate} />
        <SidebarLink to="/app/templates" icon={<Upload size={18} />} label="Templates" onClick={onNavigate} />
      </nav>
      <div className="mt-auto rounded-lg border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
        <p className="text-sm font-semibold">Starter workspace</p>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Upload templates and generate reports from one place.</p>
      </div>
    </div>
  );
}

function SidebarLink({ to, icon, label, end, onClick }) {
  return (
    <NavLink
      to={to}
      end={end}
      onClick={onClick}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition ${
          isActive
            ? "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-200"
            : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
        }`
      }
    >
      {icon}
      {label}
    </NavLink>
  );
}
