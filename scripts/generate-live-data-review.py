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
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dash-glow-up-15" / "src" / "data" / "generatedData.ts"
SCHEDULE_JSON_OUT = ROOT / "dash-glow-up-15" / "data" / "schedule.json"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
TZ = ZoneInfo("America/Denver")
FETCHED = datetime.now(TZ).replace(microsecond=0).isoformat()

ACTIVE_PREVIEW_TEAM_OVERRIDES = {
    # 2026-06-22 source QA: live preview posts for Columbus are in #teamwayne.
    # The schedule export still labels this route Team Vogel/Cord, so the
    # review build corrects the rendered active route block while preserving
    # the sheet row/source reference.
    ("columbus, oh", "2026-06-20"): ("wayne-gray", "Team Wayne/Gray"),
}


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


def normalize_market_key(value: str) -> str:
    return re.sub(r"\s+", " ", clean(value).lower()).strip()


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


def schedule_status(date_text: str, today: date | None = None) -> str:
    today = today or datetime.now(TZ).date()
    dt = datetime.fromisoformat(date_text).date()
    if dt < today:
        return 'historical'
    if dt == today:
        return 'active'
    return 'upcoming'


def route_status(start_text: str, end_text: str, today: date | None = None) -> str:
    today = today or datetime.now(TZ).date()
    start = datetime.fromisoformat(start_text).date()
    end = datetime.fromisoformat(end_text).date()
    if end < today:
        return 'historical'
    if start <= today <= end:
        return 'active'
    return 'upcoming'


def parse_2026_event_range(event: str) -> tuple[str, str] | None:
    match = re.search(r'(\d{1,2})/(\d{1,2})(?:\s*-\s*(?:(\d{1,2})/)?(\d{1,2}))', event)
    if not match:
        return None
    start_month = int(match.group(1))
    start_day = int(match.group(2))
    end_month = int(match.group(3) or start_month)
    end_day = int(match.group(4))
    start = datetime(2026, start_month, start_day).date()
    end = datetime(2026, end_month, end_day).date()
    if end < start:
        end = datetime(2026, end_month + 1, end_day).date()
    return start.isoformat(), end.isoformat()


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
                elif c.attrib.get('t') == 'inlineStr':
                    val = ''.join(t.text or '' for t in c.iter(NS + 't'))
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


WORKSHOP_SCHEDULE_SOURCE = 'data/google_exports/workshop_schedule_sheet_1psHz1_latest.xlsx'
WORKSHOP_SCHEDULE_GROUPS = (
    ('Market A', 4, 5, 6, 24),
    ('Market B', 29, 30, 31, 48),
    ('Market C', 53, 54, 55, 73),
    ('Market D', 78, 79, 80, 98),
)
MONTH_NUMBERS = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12,
}


