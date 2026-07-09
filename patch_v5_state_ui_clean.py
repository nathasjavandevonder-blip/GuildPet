from pathlib import Path

files = ["bot.py", "views/updater.py", "views/dragon_view.py"]

for filename in files:
    p = Path(filename)
    text = p.read_text()

    text = text.replace(
        "from views.view_router import get_dragon_view",
        "from views.state_view import get_state_view",
    )

    text = text.replace(
        "from views.dragon_view import DragonView",
        "from views.state_view import get_state_view",
    )

    text = text.replace("view=DragonView()", "view=get_state_view(interaction.guild.id)")
    text = text.replace("view=DragonView(guild.id)", "view=get_state_view(guild.id)")
    text = text.replace("view=get_dragon_view(interaction.guild.id)", "view=get_state_view(interaction.guild.id)")
    text = text.replace("view=get_dragon_view(guild.id)", "view=get_state_view(guild.id)")

    p.write_text(text)

# dragon_view mag state_view niet bovenaan importeren als dat circular maakt
p = Path("views/dragon_view.py")
text = p.read_text()
text = text.replace("from views.state_view import get_state_view\n", "")
text = text.replace("from views.view_router import get_dragon_view\n", "")
text = text.replace("from views.view_router import get_dragon_view, ", "from embeds import ")

# in dragon_view refreshes gebruiken we lokale import
text = text.replace(
    "view=get_state_view(interaction.guild.id)",
    "view=__import__('views.state_view', fromlist=['get_state_view']).get_state_view(interaction.guild.id)",
)

p.write_text(text)

# bot.py en updater.py mogen state_view wel importeren
for filename in ["bot.py", "views/updater.py"]:
    p = Path(filename)
    text = p.read_text()
    if "from views.state_view import get_state_view" not in text:
        text = text.replace(
            "from views.dragon_view import DragonView",
            "from views.state_view import get_state_view",
        )
    p.write_text(text)
