import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option
import keyring
import asyncio
from math import log
from typing import List
import pgeocode

from finderbot.api import get_appointments_from_postal
from finderbot.models import VaxAppointment

class VFClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

def get_appointment_scores(origin: str, appointments: List[VaxAppointment]):
    '''
    Assigns "scores" to appointments based on distance and accessibility, sorts them into a list based off this
    (lower scores are better)
    :param origin: Postal code to start the search from (first 3 letters)
    :param appointments: List of appointments
    :return: A list of appointments sorted by score
    '''
    appointments_scored = []
    for appointment in appointments:
        gd = pgeocode.GeoDistance("ca")
        distance = gd.query_postal_code(origin, appointment.location.address.postal[:3])
        if distance > 100:
            continue


        # Magic equation to modify score change based on # of vaccines left
        try:
            score_supply = -(30*log((1/64)*appointment.amount - 2))
            if score_supply > 0:
                raise ValueError
        except ValueError:
            score_supply = 0

        # Now we'll use some more magic equations to calculate score...
        score = (1/900*(distance**3)) + score_supply

        if len(appointment.requirements) > 0:
            if len(appointment.requirements) == 1:
                if appointment.requirements[0].name == "18+ in Specific Postal Codes": # This one doesn't really matter
                    pass
                else:
                    score += 100
            score += 100


        appointments_scored.append((appointment, score))

    appointments_sorted = sorted(appointments_scored, key=lambda x: x[1])
    return appointments_sorted


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
    best_appointment = get_appointment_scores(postal, appointments)[0][0]
    await asyncio.sleep(3) # Ensures that we wait >3 seconds before sending, as to not cause issues with ctx.defer
    await ctx.send("**<@%d>, Here is the closest and most accessible appointment found**:" % ctx.author.id,
             embed=appointments[0].format_to_embed())

client.run(keyring.get_password("VaxFinderDiscord", "BotToken"))
