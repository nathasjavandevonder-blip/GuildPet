from pathlib import Path


path = Path("ui/views/travel_view.py")
text = path.read_text(encoding="utf-8")


# Add imports.
if "import asyncio\n" not in text:
    text = text.replace(
        "from datetime import UTC, datetime\n\n",
        "from datetime import UTC, datetime\n\n"
        "import asyncio\n"
        "import contextlib\n\n",
        1,
    )


# Add cleanup helpers before _remaining_text.
marker = "\ndef _remaining_text(arrival_time: str | None) -> str:\n"

helpers = '''
def _remaining_seconds(arrival_time: str | None) -> int:
    if not arrival_time:
        return 0

    arrival = datetime.fromisoformat(arrival_time)

    if arrival.tzinfo is None:
        arrival = arrival.replace(tzinfo=UTC)

    return max(
        0,
        int((arrival - datetime.now(UTC)).total_seconds()),
    )


def _schedule_original_delete(
    interaction: discord.Interaction,
    seconds: int,
) -> None:
    async def delete_later() -> None:
        await asyncio.sleep(max(1, seconds))

        with contextlib.suppress(
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            await interaction.delete_original_response()

    asyncio.create_task(delete_later())


'''

if "_schedule_original_delete(" not in text:
    if marker not in text:
        raise RuntimeError("Could not find _remaining_text().")

    text = text.replace(
        marker,
        "\n" + helpers + marker.lstrip("\n"),
        1,
    )


# Schedule the travel picker to disappear five minutes after arrival.
old = '''        await refresh_main_panel_in_place(
            interaction.guild,
        )


class TravelView'''
new = '''        await refresh_main_panel_in_place(
            interaction.guild,
        )

        travel_state = get_location(interaction.guild_id)
        _schedule_original_delete(
            interaction,
            _remaining_seconds(travel_state["arrival_time"]) + 300,
        )


class TravelView'''

if old not in text:
    raise RuntimeError(
        "Could not find TravelSelect cleanup insertion point."
    )

text = text.replace(old, new, 1)


# Arrival message edited from the travel picker.
old = '''            await refresh_main_panel_in_place(
                interaction.guild,
            )
            return

        await interaction.response.edit_message(
            embed=build_travel_embed(interaction.guild_id),
            view=TravelView(interaction.guild_id),
        )
'''

new = '''            await refresh_main_panel_in_place(
                interaction.guild,
            )

            _schedule_original_delete(
                interaction,
                300,
            )
            return

        await interaction.response.edit_message(
            embed=build_travel_embed(interaction.guild_id),
            view=TravelView(interaction.guild_id),
        )
'''

if old not in text:
    raise RuntimeError(
        "Could not find TravelView refresh block."
    )

text = text.replace(old, new, 1)


# Replace TravelStateView response handling.
old = '''            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True,
                delete_after=300,
            )

            await refresh_main_panel_in_place(
                interaction.guild,
            )
            return

        await interaction.response.send_message(
            embed=build_travel_embed(interaction.guild_id),
            ephemeral=True,
            delete_after=60,
        )
'''

new = '''            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True,
            )

            await refresh_main_panel_in_place(
                interaction.guild,
            )

            _schedule_original_delete(
                interaction,
                300,
            )
            return

        await interaction.response.send_message(
            embed=build_travel_embed(interaction.guild_id),
            ephemeral=True,
        )

        _schedule_original_delete(
            interaction,
            60,
        )
'''

if old not in text:
    raise RuntimeError(
        "Could not find TravelStateView response block."
    )

text = text.replace(old, new, 1)


path.write_text(text, encoding="utf-8")
print("Travel message cleanup added.")
