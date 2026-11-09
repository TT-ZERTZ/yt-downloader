import os
import sys
import subprocess
import threading
import queue
import importlib
import shutil


def _ensure_installed(pip_name, import_name=None):
    import_name = import_name or pip_name
    try:
        return importlib.import_module(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pip_name])
        return importlib.import_module(import_name)


ctk = _ensure_installed("customtkinter")
yt_dlp = _ensure_installed("yt-dlp", "yt_dlp")
static_ffmpeg = _ensure_installed("static-ffmpeg", "static_ffmpeg")

import tkinter.filedialog as filedialog


def _get_ffmpeg_path():
    """Return (path, error) - a usable ffmpeg executable path, preferring a
    system install but falling back to a pip-fetched static binary
    (auto-downloaded and cached on first use by static-ffmpeg, no .exe
    installer needed)."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg, None
    try:
        ffmpeg_exe, _ffprobe_exe = static_ffmpeg.run.get_or_fetch_platform_executables_else_raise()
        return ffmpeg_exe, None
    except Exception as e:
        return None, str(e)


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YT Playlist Downloader")
        self.geometry("640x480")
        self.minsize(560, 420)

        self.save_path = ctk.StringVar(value="")
        self.mode = ctk.StringVar(value="Audio (WebM)")
        self.log_queue = queue.Queue()
        self.is_downloading = False

        self._build_ui()
        self._poll_log_queue()

    # ---------- UI ----------

    def _build_ui(self):
        pad = {"padx": 16, "pady": 8}

        title = ctk.CTkLabel(
            self, text="YouTube / YT Music Playlist Downloader",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=(20, 10))

        # Playlist URL
        url_frame = ctk.CTkFrame(self, fg_color="transparent")
        url_frame.pack(fill="x", **pad)
        ctk.CTkLabel(url_frame, text="Playlist URL").pack(anchor="w")
        self.url_entry = ctk.CTkEntry(
            url_frame, placeholder_text="Paste YouTube / YT Music playlist link here..."
        )
        self.url_entry.pack(fill="x", pady=(4, 0))

        # Save location
        save_frame = ctk.CTkFrame(self, fg_color="transparent")
        save_frame.pack(fill="x", **pad)
        ctk.CTkLabel(save_frame, text="Save Location").pack(anchor="w")

        save_row = ctk.CTkFrame(save_frame, fg_color="transparent")
        save_row.pack(fill="x", pady=(4, 0))
        self.save_entry = ctk.CTkEntry(save_row, textvariable=self.save_path)
        self.save_entry.pack(side="left", fill="x", expand=True)
        browse_btn = ctk.CTkButton(save_row, text="Browse", width=90, command=self._browse_folder)
        browse_btn.pack(side="left", padx=(8, 0))

        # Mode dropdown
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", **pad)
        ctk.CTkLabel(mode_frame, text="Download As").pack(anchor="w")
        self.mode_menu = ctk.CTkOptionMenu(
            mode_frame, values=["Audio (WebM)", "Video (MP4)"], variable=self.mode
        )
        self.mode_menu.pack(fill="x", pady=(4, 0))

        # Progress bar
        self.progress = ctk.CTkProgressBar(self)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=16, pady=(12, 4))

        self.status_label = ctk.CTkLabel(self, text="Idle", text_color="gray70")
        self.status_label.pack(anchor="w", padx=16)

        # Download button
        self.download_btn = ctk.CTkButton(
            self, text="DOWNLOAD", height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_download
        )
        self.download_btn.pack(fill="x", padx=16, pady=(14, 8))

        # Log box
        self.log_box = ctk.CTkTextbox(self, height=140)
        self.log_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.log_box.configure(state="disabled")

    def _browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path.set(folder)

    # ---------- Logging / progress plumbing ----------

    def _log(self, text):
        self.log_queue.put(("log", text))

    def _set_status(self, text):
        self.log_queue.put(("status", text))

    def _set_progress(self, frac):
        self.log_queue.put(("progress", frac))

    def _poll_log_queue(self):
        try:
            while True:
                kind, value = self.log_queue.get_nowait()
                if kind == "log":
                    self.log_box.configure(state="normal")
                    self.log_box.insert("end", value + "\n")
                    self.log_box.see("end")
                    self.log_box.configure(state="disabled")
                elif kind == "status":
                    self.status_label.configure(text=value)
                elif kind == "progress":
                    self.progress.set(value)
                elif kind == "done":
                    self.is_downloading = False
                    self.download_btn.configure(state="normal", text="DOWNLOAD")
        except queue.Empty:
            pass
        self.after(150, self._poll_log_queue)

    # ---------- Download logic ----------

    def _start_download(self):
        if self.is_downloading:
            return

        url = self.url_entry.get().strip()
        folder = self.save_path.get().strip()
        is_audio = self.mode.get().startswith("Audio")

        ffmpeg_path = None
        if not is_audio:  # Video mode still needs ffmpeg to merge video+audio streams
            self._set_status("Checking for ffmpeg...")
            self._log("Checking for ffmpeg (auto-downloading a copy if needed)...")
            ffmpeg_path, ffmpeg_err = _get_ffmpeg_path()
            if ffmpeg_path is None:
                self._log(f"ERROR: Could not find or auto-download ffmpeg.\nDetails: {ffmpeg_err}")
                return
            self._log(f"Using ffmpeg at: {ffmpeg_path}")

        if not url:
            self._log("ERROR: Please paste a playlist URL.")
            return
        if not folder:
            self._log("ERROR: Please choose a save location.")
            return
        if not os.path.isdir(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception as e:
                self._log(f"ERROR: Could not create folder: {e}")
                return

        self.is_downloading = True
        self.download_btn.configure(state="disabled", text="Downloading...")
        self.progress.set(0)
        self._log(f"Starting download from: {url}")
        self._set_status("Preparing...")

        thread = threading.Thread(
            target=self._run_download, args=(url, folder, self.mode.get(), ffmpeg_path), daemon=True
        )
        thread.start()

    def _progress_hook(self, d):
        if d.get("status") == "downloading":
            filename = os.path.basename(d.get("filename", ""))
            pct_str = d.get("_percent_str", "0%").strip()
            self._set_status(f"Downloading: {filename} ({pct_str})")

            # Playlist-level progress, if available
            idx = d.get("info_dict", {}).get("playlist_index")
            total = d.get("info_dict", {}).get("playlist_count") or d.get("info_dict", {}).get("n_entries")
            if idx and total:
                try:
                    self._set_progress(min((idx - 1) / total + (self._pct_fraction(pct_str) / total), 1.0))
                except Exception:
                    pass

        elif d.get("status") == "finished":
            filename = os.path.basename(d.get("filename", ""))
            self._log(f"Finished: {filename}")

    @staticmethod
    def _pct_fraction(pct_str):
        try:
            return float(pct_str.replace("%", "")) / 100.0
        except ValueError:
            return 0.0

    def _run_download(self, url, folder, mode, ffmpeg_path):
        output_template = os.path.join(folder, "%(playlist_index)02d - %(title)s.%(ext)s")

        is_audio = mode.startswith("Audio")

        ydl_opts = {
            "outtmpl": output_template,
            "ignoreerrors": True,
            "noplaylist": False,
            "progress_hooks": [self._progress_hook],
            "quiet": True,
            "no_warnings": False,
        }

        if ffmpeg_path:
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            ydl_opts["ffmpeg_location"] = ffmpeg_dir
            # Also prepend to PATH for this process, so yt-dlp/ffmpeg-python
            # subprocess calls find it no matter how they search for it.
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

        if is_audio:
            # No conversion — keep the native best-audio stream (webm/m4a),
            # avoids needing ffmpeg at all for audio downloads.
            ydl_opts.update({
                "format": "bestaudio/best",
            })
        else:
            ydl_opts.update({
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self._set_status("Done!")
            self._set_progress(1.0)
            self._log("All downloads complete.")
        except Exception as e:
            self._log(f"ERROR: {e}")
            self._set_status("Failed")
        finally:
            self.log_queue.put(("done", None))


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()
