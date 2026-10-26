"""TaskLock v5 BLUECORE — offline-first Windows task dashboard and homework focus tool.

Python 3.10+, no runtime dependencies beyond standard-library Tk/Tcl.
"""
from __future__ import annotations
import calendar
import hashlib
import json
import os
import re
import shutil
import sys
import threading
import webbrowser
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
import wave
import zipfile
from array import array
from urllib.request import Request, urlopen
from urllib.error import URLError
import tkinter as tk

try:
    import winsound
except ImportError:
    winsound = None

from tasklock_core import (VERSION, FMT, DEFAULT_SITES, REPEATS, CATEGORIES, PRIORITIES,
                           TaskStore, make_task, validate_due, normalize_sites, next_occurrence,
                           complete_task, is_due, is_homework_blocking, active_sites)
from tasklock_audio import TONES, ensure_tones
from tasklock_updates import ReleaseLookupError, latest_published_release

BG = '#070D1C'
PANEL = '#101D36'
PANEL2 = '#162948'
LINE = '#263C63'
BLUE = '#409BFF'
BLUE_DARK = '#165EC2'
CYAN = '#69D1FF'
WHITE = '#F2F7FF'
MUTED = '#93A9C7'
GREEN = '#55D5A4'
ORANGE = '#F9B65C'
RED = '#FF7487'
FONT = 'Segoe UI'
_TEXT_SCALE = 1.0
PALETTES = {
 'Bluecore': ('#070D1C','#101D36','#162948','#263C63','#409BFF','#165EC2','#69D1FF'),
 'Cyber Violet': ('#0D0B1C','#1A1737','#2B2252','#45336A','#9974FF','#6541BA','#C2A6FF'),
 'Midnight': ('#090E17','#151D2C','#202C3E','#33435A','#668DC8','#365C91','#A2BBE4'),
 'Frost': ('#0A1620','#132B3C','#1B3C50','#33576A','#38ACDE','#23739B','#9BEAFF'),
 'Inferno Red': ('#1B090D','#321018','#471D26','#773039','#F34D55','#B92D3E','#FFB087'),
 'Phantom Violet': ('#10091D','#201033','#321C4A','#583479','#AC72FF','#7445C7','#D5B4FF'),
 'Emerald Pulse': ('#071B17','#102F28','#1A4338','#2C6B55','#34D6A1','#16865F','#A2F8D1'),
 'Solar Flare': ('#211408','#372412','#4B331C','#77532A','#F6B74C','#C17A25','#FFE2A0'),
 'Arctic Frost': ('#071820','#122B39','#1B3E4D','#336574','#57D5F2','#2C92BA','#B9F2FF'),
}

SIDEBAR = '#0C172A'

def apply_palette(name):
    global BG,PANEL,PANEL2,LINE,BLUE,BLUE_DARK,CYAN,SIDEBAR
    BG,PANEL,PANEL2,LINE,BLUE,BLUE_DARK,CYAN = PALETTES.get(name,PALETTES['Bluecore'])
    SIDEBAR = '#0C172A' if name == 'Bluecore' else PANEL


def bundled(relative: str) -> Path:
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
    return base / relative


def card(parent, bg=PANEL, padx=18, pady=16):
    return tk.Frame(parent, bg=bg, padx=padx, pady=pady, highlightbackground=LINE,
                    highlightthickness=1)


def label(parent, text, size=11, bold=False, color=WHITE, bg=None, **kwargs):
    return tk.Label(parent, text=text, bg=bg or parent.cget('bg'), fg=color,
                    font=(FONT, max(8,int(size*_TEXT_SCALE)), 'bold' if bold else 'normal'), **kwargs)


def btn(parent, text, command, primary=False, small=False, fg=None, bg=None, width=None):
    color = bg or (BLUE_DARK if primary else PANEL2)
    return tk.Button(parent, text=text, command=command, bg=color, fg=fg or WHITE,
                     activebackground=BLUE, activeforeground='white',
                     font=(FONT, max(8,int((10 if small else 11)*_TEXT_SCALE)), 'bold'), relief='flat', bd=0,
                     padx=12 if small else 18, pady=7 if small else 10, cursor='hand2',
                     width=width, highlightthickness=0)


def entry(parent, var, width=32):
    return tk.Entry(parent, textvariable=var, bg=BG, fg=WHITE, insertbackground=WHITE,
                    relief='flat', highlightbackground=LINE, highlightcolor=BLUE,
                    highlightthickness=1, font=(FONT, 11), width=width, bd=7)


def combo(parent, variable, values, width=18):
    return ttk.Combobox(parent, textvariable=variable, values=values,
                        state='readonly', font=(FONT, 10), width=width)


def multiline(parent, width=30, height=3):
    return tk.Text(parent, width=width, height=height, bg=BG, fg=WHITE,
                   font=(FONT, 10), insertbackground=WHITE, relief='flat',
                   highlightthickness=1, highlightbackground=LINE, wrap='word')


class Scrolled(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.canvas = tk.Canvas(self, bg=BG, borderwidth=0, highlightthickness=0)
        self.bar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.bar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.body = tk.Frame(self.canvas, bg=BG)
        self.win = self.canvas.create_window((0, 0), window=self.body, anchor='nw')
        self.body.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.win, width=e.width))
        self.canvas.bind('<Enter>', lambda e: self.canvas.bind_all('<MouseWheel>', self._wheel))
        self.canvas.bind('<Leave>', lambda e: self.canvas.unbind_all('<MouseWheel>'))

    def _wheel(self, e):
        self.canvas.yview_scroll(int(-e.delta / 120), 'units')


class TaskLockApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f'TaskLock v{VERSION}')
        self.root.geometry('1200x800')
        self.root.minsize(1000, 650)
        self.root.configure(bg=BG)
        self.store = TaskStore()
        apply_palette(self.store.settings.get('theme','Bluecore'))
        self.root.configure(bg=BG)
        global _TEXT_SCALE
        _TEXT_SCALE = {'Compact': .9, 'Normal': 1., 'Large': 1.2}.get(self.store.settings.get('text_scale','Normal'),1.)
        self.tasks = self.store.tasks
        self.settings = self.store.settings
        self.folder = self.store.folder
        self.tone_folder = self.folder / 'ringtones'
        ensure_tones(self.tone_folder)
        self.ringtone = tk.StringVar(value=self.settings.get('ringtone', 'Digital Pulse'))
        if self.ringtone.get() not in TONES:
            self.ringtone.set('Digital Pulse')
        self.custom_tone = self.settings.get('custom_path', '')
        self.playing = False
        self.page = 'Dashboard'
        self.calendar_mode = 'Month'
        self.focus_end = None
        self.focus_job = None
        self.month = date.today().replace(day=1)
        self.selected_day = date.today()
        self.overlay = None
        self.active = None
        self.tick_job = None
        self.ignored_until = {}
        self.nav_buttons = {}
        self.icon_image = None
        self.configure_styles()
        self.build_shell()
        self.show_page('Dashboard')
        self.start_bridge()
        self.tick()
        self.root.protocol('WM_DELETE_WINDOW', self.close_app)
        if not self.settings.get('first_run_complete'):
            self.root.after(450, self.first_run)

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox', fieldbackground=PANEL2, background=PANEL2,
                        foreground='#182439', padding=5)
        style.configure('Vertical.TScrollbar', troughcolor=BG, background=PANEL2)
        style.map('TCombobox', fieldbackground=[('readonly', '#DEEAFF')],
                  foreground=[('readonly', '#14243E')])
        icon_path = bundled('assets/tasklock.png')
        if icon_path.exists():
            try:
                self.icon_image = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, self.icon_image)
            except tk.TclError:
                pass

    def build_shell(self):
        self.sidebar = tk.Frame(self.root, bg=SIDEBAR, width=216)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        logo = tk.Frame(self.sidebar, bg=SIDEBAR)
        logo.pack(fill='x', padx=22, pady=(28, 37))
        if self.icon_image:
            image = self.icon_image.subsample(24, 24)
            self.sidebar_image = image
            tk.Label(logo, image=image, bg=SIDEBAR).pack(side='left', padx=(0, 8))
        else:
            label(logo, '◈', 27, color=CYAN, bg=SIDEBAR).pack(side='left', padx=(0, 8))
        label(logo, 'TaskLock', 19, True, bg=SIDEBAR).pack(side='left')
        label(self.sidebar, 'B L U E C O R E   /   V 5', 9, True, CYAN, bg=SIDEBAR).pack(anchor='w',padx=25,pady=(0,15))
        label(self.sidebar, 'WORKSPACE', 9, True, MUTED, bg=SIDEBAR).pack(anchor='w', padx=26, pady=(0, 10))
        for icon, page in [('◈', 'Dashboard'), ('✓', 'Tasks'), ('▦', 'Calendar'),
                           ('◉', 'Focus'), ('♫', 'Sounds'), ('↻', 'Updates'), ('⚙', 'Settings')]:
            b = tk.Button(self.sidebar, text=f'  {icon}   {page}', anchor='w', relief='flat', bd=0,
                          font=(FONT, 11, 'bold'), bg=SIDEBAR, fg=MUTED,
                          activebackground=PANEL2, activeforeground=WHITE,
                          padx=20, pady=13, cursor='hand2', highlightthickness=0,
                          command=lambda p=page: self.show_page(p))
            b.pack(fill='x', padx=9, pady=2)
            self.nav_buttons[page] = b
        tk.Frame(self.sidebar, bg=SIDEBAR).pack(fill='both', expand=True)
        label(self.sidebar, 'BY TAVLOKYN STUDIOS', 9, True, CYAN, bg=SIDEBAR).pack(padx=14,pady=(0,6))
        label(self.sidebar, 'FOCUS BETTER. FINISH MORE.', 8, True, MUTED, bg=SIDEBAR).pack(padx=14, pady=(0, 6))
        label(self.sidebar, 'v' + VERSION + '  •  Always free', 9, color=CYAN, bg=SIDEBAR).pack(pady=(0, 22))
        self.workspace = tk.Frame(self.root, bg=BG)
        self.workspace.pack(side='left', fill='both', expand=True)
        head = tk.Frame(self.workspace, bg=BG)
        head.pack(fill='x', padx=30, pady=(26, 18))
        self.page_title = label(head, '', 25, True)
        self.page_title.pack(side='left')
        btn(head, '+ New Task', lambda: self.show_page('Tasks', new=True), primary=True).pack(side='right')
        self.page_sub = label(self.workspace, '', 11, color=MUTED)
        self.page_sub.pack(anchor='w', padx=32, pady=(0, 15))
        self.content = tk.Frame(self.workspace, bg=BG)
        self.content.pack(fill='both', expand=True, padx=30, pady=(0, 20))

    def show_page(self, page, **kwargs):
        self.page = page
        for name, b in self.nav_buttons.items():
            b.configure(bg=BLUE_DARK if name == page else SIDEBAR,
                        fg=WHITE if name == page else MUTED)
        descriptions = {
            'Dashboard': 'Your command center for focus, tasks and progress.',
            'Tasks': 'Add, edit, finish and organize your reminders.',
            'Calendar': 'Your schedule, at a glance.',
            'Focus': 'Homework mode keeps distracting sites out of the way.',
            'Sounds': 'Preview alerts and choose sounds for each category.',
            'Updates': 'See what changed and check for new releases.',
            'Settings': 'Themes, accessibility, backups and app safety.',
        }
        self.page_title.configure(text=page if page != 'Dashboard' else 'Your BLUECORE Dashboard')
        self.page_sub.configure(text=descriptions[page])
        for child in self.content.winfo_children():
            child.destroy()
        {
            'Dashboard': self.dashboard, 'Tasks': lambda: self.task_page(kwargs.get('new', False)),
            'Calendar': self.calendar_page, 'Focus': self.focus_page,
            'Sounds': self.sound_page, 'Updates': self.updates_page,
            'Settings': self.settings_page,
        }[page]()

    def open_tasks(self, **kwargs):
        self.show_page('Tasks', **kwargs)

    def _metric(self, parent, title, value, footnote, color=BLUE):
        box = card(parent)
        box.pack(side='left', fill='both', expand=True, padx=(0, 12))
        label(box, title.upper(), 10, True, MUTED).pack(anchor='w')
        label(box, str(value), 29, True, color).pack(anchor='w', pady=(8, 2))
        label(box, footnote, 9, color=MUTED).pack(anchor='w')

    def dashboard(self):
        scroll = Scrolled(self.content)
        scroll.pack(fill='both', expand=True)
        body = scroll.body
        today = date.today().isoformat()
        open_tasks = [t for t in self.tasks if t.get('state') != 'done']
        done = [t for t in self.tasks if t.get('state') == 'done']
        stats = tk.Frame(body, bg=BG)
        stats.pack(fill='x', pady=(0, 20))
        self._metric(stats, 'To do', len(open_tasks), 'Tasks still on your list')
        self._metric(stats, 'Due today', len([t for t in open_tasks if t['due'][:10] == today]), 'Make progress today', CYAN)
        self._metric(stats, 'Completed', len(done), 'Every finished task counts', GREEN)
        hero = card(body, bg='#122B58', padx=26, pady=22)
        hero.pack(fill='x', pady=(0, 22))
        label(hero, '◈  BLUECORE / TASK CONTROL', 10, True, CYAN, '#122B58').pack(anchor='w')
        label(hero, 'Own your day. Lock in your focus.', 20, True, bg='#122B58').pack(anchor='w', pady=(9, 5))
        label(hero, 'Start a homework task to block the sites you choose, while keeping school sites available.',
              10, color='#C7DAFB', bg='#122B58', wraplength=720, justify='left').pack(anchor='w', pady=(0, 14))
        btn(hero, '◉  Open Focus Mode  →', lambda: self.show_page('Focus'), primary=True).pack(anchor='w')
        total_today = len([t for t in self.tasks if t['due'][:10] == today]); finished_today = len([t for t in self.tasks if t['due'][:10] == today and t.get('state') == 'done'])
        p = card(body, padx=20, pady=15); p.pack(fill='x',pady=(0,18))
        label(p, f"TODAY'S PROGRESS  •  {finished_today}/{total_today} completed",12,True,CYAN).pack(anchor='w')
        bar=tk.Canvas(p,height=12,bg=PANEL,highlightthickness=0);bar.pack(fill='x',pady=(10,3))
        bar.bind('<Configure>',lambda e: (bar.delete('all'),bar.create_rectangle(0,0,e.width,12,fill=PANEL2,outline=''),bar.create_rectangle(0,0,int(e.width*finished_today/max(1,total_today)),12,fill=BLUE,outline=''))) 
        header = tk.Frame(body, bg=BG)
        header.pack(fill='x', pady=(0, 8))
        label(header, 'Up next', 17, True).pack(side='left')
        btn(header, 'View all', lambda: self.show_page('Tasks'), small=True).pack(side='right')
        upcoming = sorted(open_tasks, key=lambda x: x['due'])[:6]
        if not upcoming:
            self.empty(body, 'You are all caught up! Add a new task whenever you are ready.')
        for t in upcoming:
            self.task_row(body, t, compact=True)

    def empty(self, parent, text):
        box = card(parent, padx=24, pady=26)
        box.pack(fill='x', pady=8)
        label(box, '✧  ' + text, 12, color=MUTED, wraplength=680, justify='left').pack(anchor='w')

    def task_row(self, parent, t, compact=False):
        box = card(parent, padx=17, pady=11)
        box.pack(fill='x', pady=5)
        col = tk.Frame(box, bg=PANEL)
        col.pack(side='left', fill='both', expand=True)
        status = 'DONE' if t.get('state') == 'done' else ('DUE' if is_due(t) else 'UPCOMING')
        badge_color = GREEN if status == 'DONE' else ORANGE if status == 'DUE' else CYAN
        label(col, t['title'], 12, True).pack(anchor='w')
        label(col, f"{t['due']}   •   {t.get('category', 'Personal')}   •   {t.get('priority', 'Normal')} priority   •   {status}",
              9, color=badge_color).pack(anchor='w', pady=(5, 0))
        if not compact and t.get('subtasks'):
            subs=t['subtasks']; completed=sum(x['done'] for x in subs)
            label(col,f'↳ {completed}/{len(subs)} subtasks complete',9,color=CYAN).pack(anchor='w',pady=(5,1))
            for i,sub in enumerate(subs[:8]):
                tk.Checkbutton(col,text=sub['title'],variable=tk.BooleanVar(value=sub['done']),
                    command=lambda task=t,index=i:self.toggle_subtask(task,index),bg=PANEL,fg=WHITE,
                    selectcolor=PANEL2,activebackground=PANEL,activeforeground=CYAN,anchor='w',
                    font=(FONT,9)).pack(anchor='w')
        if not compact and t.get('notes'):
            label(col, t['notes'][:140], 9, color=MUTED, wraplength=490, justify='left').pack(anchor='w', pady=(5, 0))
        if not compact:
            if t.get('state') != 'done':
                btn(box, 'Done', lambda task=t: self.done(task), small=True, primary=True).pack(side='right', padx=(7, 0))
                btn(box, 'Edit', lambda task=t: self.edit(task), small=True).pack(side='right', padx=(7, 0))
                if t.get('homework'):
                    btn(box, 'Focus', lambda task=t: self.begin_focus(task), small=True).pack(side='right', padx=(7, 0))
            btn(box, 'Delete', lambda task=t: self.delete(task), small=True, fg=RED).pack(side='right', padx=(7, 0))

    def task_page(self, new=False):
        sc = Scrolled(self.content)
        sc.pack(fill='both', expand=True)
        body = sc.body
        if not new:
            tip = card(body, bg='#122B58', padx=19, pady=17)
            tip.pack(fill='x', pady=(0, 17))
            label(tip, 'Make a plan. Then check it off.', 17, True, bg='#122B58').pack(anchor='w')
            label(tip, 'Filter your tasks below, or use + New Task to add an assignment, chore or reminder.',
                  10, color='#C7DAFB', bg='#122B58').pack(anchor='w', pady=(7, 0))
        else:
            self.form_frame = card(body, padx=18, pady=14)
            self.form_frame.pack(fill='x', pady=(0, 17))
            self.form_editing = None
            self.form_title = tk.StringVar()
            self.form_date = tk.StringVar(value=self.selected_day.isoformat())
            self.form_time = tk.StringVar(value='18:00')
            self.form_repeat = tk.StringVar(value='Never')
            self.form_category = tk.StringVar(value='School')
            self.form_priority = tk.StringVar(value='Normal')
            self.form_homework = tk.BooleanVar(value=False)
            self.form_sites = tk.StringVar(value=DEFAULT_SITES)
            self.form_link = tk.StringVar()
            label(self.form_frame, 'Create a task', 16, True).grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 12))
            self.field(self.form_frame, 'Task title', entry(self.form_frame, self.form_title, 45), 1, 0, span=2)
            self.field(self.form_frame, 'Date (YYYY-MM-DD)', entry(self.form_frame, self.form_date, 19), 2, 0)
            self.field(self.form_frame, 'Time (24-hour)', entry(self.form_frame, self.form_time, 19), 2, 1)
            self.field(self.form_frame, 'Category', combo(self.form_frame, self.form_category, CATEGORIES), 3, 0)
            self.field(self.form_frame, 'Priority', combo(self.form_frame, self.form_priority, PRIORITIES), 3, 1)
            self.field(self.form_frame, 'Repeat', combo(self.form_frame, self.form_repeat, REPEATS), 4, 0)
            tk.Checkbutton(self.form_frame, text='Online homework — block selected sites when due',
                           variable=self.form_homework, bg=PANEL, fg=WHITE, selectcolor=PANEL2,
                           activebackground=PANEL, activeforeground=WHITE, font=(FONT, 10)).grid(row=15, column=0, columnspan=2, sticky='w', pady=8)
            self.field(self.form_frame, 'Distracting sites (separate with commas)',
                       entry(self.form_frame, self.form_sites, 46), 5, 0, span=2)
            self.field(self.form_frame, 'Assignment link (optional)',
                       entry(self.form_frame, self.form_link, 46), 6, 0, span=2)
            self.subtask_widget = multiline(self.form_frame,54,3)
            self.field(self.form_frame,'Subtasks (one per line)',self.subtask_widget,7,0,span=2)
            self.note_widget = multiline(self.form_frame, 54, 2)
            self.field(self.form_frame, 'Notes (optional)', self.note_widget, 8, 0, span=2)
            actions = tk.Frame(self.form_frame, bg=PANEL)
            actions.grid(row=16, column=0, columnspan=4, sticky='w', pady=(14, 2))
            self.save_btn = btn(actions, 'Add task', self.save_form, primary=True)
            self.save_btn.pack(side='left', padx=(0, 8))
            btn(actions, 'Clear form', self.clear_form).pack(side='left')
            self.form_frame.grid_columnconfigure(0, weight=1)
            self.form_frame.grid_columnconfigure(1, weight=1)
        bar = tk.Frame(body, bg=BG)
        bar.pack(fill='x', pady=(2, 9))
        label(bar, 'Your tasks', 17, True).pack(side='left')
        self.filter = tk.StringVar(value='Open')
        self.search = tk.StringVar()
        chooser = combo(bar, self.filter, ('Open', 'Today', 'Homework', 'Completed', 'All'), 13)
        chooser.pack(side='right', padx=(8, 0))
        chooser.bind('<<ComboboxSelected>>', lambda e: self.render_task_list())
        ent = entry(bar, self.search, 23)
        ent.pack(side='right')
        ent.insert(0, '')
        self.search.trace_add('write', lambda *_: self.render_task_list())
        self.task_list_container = tk.Frame(body, bg=BG)
        self.task_list_container.pack(fill='x')
        self.render_task_list()

    def field(self, parent, caption, widget, row, col, span=1):
        label(parent, caption, 9, True, MUTED).grid(row=row * 2 - 1, column=col,
              columnspan=span, sticky='w', padx=(0, 15), pady=(5, 4))
        widget.grid(row=row * 2, column=col, columnspan=span, sticky='ew',
                    padx=(0, 15), pady=(0, 7))

    def render_task_list(self):
        if not hasattr(self, 'task_list_container') or not self.task_list_container.winfo_exists():
            return
        for c in self.task_list_container.winfo_children():
            c.destroy()
        status = self.filter.get()
        items = sorted(self.tasks, key=lambda t: t['due'])
        if status == 'Open':
            items = [t for t in items if t.get('state') != 'done']
        elif status == 'Today':
            items = [t for t in items if t.get('state') != 'done' and t['due'].startswith(date.today().isoformat())]
        elif status == 'Homework':
            items = [t for t in items if t.get('state') != 'done' and t.get('homework')]
        elif status == 'Completed':
            items = [t for t in items if t.get('state') == 'done']
        search = self.search.get().strip().lower()
        if search:
            items = [t for t in items if search in (t['title'] + ' ' + t.get('notes', '')).lower()]
        if not items:
            self.empty(self.task_list_container, 'No matching tasks. You can add one above.')
        for t in items:
            self.task_row(self.task_list_container, t)

    def edit(self, t):
        self.show_page('Tasks', new=True)
        self.form_editing = t['id']
        self.form_title.set(t['title'])
        self.form_date.set(t['due'][:10])
        self.form_time.set(t['due'][11:])
        self.form_repeat.set(t.get('repeat', 'Never'))
        self.form_category.set(t.get('category', 'School'))
        self.form_priority.set(t.get('priority', 'Normal'))
        self.form_homework.set(t.get('homework', False))
        self.form_sites.set(', '.join(t.get('blocked_sites', [])))
        self.form_link.set(t.get('link', ''))
        self.note_widget.insert('1.0', t.get('notes', ''))
        self.subtask_widget.insert('1.0', '\n'.join(s['title'] for s in t.get('subtasks',[])))
        self.save_btn.configure(text='Save changes')

    def clear_form(self):
        self.form_editing = None
        self.form_title.set('')
        self.form_date.set(date.today().isoformat())
        self.form_time.set('18:00')
        self.form_repeat.set('Never')
        self.form_category.set('School')
        self.form_priority.set('Normal')
        self.form_homework.set(False)
        self.form_sites.set(DEFAULT_SITES)
        self.form_link.set('')
        self.note_widget.delete('1.0', 'end')
        self.subtask_widget.delete('1.0','end')
        self.save_btn.configure(text='Add task')

    def save_form(self):
        try:
            due = validate_due(self.form_date.get(), self.form_time.get())
            sites = normalize_sites(self.form_sites.get()) if self.form_homework.get() else []
            if self.form_homework.get() and not sites:
                raise ValueError('Add at least one valid domain to block, like youtube.com.')
            link = self.form_link.get().strip()
            if link and not link.lower().startswith(('https://', 'http://')):
                raise ValueError('Assignment links must start with https:// or http://.')
            item = make_task(self.form_title.get(), due, self.form_repeat.get(),
                             self.form_category.get(), self.form_priority.get(),
                             self.note_widget.get('1.0', 'end'), self.form_homework.get(), sites, link,
                             self.subtask_widget.get('1.0','end'))
        except ValueError as e:
            messagebox.showerror('Check task details', str(e), parent=self.root)
            return
        if self.form_editing:
            old = self.get_task(self.form_editing)
            if old:
                item['id'] = old['id']
                old_done={s['title']:s['done'] for s in old.get('subtasks',[])}
                for sub in item['subtasks']:
                    sub['done']=old_done.get(sub['title'],False)
                item['focus_started'] = old.get('focus_started', False) if item['homework'] else False
                item['blocked_paused'] = old.get('blocked_paused',False) if item['homework'] else False
                self.tasks[self.tasks.index(old)] = item
        else:
            self.tasks.append(item)
        self.store.save()
        self.clear_form()
        self.show_page('Tasks')

    def toggle_subtask(self,t,index):
        if 0<=index<len(t.get('subtasks',[])):
            t['subtasks'][index]['done']=not t['subtasks'][index]['done']
            self.store.save()
            self.show_page(self.page)

    def get_task(self, identifier):
        return next((t for t in self.tasks if t['id'] == identifier), None)

    def done(self, t):
        complete_task(self.tasks, t)
        self.store.save()
        if self.active and self.active['id'] == t['id']:
            self.close_overlay()
        self.show_page(self.page)

    def delete(self, t):
        if messagebox.askyesno('Delete task', f"Delete '{t['title']}'?", parent=self.root):
            self.tasks.remove(t)
            self.store.save()
            if self.active and self.active['id'] == t['id']:
                self.close_overlay()
            self.show_page(self.page)

    def begin_focus(self, t):
        t['focus_started'] = True
        self.store.save()
        if self.overlay:
            self.close_overlay()
        self.show_page('Focus')

    def end_focus(self, t):
        if messagebox.askyesno('Pause site blocking',
                'Stop blocking sites for this task? The homework will remain unfinished.', parent=self.root):
            t['focus_started'] = False
            # If the deadline has passed, the task would still block. Offer a safe pause.
            if datetime.strptime(t['due'], FMT) <= datetime.now():
                t['blocked_paused'] = True
            self.store.save()
            self.show_page('Focus')

    def calendar_page(self):
        switch = tk.Frame(self.content,bg=BG);switch.pack(fill='x',pady=(0,12))
        label(switch,'VIEW  ',10,True,MUTED).pack(side='left')
        for mode in ('Month','Week','Day'):
            btn(switch,mode,lambda m=mode:self.switch_calendar(m),small=True,
                bg=BLUE_DARK if mode==self.calendar_mode else PANEL2).pack(side='left',padx=3)
        if self.calendar_mode!='Month':
            self.agenda_view()
            return
        left = card(self.content, padx=15, pady=20)
        left.pack(side='left', fill='both', expand=True, padx=(0, 18))
        nav = tk.Frame(left, bg=PANEL)
        nav.pack(fill='x', pady=(0, 22))
        btn(nav, '◀', lambda: self.change_month(-1), small=True).pack(side='left')
        self.month_label = label(nav, self.month.strftime('%B %Y'), 17, True)
        self.month_label.pack(side='left', expand=True)
        btn(nav, '▶', lambda: self.change_month(1), small=True).pack(side='right')
        weekdays = tk.Frame(left, bg=PANEL)
        weekdays.pack(fill='x')
        for i, name in enumerate(('Mon','Tue','Wed','Thu','Fri','Sat','Sun')):
            weekdays.grid_columnconfigure(i, weight=1, uniform='days')
            label(weekdays, name, 10, True, MUTED).grid(row=0, column=i, pady=(0, 12))
        self.cal_grid = tk.Frame(left, bg=PANEL)
        self.cal_grid.pack(fill='both', expand=True)
        for i in range(7):
            self.cal_grid.grid_columnconfigure(i, weight=1, uniform='days')
        self.draw_calendar()
        right = card(self.content, padx=15, pady=18)
        right.pack(side='left', fill='both', expand=True)
        self.day_title = label(right, '', 15, True)
        self.day_title.pack(anchor='w', pady=(0, 14))
        self.day_list = tk.Frame(right, bg=PANEL)
        self.day_list.pack(fill='both', expand=True)
        btn(right, '+ Add task on this day', lambda: self.show_page('Tasks', new=True), primary=True).pack(anchor='w', pady=10)
        self.draw_day()

    def switch_calendar(self,mode):
        self.calendar_mode=mode
        self.show_page('Calendar')

    def agenda_view(self):
        bar=card(self.content);bar.pack(fill='x',pady=(0,12))
        btn(bar,'◀ Previous',lambda:self.shift_day(-7 if self.calendar_mode=='Week' else -1),small=True).pack(side='left')
        label(bar,self.selected_day.strftime('%A, %B %d, %Y'),15,True).pack(side='left',expand=True)
        btn(bar,'Next ▶',lambda:self.shift_day(7 if self.calendar_mode=='Week' else 1),small=True).pack(side='right')
        sc=Scrolled(self.content);sc.pack(fill='both',expand=True)
        start=self.selected_day
        if self.calendar_mode=='Week':start=start-timedelta(days=start.weekday())
        days=[start+timedelta(days=i) for i in range(7 if self.calendar_mode=='Week' else 1)]
        for day in days:
            title=label(sc.body,day.strftime('%A, %b %d'),14,True,CYAN);title.pack(anchor='w',pady=(11,5))
            current=[t for t in sorted(self.tasks,key=lambda x:x['due']) if t['due'][:10]==day.isoformat()]
            if not current:
                label(sc.body,'No tasks scheduled',10,color=MUTED).pack(anchor='w',pady=(0,8))
            for t in current:self.task_row(sc.body,t,compact=True)

    def shift_day(self,offset):
        self.selected_day+=timedelta(days=offset)
        self.month=self.selected_day.replace(day=1)
        self.show_page('Calendar')

    def draw_calendar(self):
        for w in self.cal_grid.winfo_children():
            w.destroy()
        self.month_label.configure(text=self.month.strftime('%B %Y'))
        for row, week in enumerate(calendar.monthcalendar(self.month.year, self.month.month)):
            self.cal_grid.grid_rowconfigure(row, weight=1)
            for col, day in enumerate(week):
                d = date(self.month.year, self.month.month, day) if day else None
                count = sum(t.get('state') != 'done' and t['due'][:10] == d.isoformat() for t in self.tasks) if d else 0
                text = f'{day}\n{"• " * min(count, 3)}' if day else ''
                selected = d == self.selected_day
                tk.Button(self.cal_grid, text=text, bg=BLUE_DARK if selected else PANEL2 if d == date.today() else PANEL,
                          fg=WHITE if d else PANEL, font=(FONT, 10, 'bold'), relief='flat',
                          activebackground=BLUE, activeforeground=WHITE, width=5, height=3,
                          state='normal' if d else 'disabled', cursor='hand2' if d else 'arrow',
                          command=lambda dt=d: self.choose_day(dt)).grid(row=row, column=col, sticky='nsew', padx=2, pady=2)

    def change_month(self, n):
        m = self.month.month + n
        y = self.month.year + (m - 1) // 12
        self.month = date(y, (m - 1) % 12 + 1, 1)
        self.draw_calendar()

    def choose_day(self, d):
        self.selected_day = d
        self.draw_calendar()
        self.draw_day()

    def draw_day(self):
        self.day_title.configure(text=self.selected_day.strftime('%A, %B %d'))
        for w in self.day_list.winfo_children():
            w.destroy()
        items = sorted((t for t in self.tasks if t['due'][:10] == self.selected_day.isoformat()
                        and t.get('state') != 'done'), key=lambda x: x['due'])
        if not items:
            label(self.day_list, 'Nothing scheduled on this date.', 11, color=MUTED).pack(anchor='w', pady=8)
        for t in items:
            block = card(self.day_list, bg=PANEL2, padx=12, pady=10)
            block.pack(fill='x', pady=5)
            label(block, t['due'][11:] + '  ' + t['title'], 11, True, bg=PANEL2, wraplength=270,
                  justify='left').pack(anchor='w')
            label(block, t.get('category', 'Personal'), 9, color=CYAN, bg=PANEL2).pack(anchor='w', pady=(3, 0))

    def focus_page(self):
        timer=card(self.content,bg='#122B58',padx=20,pady=12);timer.pack(fill='x',pady=(0,12))
        label(timer,'◉  FOCUS SESSION TIMER',13,True,CYAN,'#122B58').pack(side='left',padx=(0,18))
        self.focus_label=label(timer,self.focus_remaining(),14,True,bg='#122B58');self.focus_label.pack(side='left',padx=8)
        btn(timer,'Start timer',self.start_focus_timer,small=True,primary=True).pack(side='left',padx=5)
        btn(timer,'End timer',self.end_focus_timer,small=True).pack(side='left',padx=5)
        banner = card(self.content, bg='#112B55', padx=23, pady=20)
        banner.pack(fill='x', pady=(0, 17))
        label(banner, '◎  HOMEWORK FOCUS MODE', 20, True, CYAN, '#112B55').pack(anchor='w')
        label(banner, 'Sites are blocked only while TaskLock is running and the Chrome/Edge extension is enabled. You can pause focus whenever necessary.',
              10, color=WHITE, bg='#112B55', wraplength=760, justify='left').pack(anchor='w', pady=10)
        label(self.content, f'Currently blocked sites: {", ".join(self.current_sites()) or "None"}',
              11, True, ORANGE, wraplength=750, justify='left').pack(anchor='w', pady=(0, 15))
        sc = Scrolled(self.content)
        sc.pack(fill='both', expand=True)
        homework = [t for t in sorted(self.tasks, key=lambda x: x['due'])
                    if t.get('homework') and t.get('state') != 'done']
        if not homework:
            self.empty(sc.body, 'No homework tasks yet. Use Tasks to create your first one.')
        for t in homework:
            box = card(sc.body)
            box.pack(fill='x', pady=6)
            label(box, t['title'], 13, True).pack(anchor='w')
            status = 'ACTIVE — websites blocked' if t.get('blocked_paused') is not True and is_homework_blocking(t) else 'Not currently blocking'
            label(box, f"Due {t['due']}   •   {status}", 10,
                  color=ORANGE if 'ACTIVE' in status else MUTED).pack(anchor='w', pady=(4, 7))
            label(box, ', '.join(t.get('blocked_sites', [])) or 'No sites selected', 9, color=CYAN).pack(anchor='w')
            actions = tk.Frame(box, bg=PANEL)
            actions.pack(anchor='w', pady=(12, 0))
            if t.get('blocked_paused') or not t.get('focus_started'):
                btn(actions, 'Start / resume focus', lambda task=t: self.resume_focus(task), primary=True, small=True).pack(side='left', padx=(0, 8))
            if status.startswith('ACTIVE'):
                btn(actions, 'Pause blocking', lambda task=t: self.end_focus(task), small=True).pack(side='left', padx=(0, 8))
            if t.get('link'):
                btn(actions, 'Open assignment', lambda url=t['link']: webbrowser.open(url), small=True).pack(side='left', padx=(0, 8))
            btn(actions, 'Mark done', lambda task=t: self.done(task), small=True).pack(side='left')

    def focus_remaining(self):
        if not self.focus_end:return f"{int(self.settings.get('focus_minutes',25)):02d}:00 ready"
        secs=max(0,int((self.focus_end-datetime.now()).total_seconds()))
        return f'{secs//60:02d}:{secs%60:02d}'

    def start_focus_timer(self):
        if self.focus_job:
            try:self.root.after_cancel(self.focus_job)
            except tk.TclError:pass
            self.focus_job=None
        minutes=max(1,min(180,int(self.settings.get('focus_minutes',25))))
        self.focus_end=datetime.now()+timedelta(minutes=minutes)
        self.refresh_focus_timer()

    def end_focus_timer(self):
        self.focus_end=None
        if self.focus_job:
            try:self.root.after_cancel(self.focus_job)
            except tk.TclError:pass
            self.focus_job=None
        if self.page=='Focus':self.show_page('Focus')

    def refresh_focus_timer(self):
        if not self.focus_end:return
        if datetime.now()>=self.focus_end:
            self.focus_end=None
            if self.page=='Focus':self.show_page('Focus')
            messagebox.showinfo('Focus session complete','Your focus timer has finished. Nice work!',parent=self.root)
            return
        if self.page=='Focus' and hasattr(self,'focus_label') and self.focus_label.winfo_exists():
            self.focus_label.configure(text=self.focus_remaining())
        self.focus_job=self.root.after(1000,self.refresh_focus_timer)

    def resume_focus(self, t):
        t['focus_started'] = True
        t['blocked_paused'] = False
        self.store.save()
        self.show_page('Focus')

    def sound_page(self):
        scroll=Scrolled(self.content);scroll.pack(fill='both',expand=True)
        body=scroll.body
        box = card(body, padx=27, pady=24)
        box.pack(fill='x')
        label(box, 'Choose your reminder sound', 18, True).pack(anchor='w')
        label(box, 'Twenty original alerts with varied instrument-inspired sounds, custom WAV, or silence.', 11, color=MUTED).pack(anchor='w', pady=(6, 20))
        line = tk.Frame(box, bg=PANEL)
        line.pack(fill='x')
        chooser = combo(line, self.ringtone, TONES, 26)
        chooser.pack(side='left', padx=(0, 12))
        chooser.bind('<<ComboboxSelected>>', lambda e: self.select_ring())
        btn(line, '▶  Preview', lambda: self.play_ring(), primary=True).pack(side='left', padx=(0, 8))
        btn(line, '■  Stop', self.stop_ring).pack(side='left', padx=(0, 8))
        btn(line, 'Import WAV', self.choose_custom).pack(side='left')
        label(box, 'Ringtones play when a full-screen task reminder appears and stop when you dismiss it.',
              10, color=MUTED, wraplength=700, justify='left').pack(anchor='w', pady=(21, 3))
        vol=card(body,padx=20,pady=12);vol.pack(fill='x',pady=(12,4))
        label(vol,'Ringtone volume (generated tones)',11,True).pack(anchor='w')
        self.volume_var=tk.IntVar(value=int(self.settings.get('sound_volume',65)))
        tk.Scale(vol,from_=0,to=100,orient='horizontal',variable=self.volume_var,
            bg=PANEL,fg=WHITE,troughcolor=PANEL2,highlightthickness=0,length=350,
            command=lambda _:self.save_volume()).pack(anchor='w')
        categories=card(body,padx=20,pady=15);categories.pack(fill='x',pady=(10,4))
        label(categories,'Sounds by task category',13,True).pack(anchor='w',pady=(0,7))
        self.category_vars={}
        for c in CATEGORIES:
            line=tk.Frame(categories,bg=PANEL);line.pack(anchor='w',pady=2)
            label(line,c,10,color=MUTED,width=12,anchor='w').pack(side='left')
            v=tk.StringVar(value=self.settings.get('category_sounds',{}).get(c,'Use default'))
            self.category_vars[c]=v
            cb=combo(line,v,('Use default',)+TONES,20);cb.pack(side='left')
            cb.bind('<<ComboboxSelected>>',lambda e,category=c:self.save_category_sound(category))
        tips = card(body, padx=20, pady=17)
        tips.pack(fill='x', pady=20)
        label(tips, 'Sound library', 14, True).pack(anchor='w', pady=(0, 9))
        for title, desc in [
            ('Digital Pulse', 'Bright, futuristic three-tone pattern'),
            ('Soft Chime', 'Soft layered chimes for quieter reminders'),
            ('Urgent Alert', 'Fast attention-getting signals'),
            ('Neon Flight', 'Rising synth-inspired sequence'),
            ('Midnight Bell', 'Lower, slow bell melody'),
            ('Blue Horizon', 'Smooth uplifting notes'),
            ('Arcade Dash', 'Quick retro game-style alert'),
            ('Sunrise', 'Warm, rising reminder melody'),
            ('Cyber Signal','Futuristic bright tones'),('Orbit Rise','Upward synth sequence'),
            ('Deep Focus','Soft low alert'),('Aurora Ping','Clear gentle digital bell'),
            ('Brass Fanfare','Trumpet-inspired bright fanfare'),
            ('Trombone Groove','Low brass groove'),
            ('Drumline Call','Percussive marching pattern'),
            ('Synthwave Lift','Layered synth arpeggio'),
            ('String Serenade','Gentle string-inspired melody'),
            ('Piano Cascade','Flowing piano-inspired notes'),
            ('Marimba Steps','Wooden mallet-inspired rhythm'),
            ('Electric Guitar Hook','Plucked guitar-inspired riff'),
        ]:
            label(tips, title + '   —   ' + desc, 10, color=WHITE).pack(anchor='w', pady=3)

    def updates_page(self):
        sc = Scrolled(self.content)
        sc.pack(fill='both', expand=True)
        banner = card(sc.body, bg='#112B55', padx=24, pady=18)
        banner.pack(fill='x', pady=(0, 18))
        label(banner, f'You are running TaskLock v{VERSION}', 19, True, bg='#112B55').pack(anchor='w')
        label(banner, 'Update history lives here. New releases will be listed on your TaskLock download website.',
              10, color='#C7DAFB', bg='#112B55', wraplength=750, justify='left').pack(anchor='w', pady=8)
        actions = tk.Frame(banner, bg='#112B55')
        actions.pack(anchor='w', pady=(8, 0))
        btn(actions, 'Check for updates', self.check_updates, primary=True).pack(side='left', padx=(0, 9))
        btn(actions, 'Release downloads', self.open_releases).pack(side='left')
        releases = [
            ('v5.1.1','Update Check Reliability', 'Fixed HTTP 404 update checks with a verified official download-feed fallback and clearer error messages.'),
            ('v5.1.0','Color & Sound Edition', 'Five new themed color palettes including Inferno Red, eight new instrument-inspired ringtone melodies, and improved theme styling.'),
            ('v5.0.0','BLUECORE', 'New futuristic lock branding, advanced recurrence and subtasks, v4 backups, focus timer, calendar modes, category-based ringtones, themes, accessibility and Windows setup pipeline.'),
            ('v4.0.0', 'Blue & black redesign', 'New sidebar dashboard, colorful task lists, day-by-day calendar, editable tasks, focus dashboard, 5 additional ringtones, in-app update log and release links.'),
            ('v3.0.0', 'Homework Focus Mode', 'Online homework tasks and companion Chrome/Edge extension to block selected websites until a task is marked done or blocking is paused.'),
            ('v2.0.0', 'Ringtone Edition', 'Three original ringtones, custom WAV support and full-screen alert sounds.'),
            ('v1.0.0', 'The beginning', 'Calendar, saved tasks, repeating reminders, full-screen alerts, Done and Snooze, plus an emergency exit.'),
        ]
        label(sc.body, 'CHANGELOG', 11, True, MUTED).pack(anchor='w', pady=(4, 8))
        for version, title, details in releases:
            box = card(sc.body)
            box.pack(fill='x', pady=5)
            label(box, version + '   •   ' + title, 14, True, CYAN).pack(anchor='w')
            label(box, details, 10, color=MUTED, wraplength=750, justify='left').pack(anchor='w', pady=(7, 0))
        label(sc.body, 'Updates are installed by downloading the newer Windows release. Task data is kept in your local AppData folder.',
              10, color=MUTED, wraplength=800, justify='left').pack(anchor='w', pady=14)

    def settings_page(self):
        scroll=Scrolled(self.content);scroll.pack(fill='both',expand=True)
        body=scroll.body
        personal=card(body,padx=21,pady=15);personal.pack(fill='x',pady=(0,12))
        label(personal,'◈  Personalization & accessibility',15,True).pack(anchor='w',pady=(0,9))
        controls=tk.Frame(personal,bg=PANEL);controls.pack(anchor='w')
        self.theme_var=tk.StringVar(value=self.settings.get('theme','Bluecore'))
        self.scale_var=tk.StringVar(value=self.settings.get('text_scale','Normal'))
        label(controls,'Theme',10,color=MUTED).grid(row=0,column=0,sticky='w',padx=(0,10))
        theme=combo(controls,self.theme_var,tuple(PALETTES),18);theme.grid(row=1,column=0,padx=(0,12))
        label(controls,'Text size',10,color=MUTED).grid(row=0,column=1,sticky='w')
        scale=combo(controls,self.scale_var,('Compact','Normal','Large'),14);scale.grid(row=1,column=1,padx=(0,12))
        btn(controls,'Apply',self.apply_preferences,primary=True,small=True).grid(row=1,column=2)
        self.motion_var=tk.BooleanVar(value=bool(self.settings.get('motion',True)))
        tk.Checkbutton(personal,text='Enable subtle animations / motion',variable=self.motion_var,
            command=self.save_preferences,bg=PANEL,fg=WHITE,selectcolor=PANEL2,activebackground=PANEL,
            activeforeground=WHITE).pack(anchor='w',pady=(10,0))
        durations=tk.Frame(personal,bg=PANEL);durations.pack(anchor='w',pady=(10,0))
        self.focus_minutes_var=tk.StringVar(value=str(self.settings.get('focus_minutes',25)))
        self.snooze_minutes_var=tk.StringVar(value=str(self.settings.get('reminder_snooze',5)))
        label(durations,'Focus timer (min)',10,color=MUTED).grid(row=0,column=0,sticky='w',padx=(0,10))
        tk.Spinbox(durations,from_=1,to=180,width=8,textvariable=self.focus_minutes_var,background=PANEL2,
                   foreground=WHITE,buttonbackground=BLUE_DARK,insertbackground=WHITE).grid(row=1,column=0,padx=(0,20))
        label(durations,'Snooze (min)',10,color=MUTED).grid(row=0,column=1,sticky='w')
        tk.Spinbox(durations,from_=1,to=60,width=8,textvariable=self.snooze_minutes_var,background=PANEL2,
                   foreground=WHITE,buttonbackground=BLUE_DARK,insertbackground=WHITE).grid(row=1,column=1,padx=(0,12))
        btn(durations,'Save timer settings',self.save_durations,small=True).grid(row=1,column=2)
        data_box=card(body,padx=21,pady=15);data_box.pack(fill='x',pady=(0,12))
        label(data_box,'Data backup & restore',15,True).pack(anchor='w',pady=(0,8))
        label(data_box,'Your saved tasks remain local; a pre-v5 snapshot is created automatically on upgrade.',10,color=MUTED).pack(anchor='w')
        actions=tk.Frame(data_box,bg=PANEL);actions.pack(anchor='w',pady=(9,2))
        btn(actions,'Export backup ZIP',self.export_backup,small=True,primary=True).pack(side='left',padx=(0,8))
        btn(actions,'Restore backup ZIP',self.import_backup,small=True).pack(side='left')
        box = card(body, padx=23, pady=20)
        box.pack(fill='x', pady=(0, 16))
        label(box, 'Data folder', 15, True).pack(anchor='w')
        label(box, str(self.folder), 10, color=CYAN, wraplength=750, justify='left').pack(anchor='w', pady=(8, 13))
        btn(box, 'Open data folder', lambda: self.open_folder(self.folder)).pack(anchor='w')
        self.settings_safety_tail(body)

    def settings_safety_tail(self,body):
        browser = card(body, padx=23, pady=20)
        browser.pack(fill='x', pady=(0, 16))
        label(browser, 'Website blocking companion', 16, True).pack(anchor='w')
        label(browser, 'Chrome: chrome://extensions   •   Edge: edge://extensions\nEnable Developer mode → Load unpacked → select the Browser_Extension folder shipped with the release.\nKeep TaskLock open. Blocking is optional and always has a pause option.',
              10, color=MUTED, wraplength=780, justify='left').pack(anchor='w', pady=(8, 13))
        btn(browser, 'Open extension folder', self.open_extension_folder).pack(anchor='w')
        safety = card(body, padx=23, pady=20)
        safety.pack(fill='x')
        label(safety, 'Emergency access', 16, True).pack(anchor='w')
        label(safety, 'Full-screen reminders always allow Esc / Emergency Exit. Focus mode can be paused. TaskLock never changes your Windows login or prevents you from closing the app.',
              10, color=MUTED, wraplength=780, justify='left').pack(anchor='w', pady=(8, 0))

    def export_backup(self):
        dest=filedialog.asksaveasfilename(defaultextension='.zip',initialfile='TaskLock-Backup.zip',
            filetypes=[('TaskLock backup','*.zip')],parent=self.root)
        if not dest:return
        try:self.store.backup(Path(dest));messagebox.showinfo('Backup saved','Your tasks and preferences were backed up.',parent=self.root)
        except (OSError,ValueError) as e:messagebox.showerror('Backup failed',str(e),parent=self.root)

    def import_backup(self):
        src=filedialog.askopenfilename(filetypes=[('TaskLock backup','*.zip')],parent=self.root)
        if not src:return
        if not messagebox.askyesno('Restore backup','Replace your current tasks and preferences with this backup? A copy of your current data will be saved first.',parent=self.root):return
        try:
            self.store.restore(Path(src))
            self.tasks=self.store.tasks;self.settings=self.store.settings
            self.ringtone.set(self.settings.get('ringtone','Digital Pulse'))
            self.custom_tone=self.settings.get('custom_path','')
            self.show_page('Dashboard')
            messagebox.showinfo('Backup restored','Tasks and settings have been restored.',parent=self.root)
        except (OSError,ValueError,KeyError,zipfile.BadZipFile) as e:messagebox.showerror('Restore failed',str(e),parent=self.root)

    def save_preferences(self):
        self.settings['motion']=bool(self.motion_var.get())
        self.store.save_settings()

    def apply_preferences(self):
        self.settings['theme']=self.theme_var.get()
        self.settings['text_scale']=self.scale_var.get()
        self.save_preferences()
        global _TEXT_SCALE
        _TEXT_SCALE={'Compact':.9,'Normal':1.,'Large':1.2}.get(self.scale_var.get(),1.)
        apply_palette(self.theme_var.get())
        self.sidebar.destroy();self.workspace.destroy()
        self.nav_buttons={}
        self.root.configure(bg=BG)
        self.configure_styles()
        self.build_shell();self.show_page('Settings')

    def save_durations(self):
        try:
            focus=int(self.focus_minutes_var.get())
            snooze=int(self.snooze_minutes_var.get())
            if not 1<=focus<=180 or not 1<=snooze<=60:
                raise ValueError('Focus: 1–180 minutes; snooze: 1–60 minutes.')
        except ValueError:
            messagebox.showerror('Timer settings','Enter valid numbers. Focus: 1–180; snooze: 1–60.',parent=self.root)
            return
        self.settings['focus_minutes']=focus
        self.settings['reminder_snooze']=snooze
        self.store.save_settings()

    def save_volume(self):
        self.settings['sound_volume']=self.volume_var.get()
        self.store.save_settings()

    def save_category_sound(self,category):
        self.settings.setdefault('category_sounds',{})[category]=self.category_vars[category].get()
        self.store.save_settings()

    def open_folder(self, folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == 'win32':
                os.startfile(str(folder))
            else:
                messagebox.showinfo('Folder location', str(folder), parent=self.root)
        except OSError as e:
            messagebox.showerror('Could not open folder', str(e), parent=self.root)

    def open_extension_folder(self):
        candidates = [bundled('Browser_Extension'), Path(sys.executable).resolve().parent / 'Browser_Extension',
                      Path(__file__).resolve().parent.parent / 'Browser_Extension']
        for candidate in candidates:
            if candidate.is_dir():
                self.open_folder(candidate)
                return
        messagebox.showinfo('Extension', 'Look for Browser_Extension beside TaskLock.exe in the downloaded ZIP.\nIt is also included in the release package.', parent=self.root)

    def save_settings(self):
        self.settings['ringtone'] = self.ringtone.get()
        self.settings['custom_path'] = self.custom_tone
        self.store.save_settings()

    def choose_custom(self):
        p = filedialog.askopenfilename(title='Choose a WAV ringtone', filetypes=[('WAV sound', '*.wav')], parent=self.root)
        if not p:
            return
        try:
            if Path(p).stat().st_size > 15_000_000:
                raise ValueError('Please choose a WAV file smaller than 15 MB.')
            with wave.open(p, 'rb') as wav:
                if wav.getcomptype() != 'NONE' or wav.getsampwidth() != 2:
                    raise ValueError('Choose a 16-bit uncompressed PCM WAV file.')
            dest = self.tone_folder / 'my_ring.wav'
            dest.parent.mkdir(parents=True, exist_ok=True)
            if Path(p).resolve() != dest.resolve():
                shutil.copyfile(p, dest)
            self.custom_tone = str(dest)
            self.ringtone.set('Custom WAV')
            self.save_settings()
            self.play_ring()
        except (OSError, ValueError, wave.Error) as e:
            messagebox.showerror('File error', str(e), parent=self.root)

    def select_ring(self):
        self.save_settings()
        self.play_ring()

    def ring_path(self, task=None):
        category=task.get('category') if task else None
        preferred=self.settings.get('category_sounds',{}).get(category,'Use default') if category else 'Use default'
        name = preferred if preferred not in ('Use default',None) else self.ringtone.get()
        if name == 'Silent':
            return None
        if name == 'Custom WAV':
            return self.custom_tone if self.custom_tone and Path(self.custom_tone).exists() else None
        return str(self.tone_folder / (name.replace(' ', '_') + '.wav'))

    def play_ring(self, loop=False, task=None):
        self.stop_ring()
        path = self.ring_path(task)
        if not path or not winsound:
            return
        try:
            path=self.scaled_sound(path)
            if not path:return
            flags = winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT
            if loop:
                flags |= winsound.SND_LOOP
            winsound.PlaySound(path, flags)
            self.playing = True
        except RuntimeError:
            messagebox.showwarning('Audio problem', 'Try an uncompressed PCM WAV file.', parent=self.root)

    def scaled_sound(self,path):
        '''Volume-adjust PCM mono/stereo 16-bit WAV without changing system volume.'''
        volume=max(0,min(100,int(self.settings.get('sound_volume',65))))
        if volume==0:return None
        # Applied only to uncompressed 16-bit WAV. Other audio plays unchanged.
        try:
            src=Path(path)
            if not src.exists():return None
            with wave.open(str(src),'rb') as f:
                if f.getsampwidth()!=2 or f.getcomptype()!='NONE':return path
                params=f.getparams();frames=f.readframes(f.getnframes())
            out=self.tone_folder/'_scaled_preview.wav'
            arr=array('h');arr.frombytes(frames)
            if sys.byteorder!='little':arr.byteswap()
            factor=volume/100
            for i,v in enumerate(arr):arr[i]=int(v*factor)
            if sys.byteorder!='little':arr.byteswap()
            with wave.open(str(out),'wb') as w:
                w.setparams(params);w.writeframes(arr.tobytes())
            return str(out)
        except (OSError,ValueError,wave.Error):return path

    def stop_ring(self):
        if winsound and self.playing:
            try:
                winsound.PlaySound(None, 0)
            except RuntimeError:
                pass
        self.playing = False

    def current_sites(self):
        return sorted({site for t in self.tasks if not t.get('blocked_paused')
                       and is_homework_blocking(t) for site in t.get('blocked_sites', [])})

    def start_bridge(self):
        app = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != '/status':
                    self.send_error(404)
                    return
                # Browser extension reads state from the local app only.
                payload = json.dumps({'active': bool(app.current_sites()),
                                      'sites': app.current_sites(), 'version': VERSION}).encode()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            def log_message(self, *args):
                pass
        try:
            self.server = ThreadingHTTPServer(('127.0.0.1', 18763), Handler)
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
        except OSError:
            self.server = None

    def tick(self):
        if self.overlay is None and self.settings.get('first_run_complete',False):
            due = [t for t in self.tasks if is_due(t) and t['id'] not in self.ignored_until]
            if due:
                t = sorted(due, key=lambda item: item.get('snooze_until') or item['due'])[0]
                self.show_reminder(t)
        self.tick_job = self.root.after(5000, self.tick)

    def show_reminder(self, t):
        self.active = t
        w = tk.Toplevel(self.root)
        self.overlay = w
        w.title('TaskLock Reminder')
        w.configure(bg=BG)
        w.attributes('-fullscreen', True)
        w.configure(cursor='arrow')
        w.attributes('-topmost', True)
        w.protocol('WM_DELETE_WINDOW', self.emergency_exit)
        w.bind('<Escape>', lambda e: self.emergency_exit())
        pane = tk.Frame(w, bg=BG)
        pane.place(relx=.5, rely=.5, anchor='center')
        label(pane, '◈  TASKLOCK  /  BLUECORE ALERT', 17, True, CYAN).pack(pady=(0, 14))
        label(pane, t['title'], 31, True, wraplength=900).pack(pady=(0, 17))
        label(pane, f"Due {t['due']}  •  {t.get('category', 'Personal')}", 13, color=MUTED).pack(pady=(0, 18))
        if t.get('homework'):
            label(pane, 'Homework sites stay available. Distracting sites can be paused in Focus Mode.',
                  12, color=CYAN, wraplength=780).pack(pady=(0, 12))
            btn(pane, 'Start homework / hide alert', lambda: self.start_homework(t), primary=True).pack(pady=6)
        btn(pane, '✓  Mark as Done', lambda: self.done(t), primary=True).pack(pady=6)
        minutes=max(1,min(120,int(self.settings.get('reminder_snooze',5))))
        btn(pane,f'Snooze {minutes} minutes',lambda:self.snooze(t)).pack(pady=6)
        btn(pane, 'Emergency Exit (Esc)', self.emergency_exit, fg=RED).pack(pady=(16, 0))
        w.focus_force()
        self.play_ring(loop=True,task=t)

    def start_homework(self, t):
        t['focus_started'] = True
        t['blocked_paused'] = False
        t['snooze_until'] = (datetime.now() + timedelta(hours=1)).strftime(FMT)
        self.store.save()
        self.close_overlay()
        self.show_page('Focus')

    def snooze(self, t):
        t['snooze_until'] = (datetime.now() + timedelta(minutes=max(1,min(120,int(self.settings.get('reminder_snooze',5)))))).strftime(FMT)
        self.store.save()
        self.close_overlay()

    def emergency_exit(self):
        if self.active:
            self.active['snooze_until'] = (datetime.now() + timedelta(minutes=5)).strftime(FMT)
            self.store.save()
        self.close_overlay()

    def close_overlay(self):
        self.stop_ring()
        w = self.overlay
        self.overlay = None
        self.active = None
        if w:
            try:
                w.destroy()
            except tk.TclError:
                pass

    def release_repo(self):
        config_path = bundled('app/release_config.json')
        if not config_path.exists():
            config_path = Path(__file__).resolve().parent / 'release_config.json'
        try:
            config = json.loads(config_path.read_text(encoding='utf-8'))
            repo = config.get('github_repository', '').strip()
            if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
                return repo
        except (OSError, ValueError):
            pass
        return ''

    def open_releases(self):
        repo = self.release_repo()
        if repo:
            webbrowser.open(f'https://github.com/{repo}/releases')
        else:
            messagebox.showinfo('Release website not configured',
                'The developer needs to publish TaskLock on GitHub and set app/release_config.json.\n'
                'For now, use the included website files and release instructions.', parent=self.root)

    def check_updates(self):
        repo = self.release_repo()
        if not repo:
            return self.open_releases()

        def worker():
            try:
                remote, info = latest_published_release(repo)
                latest = '.'.join(map(str, remote))
                local = tuple(int(v) for v in VERSION.split('.'))
                if remote > local:
                    self.root.after(0, lambda v=latest, release=info: self.offer_update(v, release))
                else:
                    self.root.after(0, lambda: messagebox.showinfo(
                        'Up to date',
                        f'TaskLock v{VERSION} is up to date. No newer public release is available.',
                        parent=self.root))
            except ReleaseLookupError as exc:
                self.root.after(0, lambda error=str(exc): messagebox.showinfo(
                    'Update check unavailable',
                    'Could not verify the latest release right now.\n\n' + error,
                    parent=self.root))
        threading.Thread(target=worker, daemon=True).start()

    def offer_update(self, version, release):
        assets = release.get('assets', [])
        package = next((a for a in assets if re.fullmatch(r'TaskLock-v[0-9.]+-Setup\.exe', a.get('name', ''), re.I)), None)
        if package is None:
            package = next((a for a in assets if re.fullmatch(r'TaskLock-v[0-9.]+-Windows\.zip', a.get('name', ''), re.I)), None)
        if package is None:
            return self.open_releases()
        if not messagebox.askyesno('TaskLock update available',
                f'TaskLock v{version} is available.\n\nDownload the signed-or-unsigned release package now?\n\n'
                'You control whether and when to install the update.', parent=self.root):
            return
        destination = filedialog.asksaveasfilename(parent=self.root, title='Save TaskLock update',
                    initialdir=str(Path.home() / 'Downloads'), initialfile=package['name'],
                    defaultextension=Path(package['name']).suffix, filetypes=[('Windows release', '*.exe *.zip')])
        if not destination:
            return
        url = package.get('browser_download_url', '')
        if not url.startswith('https://github.com/'):
            messagebox.showerror('Unsafe download URL', 'The release download address is not a GitHub URL.', parent=self.root)
            return
        expected_size = package.get('size', 0)
        digest = package.get('digest', '')
        def worker():
            tmp = Path(destination).with_suffix('.part')
            try:
                h = hashlib.sha256()
                received = 0
                req = Request(url, headers={'User-Agent': f'TaskLock/{VERSION}'})
                with urlopen(req, timeout=30) as stream, open(tmp, 'wb') as out:
                    while True:
                        chunk = stream.read(1024 * 256)
                        if not chunk:
                            break
                        received += len(chunk)
                        if received > 250 * 1024 * 1024:
                            raise ValueError('Update exceeded 250 MB size limit.')
                        h.update(chunk)
                        out.write(chunk)
                if expected_size and received != expected_size:
                    raise ValueError('Downloaded file size did not match the release asset.')
                if digest.startswith('sha256:') and h.hexdigest() != digest.split(':', 1)[1].lower():
                    raise ValueError('Downloaded ZIP checksum failed verification.')
                os.replace(tmp, destination)
                self.root.after(0, lambda: messagebox.showinfo('Update downloaded',
                    'Saved update to:\n' + destination + '\n\nReview the downloaded file and install when ready. Python is not required.', parent=self.root))
            except (OSError, URLError, ValueError) as e:
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass
                self.root.after(0, lambda err=str(e): messagebox.showerror('Download failed', err, parent=self.root))
        threading.Thread(target=worker, daemon=True).start()

    def first_run(self):
        if self.settings.get('first_run_complete'):return
        w=tk.Toplevel(self.root);w.title('Welcome to TaskLock v5')
        w.configure(bg=BG);w.transient(self.root);w.grab_set();w.geometry('650x440')
        w.protocol('WM_DELETE_WINDOW',lambda:self.finish_welcome(w))
        inner=card(w,padx=30,pady=24);inner.pack(fill='both',expand=True,padx=16,pady=16)
        label(inner,'◈  TASKLOCK  /  BLUECORE',14,True,CYAN).pack(anchor='w')
        label(inner,'Welcome to your focus zone.',24,True).pack(anchor='w',pady=(20,12))
        label(inner,'Plan homework, schedule reminders, and keep distracting websites out of the way while you work.',
              12,color=MUTED,wraplength=560,justify='left').pack(anchor='w',pady=(0,18))
        label(inner,'01   Add your first task in Tasks',11,True).pack(anchor='w',pady=5)
        label(inner,'02   Choose a ringtone in Sounds',11,True).pack(anchor='w',pady=5)
        label(inner,'03   For blocking, install the Chrome/Edge companion extension',11,True).pack(anchor='w',pady=5)
        label(inner,'Safety: Esc exits alerts; blocking can always be paused.',10,color=CYAN).pack(anchor='w',pady=(18,10))
        btn(inner,'Start TaskLock  →',lambda:self.finish_welcome(w),primary=True).pack(anchor='w')
        w.focus_force()

    def finish_welcome(self,w):
        self.settings['first_run_complete']=True;self.store.save_settings()
        try:w.grab_release();w.destroy()
        except tk.TclError:pass

    def close_app(self):
        self.stop_ring()
        if self.focus_job:
            try:self.root.after_cancel(self.focus_job)
            except tk.TclError:pass
        if self.tick_job:
            self.root.after_cancel(self.tick_job)
        if getattr(self, 'server', None):
            self.server.shutdown()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    TaskLockApp(root)
    root.mainloop()
