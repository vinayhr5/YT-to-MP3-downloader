"""
╔══════════════════════════════════════════════╗
║   YouTube → MP3 320kbps Downloader           ║
║   Requires: yt-dlp, ffmpeg                   ║
║   Install:  pip install yt-dlp               ║
║             https://ffmpeg.org/download.html ║
╚══════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

# ── Colour palette ────────────────────────────────────────────────────────────
BG       = "#0d0d0d"
PANEL    = "#141414"
CARD     = "#1a1a1a"
BORDER   = "#2a2a2a"
RED      = "#ff3c3c"
RED_DIM  = "#cc2222"
WHITE    = "#f0f0f0"
GREY     = "#888888"
GREY_LT  = "#aaaaaa"
GREEN    = "#22cc66"
AMBER    = "#ffaa00"

FONT_TITLE  = ("Courier New", 22, "bold")
FONT_LABEL  = ("Courier New", 10)
FONT_MONO   = ("Courier New", 9)
FONT_BTN    = ("Courier New", 11, "bold")
FONT_SMALL  = ("Courier New", 8)

# ── Dependency check ──────────────────────────────────────────────────────────
def check_dependencies():
    missing = []
    # Check yt-dlp via the SAME python executable running this script
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import yt_dlp"],
            capture_output=True, timeout=10
        )
        if result.returncode != 0:
            raise ImportError
    except (ImportError, subprocess.TimeoutExpired, FileNotFoundError):
        missing.append(
            f"yt-dlp  →  run:  {sys.executable} -m pip install yt-dlp"
        )
    # Check ffmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, timeout=5
        )
        if result.returncode != 0:
            raise FileNotFoundError
    except (FileNotFoundError, subprocess.TimeoutExpired):
        missing.append("ffmpeg  →  https://ffmpeg.org/download.html  (add to PATH)")
    return missing


# ── Utilities ─────────────────────────────────────────────────────────────────
def sanitise_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def ts():
    return datetime.now().strftime("%H:%M:%S")


# ── Main application ──────────────────────────────────────────────────────────
class YTDownloader(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("YT → MP3  |  320 kbps")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("760x680")
        self.protocol("WM_DELETE_WINDOW", self._quit)

        self._queue: list[str] = []          # URLs waiting
        self._active = False
        self._cancel_flag = threading.Event()
        self._out_dir = Path.home() / "Music" / "YT-Downloads"
        self._out_dir.mkdir(parents=True, exist_ok=True)

        self._build_ui()
        self._log(f"[{ts()}] Python: {sys.executable}", GREY)
        self._log(f"[{ts()}] Ready. Paste one or more YouTube URLs above.", GREY_LT)
        self._check_deps_async()

    # ── UI construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 0))

        tk.Label(hdr, text="▶  YT → MP3", font=FONT_TITLE,
                 fg=RED, bg=BG).pack(side="left")
        tk.Label(hdr, text="  320 kbps · HD audio",
                 font=("Courier New", 10), fg=GREY, bg=BG,
                 anchor="sw").pack(side="left", pady=(8, 0))

        # ── Input card ──────────────────────────────────────────────────────
        card = tk.Frame(self, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1)
        card.pack(fill="x", padx=24, pady=14)

        tk.Label(card, text="PASTE YOUTUBE URL(S)  —  one per line",
                 font=FONT_SMALL, fg=GREY, bg=CARD,
                 anchor="w").pack(fill="x", padx=12, pady=(10, 2))

        self._url_text = tk.Text(
            card, height=5, bg="#0f0f0f", fg=WHITE,
            insertbackground=RED, font=FONT_MONO,
            relief="flat", borderwidth=0,
            selectbackground=RED_DIM
        )
        self._url_text.pack(fill="x", padx=12, pady=(0, 10))
        self._url_text.bind("<Control-a>", lambda e: (
            self._url_text.tag_add("sel", "1.0", "end"), "break"))

        # ── Options row ─────────────────────────────────────────────────────
        opt = tk.Frame(self, bg=BG)
        opt.pack(fill="x", padx=24)

        # Quality selector
        tk.Label(opt, text="QUALITY:", font=FONT_SMALL,
                 fg=GREY, bg=BG).pack(side="left")
        self._quality = tk.StringVar(value="320")
        for q in ("320", "256", "192", "128"):
            tk.Radiobutton(
                opt, text=f"{q}k", variable=self._quality, value=q,
                font=FONT_SMALL, fg=GREY_LT, bg=BG,
                activebackground=BG, activeforeground=WHITE,
                selectcolor=BG, indicatoron=True
            ).pack(side="left", padx=4)

        # Format selector
        tk.Label(opt, text="   FORMAT:", font=FONT_SMALL,
                 fg=GREY, bg=BG).pack(side="left")
        self._fmt = tk.StringVar(value="mp3")
        for f in ("mp3", "m4a", "flac", "wav"):
            tk.Radiobutton(
                opt, text=f.upper(), variable=self._fmt, value=f,
                font=FONT_SMALL, fg=GREY_LT, bg=BG,
                activebackground=BG, activeforeground=WHITE,
                selectcolor=BG
            ).pack(side="left", padx=4)

        # ── Output dir row ──────────────────────────────────────────────────
        drow = tk.Frame(self, bg=BG)
        drow.pack(fill="x", padx=24, pady=8)

        tk.Label(drow, text="SAVE TO:", font=FONT_SMALL,
                 fg=GREY, bg=BG).pack(side="left")
        self._dir_var = tk.StringVar(value=str(self._out_dir))
        tk.Label(drow, textvariable=self._dir_var,
                 font=FONT_SMALL, fg=GREY_LT, bg=BG,
                 anchor="w").pack(side="left", padx=6, fill="x", expand=True)
        self._mk_btn(drow, "BROWSE", self._browse_dir,
                     side="right", w=9, color=GREY)

        # ── Action buttons ───────────────────────────────────────────────────
        brow = tk.Frame(self, bg=BG)
        brow.pack(fill="x", padx=24, pady=4)

        self._dl_btn = self._mk_btn(
            brow, "⬇  DOWNLOAD", self._start_download,
            side="left", w=20, color=RED
        )
        self._mk_btn(brow, "CLEAR LOG", self._clear_log,
                     side="right", w=12, color=GREY)
        self._cancel_btn = self._mk_btn(
            brow, "✕  CANCEL", self._cancel,
            side="right", w=12, color=AMBER
        )
        self._cancel_btn.config(state="disabled")

        # ── Progress ─────────────────────────────────────────────────────────
        prow = tk.Frame(self, bg=BG)
        prow.pack(fill="x", padx=24, pady=(4, 0))

        self._status_var = tk.StringVar(value="Idle")
        tk.Label(prow, textvariable=self._status_var,
                 font=FONT_SMALL, fg=GREY, bg=BG, anchor="w").pack(
            side="left", fill="x", expand=True)

        self._pbar = ttk.Progressbar(self, mode="indeterminate",
                                     style="Red.Horizontal.TProgressbar")
        self._pbar.pack(fill="x", padx=24, pady=4)

        # Style progressbar
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Red.Horizontal.TProgressbar",
                        troughcolor=PANEL, background=RED,
                        lightcolor=RED, darkcolor=RED_DIM, bordercolor=BORDER)

        # ── Log console ──────────────────────────────────────────────────────
        tk.Label(self, text="LOG OUTPUT", font=FONT_SMALL,
                 fg=GREY, bg=BG, anchor="w").pack(
            fill="x", padx=26, pady=(6, 0))

        log_frame = tk.Frame(self, bg=BORDER)
        log_frame.pack(fill="both", expand=True, padx=24, pady=(2, 20))

        self._log_box = tk.Text(
            log_frame, bg="#080808", fg=GREY_LT, font=FONT_MONO,
            state="disabled", relief="flat", borderwidth=0,
            wrap="word", selectbackground=RED_DIM
        )
        self._log_box.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(log_frame, command=self._log_box.yview,
                          bg=PANEL, troughcolor=BG, relief="flat")
        sb.pack(side="right", fill="y")
        self._log_box.config(yscrollcommand=sb.set)

        # Colour tags for log
        self._log_box.tag_config("ok",    foreground=GREEN)
        self._log_box.tag_config("err",   foreground=RED)
        self._log_box.tag_config("info",  foreground=GREY_LT)
        self._log_box.tag_config("warn",  foreground=AMBER)
        self._log_box.tag_config("dim",   foreground=GREY)

        # ── Drop hint at bottom ──────────────────────────────────────────────
        tk.Label(self,
                 text="Supports: youtube.com  ·  youtu.be  ·  playlists",
                 font=FONT_SMALL, fg=GREY, bg=BG).pack(pady=(0, 6))

    def _mk_btn(self, parent, text, cmd, side="left", w=14, color=RED):
        btn = tk.Button(
            parent, text=text, command=cmd,
            font=FONT_BTN, bg=PANEL, fg=color,
            activebackground=color, activeforeground=BG,
            relief="flat", borderwidth=0,
            cursor="hand2", width=w,
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=color, pady=6
        )
        btn.pack(side=side, padx=(0, 8))
        btn.bind("<Enter>", lambda e: btn.config(bg=color, fg=BG))
        btn.bind("<Leave>", lambda e: btn.config(bg=PANEL, fg=color))
        return btn

    # ── Logging ────────────────────────────────────────────────────────────────
    def _log(self, msg: str, color=None, tag="info"):
        tag_map = {
            GREEN: "ok", RED: "err", AMBER: "warn",
            GREY: "dim", GREY_LT: "info"
        }
        real_tag = tag_map.get(color, tag)

        def _insert():
            self._log_box.config(state="normal")
            self._log_box.insert("end", msg + "\n", real_tag)
            self._log_box.see("end")
            self._log_box.config(state="disabled")
        self.after(0, _insert)

    def _clear_log(self):
        self._log_box.config(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.config(state="disabled")

    # ── Dependency check ───────────────────────────────────────────────────────
    def _check_deps_async(self):
        def _check():
            missing = check_dependencies()
            if missing:
                self._log("", GREY)
                self._log("⚠  MISSING DEPENDENCIES — install before downloading:", AMBER)
                for m in missing:
                    self._log(f"   • {m}", AMBER)
                self._log("", GREY)
            else:
                import yt_dlp
                ver = subprocess.run(
                    [sys.executable, "-c",
                     "import yt_dlp; print(yt_dlp.version.__version__)"],
                    capture_output=True, text=True
                ).stdout.strip()
                self._log(f"[{ts()}] yt-dlp {ver} · ffmpeg ✓", GREEN)
        threading.Thread(target=_check, daemon=True).start()

    # ── Directory chooser ─────────────────────────────────────────────────────
    def _browse_dir(self):
        d = filedialog.askdirectory(initialdir=str(self._out_dir))
        if d:
            self._out_dir = Path(d)
            self._dir_var.set(d)

    # ── Download orchestration ────────────────────────────────────────────────
    def _start_download(self):
        if self._active:
            return

        raw = self._url_text.get("1.0", "end").strip()
        urls = [u.strip() for u in raw.splitlines() if u.strip()]
        if not urls:
            messagebox.showwarning("No URLs", "Please paste at least one YouTube URL.")
            return

        missing = check_dependencies()
        if missing:
            messagebox.showerror(
                "Missing dependencies",
                "Please install the following before downloading:\n\n" +
                "\n".join(f"• {m}" for m in missing)
            )
            return

        self._queue = urls
        self._active = True
        self._cancel_flag.clear()
        self._dl_btn.config(state="disabled")
        self._cancel_btn.config(state="normal")
        self._pbar.start(12)
        self._status_var.set("Downloading…")
        self._log("─" * 60, GREY)
        self._log(f"[{ts()}] Starting {len(urls)} download(s)…", GREY_LT)

        threading.Thread(target=self._download_all, args=(urls,),
                         daemon=True).start()

    def _download_all(self, urls: list[str]):
        ok = fail = 0
        for i, url in enumerate(urls, 1):
            if self._cancel_flag.is_set():
                self._log(f"[{ts()}] ✕ Cancelled after {i-1} item(s).", AMBER)
                break
            self.after(0, lambda i=i, n=len(urls):
                self._status_var.set(f"Downloading {i}/{n}…"))
            success = self._download_one(url, i, len(urls))
            if success:
                ok += 1
            else:
                fail += 1

        self.after(0, self._finish, ok, fail)

    def _download_one(self, url: str, idx: int, total: int) -> bool:
        import yt_dlp

        fmt  = self._fmt.get()
        kbps = self._quality.get()

        self._log(f"\n[{ts()}] [{idx}/{total}] {url}", GREY_LT)

        # Codec mapping
        codec = {
            "mp3": "mp3", "m4a": "aac",
            "flac": "flac", "wav": "wav"
        }.get(fmt, "mp3")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(self._out_dir / "%(artist)s - %(title)s.%(ext)s"),
            "noplaylist": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": codec,
                    "preferredquality": kbps,
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            "writethumbnail": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._ydl_hook],
            "logger": _SilentLogger(),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", url) if info else url
                self._log(f"[{ts()}] ✓  {title}", GREEN)
            return True
        except Exception as exc:
            self._log(f"[{ts()}] ✗  Error: {exc}", RED)
            return False

    def _ydl_hook(self, d):
        if d["status"] == "downloading":
            pct  = d.get("_percent_str", "?").strip()
            spd  = d.get("_speed_str", "").strip()
            eta  = d.get("_eta_str", "").strip()
            self.after(0, self._status_var.set,
                       f"Downloading… {pct}  {spd}  ETA {eta}")
        elif d["status"] == "finished":
            self.after(0, self._status_var.set, "Converting…")

    def _finish(self, ok: int, fail: int):
        self._pbar.stop()
        self._active = False
        self._dl_btn.config(state="normal")
        self._cancel_btn.config(state="disabled")
        self._log("─" * 60, GREY)
        self._log(
            f"[{ts()}] Done — {ok} succeeded, {fail} failed. "
            f"Files saved to: {self._out_dir}",
            GREEN if fail == 0 else AMBER
        )
        self._status_var.set(f"Done  ✓{ok}  ✗{fail}")

    def _cancel(self):
        if self._active:
            self._cancel_flag.set()
            self._log(f"[{ts()}] Cancelling…", AMBER)

    def _quit(self):
        self._cancel_flag.set()
        self.destroy()


class _SilentLogger:
    def debug(self, _): pass
    def warning(self, _): pass
    def error(self, msg): pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = YTDownloader()
    app.mainloop()