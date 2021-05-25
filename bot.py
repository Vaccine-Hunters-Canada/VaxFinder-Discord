import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
import keyring

import asyncio
from finderbot.api import get_appointments_from_postal

class VFClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

client = VFClient()
slash = SlashCommand(client, sync_commands=True)

options = []
options.append(create_option(name="postal", description="THE FIRST 3 LETTERS of your postal code.",
                             option_type=3, required=True))

@slash.slash(name="find", description="Find the closest available vaccine appointment, with the fewest requirements",
            options=options)
async def pog(ctx, postal: str):
    if not (0 < len(postal) < 4):
        await ctx.send("❗ <@%d>, please only enter the *first 3 digits* of your postal code!" % ctx.author.id,
                       delete_after=8.0)
        return
    await ctx.defer()
    appointments = get_appointments_from_postal(postal)
    await asyncio.sleep(3)
    ctx.send(embed=appointments[0].format_to_embed())

client.run(keyring.get_password("VaxFinderDiscord", "BotToken"))
