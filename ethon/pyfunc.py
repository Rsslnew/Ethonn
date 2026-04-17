import subprocess
import json


def bash(cmd):
    process = subprocess.Popen(
        cmd, shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output, error = process.communicate()
    return output, error


def video_metadata(file):
    try:
        out = subprocess.check_output([
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file
        ])

        data = json.loads(out)

        # ambil video stream pertama
        stream = next(
            (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
            {}
        )

        width = int(stream.get("width", 1280))
        height = int(stream.get("height", 720))

        duration = float(data.get("format", {}).get("duration", 0))
        duration = int(duration)

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


def total_frames(file):
    try:
        out = subprocess.check_output([
            "ffprobe",
            "-v", "quiet",
            "-select_streams", "v:0",
            "-count_frames",
            "-show_entries", "stream=nb_read_frames",
            "-print_format", "json",
            file
        ])

        data = json.loads(out)
        frames = int(data["streams"][0].get("nb_read_frames", 0))
        return frames

    except Exception:
        return 0


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