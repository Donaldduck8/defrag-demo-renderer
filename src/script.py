import os
import re
import sys
import math
import time
import json
import shutil
import requests
import subprocess
import traceback

import urllib
import discord

from settings import ODFE_DIR, ODFE_VIDEO_MAX_FILE_SIZE_BITS, ODFE_VIDEO_CONFIG, convert_config_dic_to_lines, ODFE_AUDIO_BITRATE, DISCORD_CHANNELS_ALLOWED, DISCORD_BOT_TOKEN
from utils import retry_net

from retrying import retry

import zipfile
import emoji

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.abspath(os.path.dirname(__file__))

DEMOCLEANER_P = os.path.join(HERE, "DemoCleaner3.exe")
# DEMOCLEANER_P = r'C:\Users\Donald\Documents\GitHub\DemoCleaner3\bin\Debug\DemoCleaner3.exe'

ODFE_EXE_P = os.path.join(ODFE_DIR, "oDFe.x64.exe")

ODFE_BASEQ3_DIR = os.path.join(ODFE_DIR, "baseq3")

ODFE_DEFRAG_DIR = os.path.join(ODFE_DIR, "defrag")
ODFE_VIDEO_CONFIG_NAME = "video.cfg"
ODFE_VIDEO_CONFIG_P = os.path.join(ODFE_DEFRAG_DIR, ODFE_VIDEO_CONFIG_NAME)

ODFE_DEMOS_DIR = os.path.join(ODFE_DEFRAG_DIR, "demos")
ODFE_VIDEOS_DIR = os.path.join(ODFE_DEFRAG_DIR, "videos")

def create_dir(dir_p):
    if not os.path.isdir(dir_p):
        os.makedirs(dir_p)
    
create_dir(ODFE_DEMOS_DIR)
create_dir(ODFE_VIDEOS_DIR)

DEMO_TEST_P = os.path.join(ODFE_DEMOS_DIR, "test.dm_68")
VIDEO_TEST_P = os.path.join(ODFE_VIDEOS_DIR, "test.mp4")

VIDEO_HOST = "STREAMABLE"

LOCAL_MAPS = []

def get_demo_info(demo_p):
    args = [
        DEMOCLEANER_P,
        "--json",
        demo_p
    ]

    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    if "Can not parse demo" in result.stdout:
        # Fail here
        pass

    return json.loads(result.stdout)


def rename_demo(demo_p, demo_info):
    demo_name_new = demo_info["name"]["new"].replace("{", "").replace("}", "")
    demo_p_new = os.path.join(os.path.dirname(demo_p), demo_name_new)

    shutil.move(demo_p, demo_p_new)

    return demo_p_new


@retry(stop_max_attempt_number=10, wait_fixed=2000)
def replace_retry(old_p, new_p):
    os.replace(old_p, new_p)


def convert_time_notation_to_ms(time_s):
    total_ms = 0

    elements = time_s.split(".")
    elements.reverse()

    factors = [1, 1000, 60000]

    for i, element in enumerate(elements):
        total_ms += int(element) * factors[i]

    return total_ms


def convert_ms_to_time_notation(total_ms):
    ms = int(total_ms % 1000)
    total_ms -= ms
    total_ms /= 1000

    s = int(total_ms % 60)
    total_ms -= s
    total_ms /= 60

    m = int(total_ms)

    return f'{m:02}.{s:02}.{ms:03}'


def calculate_video_length(demo_info):
    start = int(demo_info["sequence"]["start"])
    end = int(demo_info["sequence"]["end"])

    video_length = (end - start) / 125  # 125 ticks per second

    return video_length


def calculate_video_bitrate(demo_info):
    # Get length of demo
    # Get maximum allowed file size for video upload
    # Return video bitrate - audio bitrate
    video_length = calculate_video_length(demo_info)

    average_bitrate = int(math.floor(ODFE_VIDEO_MAX_FILE_SIZE_BITS / video_length))
    average_bitrate -= average_bitrate % 1000

    return average_bitrate


def index_local_maps():
    global LOCAL_MAPS

    for entry_name in os.listdir(ODFE_BASEQ3_DIR):
        if not entry_name.endswith("pk3"):
            continue

        pk3_p = os.path.join(ODFE_BASEQ3_DIR, entry_name)

        with zipfile.ZipFile(pk3_p, mode="r") as pk3:
            for zip_member in pk3.infolist():
                if zip_member.filename.endswith(".bsp"):
                    bsp_name = os.path.basename(zip_member.filename).lower()

                    LOCAL_MAPS.append(bsp_name.lower())

    # Deduplicate, dunno if this is necessary but just in case
    LOCAL_MAPS = list(set(LOCAL_MAPS))


