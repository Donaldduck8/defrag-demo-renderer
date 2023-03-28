DISCORD_BOT_TOKEN = ""
DISCORD_GUILD_ID = ""

DISCORD_CHANNELS_ALLOWED = [
    "1234567890"
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
        "-preset": "slow",
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

STREAMABLE_HEADERS = {}

STREAMABLE_COOKIES = {}

CONTEXT_COOKIES = []


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

if __name__ == "__main__":
    print(convert_config_dic_to_lines(ODFE_VIDEO_CONFIG))
