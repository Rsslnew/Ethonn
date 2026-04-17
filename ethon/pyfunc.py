#fixbug

import subprocess
import json


# ───────────────────────── BASH ─────────────────────────

def bash(cmd):
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output, error = process.communicate()
    return output, error


# ───────────────────────── METADATA (FIXED) ─────────────────────────

def video_metadata(file):
    """
    Ambil metadata video yang BENAR:
    - pilih stream video (bukan audio / cover)
    - fallback aman
    - hanya 1x ffprobe (hemat & cepat)
    """
    try:
        out = subprocess.check_output([
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            "-show_format",
            file
        ])

        data = json.loads(out)

        # cari video stream (bukan attached_pic)
        v_stream = None
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                if not (s.get("disposition") or {}).get("attached_pic", 0):
                    v_stream = s
                    break

        # fallback kalau tidak ketemu
        if not v_stream:
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    v_stream = s
                    break

        width = int(v_stream.get("width", 1280)) if v_stream else 1280
        height = int(v_stream.get("height", 720)) if v_stream else 720

        duration = int(float(data.get("format", {}).get("duration", 0)))

        return {
            "width": width,
            "height": height,
            "duration": duration
        }

    except Exception as e:
        print("video_metadata error:", e)
        return {
            "width": 1280,
            "height": 720,
            "duration": 0
        }


# ───────────────────────── OPTIONAL HELPERS ─────────────────────────

def duration(file):
    try:
        out = subprocess.check_output([
            "ffprobe",
            "-v", "quiet",
            "-show_format",
            "-print_format", "json",
            file
        ])
        data = json.loads(out)
        return int(float(data["format"]["duration"]))
    except Exception:
        return 0