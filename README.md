# YT → MP3 Downloader — Complete Setup Guide

## Prerequisites

- Windows 10 / 11 (64-bit)
- Python 3.9 or later
- Internet connection

---

## Step 1 — Install Python

1. Go to **https://python.org/downloads** and download the latest installer
2. Run the installer
3. ⚠️ **Check "Add Python to PATH"** before clicking Install — this is critical
4. Complete the installation

Verify it worked — open PowerShell and run:
```
python --version
```
You should see something like `Python 3.13.5`.

---

## Step 2 — Install yt-dlp

Open PowerShell and run:
```
python -m pip install yt-dlp
```

> ⚠️ Always use `python -m pip install` (not just `pip install`).
> This ensures yt-dlp is installed into the **exact same Python** that will run the app.

Verify:
```
pip show yt-dlp
```
You should see a version like `2026.3.17` and a Location path.

---

## Step 3 — Install ffmpeg

### Download

1. Go to **https://www.gyan.dev/ffmpeg/builds/**
2. Download **`ffmpeg-release-essentials.zip`**
3. Extract the zip — right-click → **Extract All**
4. Move/rename the extracted folder so the structure is:
   ```
   C:\ffmpeg\bin\ffmpeg.exe
   C:\ffmpeg\bin\ffprobe.exe
   C:\ffmpeg\bin\ffplay.exe
   ```

### Add ffmpeg to System PATH

This is the most important step — without it, the app cannot find ffmpeg even if it's installed.

1. Press `Win + S` → search **"Edit the system environment variables"** → open it
2. Click **"Environment Variables…"** button (bottom right)
3. In the **lower** panel ("System variables"), find **Path** → click **Edit**
4. Click **New** and paste:
   ```
   C:\ffmpeg\bin
   ```
5. Click **OK** on all three dialogs to save

### Verify ffmpeg is in PATH

**Open a brand new PowerShell window** (existing windows won't see the new PATH), then run:
```
where ffmpeg
```
Expected output:
```
C:\ffmpeg\bin\ffmpeg.exe
```

If `where ffmpeg` returns nothing, the PATH was not saved correctly — repeat the steps above and make sure you're editing **System variables → Path**, not User variables.

---

## Step 4 — Run the App

Place `yt_music_downloader.py` in a folder (e.g. `D:\python-projects\`), then from PowerShell:

```
cd D:\python-projects
python yt_music_downloader.py
```

The log panel will show on startup:
```
[HH:MM:SS] Python: C:\Users\...\Python313\python.exe
[HH:MM:SS] Ready. Paste one or more YouTube URLs above.
[HH:MM:SS] yt-dlp 2026.xx.xx · ffmpeg ✓
```

All three lines in green = you're good to go. ✅

---

## Using the App

1. Paste one or more YouTube URLs into the text box (one per line)
2. Select quality: **320k** (default) / 256k / 192k / 128k
3. Select format: **MP3** (default) / M4A / FLAC / WAV
4. Optionally click **BROWSE** to change the save folder
5. Click **⬇ DOWNLOAD**

Files are saved to `C:\Users\<you>\Music\YT-Downloads\` by default.
Playlists are fully supported — paste the playlist URL and all tracks download automatically.

---

## Features

- Multi-URL batch download — paste several links at once
- Playlist support
- Quality selector: 320 / 256 / 192 / 128 kbps
- Format picker: MP3, M4A (AAC), FLAC, WAV
- Embeds album art thumbnail into every file
- Embeds metadata (title, artist, album)
- Live progress with speed + ETA
- Cancel button mid-download
- Colour-coded log console

---

## Troubleshooting

### "MISSING DEPENDENCIES — ffmpeg" in the app log

ffmpeg is not in your System PATH. Common causes:

- You added it to **User variables** instead of **System variables** — redo Step 3 using System variables
- You have the right path but the terminal was already open when you added it — **close and reopen PowerShell**, then relaunch the app
- ffmpeg is not at `C:\ffmpeg\bin` — run the command below to find it, then add the correct folder to PATH:
  ```
  Get-ChildItem -Path C:\,D:\ -Recurse -Filter "ffmpeg.exe" -ErrorAction SilentlyContinue | Select-Object FullName
  ```

### "MISSING DEPENDENCIES — yt-dlp" in the app log

yt-dlp was installed into a different Python than the one running the script. Fix:
```
python -m pip install yt-dlp
```
Always launch the app with `python yt_music_downloader.py` from the same terminal where `python --version` shows the correct version.

### Download fails / HTTP 403 error

yt-dlp may be outdated. Update it:
```
python -m pip install -U yt-dlp
```

### `where ffmpeg` returns nothing after adding to PATH

You need to open a **new** PowerShell window — PATH changes are not applied to already-open terminals.

### No audio in the downloaded file

ffmpeg is not working correctly. Run `ffmpeg -version` in a fresh terminal. If that also fails, re-extract ffmpeg and redo Step 3.

---

*For personal use only. Respect YouTube's Terms of Service.*
