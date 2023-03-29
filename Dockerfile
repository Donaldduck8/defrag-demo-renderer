FROM mcr.microsoft.com/windows:ltsc2019

# Install Python and pipget_demo_info
RUN curl -O https://www.python.org/ftp/python/3.9.6/python-3.9.6-amd64.exe
RUN python-3.9.6-amd64.exe /quiet InstallAllUsers=1 PrependPath=1 TargetDir=C:\Python39
RUN setx /M PATH "%PATH%;C:\Python39;C:\Python39\Scripts"

# Install pip
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python get-pip.py

# Update pip
RUN python -m pip install --upgrade pip
RUN pip install discord.py emoji requests retrying
RUN pip install pytest-playwright
RUN playwright install

RUN powershell -Command Set-ExecutionPolicy remotesigned

RUN powershell -Command \
        $ErrorActionPreference = 'Stop'; \
        $ProgressPreference = 'SilentlyContinue'; \
        Invoke-WebRequest \
            -UseBasicParsing \
            -Uri https://dot.net/v1/dotnet-install.ps1 \
            -OutFile dotnet-install.ps1; \
        ./dotnet-install.ps1 \
            -InstallDir '/Program Files/dotnet' \
            -Channel 6.0 \
            -Runtime dotnet; \
        Remove-Item -Force dotnet-install.ps1 \
    && setx /M PATH "%PATH%;C:\\Program Files\\dotnet"

#ADD https://aka.ms/vs/16/release/vc_redist.x64.exe /vc_redist.x64.exe
#RUN C:\vc_redist.x64.exe /install /passive /norestart /log out.txt
#ADD https://aka.ms/vs/16/release/vc_redist.x86.exe /vc_redist.x86.exe
#RUN C:\vc_redist.x86.exe /install /passive /norestart /log out.txt

ADD https://download.visualstudio.microsoft.com/download/pr/21614507-28c5-47e3-973f-85e7f66545a4/f3a2caa13afd59dd0e57ea374dbe8855/vc_redist.x64.exe /vc_redist.x64.exe
RUN C:\vc_redist.x64.exe /install /passive /norestart
ADD https://download.visualstudio.microsoft.com/download/pr/092cda8f-872f-47fd-b549-54bbb8a81877/ddc5ec3f90091ca690a67d0d697f1242/vc_redist.x86.exe /vc_redist.x86.exe
RUN C:\vc_redist.x86.exe /install /passive /norestart 

COPY /src/ C:/defrag-demo-renderer/src/
COPY /odfe/ C:/defrag-demo-renderer/odfe/

# RUN C:/defrag-demo-renderer/src/sbsms-app.exe

#CMD ["C:/defrag-demo-renderer/src/DemoCleaner3.exe", "--json", "C:/defrag-demo-renderer/odfe/defrag/demos/current.dm_68"]
#CMD ["C:/defrag-demo-renderer/src/hello_world.exe"]
#CMD ["C:/defrag-demo-renderer/src/sbsms-app.exe"]