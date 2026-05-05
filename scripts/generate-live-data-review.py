#!/usr/bin/env python3
"""Generate static dashboard data from locally exported TLWB workbooks.

No third-party deps: reads .xlsx files directly as zip+xml.
"""
from __future__ import annotations

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dash-glow-up-15" / "src" / "data" / "generatedData.ts"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
FETCHED = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def colnum(ref: str) -> int:
    letters = ''.join(c for c in ref if c.isalpha())
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def num(v, default=0.0):
    if v is None or v == "" or isinstance(v, str) and v.startswith("#"):
        return default
    try:
        return float(v)
    except Exception:
        return default


def clean(v):
    if v is None:
        return ""
    return str(v).strip()


def excel_date(v):
    n = num(v, None)
    if n is None or n <= 0:
        return ""
    # Excel serial date with 1900 leap-year bug; this matches Google export well enough for dashboard labels.
    return (datetime(1899, 12, 30) + timedelta(days=n)).date().isoformat()


def week_bucket(date_text: str) -> str:
    dt = datetime.fromisoformat(date_text)
    # Sunday week bucket for calendar-style ops review.
    start = dt - timedelta(days=(dt.weekday() + 1) % 7)
    return start.date().isoformat()


def is_excel_date(v) -> bool:
    return bool(excel_date(v))


BAD_SCHEDULE_LABELS = {
    '', 'market', 'route map', 'marketing release date', 'area + address check',
    'team & on-site contact', 'market due by', 'on-site contact', 'front end 2026',
    'date', 'times', 'venue', 'address', 'parking', 'ballroom', 'master keys',
    'location code', 'sample', 'example'
}


def looks_like_control_label(value: str) -> bool:
    s = clean(value).lower().strip('* ')
    if s in BAD_SCHEDULE_LABELS:
        return True
    if not s:
        return True
    if s.replace('.', '', 1).isdigit():
        return True
    if 'tax deed ai' in s:
        return True
    if 'airtable' in s or 'name + address check' in s or s.startswith('no events'):
        return True
    return False


def normalize_team(raw: str):
    s = clean(raw).lower()
    if 'vogel' in s or 'cord' in s or 'vogal' in s:
        return 'vogel-cord', 'Team Vogel/Cord'
    if 'wayne' in s or 'gray' in s or 'grey' in s:
        return 'wayne-gray', 'Team Wayne/Gray'
    if 'dent' in s:
        return 'dent', 'Team Dent'
    if 'wyman' in s:
        return 'wyman', 'Team Wyman'
    if 'megan' in s:
        return 'megan', 'Team Megan'
    if 'shaw' in s:
        return 'shaw', 'Team Shaw'
    if 'tony' in s:
        return 'tony', 'Team Tony'
    if 'nick' in s:
        return 'nick', 'Team Nick'
    if 'jay' in s:
        return 'jay', 'Team Jay'
    if 'drecksel' in s or 'drechsel' in s:
        return 'drecksel', 'Team Drecksel'
    return 'ops', 'Ops / Unassigned'


def schedule_status(date_text: str) -> str:
    today = datetime.now(timezone.utc).date()
    dt = datetime.fromisoformat(date_text).date()
    if dt < today:
        return 'historical'
    if dt <= today + timedelta(days=7):
        return 'active'
    return 'upcoming'


def safe_id(*parts: str) -> str:
    raw = '-'.join(clean(p).lower() for p in parts if clean(p))
    raw = re.sub(r'[^a-z0-9]+', '-', raw).strip('-')
    return raw or 'schedule-item'


