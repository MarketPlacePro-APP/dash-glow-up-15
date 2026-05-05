import { useMemo, useState } from "react";
import type { DashboardDataset, ScheduleRecord, ScheduleRouteBlock } from "@/types";
import { formatDate } from "@/lib/format";
import { PageShell, SectionCard } from "@/components/dashboard/PageShell";
import { useDashboardData } from "@/data/DashboardDataProvider";
import "./schedule-calendar.css";

type CalendarView = "month" | "week" | "list";
type SelectedSchedule = { block: ScheduleRouteBlock; events: ScheduleRecord[] } | null;

const teamTone = (teamKey: string) => `schedule-team-${teamKey || "ops"}`;
const parseDate = (value: string) => { const [year, month, day] = value.split("-").map(Number); return new Date(year, month - 1, day); };
const isoDate = (date: Date) => `${date.getFullYear()}-${`${date.getMonth() + 1}`.padStart(2, "0")}-${`${date.getDate()}`.padStart(2, "0")}`;
const addDays = (date: Date, days: number) => { const next = new Date(date); next.setDate(next.getDate() + days); return next; };
const startOfWeek = (date: Date) => addDays(date, -date.getDay());
const monthDays = (anchor: Date) => { const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1); const start = startOfWeek(first); return Array.from({ length: 42 }, (_, index) => addDays(start, index)); };
const formatRange = (startDate: string, endDate: string) => startDate === endDate ? formatDate(startDate) : `${formatDate(startDate)} → ${formatDate(endDate)}`;
const blockMatchesDate = (block: ScheduleRouteBlock, date: string) => block.startDate <= date && block.endDate >= date;

const supplementalBlocks: ScheduleRouteBlock[] = [
  { sourceKey: "slack_me_schedule_supplement", sourceName: "Slack ME team check-ins", sourceUrl: "slack://channels/teamtony,teamshaw,teamdrecksel", fetchedAt: "2026-05-05T08:29:55Z", trustLevel: "operational", sampleData: false, sourceRole: "middle_end_schedule_supplement", id: "me-la2-tony-2026-05-01", market: "LA2", route: "Middle-End Workshop", team: "Team Tony", teamKey: "tony", status: "historical", startDate: "2026-05-01", endDate: "2026-05-01", eventCount: 1, areas: ["Los Angeles"], venues: ["venue pending"], sourceSheet: "Slack ME check-ins", sourceRows: [1] },
  { sourceKey: "slack_me_schedule_supplement", sourceName: "Slack ME team check-ins", sourceUrl: "slack://channels/teamtony,teamshaw,teamdrecksel", fetchedAt: "2026-05-05T08:29:55Z", trustLevel: "operational", sampleData: false, sourceRole: "middle_end_schedule_supplement", id: "me-phoenix-shaw-2026-05-01", market: "Phoenix", route: "Middle-End Workshop", team: "Team Shaw", teamKey: "shaw", status: "historical", startDate: "2026-05-01", endDate: "2026-05-01", eventCount: 1, areas: ["Phoenix"], venues: ["venue pending"], sourceSheet: "Slack ME check-ins", sourceRows: [2] },
  { sourceKey: "slack_me_schedule_supplement", sourceName: "Slack ME team check-ins", sourceUrl: "slack://channels/teamdrecksel", fetchedAt: "2026-05-05T08:29:55Z", trustLevel: "operational", sampleData: false, sourceRole: "middle_end_schedule_supplement", id: "me-la1-drexel-2026-04-24", market: "LA1", route: "Middle-End Workshop", team: "Team Drexel", teamKey: "drexel", status: "historical", startDate: "2026-04-24", endDate: "2026-04-24", eventCount: 1, areas: ["Los Angeles"], venues: ["venue pending"], sourceSheet: "Slack ME check-ins", sourceRows: [3] },
  { sourceKey: "slack_me_schedule_supplement", sourceName: "Slack ME team check-ins", sourceUrl: "slack://channels/teamwyman", fetchedAt: "2026-05-05T08:29:55Z", trustLevel: "operational", sampleData: false, sourceRole: "middle_end_schedule_supplement", id: "me-nashville-nick-2026-01-23", market: "Nashville", route: "Middle-End Workshop", team: "Team Nick", teamKey: "nick", status: "historical", startDate: "2026-01-23", endDate: "2026-01-23", eventCount: 1, areas: ["Nashville"], venues: ["venue pending"], sourceSheet: "Slack preview finals / ME reference", sourceRows: [4] },
  { sourceKey: "slack_expo_schedule_supplement", sourceName: "Slack #expo count posts", sourceUrl: "slack://channel/expo/post/2026-04-29T15:04-06:00", fetchedAt: "2026-05-05T08:29:55Z", trustLevel: "operational", sampleData: false, sourceRole: "expo_schedule_supplement", id: "expo-may-investor-count-2026-04-29", market: "May Investor Expo", route: "Expo count update", team: "Expo", teamKey: "expo", status: "active", startDate: "2026-04-29", endDate: "2026-04-29", eventCount: 1, areas: ["Expo"], venues: ["venue/source pending"], sourceSheet: "Slack #expo", sourceRows: [5] },
];