def get_file_name_from_cd(headers):
    # https://stackoverflow.com/a/51570425
    content_disposition = headers["Content-Disposition"]

    fname = re.findall(r"filename\*=([^;]+)", content_disposition, flags=re.IGNORECASE)
    if not fname:
        fname = re.findall(r"filename=([^;]+)", content_disposition, flags=re.IGNORECASE)
    if "utf-8''" in fname[0].lower():
        fname = re.sub("utf-8''", '', fname[0], flags=re.IGNORECASE)
        fname = urllib.parse.unquote(fname)
    else:
        fname = fname[0]

    # clean space and double quotes
    return fname.strip().strip('"')


def download_map(demo_info):
    map_name = demo_info["client"]["mapname"]

    url = f'http://ws.q3df.org/getpk3bymapname.php/{map_name}'

    r = retry_net(requests.get, url=url, sleep_amount=60)

    file_name = get_file_name_from_cd(r.headers)
    file_p = os.path.join(ODFE_BASEQ3_DIR, file_name)

    with open(file_p, "wb+") as file_f:
        file_f.write(r.content)

    LOCAL_MAPS.append(map_name + ".bsp")

    return


def config_set_clean(clean):
    if clean:
        ODFE_VIDEO_CONFIG["cg_draw2D"] = "0"
        ODFE_VIDEO_CONFIG["mdd_cgaz"] = "0"
    else:
        ODFE_VIDEO_CONFIG["cg_draw2D"] = "1"
        ODFE_VIDEO_CONFIG["mdd_cgaz"] = "1"


def render_demo(demo_p, demo_info, clean=False):
    map_name = demo_info["client"]["mapname"]

    if map_name + ".bsp" not in LOCAL_MAPS:
        download_map(demo_info)

    demo_name = os.path.basename(demo_p)
    demo_name_stem = os.path.splitext(demo_name)[0]

    if clean:
        video_name = f'{demo_name_stem}_clean.mp4'
        video_name_shortened = f'{demo_name_stem}_clean'[:56] + '.mp4'
    else:
        video_name = f'{demo_name_stem}.mp4'
        video_name_shortened = f'{demo_name_stem}'[:56] + '.mp4'

    # TODO: FIX QUAKE3E RANDOMLY DECIDING TO CUT OFF THE VIDEO NAME LMAOOOO
    video_p = os.path.join(ODFE_VIDEOS_DIR, video_name_shortened)

    average_bitrate = calculate_video_bitrate(demo_info)

    if VIDEO_HOST == "STREAMABLE":
        video_bitrate = int(((average_bitrate - ODFE_AUDIO_BITRATE) / 1000) * 0.4)
    elif VIDEO_HOST == "YOUTUBE":
        video_bitrate = int(((average_bitrate - ODFE_AUDIO_BITRATE) / 1000) * 0.8)

    video_bitrate = min(video_bitrate, 14000)
    video_bitrate_s = str(video_bitrate) + "k"

    ODFE_VIDEO_CONFIG["cl_aviPipeFormat"]["-b:v"] = video_bitrate_s
    ODFE_VIDEO_CONFIG["cl_aviPipeFormat"]["-maxrate"] = video_bitrate_s

    config_set_clean(clean)

    lines = convert_config_dic_to_lines(ODFE_VIDEO_CONFIG)

    lines.append(f'demo "{demo_name}"')
    lines.append(f'video-pipe "{video_name}"')
    lines.append(f'set nextdemo "wait 100; quit"')

    lines_s = "\n".join(lines)

    with open(ODFE_VIDEO_CONFIG_P, "w+") as config_f:
        config_f.write(lines_s)

    # Call oDFe.exe with parameters
    args = [
        ODFE_EXE_P,
        "+exec",
        ODFE_VIDEO_CONFIG_NAME
    ]

    result = subprocess.run(args)

    # TODO: FIX QUAKE3E RANDOMLY DECIDING TO CUT OFF THE VIDEO NAME LMAOOOO
    if video_name_shortened != video_name:
        video_p_full = os.path.join(ODFE_VIDEOS_DIR, video_name)

        replace_retry(video_p, video_p_full)
        return video_p_full

    # Return video_p
    return video_p


def upload_video_streamable_playwright_wrapper(video_p):
    args = [
        "py",
        os.path.join(HERE, "upload_and_respond.py"),
        video_p
    ]

    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=HERE)
    print(result.stderr)
    shortcode = result.stdout.strip()

    return shortcode


def can_pip_teamrun_render(demo_infos):
    if len(demo_infos) <= 1:
        return False

    # All demos must have validation df_mp_interferenceoff 0
    for demo_info in demo_infos:
        if "df_mp_interferenceoff" not in demo_info["validity"]:
            return False

        if demo_info["validity"]["df_mp_interferenceoff"] != "0":
            return False

    # All demos must have the same mapname
    if len(set([demo_info["client"]["mapname"] for demo_info in demo_infos])) > 1:
        return False

    # All demos must have reasonably similar sequence servertime starts
    skips = calculate_skips(demo_infos)

    for skip in skips:
        if skip > 60.0:
            return False

    # All demos must be less than 4 minutes long
    for demo_info in demo_infos:
        if calculate_video_length(demo_info) / 1000 > 240:
            return False

    return True


