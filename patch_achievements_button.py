from pathlib import Path

p = Path("views/dragon_view.py")
text = p.read_text()

if "get_achievement_progress" not in text:
    text = text.replace(
        "from achievements import check_achievements, ACHIEVEMENTS",
        "from achievements import check_achievements, ACHIEVEMENTS, get_achievement_progress",
    )

button = '''
    @discord.ui.button(label="Achievements", emoji="🏆", style=discord.ButtonStyle.secondary, custom_id="dragon_achievements")
    async def achievements(self, interaction, button):
        rows = get_achievement_progress(interaction.guild.id, interaction.user.id)

        if not rows:
            await interaction.response.send_message("🏆 No achievement progress yet.", ephemeral=True, delete_after=30)
            return

        lines = []
        for a in rows:
            if a["done"]:
                lines.append(f"✅ **{a['name']}** — complete")
            else:
                lines.append(
                    f"⬜ **{a['name']}** — {a['current']}/{a['target']} "
                    f"(**{a['remaining']} left**)\\n_{a['desc']}_"
                )

        await interaction.response.send_message(
            "🏆 **Your Dragon Achievements**\\n\\n" + "\\n\\n".join(lines),
            ephemeral=True,
            delete_after=30,
        )

'''

if 'custom_id="dragon_achievements"' not in text:
    marker = '    @discord.ui.button(label="Memories"'
    text = text.replace(marker, button + marker)

# make common ephemeral button replies auto disappear after 30 sec
text = text.replace("ephemeral=True,", "ephemeral=True, delete_after=30,")
text = text.replace("ephemeral=True)", "ephemeral=True, delete_after=30)")

p.write_text(text)
