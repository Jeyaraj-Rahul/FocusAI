import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Info, TriangleAlert, X } from "lucide-react";
import { createContext, useCallback, useContext, useMemo, useState } from "react";

const ToastContext = createContext(null);

const icons = {
  success: <CheckCircle2 className="h-5 w-5 text-emerald-500" />,
  error: <TriangleAlert className="h-5 w-5 text-red-500" />,
  info: <Info className="h-5 w-5 text-blue-500" />
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((items) => items.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    ({ title, message, type = "info", duration = 3500 }) => {
      const id = crypto.randomUUID();
      setToasts((items) => [...items, { id, title, message, type }]);
      window.setTimeout(() => removeToast(id), duration);
    },
    [removeToast]
  );

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 top-4 z-[80] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-3 sm:right-6 sm:top-6">
        <AnimatePresence initial={false}>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: -12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -12, scale: 0.98 }}
              className="rounded-lg border border-slate-200 bg-white p-4 shadow-lg dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex items-start gap-3">
                {icons[toast.type] || icons.info}
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-950 dark:text-white">{toast.title}</p>
                  {toast.message ? <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{toast.message}</p> : null}
                </div>
                <button className="rounded-md p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => removeToast(toast.id)} aria-label="Dismiss notification">
                  <X size={16} />
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used inside ToastProvider");
  }
  return context;
}
