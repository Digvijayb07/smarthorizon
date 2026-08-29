import { useState } from "react";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Bell, CircleUser, ChevronDown, ShieldCheck, FileText, Lock, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { useRole, type RoleId } from "@/context/RoleContext";

export interface DashboardHeaderProps {
  title?: string;
  userRole?: string;
  userName?: string;
}

export function DashboardHeader({
  title,
  userRole: userRoleProp,
  userName: userNameProp,
}: DashboardHeaderProps) {
  const { role, setRole, user, dashboardTitle } = useRole();
  const [roleMenuOpen, setRoleMenuOpen] = useState(false);

  const displayTitle = title || dashboardTitle;
  const activeRole = (userRoleProp as RoleId) || role;
  const displayUserName = userNameProp || user.name;

  const rolesList: { id: RoleId; label: string; icon: any }[] = [
    { id: "investigator", label: "Investigator", icon: ShieldCheck },
    { id: "manager", label: "Manager", icon: FileText },
    { id: "administrator", label: "Administrator", icon: Lock },
  ];

  return (
    <header className="border-b border-border/80 bg-background/95 backdrop-blur-md sticky top-0 z-20 shadow-2xs">
      <div className="flex items-center justify-between gap-4 px-4 py-3.5 sm:px-6 lg:px-8">
        {/* Left side */}
        <div className="flex-1 min-w-0">
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground truncate">{displayTitle}</h1>
          <p className="mt-0.5 text-xs text-muted-foreground truncate">
            Session: <span className="font-semibold text-foreground capitalize">{activeRole}</span> ({user.email})
          </p>
        </div>

        {/* Right side - Notifications, Role Switcher and Profile */}
        <div className="flex items-center gap-2.5 sm:gap-3.5">
          <ThemeToggle compact />

          {/* Quick Role Switcher for Demo */}
          <div className="relative">
            <button
              onClick={() => setRoleMenuOpen(!roleMenuOpen)}
              className={cn(
                "flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-1.5 text-xs font-semibold text-foreground transition-all duration-150",
                "hover:bg-muted/60 hover:border-border",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              )}
              aria-label="Switch role"
            >
              <span className="size-2 rounded-full bg-primary animate-pulse" />
              <span className="capitalize">{activeRole} View</span>
              <ChevronDown className="size-3.5 text-muted-foreground" />
            </button>

            {roleMenuOpen && (
              <>
                <div
                  className="fixed inset-0 z-30"
                  onClick={() => setRoleMenuOpen(false)}
                />
                <div className="absolute right-0 top-full mt-2 z-40 w-52 rounded-2xl border border-border bg-card p-1.5 shadow-lg">
                  <p className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground font-mono">
                    Switch Demo Role
                  </p>
                  {rolesList.map((item) => {
                    const RoleIcon = item.icon;
                    const isSelected = activeRole === item.id;
                    return (
                      <button
                        key={item.id}
                        onClick={() => {
                          setRole(item.id);
                          setRoleMenuOpen(false);
                        }}
                        className={cn(
                          "flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs font-medium transition-colors",
                          isSelected
                            ? "bg-primary/10 text-primary font-semibold"
                            : "text-foreground hover:bg-muted/60",
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <RoleIcon className="size-3.5" />
                          <span>{item.label}</span>
                        </div>
                        {isSelected && <Check className="size-3 text-primary" />}
                      </button>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          {/* Notification bell */}
          <button
            className={cn(
              "relative rounded-xl border border-border bg-card p-2 text-foreground transition-colors duration-150",
              "hover:bg-muted/60",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet/20",
            )}
            aria-label="Notifications"
          >
            <Bell className="size-4" />
            <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-risk-high" aria-hidden />
          </button>

          {/* User profile */}
          <div
            className={cn(
              "flex items-center gap-2.5 rounded-xl border border-border bg-card px-2.5 py-1.5 transition-colors duration-150",
            )}
          >
            <div className="hidden text-right lg:block">
              <p className="text-xs font-semibold text-foreground leading-tight">{displayUserName}</p>
              <p className="text-[11px] text-muted-foreground capitalize leading-tight mt-0.5">{activeRole}</p>
            </div>
            <div className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold text-xs shadow-xs">
              {displayUserName.charAt(0)}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