def parse_2026_written_range(value: str) -> tuple[str, str] | None:
    """Parse Workshop Team Scheduling labels such as 'July 31-Aug 2'."""
    text = clean(value).replace('–', '-').replace('—', '-')
    match = re.search(
        r'([A-Za-z]+)\s*(\d{1,2})(?:st|nd|rd|th)?\s*-\s*'
        r'(?:([A-Za-z]+)\s*)?(\d{1,2})(?:st|nd|rd|th)?',
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    start_month = MONTH_NUMBERS.get(match.group(1).lower())
    end_month = MONTH_NUMBERS.get((match.group(3) or match.group(1)).lower())
    if not start_month or not end_month:
        return None
    try:
        start = datetime(2026, start_month, int(match.group(2))).date()
        end = datetime(2026, end_month, int(match.group(4))).date()
    except ValueError:
        return None
    if end < start:
        return None
    return start.isoformat(), end.isoformat()


def normalize_workshop_team(raw: str) -> tuple[str, str]:
    value = clean(raw).lower()
    if 'jazey' in value or 'drecksel' in value or 'drechsel' in value:
        return 'drexel', 'Team Drexel'
    if 'nicholas' in value or 'lamagna' in value or 'nick' in value:
        return 'nick', 'Team Nick'
    if 'megan' in value or 'shaw' in value:
        return 'shaw', 'Team Shaw'
    if 'tony' in value or 'rosenbum' in value:
        return 'tony', 'Team Tony'
    if 'nate' in value or 'harris' in value:
        return 'nate', 'Team Nate'
    return 'ops', f'{clean(raw) or "Speaker pending"} / speaker'


def extract_workshop_venue(rooming_list: str) -> str:
    value = clean(rooming_list)
    if '|' not in value:
        return ''
    return clean(value.rsplit('|', 1)[-1])


def parse_workshop_schedule_rows(rows: list[list[str]], today=None) -> tuple[list[dict], list[dict]]:
    """Build current/future ME workshop calendar records from the wide 2026 schedule."""
    today = today or datetime.now(TZ).date()
    blocks: list[dict] = []
    events: list[dict] = []

    def source_row(row_number: int) -> list[str]:
        return rows[row_number - 1] if 0 < row_number <= len(rows) else []

    for group_label, date_row, market_row, speaker_row, rooming_row in WORKSHOP_SCHEDULE_GROUPS:
        date_values = source_row(date_row)
        market_values = source_row(market_row)
        speaker_values = source_row(speaker_row)
        rooming_values = source_row(rooming_row)
        max_columns = max(map(len, (date_values, market_values, speaker_values, rooming_values)), default=0)
        for column in range(1, max_columns):
            date_range = parse_2026_written_range(date_values[column] if column < len(date_values) else '')
            market = clean(market_values[column] if column < len(market_values) else '')
            if not date_range or not market or market.upper() in {'OFF', 'EXPO'}:
                continue
            start_date, end_date = date_range
            if datetime.fromisoformat(end_date).date() < today:
                continue
            speaker = clean(speaker_values[column] if column < len(speaker_values) else '')
            rooming_list = clean(rooming_values[column] if column < len(rooming_values) else '')
            venue = extract_workshop_venue(rooming_list) or 'venue pending'
            team_key, team = normalize_workshop_team(speaker)
            status = route_status(start_date, end_date, today=today)
            source_rows = [market_row, speaker_row, rooming_row]
            block_id = safe_id('me-workshop-schedule', market, team_key, start_date, end_date, str(column + 1))
            block = {
                **meta('workshop_team_schedule', 'Workshop Team Scheduling', WORKSHOP_SCHEDULE_SOURCE, 'operational', 'middle_end_schedule_supplement'),
                'id': block_id,
                'market': market,
                'route': 'Middle-End Workshop',
                'team': team,
                'teamKey': team_key,
                'status': status,
                'startDate': start_date,
                'endDate': end_date,
                'eventCount': 1,
                'areas': [market],
                'venues': [venue],
                'sourceSheet': f'2026 Schedule · {group_label}',
                'sourceRows': source_rows,
            }
            event = {
                **meta('workshop_team_schedule', 'Workshop Team Scheduling', WORKSHOP_SCHEDULE_SOURCE, 'operational', 'middle_end_schedule_supplement'),
                'id': f'{block_id}-event',
                'market': market,
                'route': 'Middle-End Workshop',
                'team': team,
                'teamKey': team_key,
                'weekOf': start_date,
                'startDate': start_date,
                'endDate': end_date,
                'location': venue,
                'state': status,
                'owner': team,
                'eventType': 'middle_end_workshop',
                'area': market,
                'city': market,
                'venue': venue,
                'address': '',
                'times': 'time pending',
                'parking': '',
                'ballroom': '',
                'locationCode': '',
                'hotelStatus': '',
                'onSiteContact': '',
                'sourceSheet': f'2026 Schedule · {group_label}',
                'sourceRow': market_row,
                'sourceTabRole': 'middle_end_schedule',
                'notes': f'Parsed from Workshop Team Scheduling column {column + 1}; rooming source: {rooming_list or "pending"}.',
            }
            blocks.append(block)
            events.append(event)
    return blocks, events


def generate():
    sessions_wb = Workbook(ROOT / 'data/google_exports/numbers_per_session_1dfke_latest.xlsx')
    schedule_wb = Workbook(ROOT / 'data/google_exports/upcoming_schedule_1F05mJ_latest.xlsx')
    workshop_schedule_wb = Workbook(ROOT / WORKSHOP_SCHEDULE_SOURCE)
    comparisons_wb = Workbook(ROOT / 'data/lindsey_shared_2026-04-25/Market_Comparisons.xlsx')
    ws_wb = Workbook(ROOT / 'data/google_exports/ws_sales_tracker_1CmJ_latest.xlsx')

    sessions = []
    market_session_rows = defaultdict(list)
    for i, row in enumerate(sessions_wb.rows('Sheet2')):
        if i == 0 or len(row) < 8:
            continue
        market = clean(row[0])
        if not market:
            continue
        rec = {
            **meta('numbers_per_session_adapter', 'Numbers Per Session export', 'data/google_exports/numbers_per_session_1dfke_latest.xlsx', 'operational', 'session_truth'),
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
            **meta('numbers_per_session_adapter', 'Numbers Per Session export', 'data/google_exports/numbers_per_session_1dfke_latest.xlsx', 'operational', 'session_rollup'),
            'market': market,
            'date': latest,
            'team': 'Ops / Unassigned',
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
                **meta('schedule_adapter', 'Upcoming schedule export', 'data/google_exports/upcoming_schedule_1F05mJ_latest.xlsx', 'operational', 'upcoming_schedule'),
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

    for event in schedule:
        for (market_key, start_date), (override_key, override_team) in ACTIVE_PREVIEW_TEAM_OVERRIDES.items():
            start_dt = datetime.fromisoformat(start_date).date()
            event_dt = datetime.fromisoformat(event["startDate"]).date()
            in_route_window = start_dt <= event_dt <= start_dt + timedelta(days=7)
            if normalize_market_key(event["market"]) == market_key and in_route_window:
                event["teamKey"] = override_key
                event["team"] = override_team
                event["owner"] = override_team
                event["notes"] = f"{event.get('notes', '')} Active preview source override: live Slack posts are in #{override_key.split('-')[0]}.".strip()

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
                **meta('schedule_adapter', 'Upcoming schedule export', 'data/google_exports/upcoming_schedule_1F05mJ_latest.xlsx', 'operational', 'schedule_route_block'),
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

    workshop_schedule_rows = list(workshop_schedule_wb.rows('2026 Schedule'))
    workshop_schedule_blocks, workshop_schedule_events = parse_workshop_schedule_rows(workshop_schedule_rows)
    future_workshop_cutoff = datetime.now(TZ).date() + timedelta(days=7)
    if not any(datetime.fromisoformat(block['startDate']).date() > future_workshop_cutoff for block in workshop_schedule_blocks):
        raise RuntimeError(
            'Workshop Team Scheduling has no parsed workshops more than seven days ahead; '
            'refusing to publish a schedule that stops after the current weekend.'
        )
    schedule.extend(workshop_schedule_events)

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
            'team': 'Team not listed in source',
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
            'team': 'Prior team not listed in source',
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
    middle_end_workshop_blocks = []
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
            **meta('lindsey_dashboard_adapter', '2026 WS Sales Tracker', 'data/google_exports/ws_sales_tracker_1CmJ_latest.xlsx', 'tracker', 'sales_tracker'),
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
            date_range = parse_2026_event_range(event)
            speaker_key, speaker_team = normalize_team(spk)
            if date_range:
                start_date, end_date = date_range
                middle_end_workshop_blocks.append({
                    **meta('ws_sales_tracker_schedule_supplement', '2026 WS Sales Tracker schedule supplement', 'data/google_exports/ws_sales_tracker_1CmJ_latest.xlsx', 'operational', 'middle_end_schedule_supplement'),
                    'id': safe_id('me-workshop', market_name, speaker_team, start_date, end_date, str(i + 1)),
                    'market': market_name,
                    'route': 'Middle-End Workshop',
                    'team': speaker_team if speaker_key != 'ops' else f'{spk} / speaker',
                    'teamKey': speaker_key if speaker_key != 'ops' else safe_id(spk),
                    'status': route_status(start_date, end_date),
                    'startDate': start_date,
                    'endDate': end_date,
                    'eventCount': 1,
                    'areas': [market_name],
                    'venues': ['venue pending'],
                    'sourceSheet': '2026 Event Breakdown',
                    'sourceRows': [i + 1],
                })
            market_ops.append({
                **meta('lindsey_dashboard_adapter', '2026 WS Sales Tracker', 'data/google_exports/ws_sales_tracker_1CmJ_latest.xlsx', 'tracker', 'workshop_sales'),
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
            **meta('speaker_benchmark_adapter', '2026 WS Sales Tracker speaker rollup', 'data/google_exports/ws_sales_tracker_1CmJ_latest.xlsx', 'analytic', 'speaker_rollup'),
            'speaker': spk,
            'grossMonetization': vals['gross'],
            'balancedScore': vals['gross'] / max(vals['bu'], 1),
            'buyerTierA': 0,
            'buyerTierB': 0,
            'buyerTierC': vals['bu'],
            'collectedQuality': vals['collectedQuality'],
        })

    expo_blocks = [{
        **meta('slack_expo_schedule_supplement', 'Slack #expo post-event reset', 'slack://channel/expo', 'operational', 'expo_schedule_supplement'),
        'id': 'expo-may-investor-2026-05-29',
        'market': 'May Investor Expo',
        'route': 'Investor Expo',
        'team': 'Expo',
        'teamKey': 'expo',
        'status': 'historical',
        'startDate': '2026-05-29',
        'endDate': '2026-05-29',
        'eventCount': 1,
        'areas': ['Expo'],
        'venues': ['Completed; next Expo count pending'],
        'sourceSheet': 'Slack #expo post-event reset',
        'sourceRows': [1],
    }]

    today_iso = datetime.now(TZ).date().isoformat()
    historical_tracker_workshops = [
        block for block in middle_end_workshop_blocks
        if block['endDate'] < today_iso
    ]
    schedule_route_blocks.extend(historical_tracker_workshops)
    schedule_route_blocks.extend(workshop_schedule_blocks)
    schedule_route_blocks.extend(expo_blocks)

    # Keep the full operational year plus ME supplements. The prior 400-record
    # cap silently dropped late-year/future workshop rows after sorting by date.
    schedule = sorted(schedule, key=lambda r: r['startDate'])[:1000]
    status_rank = {'active': 0, 'upcoming': 1, 'historical': 2, 'reference': 3}
    schedule_route_blocks = sorted(schedule_route_blocks, key=lambda r: (status_rank.get(r['status'], 9), r['startDate']))[:200]
    SCHEDULE_JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_JSON_OUT.write_text(json.dumps({
        'generated_at': FETCHED,
        'timezone': 'America/Denver',
        'source': {
            'source_id': 'upcoming_schedule',
            'source_name': 'TLWB/MO Schedule sheet',
            'source_type': 'google_sheet',
            'source_family': 'schedule',
            'trust_role': 'schedule_truth',
            'sheet_id': '1F05mJPz4m8Kzxc8ROTQc4puRBky263ghSUMTg4kxKqY',
            'parser': 'scripts/generate-live-data-review.py::FE Venue Booking Status parser',
            'expected_cadence': {
                'operational_schedule': '24h while routes are current/upcoming',
                'route_blocks': '24h while routes are current/upcoming',
                'historical': 'neutral/fine after route completion unless source check fails',
            },
        },
        'sections': {
            'preview_routes': [block for block in schedule_route_blocks if block['route'] and block['teamKey'] in {'wayne-gray', 'vogel-cord', 'dent', 'wyman', 'megan'}],
            'middle_end_workshop_routes': [block for block in schedule_route_blocks if block.get('sourceRole') == 'middle_end_schedule_supplement'],
            'expo': [block for block in schedule_route_blocks if block.get('sourceRole') == 'expo_schedule_supplement'],
            'upcoming_events': [block for block in schedule_route_blocks if block['status'] in {'active', 'upcoming'}],
        },
        'records': schedule,
        'route_blocks': schedule_route_blocks,
    }, indent=2) + "\n")
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
    print(f"Wrote {SCHEDULE_JSON_OUT}")
    print({k: len(v) for k, v in data.items()})


if __name__ == '__main__':
    generate()
