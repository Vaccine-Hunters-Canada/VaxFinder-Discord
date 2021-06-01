import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice
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
        distance = 0

        # Magic equation to modify score change based on # of vaccines left
        try:
            score_supply = -(30*log((1/64)*appointment.amount - 2))
            if score_supply > 0:
                raise ValueError
        except ValueError:
            score_supply = 0

        # Now we'll use some more magic equations to calculate score...
        score = (1/900*(distance**3)) + score_supply

        score = (1/900*(distance**3))

        if len(appointment.requirements) > 0:
            if len(appointment.requirements) == 1:
                if appointment.requirements[0].name == "HotSpot": # This one doesn't really matter
                    pass
                else:
                    score += 100
            else:
                score += 100


        appointments_scored.append((appointment, score))

    appointments_sorted = sorted(appointments_scored, key=lambda x: x[1])
    return appointments_sorted


client = VFClient()
slash = SlashCommand(client, sync_commands=True)

options = []
options.append(create_option(name="postal", description="THE FIRST 3 LETTERS of your postal code.",
                             option_type=3, required=True))

dose_choices = [create_choice(name="1", value=1), create_choice(name="2", value=2)]
options.append(create_option(name="dose", description="Dose # you are looking for", option_type=4, required=True,
                             choices=dose_choices))


@slash.slash(name="find", description="Find the closest available vaccine appointment, with the fewest requirements",
            options=options)
async def find(ctx, postal: str, dose: int):
    if not (0 < len(postal) < 4):
        await ctx.send("❗ <@%d>, please only enter the *first 3 digits* of your postal code!" % ctx.author.id,
                       delete_after=8.0)
        return
    await ctx.defer()

    appointments = get_appointments_from_postal(postal, dose=dose)
    await asyncio.sleep(3) # Ensures that we wait >3 seconds before sending, as to not cause issues with ctx.defer

    if not appointments:
        await ctx.send("**Sorry <@%d> - no appointments were found near your postal code (%s)!**" %
                       (ctx.author.id, postal), delete_after=8.0)
        return

    best_appointment = get_appointment_scores(postal, appointments)[0][0]
    await ctx.send("**<@%d>, DMing the best appointment!**" % ctx.author.id, delete_after=8.0)
    try:
        await ctx.author.send("**<@%d>, Here is the closest and most accessible appointment found**:" % ctx.author.id,
                embed=best_appointment.format_to_embed())
    except discord.errors.Forbidden:
        await ctx.send("<@%d>, you've disabled DMs from server members, so no appointments can be sent."
                 "Please enable this to use the bot." % ctx.author.id)

@slash.slash(name="findall", description="Find all vaccine appointments nearby and send via DM", options=options)
async def findall(ctx, postal:str, dose: int):
    if not (0 < len(postal) < 4):
        await ctx.send("❗ <@%d>, please only enter the *first 3 digits* of your postal code!" % ctx.author.id,
                       delete_after=8.0)
        return
    await ctx.defer()

    appointments = get_appointments_from_postal(postal, dose=dose)

    if not appointments:
        await ctx.send("**Sorry <@%d> - no appointments were found near your postal code (%s)!**" %
                       (ctx.author.id, postal), delete_after=8.0)
        return

    await ctx.send("<@%d>, sending you available appointments via direct message!" % ctx.author.id)
    user = ctx.author
    appointments_accessible = [appointment for appointment in appointments if len(appointment.requirements) == 0]
    try:
        if appointments_accessible:
            await user.send(
                "\U0001F537 **Here are locations with no known elgibility requirements (12+/18+, "
                "may not be accurate - check yourself via phone or website):**")
            for appointment in appointments_accessible:
                await user.send(embed=appointment.format_to_embed())
            if len(appointments_accessible) != len(appointments):
                await user.send(
                    "\U0001F536 **Here are all other available appointments (locations may show twice, as "
                    "doses are allocated differently based on elgibility):**")

            appointments = [appointment for appointment in appointments if appointment not in appointments_accessible]

        for appointment in appointments:
            await user.send(embed=appointment.format_to_embed())
    except discord.errors.Forbidden:
        await ctx.send("<@%d>, you've disabled DMs from server members, so no appointments can be sent. "
                 "Please enable this to use the bot." % ctx.author.id)

client.run(keyring.get_password("VaxFinderDiscord", "BotToken"))
