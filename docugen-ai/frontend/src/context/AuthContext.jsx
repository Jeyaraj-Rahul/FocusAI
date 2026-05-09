import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { setAuthToken } from "../lib/api";
import { fetchCurrentUser, loginUser, logoutUser, registerUser } from "../services/authService";

const TOKEN_KEY = "docugen_ai_token";
const USER_KEY = "docugen_ai_user";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem(USER_KEY);
    return storedUser ? JSON.parse(storedUser) : null;
  });
  const [initializing, setInitializing] = useState(Boolean(token));

  useEffect(() => {
    setAuthToken(token);
  }, [token]);

  useEffect(() => {
    let active = true;
    async function hydrateUser() {
      if (!token) {
        setInitializing(false);
        return;
      }
      try {
        const currentUser = await fetchCurrentUser();
        if (active) persistSession(token, currentUser);
      } catch {
        if (active) clearSession();
      } finally {
        if (active) setInitializing(false);
      }
    }
    hydrateUser();
    return () => {
      active = false;
    };
  }, []);

  function persistSession(nextToken, nextUser) {
    setToken(nextToken);
    setUser(nextUser);
    setAuthToken(nextToken);
    localStorage.setItem(TOKEN_KEY, nextToken);
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser));
  }

  function clearSession() {
    setToken(null);
    setUser(null);
    setAuthToken(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  const value = useMemo(
    () => ({
      token,
      user,
      initializing,
      isAuthenticated: Boolean(token),
      async login(credentials) {
        const data = await loginUser(credentials);
        persistSession(data.access_token, data.user);
      },
      async register(payload) {
        const data = await registerUser(payload);
        persistSession(data.access_token, data.user);
      },
      async logout() {
        try {
          if (token) await logoutUser();
        } finally {
          clearSession();
        }
      }
    }),
    [token, user, initializing]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used inside AuthProvider");
  }
  return context;
}
