import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from tasklock_core import (TaskStore, make_task, complete_task, normalize_sites,
                           validate_due, active_sites, is_due, normalized_task, is_homework_blocking)
from tasklock_audio import SCORES, TONES, INSTRUMENTS, ensure_tones


def test_migrate_v3(tmp_path):
    old = [{"id":"v3","title":"Math","due":"2026-10-25 18:00","repeat":"Weekly",
            "snooze_until":None,"homework":True,"blocked_sites":["youtube.com"]}]
    (tmp_path/'tasks.json').write_text(__import__('json').dumps(old))
    db = TaskStore(tmp_path)
    assert db.tasks[0]['title'] == 'Math'
    assert db.tasks[0]['category'] == 'School'
    assert db.tasks[0]['state'] == 'open'
    db.save()
    assert TaskStore(tmp_path).tasks[0]['id'] == 'v3'


def test_done_and_recurring():
    t = make_task('Study', '2026-10-25 18:00', repeat='Daily', homework=True, blocked_sites=['youtube.com'])
    arr = [t]
    complete_task(arr,t,datetime(2026,10,27,18,0))
    assert t['due'] == '2026-10-28 18:00'
    assert len(arr) == 2 and arr[1]['state'] == 'done'
    assert arr[1]['repeat'] == 'Never'


def test_blocking_and_due():
    t = make_task('Homework', '2026-11-10 17:00', homework=True, blocked_sites=['youtube.com'])
    now = datetime(2026,10,25,19,0)
    assert not is_homework_blocking(t,now)
    t['focus_started'] = True
    assert active_sites([t],now) == ['youtube.com']
    t['snooze_until'] = '2026-11-12 18:00'
    assert not is_due(t,now)
    complete_task([t],t,now)
    assert not is_homework_blocking(t,now)


def test_sites_validate():
    assert normalize_sites('HTTPS://YouTube.com/watch, tiktok.com, youtube.com, bad host, https://classroom.google.com/') == ['youtube.com','tiktok.com','classroom.google.com']
    assert validate_due('2026-10-25','18:02') == '2026-10-25 18:02'


def test_audio(tmp_path):
    ensure_tones(tmp_path)
    assert len(list(tmp_path.glob('*.wav'))) == 20
    assert set(INSTRUMENTS) == set(SCORES)
    assert 'Brass Fanfare' in TONES and 'Drumline Call' in TONES
    assert (tmp_path/'Electric_Guitar_Hook.wav').exists()
    import wave
    with wave.open(str(tmp_path/'Neon_Flight.wav')) as f:
        assert f.getnchannels() == 1 and f.getnframes() > 1000
