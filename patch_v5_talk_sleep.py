from pathlib import Path

# ---------- v5_systems.py: sleep helpers ----------
p = Path("v5_systems.py")
text = p.read_text()

if "def handle_sleep_interaction" not in text:
    text += r'''

def handle_sleep_interaction(guild_id, user, action):
    """
    Sleeping dragon interaction.
    action: whisper, cuddle, wake_gently, let_sleep
    """
    import random
    from database import connect, get_dragon

    d = get_dragon(guild_id)
    if not d["sleeping"]:
        return False, "The dragon is already awake."

    messages = {
        "whisper": [
            "🤫 You whisper softly. The dragon smiles in its sleep.",
            "🤫 The dragon hears your voice and relaxes deeper into the nest.",
        ],
        "cuddle": [
            "💖 You carefully sit beside the dragon. It feels safe.",
            "💖 The dragon curls closer without waking up.",
        ],
        "let_sleep": [
            "😴 You let the dragon sleep peacefully.",
            "🌙 The lair stays quiet. The dragon keeps dreaming.",
        ],
    }

    con = connect()
    cur = con.cursor()

    if action == "wake_gently":
        if random.random() < 0.80:
            msg = "☕ You gently wake the dragon. It slowly opens its eyes and gives a sleepy smile."
            cur.execute(
                "UPDATE dragon SET sleeping=0, pose='waking', mood='Sleepy', energy=MIN(energy+5,100), bond=MIN(bond+2,100), dragon_message=?, last_action_text=? WHERE guild_id=?",
                ("Yawwwn... good morning, keeper.", f"**{user.display_name}** gently woke the dragon.", guild_id),
            )
            con.commit()
            con.close()
            record_contribution(guild_id, user, "wake_gently", 2)
            add_memory(guild_id, f"{user.display_name} gently woke me from my sleep.", user=user, memory_type="Sleep", importance=1)
            return True, msg
        else:
            msg = "😴 The dragon mumbles: *Five more minutes...*"
            cur.execute(
                "UPDATE dragon SET mood='Sleepy', dragon_message=?, last_action_text=? WHERE guild_id=?",
                ("Five more minutes...", f"**{user.display_name}** tried to wake the dragon gently, but it kept sleeping.", guild_id),
            )
            con.commit()
            con.close()
            record_contribution(guild_id, user, "wake_attempt", 1)
            return True, msg

    if action == "whisper":
        cur.execute(
            "UPDATE dragon SET bond=MIN(bond+1,100), happiness=MIN(happiness+1,100), mood='Sleepy', dragon_message=?, last_action_text=? WHERE guild_id=?",
            ("I heard a kind voice in my dreams...", f"**{user.display_name}** whispered to the sleeping dragon.", guild_id),
        )
        reward = 1
    elif action == "cuddle":
        cur.execute(
            "UPDATE dragon SET bond=MIN(bond+2,100), happiness=MIN(happiness+2,100), mood='Sleepy', dragon_message=?, last_action_text=? WHERE guild_id=?",
            ("I feel safe...", f"**{user.display_name}** kept the sleeping dragon company.", guild_id),
        )
        reward = 2
    else:
        cur.execute(
            "UPDATE dragon SET energy=MIN(energy+3,100), mood='Sleepy', dragon_message=?, last_action_text=? WHERE guild_id=?",
            ("Zzz... peaceful dreams...", f"**{user.display_name}** let the dragon sleep peacefully.", guild_id),
        )
        reward = 1

    con.commit()
    con.close()
    record_contribution(guild_id, user, action, reward)
    return True, random.choice(messages.get(action, messages["let_sleep"]))
'''
    p.write_text(text)

# ---------- dragon.py: rest should actually put dragon to sleep ----------
p = Path("dragon.py")
text = p.read_text()

if '"sleeping": 1' not in text:
    text = text.replace(
        '"rest": { "energy": 35, "happiness": 2, "xp": 1, "tokens": 4, "guild_tokens": 2, "points": 4, "pose": "sleeping", "text": "let the dragon rest ", }',
        '"rest": { "energy": 35, "happiness": 2, "xp": 1, "tokens": 4, "guild_tokens": 2, "points": 4, "pose": "sleeping", "sleeping": 1, "text": "let the dragon rest ", }'
    )

text = text.replace(
    "sleeping=0, last_action_text=?, dragon_message=? WHERE guild_id=?",
    "sleeping=?, last_action_text=?, dragon_message=? WHERE guild_id=?"
)

text = text.replace(
    'e["pose"], "None", text, dragon_message, guild_id,',
    'e["pose"], "None", e.get("sleeping", 0), text, dragon_message, guild_id,'
)

p.write_text(text)

# ---------- views/dragon_view.py: add Talk button and sleeping-aware normal buttons ----------
p = Path("views/dragon_view.py")
text = p.read_text()

if "handle_sleep_interaction" not in text:
    text = text.replace(
        "from views.adventure_view import AdventureView",
        "from views.adventure_view import AdventureView\nfrom database import get_dragon\nfrom v5_systems import talk_response, record_contribution, handle_sleep_interaction"
    )

# If sleeping, normal care buttons show gentle wake choices instead of doing normal action
old = 'async def handle(self, interaction: discord.Interaction, action: str): ok, mins = check_cooldown(interaction.guild.id, interaction.user.id, action, 30)'
new = '''async def handle(self, interaction: discord.Interaction, action: str):
        d = get_dragon(interaction.guild.id)
        if d["sleeping"] and action not in ["rest", "bond"]:
            label_map = {
                "feed": "wake_gently",
                "play": "cuddle",
                "train": "wake_gently",
                "clean": "whisper",
            }
            sleep_action = label_map.get(action, "whisper")
            ok_sleep, msg = handle_sleep_interaction(interaction.guild.id, interaction.user, sleep_action)
            embed, file = make_dragon_embed(interaction.guild.id)
            if file:
                await interaction.response.edit_message(embed=embed, attachments=[file], view=DragonView())
            else:
                await interaction.response.edit_message(embed=embed, attachments=[], view=DragonView())
            await interaction.followup.send(msg, ephemeral=True)
            return

        ok, mins = check_cooldown(interaction.guild.id, interaction.user.id, action, 30)'''

if old in text:
    text = text.replace(old, new)

# Add only Talk button, no pet/praise/lair/event
if 'custom_id="dragon_v5_talk"' not in text:
    marker = '@discord.ui.button(label="Memories"'
    talk_button = '''@discord.ui.button(label="Talk", emoji="💬", style=discord.ButtonStyle.secondary, custom_id="dragon_v5_talk")
    async def v5_talk(self, interaction, button):
        text, mood, personality, personal_bond = talk_response(interaction.guild.id, interaction.user)
        record_contribution(interaction.guild.id, interaction.user, "talk", 1)
        await interaction.response.send_message(
            f"💬 **The dragon speaks**\\n\\n{text}\\n\\n**Mood:** {mood}\\n**Personality:** {personality}\\n**Your bond:** {personal_bond}",
            ephemeral=True,
        )

    '''
    if marker in text:
        text = text.replace(marker, talk_button + marker)
    else:
        text = text.rstrip() + "\n    " + talk_button

p.write_text(text)
