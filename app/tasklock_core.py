"""TaskLock v5 — offline-first, backwards compatible task/storage core.

No network access, telemetry, or background installation is performed here.
"""
from __future__ import annotations
import calendar
import json
import os
from pathlib import Path
import shutil
import tempfile
import uuid
import zipfile
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit

VERSION = '5.1.0'
FMT = '%Y-%m-%d %H:%M'
DEFAULT_SITES = 'youtube.com, tiktok.com, instagram.com'
REPEATS = ('Never', 'Daily', 'Weekdays', 'Weekly', 'Every 2 Weeks', 'Monthly', 'Every 3 Months', 'Yearly')
CATEGORIES = ('School', 'Chores', 'Personal', 'Work', 'Other')
PRIORITIES = ('Normal', 'High', 'Low')
DEFAULT_SETTINGS = {'ringtone': 'Digital Pulse', 'sound_volume': 65, 'category_sounds': {},
                    'theme': 'Bluecore', 'text_scale': 'Normal', 'motion': True,
                    'first_run_complete': False, 'focus_minutes': 25, 'reminder_snooze': 5}


def app_folder() -> Path:
    return Path(os.environ.get('APPDATA', str(Path.home() / '.local' / 'share'))) / 'TaskLock'


def normalize_sites(raw: str) -> list[str]:
    sites = []
    for value in raw.split(','):
        candidate = value.strip().lower()
        try:
            if '://' not in candidate:
                candidate = 'https://' + candidate
            parts = urlsplit(candidate)
            host = (parts.hostname or '').rstrip('.')
            if parts.username or parts.password or not host or '.' not in host:
                continue
            if not all(part and part[0].isalnum() and part[-1].isalnum()
                       and all(c.isalnum() or c == '-' for c in part) for part in host.split('.')):
                continue
            if host not in sites:
                sites.append(host)
        except ValueError:
            continue
    return sites


def validate_due(day: str, clock: str) -> str:
    return datetime.strptime(day.strip() + ' ' + clock.strip(), FMT).strftime(FMT)


def normalize_subtasks(value):
    if isinstance(value, str):
        value = [{'title': s.strip(), 'done': False} for s in value.splitlines() if s.strip()]
    if not isinstance(value, list):
        return []
    result = []
    for s in value[:100]:
        if isinstance(s, str):
            s = {'title': s, 'done': False}
        if isinstance(s, dict) and str(s.get('title', '')).strip():
            result.append({'title': str(s['title']).strip()[:200], 'done': bool(s.get('done'))})
    return result


def make_task(title: str, due: str, repeat='Never', category='School', priority='Normal',
              notes='', homework=False, blocked_sites=None, link='', subtasks=None) -> dict:
    if not title.strip():
        raise ValueError('Give the task a name.')
    datetime.strptime(due, FMT)
    if repeat not in REPEATS or category not in CATEGORIES or priority not in PRIORITIES:
        raise ValueError('Invalid task setting.')
    return {
        'id': uuid.uuid4().hex, 'title': title.strip()[:200], 'due': due,
        'repeat': repeat, 'category': category, 'priority': priority,
        'notes': notes.strip(), 'homework': bool(homework),
        'blocked_sites': blocked_sites or [], 'link': link.strip(),
        'subtasks': normalize_subtasks(subtasks), 'snooze_until': None,
        'focus_started': False, 'blocked_paused': False, 'state': 'open', 'completed_at': None,
    }


def normalized_task(t: dict) -> dict:
    """Migrate existing v1–v4 JSON records without removing extra fields."""
    item = dict(t)
    item.setdefault('id', uuid.uuid4().hex)
    item.setdefault('title', 'Untitled task')
    item.setdefault('repeat', 'Never')
    item.setdefault('category', 'School' if item.get('homework') else 'Personal')
    item.setdefault('priority', 'Normal')
    item.setdefault('notes', '')
    item.setdefault('link', '')
    item.setdefault('homework', False)
    item.setdefault('blocked_sites', [])
    item.setdefault('snooze_until', None)
    item.setdefault('focus_started', False)
    item.setdefault('blocked_paused', False)
    item.setdefault('state', 'open')
    item.setdefault('completed_at', None)
    item['subtasks'] = normalize_subtasks(item.get('subtasks', []))
    if item['repeat'] not in REPEATS:
        item['repeat'] = 'Never'
    return item


def add_months(dt: datetime, n: int) -> datetime:
    month = dt.month - 1 + n
    year = dt.year + month // 12
    month = month % 12 + 1
    return dt.replace(year=year, month=month, day=min(dt.day, calendar.monthrange(year, month)[1]))


def next_occurrence(dt: datetime, repeat: str) -> datetime | None:
    if repeat == 'Daily':
        return dt + timedelta(days=1)
    if repeat == 'Weekdays':
        nxt = dt + timedelta(days=1)
        while nxt.weekday() >= 5:
            nxt += timedelta(days=1)
        return nxt
    if repeat == 'Weekly':
        return dt + timedelta(days=7)
    if repeat == 'Every 2 Weeks':
        return dt + timedelta(days=14)
    if repeat == 'Monthly':
        return add_months(dt, 1)
    if repeat == 'Every 3 Months':
        return add_months(dt, 3)
    if repeat == 'Yearly':
        return add_months(dt, 12)
    return None


