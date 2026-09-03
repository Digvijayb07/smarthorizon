import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { login as apiLogin, setAuthToken, getAuthToken } from "@/lib/api";

export type RoleId = "investigator" | "manager" | "administrator";

export interface UserProfile {
  name: string;
  email: string;
  title: string;
  role: RoleId;
}

export const ROLE_PROFILES: Record<RoleId, UserProfile> = {
  investigator: {
    name: "Marcus Johnson",
    email: "marcus.johnson@smarthorizon.ai",
    title: "Senior AML Investigator",
    role: "investigator",
  },
  manager: {
    name: "Sarah Chen",
    email: "sarah.chen@smarthorizon.ai",
    title: "AML Operations Manager",
    role: "manager",
  },
  administrator: {
    name: "Alex Chen",
    email: "alex.chen@smarthorizon.ai",
    title: "System Administrator",
    role: "administrator",
  },
};

export const ROLE_TITLES: Record<RoleId, string> = {
  investigator: "Investigation Overview",
  manager: "Review & Approvals",
  administrator: "System Administration",
};

interface RoleContextType {
  role: RoleId;
  setRole: (role: RoleId) => void;
  clearRole: () => void;
  user: UserProfile;
  dashboardTitle: string;
  isAuthenticated: boolean;
  loginWithRole: (role: RoleId) => Promise<void>;
  logout: () => void;
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

const STORAGE_KEY = "smart-horizon-role";

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<RoleId>("investigator");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = sessionStorage.getItem(STORAGE_KEY) as RoleId | null;
      if (
        stored &&
        (stored === "investigator" || stored === "manager" || stored === "administrator")
      ) {
        setRoleState(stored);
      }
      // Check if we have a valid auth token
      const token = getAuthToken();
      if (token) {
        setIsAuthenticated(true);
      }
    }
  }, []);

  const setRole = useCallback(
    (newRole: RoleId) => {
      setRoleState(newRole);
      if (typeof window !== "undefined") {
        sessionStorage.setItem(STORAGE_KEY, newRole);
      }
    },
    [],
  );

  const clearRole = useCallback(() => {
    setRoleState("investigator");
    setIsAuthenticated(false);
    setAuthToken(null);
    if (typeof window !== "undefined") {
      sessionStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem("horizon-auth-token");
    }
  }, []);

  const loginWithRole = useCallback(
    async (targetRole: RoleId) => {
      const profile = ROLE_PROFILES[targetRole];
      try {
        // Call the backend auth endpoint
        await apiLogin(profile.email, "demo-password");
        setRoleState(targetRole);
        setIsAuthenticated(true);
        if (typeof window !== "undefined") {
          sessionStorage.setItem(STORAGE_KEY, targetRole);
        }
      } catch (err) {
        console.error("Login failed:", err);
        throw err;
      }
    },
    [setRole],
  );

  const logout = useCallback(() => {
    clearRole();
  }, [clearRole]);

  const value: RoleContextType = {
    role,
    setRole,
    clearRole,
    user: ROLE_PROFILES[role] || ROLE_PROFILES.investigator,
    dashboardTitle: ROLE_TITLES[role] || "Dashboard",
    isAuthenticated,
    loginWithRole,
    logout,
  };

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>;
}

export function useRole(): RoleContextType {
  const context = useContext(RoleContext);
  if (!context) {
    throw new Error("useRole must be used within a RoleProvider");
  }
  return context;
}
