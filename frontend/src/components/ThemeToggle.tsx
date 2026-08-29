import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@/context/ThemeContext";

type ThemeToggleProps = {
  className?: string;
  compact?: boolean;
};

export function ThemeToggle({ className, compact = false }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={cn(
        "inline-flex items-center justify-center rounded-xl border border-border bg-card text-foreground transition-colors duration-150",
        "hover:bg-muted/60",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        compact ? "size-9 p-0" : "gap-1.5 px-3 py-1.5 text-xs font-semibold",
        className,
      )}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      {isDark ? (
        <>
          <Sun className="size-4" aria-hidden />
          {!compact ? <span>Light</span> : null}
        </>
      ) : (
        <>
          <Moon className="size-4" aria-hidden />
          {!compact ? <span>Dark</span> : null}
        </>
      )}
    </button>
  );
}
