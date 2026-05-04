import { Search, Bell, Calendar, ChevronDown } from "lucide-react";

export const Topbar = () => {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/70 backdrop-blur-xl">
      <div className="flex items-center gap-4 px-6 lg:px-8 h-16">
        <div>
          <p className="text-[10px] font-semibold tracking-[0.18em] text-muted-foreground">
            EXECUTIVE OVERVIEW
          </p>
          <h2 className="text-base font-bold leading-tight">TLWB KPI Dashboard</h2>
        </div>

        <div className="hidden md:flex flex-1 max-w-md mx-auto">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              placeholder="Search markets, teams, KPIs…"
              className="w-full h-10 pl-10 pr-4 rounded-lg bg-muted/50 border border-border text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring/40 focus:border-ring/40 transition"
            />
          </div>
        </div>

        <div className="ml-auto flex items-center gap-2">
          <button className="hidden sm:inline-flex items-center gap-2 h-10 px-3.5 rounded-lg border border-border bg-card hover:bg-muted/60 text-sm font-medium transition">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span>This week</span>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
          <button className="relative h-10 w-10 rounded-lg border border-border bg-card hover:bg-muted/60 flex items-center justify-center transition">
            <Bell className="h-4 w-4" />
            <span className="absolute top-2 right-2 h-1.5 w-1.5 rounded-full bg-primary" />
          </button>
          <div className="h-10 pl-1 pr-3 flex items-center gap-2 rounded-lg border border-border bg-card">
            <div className="h-7 w-7 rounded-md bg-gradient-to-br from-primary to-primary-glow text-primary-foreground text-xs font-bold flex items-center justify-center">
              TL
            </div>
            <div className="hidden sm:block leading-tight">
              <p className="text-xs font-semibold">Tax Lien WB</p>
              <p className="text-[10px] text-muted-foreground">Operations</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};