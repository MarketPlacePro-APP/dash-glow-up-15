import { Calendar, ChevronDown } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import { navItems } from "./Sidebar";
import { cn } from "@/lib/utils";

const titles: Record<string, { eyebrow: string; title: string }> = {
  "/": { eyebrow: "EXECUTIVE OVERVIEW", title: "TLWB KPI Dashboard" },
  "/marketing": { eyebrow: "MARKETING", title: "Active Marketing" },
  "/preview": { eyebrow: "PREVIEW", title: "Active Preview" },
  "/workshop": { eyebrow: "WORKSHOP / MIDDLE-END", title: "Workshop & ME" },
  "/schedule": { eyebrow: "SCHEDULE", title: "Schedule Calendar" },
  "/inside-sales": { eyebrow: "INSIDE SALES", title: "Inside Sales DPL" },
  "/data-qa": { eyebrow: "DATA QA", title: "Source Freshness & Health" },
};

export const Topbar = () => {
  const { pathname } = useLocation();
  const meta = titles[pathname] ?? titles["/"];
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/70 backdrop-blur-xl">
      <div className="flex items-center gap-4 px-6 lg:px-8 h-16">
        <div>
          <p className="text-[10px] font-semibold tracking-[0.18em] text-muted-foreground">
            {meta.eyebrow}
          </p>
          <h2 className="text-base font-bold leading-tight">{meta.title}</h2>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button className="hidden sm:inline-flex items-center gap-2 h-10 px-3.5 rounded-lg border border-border bg-card hover:bg-muted/60 text-sm font-medium transition">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span>Snapshot</span>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
        </div>
      </div>
      <nav className="lg:hidden border-t border-border px-3 py-2 overflow-x-auto flex gap-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => cn(
              "shrink-0 rounded-full border px-3 py-1.5 text-xs font-semibold transition",
              isActive ? "border-primary/40 bg-primary/15 text-primary" : "border-border bg-card/70 text-muted-foreground"
            )}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
};