class Workbook:
    def __init__(self, path: Path):
        self.path = path
        self.z = zipfile.ZipFile(path)
        self.shared = []
        if 'xl/sharedStrings.xml' in self.z.namelist():
            root = ET.fromstring(self.z.read('xl/sharedStrings.xml'))
            for si in root.findall(NS + 'si'):
                self.shared.append(''.join(t.text or '' for t in si.iter(NS + 't')))
        wb = ET.fromstring(self.z.read('xl/workbook.xml'))
        rels = ET.fromstring(self.z.read('xl/_rels/workbook.xml.rels'))
        relmap = {r.attrib['Id']: r.attrib['Target'] for r in rels}
        self.sheets = {}
        for s in wb.find(NS + 'sheets'):
            name = s.attrib['name']
            target = relmap[s.attrib[RNS + 'id']]
            if target.startswith('/'):
                target = target.lstrip('/')
            elif target.startswith('worksheets/'):
                target = 'xl/' + target
            else:
                target = 'xl/' + target
            self.sheets[name] = target

    def rows(self, sheet: str):
        root = ET.fromstring(self.z.read(self.sheets[sheet]))
        for row in root.iter(NS + 'row'):
            vals = []
            last = -1
            for c in row.findall(NS + 'c'):
                idx = colnum(c.attrib.get('r', 'A1'))
                while last + 1 < idx:
                    vals.append('')
                    last += 1
                v = c.find(NS + 'v')
                val = ''
                if v is not None:
                    val = v.text or ''
                    if c.attrib.get('t') == 's':
                        try:
                            val = self.shared[int(val)]
                        except Exception:
                            pass
                vals.append(val)
                last = idx
            yield vals


def meta(key, name, url, trust='operational', role=None):
    d = {
        'sourceKey': key,
        'sourceName': name,
        'sourceUrl': url,
        'fetchedAt': FETCHED,
        'trustLevel': trust,
        'sampleData': False,
    }
    if role:
        d['sourceRole'] = role
    return d


