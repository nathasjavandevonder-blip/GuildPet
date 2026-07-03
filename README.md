# v1.1 Visual Engine Update

Copy these files into your GitHub repo and commit:

- `config.py`
- `visuals.py`
- `embeds.py`
- `bot.py`
- `views/dragon_view.py`
- `views/updater.py`

Also add the `assets/` folders.

## Image names

Put images here:

```text
assets/dragons/egg/idle.png
assets/dragons/egg/eating.png
assets/dragons/egg/sleeping.png
assets/dragons/hatchling/idle.png
assets/dragons/hatchling/eating.png
assets/dragons/hatchling/training.png
```

Supported extensions:

```text
.png
.jpg
.jpeg
.webp
```

If an exact pose is missing, the bot falls back to `idle.png`.

## VPS update

```bash
cd ~/bot/dragonbot
git pull
sudo systemctl restart dragonbot
```