def complete_task(tasks: list[dict], item: dict, now: datetime | None = None) -> None:
    now = now or datetime.now()
    if item.get('state') == 'done':
        return
    nxt = next_occurrence(datetime.strptime(item['due'], FMT), item.get('repeat', 'Never'))
    if nxt is not None:
        while nxt <= now:
            nxt = next_occurrence(nxt, item['repeat'])
        import copy
        snapshot = copy.deepcopy(item)
        snapshot.update(id=uuid.uuid4().hex, repeat='Never', state='done',
                        completed_at=now.strftime(FMT), focus_started=False, blocked_paused=False,
                        snooze_until=None)
        tasks.append(snapshot)
        item['due'] = nxt.strftime(FMT)
        item['subtasks'] = [{**s, 'done': False} for s in item.get('subtasks', [])]
        item['focus_started'] = False
        item['blocked_paused'] = False
        item['snooze_until'] = None
    else:
        item.update(state='done', completed_at=now.strftime(FMT),
                    focus_started=False, blocked_paused=False, snooze_until=None)


def is_homework_blocking(t: dict, now: datetime | None = None) -> bool:
    if t.get('state', 'open') != 'open' or not t.get('homework') or t.get('blocked_paused'):
        return False
    now = now or datetime.now()
    try:
        return bool(t.get('focus_started')) or datetime.strptime(t['due'], FMT) <= now
    except (ValueError, KeyError):
        return False


def active_sites(tasks: list[dict], now: datetime | None = None) -> list[str]:
    return sorted({s for t in tasks if is_homework_blocking(t, now) for s in t.get('blocked_sites', [])})


def is_due(t: dict, now: datetime | None = None) -> bool:
    if t.get('state', 'open') != 'open':
        return False
    now = now or datetime.now()
    try:
        return datetime.strptime(t.get('snooze_until') or t['due'], FMT) <= now
    except (ValueError, KeyError, TypeError):
        return False


class TaskStore:
    def __init__(self, folder: Path | None = None):
        self.folder = Path(folder) if folder else app_folder()
        self.tasks_path = self.folder / 'tasks.json'
        self.settings_path = self.folder / 'settings.json'
        self.folder.mkdir(parents=True, exist_ok=True)
        self._migration_backup()
        self.tasks = self._read_tasks()
        raw = self._read_json(self.settings_path, {})
        self.settings = {**DEFAULT_SETTINGS, **(raw if isinstance(raw, dict) else {})}

    def _migration_backup(self):
        """Create a one-time copy before v5 reads old data. Never overwrite backup."""
        backup = self.folder / 'pre_v5_backup'
        if backup.exists() or not any(p.exists() for p in (self.tasks_path, self.settings_path)):
            return
        backup.mkdir(exist_ok=True)
        for source in (self.tasks_path, self.settings_path):
            if source.exists():
                shutil.copy2(source, backup / source.name)

    @staticmethod
    def _read_json(path, default):
        try:
            with open(path, encoding='utf-8') as f:
                return json.load(f)
        except (OSError, ValueError):
            return default

    def _read_tasks(self):
        data = self._read_json(self.tasks_path, [])
        if not isinstance(data, list):
            return []
        return [normalized_task(t) for t in data if isinstance(t, dict) and isinstance(t.get('due'), str) and valid_task_due(t['due'])]

    @staticmethod
    def _atomic_json(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix='.tasklock-', suffix='.json', dir=path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def save(self):
        self._atomic_json(self.tasks_path, self.tasks)

    def save_settings(self):
        self._atomic_json(self.settings_path, self.settings)

    def backup(self, dest: Path):
        """User-initiated portable backup: tasks and settings, with optional custom WAV."""
        dest = Path(dest)
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('tasks.json', json.dumps(self.tasks, indent=2, ensure_ascii=False))
            z.writestr('settings.json', json.dumps(self.settings, indent=2, ensure_ascii=False))
            path = Path(self.settings.get('custom_path') or '')
            if path.is_file() and path.suffix.lower() == '.wav' and path.stat().st_size <= 15_000_000:
                z.write(path, 'custom_ringtone.wav')

    def restore(self, src: Path):
        """Validate restore before replacing current files; preserve prior data in snapshot."""
        src = Path(src)
        if src.stat().st_size > 25_000_000:
            raise ValueError('Backup file is too large.')
        with zipfile.ZipFile(src) as z:
            if not {'tasks.json', 'settings.json'} <= set(z.namelist()):
                raise ValueError('Not a TaskLock backup.')
            if z.getinfo('tasks.json').file_size > 5_000_000 or z.getinfo('settings.json').file_size > 1_000_000:
                raise ValueError('Backup contains an oversized data file.')
            tasks = json.loads(z.read('tasks.json'))
            settings = json.loads(z.read('settings.json'))
            if not isinstance(tasks, list) or not isinstance(settings, dict):
                raise ValueError('Backup content is invalid.')
            if any(not isinstance(t, dict) or not valid_task_due(t.get('due')) for t in tasks):
                raise ValueError('Backup contains an invalid task date.')
            self.backup(self.folder / 'before_restore.zip')
            self.tasks = [normalized_task(t) for t in tasks]
            self.settings = {**DEFAULT_SETTINGS, **settings}
            if 'custom_ringtone.wav' in z.namelist() and z.getinfo('custom_ringtone.wav').file_size <= 15_000_000:
                path = self.folder / 'ringtones' / 'Restored_Custom.wav'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(z.read('custom_ringtone.wav'))
                self.settings['custom_path'] = str(path)
            self.save()
            self.save_settings()


def valid_task_due(due):
    try:
        datetime.strptime(due, FMT)
        return True
    except (TypeError, ValueError):
        return False
