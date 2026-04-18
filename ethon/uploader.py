import yt_dlp
import requests
import re
import os
import asyncio
import shlex


# ================= SAFE ASYNC BASH =================

async def bash(cmd):
    process = await asyncio.create_subprocess_exec(
        *shlex.split(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return stdout.decode().strip(), stderr.decode().strip()


# ================= SAFE FILENAME =================

def safe_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name)


# ================= YOUTUBE DOWNLOAD =================

async def download_from_youtube(url):
    ydl_opts = {
        "format": "best",
        "outtmpl": "%(title).200s.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = safe_filename(info.get("title", "video"))
        ext = info.get("ext", "mp4")

        filename = f"{title}.{ext}"

        filename = ydl.prepare_filename(info)
            
        return filename

# ================= GENERIC YTDL =================

async def ytdl(url):
    ydl_opts = {
        "format": "best",
        "outtmpl": "%(title).200s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
    }

    # auto handle HLS / m3u8
    if "m3u8" in url or "HLS" in url:
        ydl_opts["hls_prefer_ffmpeg"] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = safe_filename(info.get("title", "video"))
        ext = info.get("ext", "mp4")

        filename = f"{title}.{ext}"

        for f in os.listdir():
            if f.startswith(title) and f.endswith(ext):
                return f

        return filename


# ================= CHECK DOWNLOADABLE =================

def is_downloadable(url):
    try:
        h = requests.head(url, allow_redirects=True, timeout=10)
        content_type = h.headers.get("content-type", "").lower()

        if "text" in content_type or "html" in content_type:
            return False

        return True
    except Exception:
        return False


# ================= GET FILENAME =================

def get_filename_from_cd(cd):
    if not cd:
        return None

    fname = re.findall('filename="?([^"]+)"?', cd)
    if fname:
        return fname[0]

    return None


# ================= WEB DOWNLOAD =================

async def weburl(url):
    if not is_downloadable(url):
        return None

    loop = asyncio.get_event_loop()

    def _download():
        with requests.get(url, stream=True, allow_redirects=True, timeout=30) as r:
            r.raise_for_status()

            filename = get_filename_from_cd(r.headers.get("content-disposition"))

            if not filename:
                filename = url.split("/")[-1].split("?")[0]

            filename = safe_filename(filename or "file")

            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return filename  # ⬅️ ini juga harus di dalam function

    return await loop.run_in_executor(None, _download)