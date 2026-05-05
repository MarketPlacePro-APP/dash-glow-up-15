import { NavLink } from "react-router-dom";
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

export const navItems = [
  { to: "/", label: "Executive", icon: LayoutDashboard, end: true },
  { to: "/marketing", label: "Marketing", icon: Megaphone },
  { to: "/preview", label: "Preview", icon: Eye },
  { to: "/workshop", label: "Workshop / ME", icon: GraduationCap },
  { to: "/schedule", label: "Schedule", icon: CalendarDays },
  { to: "/inside-sales", label: "Inside Sales", icon: PhoneCall },
  { to: "/data-qa", label: "Data QA", icon: ShieldCheck },
];

export const Sidebar = () => {
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
          Review snapshot with source freshness visible in Data QA.
        </p>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        <p className="px-3 py-2 text-[10px] font-semibold tracking-[0.2em] text-muted-foreground">
          DASHBOARD
        </p>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-[inset_0_0_0_1px_hsl(var(--sidebar-border))]"
                    : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors",
                      isActive
                        ? "text-primary"
                        : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-success/15 text-success font-semibold">
                      {item.badge}
                    </span>
                  )}
                </>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="m-3 p-4 rounded-xl glass border border-border">
        <div className="flex items-center gap-2 mb-2">
          <span className="h-2 w-2 rounded-full bg-success animate-pulse-soft" />
          <p className="text-xs font-semibold">Review snapshot</p>
        </div>
        <p className="text-[11px] text-muted-foreground leading-relaxed">
          Not production. Source freshness and pending fields are visible in Data QA.
        </p>
      </div>
    </aside>
  );
};