def discord_bot_loop():
    intents = discord.Intents.all()
    intents.members = True
    intents.messages = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print("Ready.")

    async def render_message_attachments_and_reply(message):
        print("render_message_attachments_and_reply: " + str(message))

        demo_paths = []
        demo_infos = []

        for _, attachment in enumerate(message.attachments):
            attachment_url = attachment.url

            if attachment_url.endswith(".dm_68"):
                demo_name = os.path.basename(urllib.parse.urlparse(urllib.parse.unquote(attachment_url)).path)  # what?????
                demo_p = os.path.join(ODFE_DEMOS_DIR, demo_name)

                # Download demo
                demo_b = retry_net(requests.get, url=attachment_url).content

                with open(demo_p, "wb+") as demo_f:
                    demo_f.write(demo_b)

                demo_info = get_demo_info(demo_p)
                demo_p = rename_demo(demo_p, demo_info)
                demo_name = os.path.basename(demo_p)

                demo_paths.append(demo_p)
                demo_infos.append(demo_info)

        should_normal_render = True
        should_pip_teamrun_render = False

        choice_message = None

        # Check if this message is a PIP teamrun render or a bunch of individual demos
        if can_pip_teamrun_render(demo_infos):
            should_normal_render = False

            # WHAT THE FUCK IS DISCORD DOING???? WHY CANT I JUST SEND THE STRING?????????????????????????
            emoji_one = emoji.emojize(":keycap_1:")
            emoji_two = emoji.emojize(":keycap_2:")
            emoji_three = emoji.emojize(":keycap_3:")

            # Allow user to choose normal, PIP or both
            choice_message = await message.reply(f"It seems like you've posted teamrun demos. Would you like to {emoji_one} render the videos normally, {emoji_two} as a picture-in-picture video, or {emoji_three} both?")

            await choice_message.add_reaction(emoji_one)
            await choice_message.add_reaction(emoji_two)
            await choice_message.add_reaction(emoji_three)

            def check(reaction, user):
                print(reaction.message.id, choice_message.id)
                return reaction.message.id == choice_message.id and user == message.author and str(reaction.emoji) in [emoji_one, emoji_two, emoji_three]

            reaction, user = await client.wait_for("reaction_add", timeout=30.0, check=check)

            if str(reaction) == str(emoji_one):
                should_normal_render = True
            elif str(reaction) == str(emoji_two):
                should_pip_teamrun_render = True
            elif str(reaction) == str(emoji_three):
                should_normal_render = True
                should_pip_teamrun_render = True

        if should_pip_teamrun_render:
            try:
                await message.add_reaction('⏳')
            except Exception as e:
                pass

            video_p = render_teamrun_pip(demo_paths, demo_infos)

            try:
                await message.add_reaction('⏫')
            except Exception as e:
                pass

            # Upload video somewhere
            if VIDEO_HOST == "STREAMABLE":
                video_id = upload_video_streamable_playwright_wrapper(video_p)
                video_url = f'https://streamable.com/{video_id}'

                await message.reply(video_url)

            try:
                await message.remove_reaction('⏳', client.user)
                await message.remove_reaction('⏫', client.user)
                await message.add_reaction('☑️')
            except Exception as e:
                traceback.print_exc()
                pass

        if should_normal_render:
            try:
                await message.add_reaction('⏳')
            except Exception as e:
                pass

            for demo_p, demo_info in zip(demo_paths, demo_infos):
                # Render demo
                video_p = render_demo(demo_p, demo_info)

                try:
                    await message.add_reaction('⏫')
                except Exception as e:
                    pass

                # Upload video somewhere
                if VIDEO_HOST == "STREAMABLE":
                    video_id = upload_video_streamable_playwright_wrapper(video_p)
                    video_url = f'https://streamable.com/{video_id}'

                    await message.reply(video_url)

                try:
                    await message.remove_reaction('⏳', client.user)
                    await message.remove_reaction('⏫', client.user)
                    await message.add_reaction('☑️')
                except Exception as e:
                    traceback.print_exc()
                    pass

        if choice_message:
            await choice_message.delete()

    @client.event
    async def on_message(message):
        # Ignore own messages
        if message.author == client.user:
            return

        # Limited to channels I specify
        if str(message.channel.id) not in DISCORD_CHANNELS_ALLOWED:
            return

        if not message.attachments:
            return

        time.sleep(2)
        print("GOOBER")
        await render_message_attachments_and_reply(message)

        # Now check the recent history of this channel to get more that might have slipped through the cracks of the event system
        historical_slice_size = 20
        historical_slice = 0

        while True:
            recent_messages = (await message.channel.history(limit = historical_slice_size * historical_slice + 1).flatten())[historical_slice_size * historical_slice:]

            for other_msg in recent_messages:
                if other_msg.created_at <= message.created_at:
                    return

                print(other_msg.content)

                if not other_msg.attachments:
                    continue

                await render_message_attachments_and_reply(other_msg)

            historical_slice += 1

    client.run(DISCORD_BOT_TOKEN)


