"""Developer smoke test: run via xvfb-run -a python tests/gui_smoke.py."""
import sys,os,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
os.environ['APPDATA']=tempfile.mkdtemp(prefix='tasklock-v5-smoke-')
import tkinter as tk
from tkinter import messagebox
messagebox.showinfo=lambda *a,**k:None
messagebox.showerror=lambda *a,**k:print('ERROR-DIALOG',a)
messagebox.askyesno=lambda *a,**k:True
from TaskLock import TaskLockApp
r=tk.Tk();a=TaskLockApp(r)
a.settings['first_run_complete']=True
for page in ['Dashboard','Tasks','Calendar','Focus','Sounds','Updates','Settings']:
    a.show_page(page)
    r.update_idletasks();r.update()
    print('SHOW_PAGE',page)
a.show_page('Tasks',new=True);r.update()
a.form_title.set('TaskLock v5 Smoke Test')
a.form_due = None
a.subtask_widget.insert('1.0','Test one\nTest two')
a.save_form()
assert len(a.tasks)==1
for mode in ['Day','Week','Month']:
    a.calendar_mode=mode;a.show_page('Calendar');r.update();print('CAL_MODE',mode)
a.show_page('Settings');r.update();a.theme_var.set('Bluecore');a.apply_preferences();r.update();print('THEME_APPLIED')
a.show_page('Sounds');r.update()
a.show_page('Focus');r.update();a.start_focus_timer();assert a.focus_end is not None
a.end_focus_timer();assert a.focus_end is None
# Test that the real localhost bridge agrees with Focus Mode and a safe pause.
import urllib.request,json
t=a.tasks[0];t['homework']=True;t['blocked_sites']=['youtube.com']
a.resume_focus(t)
with urllib.request.urlopen('http://127.0.0.1:18763/status',timeout=4) as resp:
    assert json.load(resp)['sites']==['youtube.com']
a.end_focus(t)
with urllib.request.urlopen('http://127.0.0.1:18763/status',timeout=4) as resp:
    assert json.load(resp)['sites']==[]
print('LOCAL_BRIDGE_FOCUS_PAUSE_OK')
a.show_page('Tasks');r.update()
a.show_page('Dashboard');r.update()
# Test emergency reminder dismissal without disturbing other apps.
a.show_reminder(a.tasks[0]);r.update();assert a.overlay is not None
a.emergency_exit();r.update();assert a.overlay is None
assert a.tasks[0]['snooze_until'] is not None
print('FULLSCREEN_EMERGENCY_EXIT_OK')
try:
 from PIL import ImageGrab
 ImageGrab.grab(bbox=(0,0,1200,800)).save(str(Path(__file__).resolve().parents[1]/'assets'/'v5-dashboard-preview.png'))
 print('SCREENSHOT_OK')
except Exception as e: print('SCREENSHOT_ERROR',repr(e))
a.close_app()
print('SMOKE_COMPLETE')
