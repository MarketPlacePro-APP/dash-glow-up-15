import { Calendar, ChevronDown } from "lucide-react";
import { useLocation } from "react-router-dom";

const titles: Record<string, { eyebrow: string; title: string }> = {
  "/": { eyebrow: "EXECUTIVE OVERVIEW", title: "TLWB KPI Dashboard" },
  "/marketing": { eyebrow: "MARKETING", title: "Active Markets & Spend" },
  "/preview": { eyebrow: "PREVIEW", title: "Preview Conversion" },
  "/workshop": { eyebrow: "WORKSHOP / MIDDLE-END", title: "Show & Sold Performance" },
  "/schedule": { eyebrow: "SCHEDULE", title: "Upcoming Events" },
  "/inside-sales": { eyebrow: "INSIDE SALES", title: "Team Performance" },
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
            <span>This week</span>
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
        </div>
      </div>
    </header>
  );
};