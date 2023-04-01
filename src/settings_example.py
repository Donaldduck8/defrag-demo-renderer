import os
import json
import login

HERE = os.path.abspath(os.path.dirname(__file__))

ODFE_DIR = os.path.join(os.path.dirname(HERE), "odfe")

DISCORD_BOT_TOKEN = ""
DISCORD_GUILD_ID = ""

DISCORD_CHANNELS_ALLOWED = [
    ""
]

ODFE_VIDEO_CONFIG = {
    "r_customWidth": "1920",
    "r_customHeight": "1080",
    "cg_draw2D": "1",
    "mdd_cgaz": "1",
    "vid_restart": "",
    "cl_aviPipeFormat": {
        "-threads": "6",
        "-b:v": "1000k",  # Placeholder, will be replaced by render_demo()
        "-maxrate": "1000k",
        "-bufsize": "1000k",
        "-preset": "fast",
        "-vcodec": "libx264",
        "-flags": "+cgop",
        "-pix_fmt": "yuv420p",
        "-bf": "2",
        "-codec:a": "aac",
        "-strict": "-2",
        "-b:a": "160k",
        "-r:a": "44100",
        "-movflags": "faststart"
    },
    "cl_aviFrameRate": "60"
}

STREAMABLE_COOKIES = {}
STREAMABLE_HEADERS = {}
CONTEXT_COOKIES = []

def load_streamable_data():
    # Get streamable cookies
    streamable_cookies_p = os.path.join(HERE, "streamable_cookies.json")

    # If cookies don't exist, make user log in
    while not os.path.isfile(streamable_cookies_p):
        login.run()

    with open(streamable_cookies_p, "r") as f:
        global STREAMABLE_COOKIES
        STREAMABLE_COOKIES = json.loads(f.read())

    # Headers can be empty aside from the Cookie field
    global STREAMABLE_HEADERS
    STREAMABLE_HEADERS = {}
    STREAMABLE_HEADERS["Cookie"] = "; ".join([f"{k}={v}" for k,v in STREAMABLE_COOKIES.items()])

    # Playwright context cookies
    global CONTEXT_COOKIES 
    CONTEXT_COOKIES = [{"name": k, "value": v, "url": "https://streamable.com"} for k,v in STREAMABLE_COOKIES.items()]

def convert_config_dic_to_lines(config):
    lines = []

    for k, v in config.items():
        if len(v) == 0:
            lines.append(k)
        else:
            if isinstance(v, dict):
                _lines = []
                for _k, _v in v.items():
                    _lines.append(f'{_k} {_v}')

                _lines_s = " ".join(_lines)

                lines.append(f'set {k} "{_lines_s}"')
            else:
                lines.append(f'seta {k} "{v}"')

    return lines


ODFE_VIDEO_MAX_FILE_SIZE_BITS = 250 * 1024 * 1024 * 8
ODFE_AUDIO_BITRATE = 160000  # ATTENTION: This is defined in the config as well, which you will have to change if you change this

load_streamable_data()

if __name__ == "__main__":
    print(convert_config_dic_to_lines(ODFE_VIDEO_CONFIG))