const supplementalEvents: ScheduleRecord[] = supplementalBlocks.map((block, index) => ({
  sourceKey: block.sourceKey, sourceName: block.sourceName, sourceUrl: block.sourceUrl, fetchedAt: block.fetchedAt, trustLevel: block.trustLevel, sampleData: false, sourceRole: block.sourceRole,
  id: `${block.id}-event`, market: block.market, route: block.route, team: block.team, teamKey: block.teamKey, weekOf: block.startDate, startDate: block.startDate, endDate: block.endDate, location: block.venues[0] ?? "venue pending", state: block.status === "active" ? "active" : "historical", owner: block.team, eventType: block.teamKey === "expo" ? "expo" : "middle_end_workshop", area: block.areas[0], city: block.areas[0], venue: block.venues[0], times: "time pending", sourceSheet: block.sourceSheet, sourceRow: block.sourceRows[0] ?? index + 1, sourceTabRole: "reference", notes: "Supplemental calendar item added because ME/Expo items were missing from the FE route schedule export."
}));

function ScheduleCalendar({ data }: { data: DashboardDataset }) {
  const allBlocks = useMemo(() => [...data.scheduleRouteBlocks, ...supplementalBlocks], [data.scheduleRouteBlocks]);
  const allSchedule = useMemo(() => [...data.schedule, ...supplementalEvents], [data.schedule]);
  const [view, setView] = useState<CalendarView>("month");
  const [teamFilter, setTeamFilter] = useState("everyone");
  const [anchorDate, setAnchorDate] = useState(() => { const activeOrUpcoming = allBlocks.find((block) => block.status === "active" || block.status === "upcoming"); return activeOrUpcoming ? parseDate(activeOrUpcoming.startDate) : new Date(); });
  const [selected, setSelected] = useState<SelectedSchedule>(null);

  const eventsByBlock = useMemo(() => allBlocks.reduce((map, block) => { const sourceRows = new Set(block.sourceRows); const rows = allSchedule.filter((event) => event.market === block.market && event.route === block.route && event.teamKey === block.teamKey && sourceRows.has(event.sourceRow)); map.set(block.id, rows); return map; }, new Map<string, ScheduleRecord[]>()), [allSchedule, allBlocks]);
  const teams = useMemo(() => { const merged = new Map<string, string>(); allBlocks.forEach((block) => { if (block.teamKey) merged.set(block.teamKey, block.team); }); return [["everyone", "Everyone"], ...Array.from(merged.entries()).sort((a, b) => a[1].localeCompare(b[1]))] as Array<[string, string]>; }, [allBlocks]);
  const visibleBlocks = useMemo(() => { const statusRank: Record<string, number> = { active: 0, upcoming: 1, historical: 2, cancelled: 3 }; return allBlocks.filter((block) => teamFilter === "everyone" || block.teamKey === teamFilter).slice().sort((a, b) => (statusRank[a.status] ?? 9) - (statusRank[b.status] ?? 9) || parseDate(a.startDate).getTime() - parseDate(b.startDate).getTime()); }, [allBlocks, teamFilter]);
  const visibleEvents = useMemo(() => allSchedule.filter((event) => teamFilter === "everyone" || event.teamKey === teamFilter), [allSchedule, teamFilter]);
  const days = view === "week" ? Array.from({ length: 7 }, (_, index) => addDays(startOfWeek(anchorDate), index)) : monthDays(anchorDate);
  const navigate = (direction: -1 | 1) => { const next = new Date(anchorDate); if (view === "month") next.setMonth(next.getMonth() + direction); else next.setDate(next.getDate() + direction * 7); setAnchorDate(next); };
  const openBlock = (block: ScheduleRouteBlock) => setSelected({ block, events: eventsByBlock.get(block.id) ?? [] });

  if (allSchedule.length === 0) return <section className="glass border border-border rounded-2xl p-6"><h3>Schedule</h3><p className="text-sm text-muted-foreground">No schedule data is available yet.</p></section>;
  const currentMonthLabel = anchorDate.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  const weekLabel = `${formatDate(isoDate(days[0]))} → ${formatDate(isoDate(days[6]))}`;

  return <div className="space-y-6">
    <section className="schedule-toolbar" aria-label="Schedule calendar controls">
      <div className="schedule-view-toggle" role="group" aria-label="Calendar view">{(["month", "week", "list"] as CalendarView[]).map((option) => <button key={option} type="button" className={view === option ? "active" : ""} onClick={() => setView(option)}>{option[0].toUpperCase() + option.slice(1)}</button>)}</div>
      <label className="select-shell schedule-team-filter"><span>Team filter</span><select value={teamFilter} onChange={(event) => setTeamFilter(event.target.value)}>{teams.map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
      <div className="schedule-date-nav"><button type="button" className="ghost-button" onClick={() => navigate(-1)}>Previous</button><button type="button" className="ghost-button" onClick={() => setAnchorDate(new Date())}>Today</button><button type="button" className="ghost-button" onClick={() => navigate(1)}>Next</button></div>
      <div className="schedule-range-label">{view === "month" ? currentMonthLabel : view === "week" ? weekLabel : `${visibleEvents.length} visible events`}</div>
    </section>

    {view !== "list" ? <SectionCard title={view === "month" ? "Month Calendar" : "Week Calendar"} subtitle="Team-colored route blocks include past and upcoming events. Click any block for venue, address, and source row detail.">
      <div className={`schedule-calendar-grid ${view === "week" ? "week-view" : ""}`}>{["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => <div key={day} className="schedule-weekday">{day}</div>)}{days.map((day) => { const date = isoDate(day); const allDayBlocks = visibleBlocks.filter((block) => blockMatchesDate(block, date)); const dayBlocks = allDayBlocks.slice(0, view === "week" ? 8 : 4); const isOutsideMonth = view === "month" && day.getMonth() !== anchorDate.getMonth(); return <article key={date} className={`schedule-day-cell ${isOutsideMonth ? "outside-month" : ""}`}><div className="schedule-day-number">{day.getDate()}</div><div className="schedule-day-events">{dayBlocks.map((block) => <button key={`${block.id}-${date}`} type="button" className={`schedule-event-chip ${teamTone(block.teamKey)} status-${block.status}`} onClick={() => openBlock(block)}><strong>{block.market}</strong><span>{block.team}</span>{view === "week" ? <small>{block.areas.slice(0, 2).join(" / ") || block.route}</small> : null}</button>)}{allDayBlocks.length > dayBlocks.length ? <span className="schedule-more-chip">+{allDayBlocks.length - dayBlocks.length} more</span> : null}</div></article>; })}</div>
    </SectionCard> : <SectionCard title="Schedule List" subtitle="Source-row list from TLWB/MO Schedule. Calendar remains the primary view; this is for QA and source lookup."><div className="schedule-list-grid">{visibleEvents.map((event) => <button key={event.id} type="button" className={`schedule-list-row ${teamTone(event.teamKey)}`} onClick={() => { const block = visibleBlocks.find((item) => item.market === event.market && item.route === event.route && item.teamKey === event.teamKey); if (block) openBlock(block); }}><span><strong>{formatDate(event.startDate)}</strong><small>{event.times || "time pending"}</small></span><span><strong>{event.market}</strong><small>{event.route}</small></span><span><strong>{event.team}</strong><small>{event.area || event.city || "area pending"}</small></span><span><strong>{event.venue || "venue pending"}</strong><small>row {event.sourceRow}</small></span></button>)}</div></SectionCard>}

    {selected ? <div className="schedule-drawer-backdrop" role="presentation" onClick={() => setSelected(null)}><aside className="schedule-detail-drawer" role="dialog" aria-modal="true" aria-label="Schedule event details" onClick={(event) => event.stopPropagation()}><div className="drawer-header"><div><p className="text-[10px] font-semibold tracking-[0.18em] text-muted-foreground">SCHEDULE DETAIL</p><h3>{selected.block.market}</h3><p className="text-sm text-muted-foreground">{selected.block.team} • {formatRange(selected.block.startDate, selected.block.endDate)}</p></div><button type="button" className="ghost-button" onClick={() => setSelected(null)}>Close</button></div><div className="detail-field-grid"><div><span>Route</span><strong>{selected.block.route || "pending"}</strong></div><div><span>Status</span><strong>{selected.block.status}</strong></div><div><span>Events</span><strong>{selected.block.eventCount}</strong></div><div><span>Source</span><strong>{selected.block.sourceSheet}</strong></div></div><div className="drawer-event-stack">{selected.events.map((event) => <article key={event.id} className="drawer-event-card"><div className="drawer-event-title"><strong>{formatDate(event.startDate)}</strong><span>{event.times || "time pending"}</span></div><p><b>Area:</b> {event.area || "pending"}</p><p><b>Venue:</b> {event.venue || "pending"}</p><p><b>Address:</b> {event.address || "pending"}</p><p><b>Hotel status:</b> {event.hotelStatus || "pending"} {event.ballroom ? `• Ballroom: ${event.ballroom}` : ""}</p><p><b>Parking:</b> {event.parking || "pending"}</p><p><b>On-site contact:</b> {event.onSiteContact || "pending"}</p><p className="source-note">Source: TLWB/MO Schedule › {event.sourceSheet} › row {event.sourceRow}</p></article>)}</div></aside></div> : null}
  </div>;
}

const Schedule = () => {
  const data = useDashboardData();
  return <PageShell eyebrow="SCHEDULE" title="Schedule Calendar" description="Operational Google Calendar-style view built from the TLWB/MO Schedule Google Sheet. Lovable's simpler agenda list was intentionally replaced."><div className="schedule-source-pill">Source: FE Venue Booking Status · TLWB/MO Schedule Sheet</div><ScheduleCalendar data={data} /></PageShell>;
};

export default Schedule;
