import React, { createContext, useContext, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, unwrap, setAuthToken, getAuthToken, type Athlete } from "../api/client";

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
  const queryClient = useQueryClient();
  const [token, setTokenState] = useState<string | null>(getAuthToken());

  const { data: athlete = null, isLoading, refetch } = useQuery<Athlete | null>({
    queryKey: ["user-profile"],
    queryFn: async () => {
      const { data, error } = await api.GET("/myactivities/user");
      if (error || !data) {
        setAuthToken(null);
        setTokenState(null);
        return null;
      }
      return data;
    },
    enabled: Boolean(token),
    retry: false,
  });

  const authenticate = async (
    request: () => Promise<{ data?: { access_token: string; athlete: Athlete }; error?: unknown }>,
    fallbackError: string
  ) => {
    const data = unwrap(await request(), fallbackError);
    setAuthToken(data.access_token);
    setTokenState(data.access_token);
    queryClient.setQueryData(["user-profile"], data.athlete);
  };

  const login = (email: string, password: string) =>
    authenticate(
      () => api.POST("/myactivities/auth/login", { body: { email, password } }),
      "Invalid email or password"
    );

  const register = (email: string, password: string, name?: string) =>
    authenticate(
      () => api.POST("/myactivities/auth/register", { body: { email, password, name } }),
      "Registration failed"
    );

  const logout = () => {
    setAuthToken(null);
    setTokenState(null);
    queryClient.clear();
  };

  const refreshProfile = async () => {
    if (token) {
      await refetch();
    }
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        athlete,
        isLoading: Boolean(token) && isLoading,
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