def build_pip_command(video_paths, skips, output_p, video_bitrate_s):
    inputs = []
    pips = []
    overlays = []

    for i, video in enumerate(video_paths):
        inputs.append(f'-y -ss {skips[i]} -i {video_paths[i]}')
        if i > 0:
            pips.append(f'[{i}:v]scale=iw/4:-1:flags=lanczos[pip{i}]')

            bg_s = f'bg{i}'
            output_s = bg_s if i != len(video_paths) - 1 else "v"

            if i == 1:
                overlays.append(f'[0:v][pip1]overlay=main_w-overlay_w-10:main_h-overlay_h-10[{output_s}]')
            elif i == 2:
                overlays.append(f'[bg1][pip2]overlay=(main_w-overlay_w)/2:main_h-overlay_h-10[{output_s}]')
            elif i == 3:
                overlays.append(f'[bg2][pip3]overlay=10:main_h-overlay_h-10,format=yuv420p[{output_s}]')

    inputs_s = " ".join(inputs)
    pips_s = "; ".join(pips)
    overlays_s = "; ".join(overlays)

    command = f'ffmpeg {inputs_s} -filter_complex "{pips_s}; {overlays_s}; [0:a]amerge=inputs=1[a]" -map "[v]" -map "[a]" -b:v {video_bitrate_s} -maxrate {video_bitrate_s} -bufsize 1M {output_p}'

    return command


def calculate_skips(demo_infos):
    # Which demo starts the latest?
    max_server_time_start = max([int(demo_info["sequence"]["serverTimeStart"]) for demo_info in demo_infos])

    # How many seconds of each demo do we need to skip?
    skips = [(max_server_time_start - int(demo_info["sequence"]["serverTimeStart"])) / (125 * 8) for demo_info in demo_infos]

    return skips


def sanitize_player_name(player_name):
    player_name = re.sub(r'\^\d', "", player_name)
    return player_name


def get_teamrun_name(demo_infos):
    map_name = demo_infos[0]["client"]["mapname"]
    physics = demo_infos[0]["game"]["gameplay"].partition("(")[2].partition(")")[0]
    player_names_s = ".".join([sanitize_player_name(demo_info["player"]["name"]) for demo_info in demo_infos])
    teamrun_time = sum([convert_time_notation_to_ms(re.search(r"^(.+)\[(.+)\.(.+)\]([\d\.]+)\((.+)\.(.+)\)", demo_info["name"]["new"]).group(4)) for demo_info in demo_infos])
    teamrun_time_s = convert_ms_to_time_notation(teamrun_time)

    teamrun_name = f'{map_name}[{len(demo_infos)}p.{physics}]{teamrun_time_s}({player_names_s})'

    return teamrun_name


def render_teamrun_pip(demo_paths, demo_infos=None):
    if not demo_infos:
        demo_infos = [get_demo_info(demo_p) for demo_p in demo_paths]

    skips = calculate_skips(demo_infos)

    video_paths = []

    for i, demo_p in enumerate(demo_paths):
        if i == 0:
            video_paths.append(render_demo(demo_p, demo_infos[i], clean=False))
        else:
            video_paths.append(render_demo(demo_p, demo_infos[i], clean=True))

    average_bitrate = calculate_video_bitrate(demo_infos[0])

    if VIDEO_HOST == "STREAMABLE":
        video_bitrate = int(((average_bitrate - ODFE_AUDIO_BITRATE) / 1000) * 0.4)
    elif VIDEO_HOST == "YOUTUBE":
        video_bitrate = int(((average_bitrate - ODFE_AUDIO_BITRATE) / 1000) * 0.8)

    video_bitrate = min(video_bitrate, 14000)
    video_bitrate_s = str(video_bitrate) + "k"

    video_pip_p = os.path.join(ODFE_VIDEOS_DIR, get_teamrun_name(demo_infos) + ".mp4")

    ffmpeg_command = build_pip_command(video_paths, skips, video_pip_p, video_bitrate_s)

    while True:
        result = subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        if "moov atom not found" in result.stdout or "moov atom not found" in result.stderr:
            print("TRYING AGAIN")
            # Just try again lmao
            continue
        else:
            break

    return video_pip_p


if __name__ == "__main__":
    index_local_maps()

    discord_bot_loop()
