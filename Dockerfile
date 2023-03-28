FROM 3.10-windowsservercore-ltsc2022
SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]
RUN python3 -m pip install --upgrade pip
RUN pip install pytest-playwright
RUN playwright install
RUN pip install discord.py
RUN pip install zipfile
RUN pip install emoji
RUN pip install requests
RUN pip install subprocess
RUN pip install traceback
RUN pip install retrying
