Fixed files:
- embeds.py
- bot.py
- visuals.py
- views/dragon_view.py
- views/updater.py

This fixes the visible \n problem in Discord and keeps image attachment support.

Upload/overwrite these files in GitHub, commit, push, then on VPS:

cd ~/bot/dragonbot
git pull
sudo systemctl restart dragonbot
