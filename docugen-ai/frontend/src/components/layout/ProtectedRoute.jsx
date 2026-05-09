import { Navigate, useLocation } from "react-router-dom";
import LoadingSpinner from "../common/LoadingSpinner.jsx";
import { useAuth } from "../../hooks/useAuth";

export default function ProtectedRoute({ children }) {
  const { initializing, isAuthenticated } = useAuth();
  const location = useLocation();

  if (initializing) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50 text-slate-600 dark:bg-slate-950 dark:text-slate-300">
        <LoadingSpinner label="Checking session" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
