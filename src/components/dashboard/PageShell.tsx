import { ReactNode } from "react";
import { cn } from "@/lib/utils";

export const PageShell = ({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  children: ReactNode;
}) => (
  <div className="px-6 lg:px-8 py-8 max-w-[1600px] mx-auto space-y-8">
    <section className="relative overflow-hidden rounded-2xl glass border border-border p-6 lg:p-8 animate-fade-up">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent pointer-events-none" />
      <div className="relative space-y-2 max-w-2xl">
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-primary/15 text-primary text-[11px] font-semibold tracking-wide">
          {eyebrow}
        </div>
        <h1 className="text-2xl lg:text-3xl font-bold tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
    </section>
    {children}
  </div>
);

export const SectionCard = ({
  title,
  eyebrow,
  subtitle,
  action,
  children,
  className,
}: {
  title: string;
  eyebrow?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) => (
  <section
    className={cn(
      "glass border border-border rounded-2xl p-6 animate-fade-up",
      className
    )}
  >
    <div className="flex items-start justify-between flex-wrap gap-3 mb-5">
      <div>
        {eyebrow && (
          <p className="text-[10px] font-semibold tracking-[0.18em] text-muted-foreground">
            {eyebrow.toUpperCase()}
          </p>
        )}
        <h3 className="text-lg font-bold leading-tight">{title}</h3>
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
    {children}
  </section>
);

export const Stat = ({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: "success" | "warning" | "primary";
}) => (
  <div>
    <p className="text-[10px] font-semibold tracking-wide uppercase text-muted-foreground">
      {label}
    </p>
    <p
      className={cn(
        "text-base font-bold mt-0.5",
        accent === "success" && "text-success",
        accent === "warning" && "text-warning",
        accent === "primary" && "text-primary"
      )}
    >
      {value}
    </p>
  </div>
);