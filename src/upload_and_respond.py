import os
import re
import sys
import math
import time
import json
import base64
import random
import shutil
import string
import datetime
import requests
import subprocess
import traceback

import hashlib
import urllib
import discord

from bs4 import BeautifulSoup

from settings import *
from utils import *

from playwright.sync_api import sync_playwright, TimeoutError

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.abspath(os.path.dirname(__file__))

streamable_session = requests.Session()

# Taken from settings
streamable_session.headers.update(STREAMABLE_HEADERS)
streamable_session.cookies.update(STREAMABLE_COOKIES)


def upload_video_streamable_playwright(video_p):
    with sync_playwright() as playwright:
        #args=["--shm-size=8gb"]
        browser = playwright.firefox.launch(headless=True)
        context = browser.new_context(user_agent=streamable_session.headers["User-Agent"], extra_http_headers={"Cookie": streamable_session.headers["Cookie"]})

        context.add_cookies(CONTEXT_COOKIES)

        # Open new page
        page = context.new_page()

        # Go to url
        page.goto("https://streamable.com/")
        page.on("filechooser", lambda file_chooser: file_chooser.set_files(video_p))

        print("Waiting for upload button")
        page.wait_for_selector('button:has-text("Upload video")')

        time.sleep(3)

        # Get number of videos or list of shortcodes so far
        content = page.content()
        soup = BeautifulSoup(content, "html.parser")

        videos = soup.find_all("div", {"class": re.compile(r".+?video-item.*")})
        shortcodes = []

        for video in videos:
            e = video.find("a", {"id": "video-url-input"})
            href = e["href"]
            shortcode = href.split("/")[-1]
            shortcodes.append(shortcode)

        print("Clicking upload button")

        time.sleep(2)

        page.click('button:has-text("Upload video")')

        time.sleep(2)

        shortcode_found = False

        while True:
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")
            videos = soup.find_all("div", {"class": re.compile(r".+?video-item.*")})

            for video in videos:
                e = video.find("a", {"id": "video-url-input"})
                href = e["href"]
                shortcode = href.split("/")[-1]

                if shortcode not in shortcodes:
                    shortcode_found = True


            
            if shortcode_found:
                e = videos[0].find("a", {"id": "video-url-input"})
                href = e["href"]
                shortcode = href.split("/")[-1]
                break

            time.sleep(4)

        while True:
            content = page.content()
            soup = BeautifulSoup(content, "html.parser")

            progress_bars = soup.find_all("div", {"class": "progress-status"})

            if len(progress_bars) == 0:
                break

            time.sleep(1)

    return shortcode


if __name__ == "__main__":
    sys.stdout = open(os.devnull, "w")

    video_p = sys.argv[1]
    shortcode = upload_video_streamable_playwright(video_p)

    sys.stdout = sys.__stdout__
    print(shortcode)
