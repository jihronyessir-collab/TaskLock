import sys, json, zipfile
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from tasklock_core import TaskStore, make_task, next_occurrence, complete_task, active_sites

def test_backwards_migration_and_snapshot(tmp_path):
    original=[{'title':'Economics','due':'2026-10-25 19:00','homework':True,'blocked_sites':['youtube.com'],'repeat':'Weekly'}]
    (tmp_path/'tasks.json').write_text(json.dumps(original))
    db=TaskStore(tmp_path)
    assert db.tasks[0]['title']=='Economics'
    assert db.tasks[0]['subtasks']==[]
    assert (tmp_path/'pre_v5_backup'/'tasks.json').exists()
    assert json.loads((tmp_path/'pre_v5_backup'/'tasks.json').read_text())==original

def test_repeat_weekdays_and_month_rollover():
    assert next_occurrence(datetime(2026,10,23,18,0),'Weekdays')==datetime(2026,10,26,18,0)
    assert next_occurrence(datetime(2026,1,31,8,0),'Monthly')==datetime(2026,2,28,8,0)
    assert next_occurrence(datetime(2024,2,29,8,0),'Yearly')==datetime(2025,2,28,8,0)
    assert next_occurrence(datetime(2026,1,4,10,0),'Every 2 Weeks')==datetime(2026,1,18,10,0)

def test_recurring_completion_resets_subtasks():
    t=make_task('Daily','2026-10-01 12:00','Daily',subtasks='One\nTwo')
    t['subtasks'][0]['done']=True
    a=[t]
    complete_task(a,t,datetime(2026,10,25,12,0))
    assert a[1]['subtasks'][0]['done']
    assert not a[0]['subtasks'][0]['done']

def test_pause_blocking():
    t=make_task('Homework','2026-10-25 12:00',homework=True,blocked_sites=['youtube.com'])
    now=datetime(2026,10,25,20)
    assert active_sites([t],now)==['youtube.com']
    t['blocked_paused']=True
    assert active_sites([t],now)==[]

def test_backup_restore(tmp_path):
    db=TaskStore(tmp_path)
    db.tasks.append(make_task('Study','2026-10-25 12:00',subtasks='Chapter 1\nChapter 2'))
    db.save()
    f=tmp_path/'export.zip'
    db.backup(f)
    with zipfile.ZipFile(f) as z:assert 'tasks.json' in z.namelist()
    db.tasks=[];db.save();db.restore(f)
    assert db.tasks[0]['title']=='Study'
    assert (tmp_path/'before_restore.zip').is_file()

def test_reject_malformed_restore(tmp_path):
    db=TaskStore(tmp_path)
    f=tmp_path/'bad.zip'
    with zipfile.ZipFile(f,'w') as z:
        z.writestr('tasks.json','{"not":"a list"}')
        z.writestr('settings.json','{}')
    try:db.restore(f)
    except ValueError:pass
    else:raise AssertionError('Malformed backup must be rejected')
