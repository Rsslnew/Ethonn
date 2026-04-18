import subprocess
import json

def bash(cmd):
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    return output, error


def video_metadata(file):
    try:
        out = subprocess.check_output([
            "ffprobe",
            "-v", "quiet",
            "-show_format",
            "-show_streams",
            "-print_format", "json",
            file
        ])
        data = json.loads(out)

        stream = data['streams'][0]
        width = int(stream.get('width', 1280))
        height = int(stream.get('height', 720))
        duration = int(float(data['format'].get('duration', 0)))

        return {
            'width': width,
            'height': height,
            'duration': duration
        }

    except Exception as e:
        print("Error:", e)
        return {
            'width': 1280,
            'height': 720,
            'duration': 0
        }

# function to find the resolution of the input video file

import subprocess
import shlex
import json

def findVideoResolution(pathToInputVideo):
    cmd = "ffprobe -v quiet -print_format json -show_streams"
    args = shlex.split(cmd)
    args.append(pathToInputVideo)
    # run the ffprobe process, decode stdout into utf-8 & convert to JSON
    ffprobeOutput = subprocess.check_output(args).decode('utf-8')
    ffprobeOutput = json.loads(ffprobeOutput)

    # find height and width
    height = ffprobeOutput['streams'][0]['height']
    width = ffprobeOutput['streams'][0]['width']

    # find duration
    out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_format", "-print_format", "json", pathToInputVideo])
    ffprobe_data = json.loads(out)
    duration_seconds = float(ffprobe_data["format"]["duration"])

    return int(height), int(width), int(duration_seconds)

def duration(pathToInputVideo):
    out = subprocess.check_output(["ffprobe", "-v", "quiet", "-show_format", "-print_format", "json", pathToInputVideo])
    ffprobe_data = json.loads(out)
    duration_seconds = float(ffprobe_data["format"]["duration"])
    return int(duration_seconds)
  
def video_metadata(file):
    height = 720
    width = 1280
    duration = 0
    try:
        height, width, duration = findVideoResolution(file)
        if duration == 0:
            data = videometadata(file)
            duration = data["duration"]
            if duration is None:
                duration = 0
    except Exception as e:
        try: 
            if 'height' in str(e):
                data = videometadata(file)
                height = data["height"]
                width = data["width"]
                duration = duration(file)
                if duration == 0:
                    data = videometadata(file)
                    duration = data["duration"]
                    if duration is None:
                        duration = 0
        except Exception as e:
            print(e)
            height, width, duration = 720, 1280, 0
    data = {'width' : width, 'height' : height, 'duration' : duration }
    return data
