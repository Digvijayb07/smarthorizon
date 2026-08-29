import React, { createContext, useContext, useEffect, useState } from "react";

export type RoleId = "investigator" | "manager" | "administrator";

export interface UserProfile {
  name: string;
  email: string;
  title: string;
}

export const ROLE_PROFILES: Record<RoleId, UserProfile> = {
  investigator: {
    name: "Marcus Johnson",
    email: "marcus.johnson@smarthorizon.ai",
    title: "Senior AML Investigator",
  },
  manager: {
    name: "Sarah Chen",
    email: "sarah.chen@smarthorizon.ai",
    title: "AML Operations Manager",
  },
  administrator: {
    name: "Alex Chen",
    email: "alex.chen@smarthorizon.ai",
    title: "System Administrator",
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
}

const RoleContext = createContext<RoleContextType | undefined>(undefined);

const STORAGE_KEY = "smart-horizon-role";

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [role, setRoleState] = useState<RoleId>("investigator");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = sessionStorage.getItem(STORAGE_KEY) as RoleId | null;
      if (stored && (stored === "investigator" || stored === "manager" || stored === "administrator")) {
        setRoleState(stored);
      }
    }
  }, []);

  const setRole = (newRole: RoleId) => {
    setRoleState(newRole);
    if (typeof window !== "undefined") {
      sessionStorage.setItem(STORAGE_KEY, newRole);
    }
  };

  const clearRole = () => {
    setRoleState("investigator");
    if (typeof window !== "undefined") {
      sessionStorage.removeItem(STORAGE_KEY);
    }
  };

  const value: RoleContextType = {
    role,
    setRole,
    clearRole,
    user: ROLE_PROFILES[role] || ROLE_PROFILES.investigator,
    dashboardTitle: ROLE_TITLES[role] || "Dashboard",
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
