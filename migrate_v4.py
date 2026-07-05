from database import init_db, connect
from rpg import ensure_default_quests
init_db()
con=connect(); cur=con.cursor(); cur.execute("SELECT guild_id FROM dragon")
for (guild_id,) in cur.fetchall(): ensure_default_quests(guild_id)
con.close()
print("GuildPet v4 migration complete: inventory, equipment and quests tables ready.")
