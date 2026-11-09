# YT Playlist Downloader
# DONT FORGET TO STAR THE REPO! ⭐⭐⭐
A simple desktop GUI (built with customtkinter) for downloading entire YouTube / YouTube Music playlists — as audio or video — with one click.

Features
🔗 Paste any YouTube or YouTube Music playlist link
📁 Pick a save folder with a built-in file browser
🎚️ Choose Audio (WebM) or Video (MP4) mode
⬇️ One DOWNLOAD button grabs every track/video in the playlist
📊 Live progress bar + scrolling log of what's downloading
🧵 Runs downloads in a background thread — the UI never freezes
📦 Auto-installs its own dependencies on first run (customtkinter, yt-dlp, and static-ffmpeg if needed for video merging) — no manual pip install required
🔢 Files are saved with their playlist order prefixed, e.g. 01 - Song Title.webm
Requirements
Python 3.9+
An internet connection (for the initial dependency auto-install and for downloading)

That's it — everything else installs itself the first time you run the script.

Note on Video mode: merging separate video + audio streams into MP4 requires ffmpeg. The app will try to find it automatically (your system install first, then a portable one it downloads via static-ffmpeg). Audio mode does not require ffmpeg — it saves the native best-quality audio stream as-is (.webm/.m4a).

Installation
bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
python yt_playlist_downloader.py

No need to manually install packages — just run the script and it'll handle its own dependencies.

Usage
Paste a YouTube or YT Music playlist URL into the first field.
Click Browse and choose where the files should be saved.
Pick Audio (WebM) or Video (MP4) from the dropdown.
Click DOWNLOAD and watch the progress bar / log.

Downloaded files land directly in the folder you chose, numbered in playlist order.

Disclaimer

This tool is intended for downloading content you own the rights to, Creative Commons / royalty-free material, or for personal archiving. Downloading copyrighted content without permission may violate YouTube's Terms of Service — that responsibility is on the end user.

License

MIT — feel free to use, modify, and share.

# thanks for using my software
