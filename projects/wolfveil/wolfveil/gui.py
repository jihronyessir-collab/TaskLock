"""Wolfveil early alpha Windows GUI. Uses the official WireGuard installation.

No automatic connection, DNS modification, or live ad blocking.
"""
from __future__ import annotations

import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from .config import ConfigError, validate_config_file
from .manager import WireGuardUnavailable, connect, disconnect, status


BG = "#07111D"
PANEL = "#102238"
ACCENT = "#55B7FF"
TEXT = "#EAF4FF"
MUTED = "#A4BED6"


class WolfveilWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Wolfveil — Early Development")
        root.geometry("620x455")
        root.minsize(520, 420)
        root.configure(bg=BG)
        self.config_path = tk.StringVar()
        self.tunnel_name: str | None = None
        self.message = tk.StringVar(value="Choose a WireGuard .conf file to begin.")
        self.connection = tk.StringVar(value="Not connected")
        self._busy = False

        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=26, pady=(22, 14))
        tk.Label(header, text="WOLFVEIL", font=("Segoe UI", 25, "bold"),
                 fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(header, text="TAVLOKYN STUDIOS  /  PRIVACY PROTOTYPE",
                 font=("Segoe UI", 9, "bold"), fg=ACCENT, bg=BG).pack(anchor="w")

        card = tk.Frame(root, bg=PANEL, padx=18, pady=18)
        card.pack(fill="x", padx=26, pady=10)
        tk.Label(card, text="Tunnel configuration", font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=PANEL).pack(anchor="w")
        tk.Label(card, text="Use a configuration from a WireGuard server you trust.",
                 font=("Segoe UI", 9), fg=MUTED, bg=PANEL).pack(anchor="w", pady=(4, 12))
        line = tk.Frame(card, bg=PANEL)
        line.pack(fill="x")
        tk.Entry(line, textvariable=self.config_path, state="readonly",
                 font=("Segoe UI", 10), readonlybackground=BG, fg=TEXT,
                 relief="flat").pack(side="left", fill="x", expand=True, ipady=8)
        tk.Button(line, text="Browse .conf", command=self.browse, bg=ACCENT, fg=BG,
                  relief="flat", font=("Segoe UI", 10, "bold"), padx=12).pack(side="left", padx=(8, 0), ipady=5)

        tk.Label(card, textvariable=self.connection, fg=ACCENT, bg=PANEL,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(18, 12))
        controls = tk.Frame(card, bg=PANEL)
        controls.pack(fill="x")
        self.connect_button = tk.Button(controls, text="Connect", command=self.on_connect,
                                        bg=ACCENT, fg=BG, relief="flat",
                                        font=("Segoe UI", 10, "bold"), padx=18, pady=8)
        self.connect_button.pack(side="left")
        self.disconnect_button = tk.Button(controls, text="Disconnect", command=self.on_disconnect,
                                           bg="#28455F", fg=TEXT, relief="flat",
                                           font=("Segoe UI", 10, "bold"), padx=18, pady=8)
        self.disconnect_button.pack(side="left", padx=10)
        tk.Button(controls, text="Refresh status", command=self.refresh, bg="#28455F",
                  fg=TEXT, relief="flat", padx=12, pady=8).pack(side="left")

        tk.Label(root, textvariable=self.message, bg=BG, fg=MUTED, wraplength=540,
                 justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=28, pady=(12, 6))
        tk.Label(root, text="Ad/tracker blocking: PLANNED, NOT ACTIVE. A VPN does not replace antivirus.",
                 bg=BG, fg="#F3C47A", font=("Segoe UI", 9),
                 wraplength=540, justify="left").pack(anchor="w", padx=28, pady=8)
        self._set_busy(False)

    def _set_busy(self, busy: bool):
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.connect_button.configure(state=state)
        self.disconnect_button.configure(state=state)

    def browse(self):
        if self._busy:
            return
        selected = filedialog.askopenfilename(
            parent=self.root, title="Choose a WireGuard configuration",
            filetypes=[("WireGuard configurations", "*.conf")])
        if not selected:
            return
        try:
            info = validate_config_file(selected)
        except ConfigError as exc:
            messagebox.showerror("Invalid configuration", str(exc), parent=self.root)
            return
        self.config_path.set(selected)
        self.tunnel_name = info.name
        self.message.set(f"Validated tunnel '{info.name}' with {info.peers} peer(s). "
                         "Private keys are not shown.")
        self.refresh()

    def refresh(self):
        if not self.tunnel_name or self._busy:
            return
        self.connection.set("Tunnel status: " + status(self.tunnel_name))

    def _run(self, operation, success_message: str):
        self._set_busy(True)
        self.message.set("Waiting for WireGuard and Windows permissions…")
        def worker():
            try:
                operation()
                error = None
            except (ConfigError, WireGuardUnavailable, OSError, PermissionError) as exc:
                error = str(exc)
            def finish():
                self._set_busy(False)
                self.message.set(error or success_message)
                self.refresh()
            self.root.after(0, finish)
        threading.Thread(target=worker, daemon=True).start()

    def on_connect(self):
        if self._busy:
            return
        config = self.config_path.get()
        if not config:
            messagebox.showinfo("Choose a configuration", "Select a trusted .conf file first.",
                                parent=self.root)
            return
        if not messagebox.askyesno("Connect with WireGuard",
                "Install and start this WireGuard tunnel service? "
                "Windows may ask for administrator approval. "
                "Wolfveil does not yet provide active ad blocking.",
                parent=self.root):
            return
        self._run(lambda: connect(config, confirmed=True),
                  "WireGuard tunnel installation requested. Verify traffic and DNS before relying on it.")

    def on_disconnect(self):
        if self._busy or not self.tunnel_name:
            return
        name = self.tunnel_name
        if not messagebox.askyesno("Disconnect tunnel",
                f"Remove the WireGuard tunnel service '{name}'?", parent=self.root):
            return
        self._run(lambda: disconnect(name, confirmed=True),
                  "WireGuard tunnel service removed.")


def main():
    root = tk.Tk()
    WolfveilWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
