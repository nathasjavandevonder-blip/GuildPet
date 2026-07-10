from pathlib import Path

path = Path("bot_v5.py")
text = path.read_text(encoding="utf-8")

if "from discord.ext import commands, tasks" not in text:
    text = text.replace(
        "from discord.ext import commands\n",
        "from discord.ext import commands, tasks\n",
        1,
    )

if "from systems.world.service import world_tick" not in text:
    text = text.replace(
        "from systems.state.service import ensure_state, get_state\n",
        "from systems.state.service import ensure_state, get_state\n"
        "from systems.world.service import world_tick\n",
        1,
    )

setup_old = """        await restore_registered_panels(self)
        await self.tree.sync()
"""

setup_new = """        await restore_registered_panels(self)

        if not world_clock_task.is_running():
            world_clock_task.start()

        await self.tree.sync()
"""

if setup_old not in text:
    raise SystemExit("setup_hook block not found.")

text = text.replace(setup_old, setup_new, 1)

marker = "\n\n@bot.event\nasync def on_ready()"

task_code = '''

@tasks.loop(minutes=30)
async def world_clock_task() -> None:
    for guild in bot.guilds:
        try:
            world_tick(guild.id)
            await refresh_main_panel_in_place(guild)
        except Exception as exc:
            print(
                f"World tick failed for {guild.name}: {exc}"
            )


@world_clock_task.before_loop
async def before_world_clock_task() -> None:
    await bot.wait_until_ready()
'''

if task_code not in text:
    text = text.replace(
        marker,
        task_code + marker,
        1,
    )

path.write_text(text, encoding="utf-8")
print("Updated bot_v5.py")
