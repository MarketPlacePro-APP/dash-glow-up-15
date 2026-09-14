"""Read-only freshness observer; exit status means NEW attention, not KPI health.

Every run preserves the actual health verdict and incident state in an artifact.
Routine failed source checks are Harlow work. Notify once per incident/severity
for 90-minute access/availability loss or 24-hour unresolved freshness loss.
No deploys, source edits, mailbox rules, external messaging, or health rewrites.
"""
import base64
import io
import json
import os
import urllib.request
import urllib.error
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

URL = 'https://tlwb-kpi.vercel.app/api/status'
STATE_NAME = 'kpi-attention-state-v1'


def dt(value):
    try:
        result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return result if result.tzinfo else None
    except (ValueError, TypeError):
        return None


def due_cycle(now):
    local = now.astimezone(ZoneInfo('America/Denver'))
    slots = [datetime.combine((local + timedelta(days=d)).date(), datetime.min.time(), local.tzinfo).replace(hour=h, minute=5)
             for d in (-1, 0) for h in (8, 12, 16, 20)]
    return max(s for s in slots if s + timedelta(minutes=90) <= local)


def decide(observation, prior, now):
    completed = dt(observation.get('completed_at'))
    healthy = (observation.get('reachable') is True and completed is not None
               and completed <= now + timedelta(minutes=5)
               and completed >= due_cycle(now)
               and observation.get('result') in ('deployed', 'no_change'))
    if healthy:
        return {'schema': 1, 'checked_at': now.isoformat(), 'health': 'healthy',
                'incident_since': None, 'access_since': None, 'notified': [],
                'notify': False, 'attention': '', 'observation': observation}
    since = dt(prior.get('incident_since')) or now
    access_since = (dt(prior.get('access_since')) or now) if not observation.get('reachable') else None
    notified = list(prior.get('notified') or [])
    attention = ''
    category = None
    if access_since and now - access_since >= timedelta(minutes=90):
        category = 'access'
        attention = 'Troy attention: dashboard access or availability has failed for at least 90 minutes. Do not rely on the dashboard until access is restored; Harlow must identify any login or permission action needed.'
    elif now - since >= timedelta(hours=24):
        category = 'freshness'
        attention = 'Troy attention: KPI freshness has remained unresolved for at least 24 hours. Use source reports for decisions until Harlow verifies recovery; this is a prolonged interruption, not another routine retry.'
    notify = bool(category and category not in notified)
    if notify:
        notified.append(category)
    return {'schema': 1, 'checked_at': now.isoformat(), 'health': 'degraded',
            'incident_since': since.isoformat(), 'access_since': access_since.isoformat() if access_since else None,
            'notified': notified, 'notify': notify, 'attention': attention,
            'observation': observation}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github(path):
    req = urllib.request.Request('https://api.github.com/' + path,
        headers={'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'],
                 'Accept': 'application/vnd.github+json', 'User-Agent': 'KPI-attention-monitor'})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def prior_state():
    repo, branch = os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_REF_NAME']
    artifacts = github(f'repos/{repo}/actions/artifacts?name={STATE_NAME}&per_page=100')['artifacts']
    for artifact in sorted(artifacts, key=lambda a: a['id'], reverse=True):
        run = artifact.get('workflow_run') or {}
        if artifact.get('expired') or run.get('head_branch') != branch:
            continue
        detail = github(f'repos/{repo}/actions/runs/{run["id"]}')
        if detail.get('workflow_id') != 345822514:
            continue
        req = urllib.request.Request(artifact['archive_download_url'], headers={
            'Authorization': 'Bearer ' + os.environ['GITHUB_TOKEN'], 'User-Agent': 'KPI-attention-monitor'})
        try:
            response = urllib.request.build_opener(NoRedirect()).open(req, timeout=25)
        except urllib.error.HTTPError as exc:
            if exc.code != 302:
                raise
            location = exc.headers['Location']
            if not location.startswith('https://'):
                raise ValueError('Unsafe artifact redirect')
            # Do not forward GitHub credentials to artifact storage.
            response = urllib.request.urlopen(location, timeout=25)
        with response:
            blob = response.read(131073)
        if len(blob) > 131072:
            raise ValueError('State artifact too large')
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            info = archive.getinfo('state.json')
            if info.file_size > 65536:
                raise ValueError('State JSON too large')
            state = json.loads(archive.read(info))
        if state.get('schema') != 1:
            raise ValueError('Unknown state schema')
        return state
    return {}


def observe():
    auth = base64.b64encode((os.environ['TLWB_KPI_AUTH_USERNAME'] + ':' + os.environ['TLWB_KPI_AUTH_PASSWORD']).encode()).decode()
    try:
        request = urllib.request.Request(URL, headers={'Authorization': 'Basic ' + auth})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
        refresh = data.get('refresh') or {}
        completed = refresh.get('last_check_completed_at') or data.get('last_checked')
        if not dt(completed):
            return {'reachable': False, 'error': 'invalid_status_timestamp'}
        return {'reachable': True, 'completed_at': completed,
                'published_at': data.get('last_published'),
                'result': refresh.get('last_check_result'),
                'source_health': data.get('source_health')}
    except Exception as exc:
        return {'reachable': False, 'error': type(exc).__name__}


def main():
    now = datetime.now(timezone.utc)
    prior = prior_state()  # fail visibly if continuity cannot be trusted
    state = decide(observe(), prior, now)
    out = Path('attention-output')
    out.mkdir(exist_ok=True)
    (out / 'state.json').write_text(json.dumps(state, indent=2) + '\n')
    text = ('# TLWB KPI attention assessment\n\n'
            f'Actual dashboard freshness: **{state["health"]}**.\n\n'
            f'New Troy attention required: **{state["notify"]}**.\n\n'
            'A successful workflow means the attention policy ran, NOT that dashboard data is fresh. '
            'Routine failures remain recorded for Harlow; repeated notices are suppressed until verified recovery.\n\n'
            + (state['attention'] if state['notify'] else 'No new executive alert. Diagnostic state is retained in the artifact.'))
    (out / 'summary.md').write_text(text)
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as output:
        output.write(text)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
        output.write('notify=' + str(state['notify']).lower() + '\n')
    print(json.dumps({'health': state['health'], 'notify': state['notify']}))


if __name__ == '__main__':
    main()
