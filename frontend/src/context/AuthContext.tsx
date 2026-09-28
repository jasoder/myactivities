import React, { createContext, useContext, useState, useEffect } from "react";
import { api, setAuthToken, getAuthToken, type Athlete } from "../api/client";

interface AuthContextType {
  token: string | null;
  athlete: Athlete | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setTokenState] = useState<string | null>(getAuthToken());
  const [athlete, setAthlete] = useState<Athlete | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchProfile = async () => {
    try {
      const { data, error } = await api.GET("/myactivities/user");
      if (data) {
        setAthlete(data);
      } else if (error) {
        setAuthToken(null);
        setTokenState(null);
        setAthlete(null);
      }
    } catch {
      setAuthToken(null);
      setTokenState(null);
      setAthlete(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchProfile();
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    const { data, error } = await api.POST("/myactivities/auth/login", {
      body: { email, password },
    });

    if (error || !data) {
      setIsLoading(false);
      const detail = (error as any)?.detail || "Invalid email or password";
      throw new Error(detail);
    }

    setAuthToken(data.access_token);
    setTokenState(data.access_token);
    setAthlete(data.athlete);
    setIsLoading(false);
  };

  const register = async (email: string, password: string, name?: string) => {
    setIsLoading(true);
    const { data, error } = await api.POST("/myactivities/auth/register", {
      body: { email, password, name },
    });

    if (error || !data) {
      setIsLoading(false);
      const detail = (error as any)?.detail || "Registration failed";
      throw new Error(detail);
    }

    setAuthToken(data.access_token);
    setTokenState(data.access_token);
    setAthlete(data.athlete);
    setIsLoading(false);
  };

  const logout = () => {
    setAuthToken(null);
    setTokenState(null);
    setAthlete(null);
  };

  const refreshProfile = async () => {
    if (token) {
      await fetchProfile();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        athlete,
        isLoading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