def generate():
    sessions_wb = Workbook(ROOT / 'data/google_exports/numbers_per_session_1dfke_2026-04-28.xlsx')
    schedule_wb = Workbook(ROOT / 'data/google_exports/upcoming_schedule_1F05mJ_2026-04-28.xlsx')
    comparisons_wb = Workbook(ROOT / 'data/lindsey_shared_2026-04-25/Market_Comparisons.xlsx')
    ws_wb = Workbook(ROOT / 'data/lindsey_shared_2026-04-25/2026_WS_Sales_Tracker.xlsx')

    sessions = []
    market_session_rows = defaultdict(list)
    for i, row in enumerate(sessions_wb.rows('Sheet2')):
        if i == 0 or len(row) < 8:
            continue
        market = clean(row[0])
        if not market:
            continue
        rec = {
            **meta('numbers_per_session_adapter', 'Numbers Per Session export', 'data/google_exports/numbers_per_session_1dfke_2026-04-28.xlsx', 'operational', 'session_truth'),
            'market': market,
            'date': excel_date(row[2]),
            'sessionNumber': int(num(row[3], 0)),
            'location': clean(row[4]),
            'registration': int(num(row[5])),
            'attended': int(num(row[6])),
            'deals': int(num(row[7])),
            'showRate': num(row[8]),
            'written': 0,
            'collected': 0,
            'spend': 0,
            'cpa': 0,
            'dpl': 0,
        }
        sessions.append(rec)
        market_session_rows[market].append(rec)

    finals = []
    for market, rows in market_session_rows.items():
        regs = sum(r['registration'] for r in rows)
        attended = sum(r['attended'] for r in rows)
        deals = sum(r['deals'] for r in rows)
        latest = max((r['date'] for r in rows if r['date']), default='')
        finals.append({
            **meta('numbers_per_session_adapter', 'Numbers Per Session export', 'data/google_exports/numbers_per_session_1dfke_2026-04-28.xlsx', 'operational', 'session_rollup'),
            'market': market,
            'date': latest,
            'team': 'Unassigned / source pending',
            'finalRegistrations': regs,
            'finalAttendees': attended,
            'finalDeals': deals,
            'showRate': attended / regs if regs else 0,
        })
    finals.sort(key=lambda r: r['date'], reverse=True)

    # Schedule from FE Venue Booking Status. The sheet is block-structured: a route market row
    # is followed by contact/team rows and then dated venue rows. Do not treat col A/B junk
    # (serials, headers, On-Site Contact, *Tax Deed AI, etc.) as owner/team.
    schedule = []
    schedule_rows = list(schedule_wb.rows('FE Venue Booking Status'))
    blocks = []
    current_start = None
    for idx, row in enumerate(schedule_rows):
        padded = row + [''] * 14
        market_candidate = clean(padded[2])
        # A real route block has a non-control market label in the Market column.
        if market_candidate and not looks_like_control_label(market_candidate) and not is_excel_date(market_candidate):
            if current_start is not None:
                blocks.append((current_start, idx))
            current_start = idx
    if current_start is not None:
        blocks.append((current_start, len(schedule_rows)))

    for start, end in blocks:
        block_rows = schedule_rows[start:end]
        route_row = (block_rows[0] + [''] * 14)
        market = clean(route_row[2])
        route_value = clean(route_row[4])
        if 'airtable' in market.lower() and route_value and not looks_like_control_label(route_value):
            market = route_value
        if looks_like_control_label(market):
            continue
        route = route_value or clean(route_row[5]) or market
        team_key, team = 'ops', 'Ops / Unassigned'
        on_site_contact = ''
        for local_row in block_rows[:14]:
            padded = local_row + [''] * 14
            for cell in padded[:3]:
                value = clean(cell)
                if value.lower() == 'on-site contact':
                    continue
                if value and not on_site_contact and not looks_like_control_label(value) and not value.lower().startswith('team') and not value.replace('-', '').replace('(', '').replace(')', '').replace(' ', '').isdigit():
                    on_site_contact = value
                if 'team' in value.lower() or any(name in value.lower() for name in ['vogel', 'cord', 'wayne', 'gray', 'grey', 'dent', 'wyman', 'megan', 'shaw', 'tony', 'nick', 'jay', 'drecksel', 'drechsel']):
                    candidate_key, candidate_team = normalize_team(value)
                    if candidate_key != 'ops':
                        team_key, team = candidate_key, candidate_team
                        break
            if team_key != 'ops':
                break

        for offset, row in enumerate(block_rows):
            padded = row + [''] * 14
            date = excel_date(padded[6])
            area = clean(padded[5])
            times = clean(padded[7])
            venue = clean(padded[8])
            address = clean(padded[9])
            # Reject route/header/control rows with no operational event detail.
            if not date or (not area and not times and not venue and not address):
                continue
            source_row = start + offset + 1
            status = schedule_status(date)
            location = venue or area or address or market
            event_id = safe_id('schedule', market, route, team_key, date, str(source_row))
            schedule.append({
                **meta('schedule_adapter', 'Upcoming schedule export', 'data/google_exports/upcoming_schedule_1F05mJ_2026-04-28.xlsx', 'operational', 'upcoming_schedule'),
                'id': event_id,
                'market': market,
                'route': route,
                'team': team,
                'teamKey': team_key,
                'weekOf': week_bucket(date),
                'startDate': date,
                'endDate': date,
                'location': location,
                'state': status,
                'owner': team,
                'eventType': 'front_end_preview',
                'area': area,
                'city': area,
                'venue': venue,
                'address': address,
                'times': times,
                'parking': clean(padded[10]),
                'ballroom': clean(padded[11]),
                'locationCode': clean(padded[13]),
                'hotelStatus': clean(padded[3]),
                'onSiteContact': on_site_contact,
                'sourceSheet': 'FE Venue Booking Status',
                'sourceRow': source_row,
                'sourceTabRole': 'operational_schedule',
                'notes': 'Parsed from TLWB/MO Schedule route block; team normalized by generator.',
            })

    route_groups = defaultdict(list)
    for event in schedule:
        route_groups[(event['market'], event['route'], event['teamKey'])].append(event)
    schedule_route_blocks = []
    for (market, route, team_key), events in route_groups.items():
        events = sorted(events, key=lambda e: e['startDate'])
        runs = []
        current_run = []
        previous_date = None
        for event in events:
            event_date = datetime.fromisoformat(event['startDate']).date()
            if previous_date is not None and (event_date - previous_date).days > 1:
                runs.append(current_run)
                current_run = []
            current_run.append(event)
            previous_date = event_date
        if current_run:
            runs.append(current_run)
        for run_index, run_events in enumerate(runs, 1):
            team = run_events[0]['team']
            start_date = run_events[0]['startDate']
            end_date = run_events[-1]['endDate']
            statuses = {e['state'] for e in run_events}
            status = 'active' if 'active' in statuses else 'upcoming' if 'upcoming' in statuses else 'historical'
            schedule_route_blocks.append({
                **meta('schedule_adapter', 'Upcoming schedule export', 'data/google_exports/upcoming_schedule_1F05mJ_2026-04-28.xlsx', 'operational', 'schedule_route_block'),
                'id': safe_id('route', market, route, team_key, start_date, end_date, str(run_index)),
                'market': market,
                'route': route,
                'team': team,
                'teamKey': team_key,
                'status': status,
                'startDate': start_date,
                'endDate': end_date,
                'eventCount': len(run_events),
                'areas': sorted({e.get('area', '') for e in run_events if e.get('area')}),
                'venues': sorted({e.get('venue', '') for e in run_events if e.get('venue')}),
                'sourceSheet': 'FE Venue Booking Status',
                'sourceRows': [e['sourceRow'] for e in run_events],
            })

    # Market forecasting gives active preview marketing/forecast stats.
    tracker = []
    market_ops = []
    latest_forecast = {}
    for row in comparisons_wb.rows('Market Forecasting'):
        if len(row) < 10 or clean(row[0]) in {'', 'Event'}:
            continue
        market = clean(row[0])
        current_date = excel_date(row[1])
        if not market or not current_date:
            continue
        latest_forecast[market] = row
    for market, row in latest_forecast.items():
        current_reg = int(num(row[4]))
        reg_forecast = int(num(row[5]))
        cpr = num(row[6])
        show_forecast = int(num(row[7]))
        sale_forecast = int(num(row[8]))
        cpa_forecast = num(row[9])
        spend = current_reg * cpr if current_reg and cpr else max(0, sale_forecast * cpa_forecast)
        tracker.append({
            **meta('market_comparisons_adapter', 'Market Comparisons / Forecasting', 'data/lindsey_shared_2026-04-25/Market_Comparisons.xlsx', 'analytic', 'forecasting'),
            'market': market,
            'date': excel_date(row[3]) or excel_date(row[2]) or excel_date(row[1]),
            'totalRegistered': current_reg,
            'totalAttended': show_forecast,
            'totalBuyers': sale_forecast,
            'spend': spend,
            'written': max(0, num(row[12])),
            'collected': 0,
            'collected90Day': 0,
            'channels': [],
        })
        market_ops.append({
            **meta('market_comparisons_adapter', 'Market Comparisons / Forecasting', 'data/lindsey_shared_2026-04-25/Market_Comparisons.xlsx', 'analytic', 'active_forecast'),
            'mode': 'preview',
            'team': 'Team/source pending',
            'market': market,
            'date': excel_date(row[3]) or excel_date(row[2]) or excel_date(row[1]),
            'status': 'active',
            'registrations': current_reg,
            'sold': sale_forecast,
            'attended': show_forecast,
            'deals': sale_forecast,
            'confirmedMeBuyers': sale_forecast,
            'showUpRate': show_forecast / current_reg if current_reg else 0,
            'spend': spend,
            'costPerRegistration': spend / current_reg if current_reg else 0,
            'bisCost': spend / show_forecast if show_forecast else 0,
            'cpa': spend / sale_forecast if sale_forecast else 0,
            'notes': 'Active forecast row; confirm team assignment and final spend source.',
        })

    # Completed market forecast rows for prior market comparisons.
    latest_completed = {}
    for row in comparisons_wb.rows('Completed Markets'):
        if len(row) < 10 or clean(row[0]) in {'', 'Event'}:
            continue
        market = clean(row[0])
        cur = excel_date(row[1])
        if not market or not cur:
            continue
        latest_completed[market] = row
    for market, row in latest_completed.items():
        regs = int(num(row[4]))
        show = int(num(row[7]))
        sales = int(num(row[8]))
        cpr = num(row[6])
        spend = regs * cpr if regs and cpr else 0
        market_ops.append({
            **meta('market_comparisons_adapter', 'Market Comparisons / Completed Markets', 'data/lindsey_shared_2026-04-25/Market_Comparisons.xlsx', 'analytic', 'prior_market_comparison'),
            'mode': 'preview',
            'team': 'Prior team/source pending',
            'market': market,
            'date': excel_date(row[3]) or excel_date(row[2]) or excel_date(row[1]),
            'status': 'last_completed',
            'registrations': regs,
            'sold': sales,
            'attended': show,
            'deals': sales,
            'confirmedMeBuyers': sales,
            'showUpRate': show / regs if regs else 0,
            'spend': spend,
            'costPerRegistration': spend / regs if regs else 0,
            'bisCost': spend / show if show else 0,
            'cpa': spend / sales if sales else 0,
            'notes': 'Latest completed-market comparison row; team/speaker not carried in this sheet.',
        })

    # Workshop/PV sales tracker. PV rows augment preview final/ME-confirmed; WS rows drive workshop page.
    team_kpis = []
    speaker = defaultdict(lambda: {'gross': 0, 'bu': 0, 'collectedQuality': 0})
    for i, row in enumerate(ws_wb.rows('2026 Event Breakdown')):
        if i == 0 or len(row) < 13:
            continue
        event = clean(row[0])
        if not event:
            continue
        bu = int(num(row[1]))
        written = num(row[2])
        gross = num(row[5])
        cancels = abs(num(row[6]))
        inside = num(row[8])
        spk = clean(row[9]) or 'Speaker pending'
        me_registered = int(num(row[11]))
        me_attended = int(num(row[12]))
        quarter = clean(row[10]) or '2026'
        period = 'ytd'
        team_kpis.append({
            **meta('lindsey_dashboard_adapter', '2026 WS Sales Tracker', 'data/lindsey_shared_2026-04-25/2026_WS_Sales_Tracker.xlsx', 'tracker', 'sales_tracker'),
            'periodLabel': quarter,
            'periodType': period,
            'team': spk,
            'leads': me_registered,
            'written': written,
            'collected': gross,
            'dpl': written / me_attended if me_attended else 0,
            'cancelCount': 0,
            'cancelDollars': cancels,
            'cancelRate': cancels / written if written else 0,
            'refundCount': 0,
            'refundDollars': 0,
            'refundRate': 0,
            'bouncedAchCount': 0,
            'bouncedAchDollars': 0,
            'bouncedAchRate': 0,
            'recollectedDollars': 0,
            'netRealizedCash': gross - cancels,
        })
        speaker[spk]['gross'] += gross
        speaker[spk]['bu'] += bu
        speaker[spk]['collectedQuality'] += max(0, gross - cancels)
        if ' WS ' in event or ' WS' in event:
            market_name = re.sub(r'\s*WS.*$', '', event).strip()
            market_ops.append({
                **meta('lindsey_dashboard_adapter', '2026 WS Sales Tracker', 'data/lindsey_shared_2026-04-25/2026_WS_Sales_Tracker.xlsx', 'tracker', 'workshop_sales'),
                'mode': 'workshop',
                'team': spk,
                'market': market_name,
                'date': '',
                'status': 'final',
                'registrations': me_registered,
                'sold': bu,
                'attended': me_attended,
                'deals': bu,
                'confirmedMeBuyers': me_registered,
                'showUpRate': me_attended / me_registered if me_registered else 0,
                'notes': event,
            })

    speaker_benchmarks = []
    for spk, vals in speaker.items():
        if vals['bu'] <= 0 and vals['gross'] <= 0:
            continue
        speaker_benchmarks.append({
            **meta('speaker_benchmark_adapter', '2026 WS Sales Tracker speaker rollup', 'data/lindsey_shared_2026-04-25/2026_WS_Sales_Tracker.xlsx', 'analytic', 'speaker_rollup'),
            'speaker': spk,
            'grossMonetization': vals['gross'],
            'balancedScore': vals['gross'] / max(vals['bu'], 1),
            'buyerTierA': 0,
            'buyerTierB': 0,
            'buyerTierC': vals['bu'],
            'collectedQuality': vals['collectedQuality'],
        })

    # De-duplicate/sort, keep pages readable.
    schedule = sorted(schedule, key=lambda r: r['startDate'])[:400]
    schedule_route_blocks = sorted(schedule_route_blocks, key=lambda r: r['startDate'])[:200]
    sessions = sorted(sessions, key=lambda r: (r['date'], r['market'], r['sessionNumber']), reverse=True)
    market_ops = market_ops[:500]
    team_kpis = team_kpis[:500]
    speaker_benchmarks = sorted(speaker_benchmarks, key=lambda r: r['grossMonetization'], reverse=True)[:100]

    data = {
        'finals': finals,
        'tracker': tracker,
        'sessions': sessions,
        'schedule': schedule,
        'scheduleRouteBlocks': schedule_route_blocks,
        'legacySchedule': [],
        'teamKpis': team_kpis,
        'segMetrics': [],
        'speakerBenchmarks': speaker_benchmarks,
        'marketOps': market_ops,
    }
    OUT.write_text(
        "import type { DashboardDataset } from '../types';\n\n" +
        "export const generatedDashboardData: DashboardDataset = " + json.dumps(data, indent=2) + " as DashboardDataset;\n"
    )
    print(f"Wrote {OUT}")
    print({k: len(v) for k, v in data.items()})


if __name__ == '__main__':
    generate()
