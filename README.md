# defrag-demo-renderer

A Discord bot that automatically renders Defrag demos and uploads them to Streamable! 

- This version features picture-in-picture rendering for teamruns to facilitate routing analysis.

![](https://cdn.discordapp.com/attachments/930860983432409143/1091871194489307307/vlcsnap-2023-04-02-01h45m55s398.png)

## Installation

1. Obtain and put the `pakX.pk3` files in `odfe/baseq3`
2. Create `settings.py` and populate it
	1. Set up a Discord bot, enable all intents and place its Discord token in `settings.py`
	2. Choose which channels your bot should listen to, copy their IDs and place them in `settings.py`
	3. Create a Streamable account and enter your e-mail address and password in `email_and_password.json`
	
3. Download `ffmpeg.exe` and put it on your PATH
4. Run `pip install -r requirements.txt`
5. Run `playwright install`
6. Install .NET Framework 3.5 under "Turn Windows features on or off"

## Thanks

+ Enter - for creating DemoCleaner3
+ neyo - for creating demome
