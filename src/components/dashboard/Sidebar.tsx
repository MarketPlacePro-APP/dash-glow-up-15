import { useState } from "react";
import {
  LayoutDashboard,
  Megaphone,
  Eye,
  GraduationCap,
  CalendarDays,
  PhoneCall,
  ShieldCheck,
} from "lucide-react";
import { cn } from "@/lib/utils";
import tlwbLogo from "@/assets/tlwb-logo.png";

const navItems = [
  { id: "executive", label: "Executive", icon: LayoutDashboard, badge: "Live" },
  { id: "marketing", label: "Marketing", icon: Megaphone },
  { id: "preview", label: "Preview", icon: Eye },
  { id: "workshop", label: "Workshop / ME", icon: GraduationCap },
  { id: "schedule", label: "Schedule", icon: CalendarDays },
  { id: "inside-sales", label: "Inside Sales", icon: PhoneCall },
  { id: "data-qa", label: "Data QA", icon: ShieldCheck },
];

export const Sidebar = () => {
  const [active, setActive] = useState("executive");

  return (
    <aside className="hidden lg:flex w-64 shrink-0 flex-col border-r border-border bg-sidebar/60 backdrop-blur-xl">
      <div className="px-6 py-6 border-b border-sidebar-border">
        <img
          src={tlwbLogo}
          alt="Tax Lien Wealth Builders"
          className="w-full h-auto object-contain"
        />
        <p className="mt-3 text-[10px] font-semibold tracking-[0.2em] text-muted-foreground">
          KPI DASHBOARD
        </p>
        <p className="mt-4 text-xs text-muted-foreground leading-relaxed">
          Marketing, Preview, Workshop, Schedule, and Inside Sales — unified.
        </p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        <p className="px-3 py-2 text-[10px] font-semibold tracking-[0.2em] text-muted-foreground">
          DASHBOARD
        </p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActive(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-[inset_0_0_0_1px_hsl(var(--sidebar-border))]"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-colors",
                  isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                )}
              />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge && (
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-success/15 text-success font-semibold">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      <div className="m-3 p-4 rounded-xl glass border border-border">
        <div className="flex items-center gap-2 mb-2">
          <span className="h-2 w-2 rounded-full bg-success animate-pulse-soft" />
          <p className="text-xs font-semibold">Operating view</p>
        </div>
        <p className="text-[11px] text-muted-foreground leading-relaxed">
          Reporting window live. Source freshness visible in Data QA.
        </p>
      </div>
    </aside>
  );
};