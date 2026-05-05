import { CalendarDays, MapPin } from "lucide-react";
import { PageShell, SectionCard } from "@/components/dashboard/PageShell";
import { cn } from "@/lib/utils";

type Event = {
  type: "Workshop" | "Preview" | "Middle-End";
  city: string;
  date: string;
  day: string;
  team: string;
};

const events: Event[] = [
  { type: "Workshop", city: "Minneapolis", date: "May 16", day: "Sat", team: "Team Vogel" },
  { type: "Workshop", city: "West Palm Beach", date: "May 16", day: "Sat", team: "Team Dent" },
  { type: "Middle-End", city: "Long Island", date: "May 8", day: "Thu", team: "Team Tony" },
  { type: "Middle-End", city: "Fort Lauderdale", date: "May 8", day: "Thu", team: "Team Shaw" },
  { type: "Preview", city: "Norfolk", date: "May 5", day: "Mon", team: "Team Dent" },
  { type: "Preview", city: "Atlanta", date: "May 6", day: "Tue", team: "Team Vogel" },
];

const typeStyles: Record<Event["type"], string> = {
  Workshop: "bg-primary/15 text-primary",
  Preview: "bg-warning/15 text-warning",
  "Middle-End": "bg-success/15 text-success",
};

const Schedule = () => {
  const grouped = events.reduce<Record<string, Event[]>>((acc, e) => {
    acc[e.date] = acc[e.date] || [];
    acc[e.date].push(e);
    return acc;
  }, {});

  return (
    <PageShell
      eyebrow="SCHEDULE"
      title="Upcoming Events"
      description="Workshops, Previews, and Middle-End sessions across the next reporting window."
    >
      <SectionCard eyebrow="Calendar" title="By date">
        <div className="space-y-4">
          {Object.entries(grouped).map(([date, items]) => (
            <div key={date} className="rounded-xl border border-border bg-card/50 p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-10 w-10 rounded-lg bg-primary/10 text-primary flex flex-col items-center justify-center">
                  <CalendarDays className="h-4 w-4" />
                </div>
                <div>
                  <p className="font-semibold leading-tight">{date}</p>
                  <p className="text-xs text-muted-foreground">{items[0].day}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {items.map((e) => (
                  <div
                    key={`${e.city}-${e.type}`}
                    className="rounded-lg border border-border bg-background/40 p-3 flex items-center justify-between gap-3"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "text-[10px] font-semibold px-1.5 py-0.5 rounded-md",
                            typeStyles[e.type]
                          )}
                        >
                          {e.type}
                        </span>
                        <span className="text-xs text-muted-foreground truncate">{e.team}</span>
                      </div>
                      <p className="font-semibold mt-1 flex items-center gap-1">
                        <MapPin className="h-3 w-3 text-muted-foreground" />
                        {e.city}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </SectionCard>
    </PageShell>
  );
};

export default Schedule;