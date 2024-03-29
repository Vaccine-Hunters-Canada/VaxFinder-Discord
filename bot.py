import discord
from discord_slash import SlashCommand
from discord_slash.utils.manage_commands import create_option, create_choice
from discord.ext.tasks import loop
import asyncio
from math import log, isnan
from typing import List
import pgeocode
import keyring
import datetime


from finderbot.API.vaccineontario import VaccineOntarioAPI
from finderbot.API.vaxfinder import VaxFinderAPI
from finderbot.models import VaxAppointment
from finderbot import logging


class VFClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.useCounter = 0

    async def on_ready(self):
        print('Logged on as', self.user)

    @loop(seconds=3600)
    async def logUses(self):
        logging.log("Uses in the last hour: %d" % self.useCounter, "data")
        self.useCounter = 0


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
        address = appointment.location.address
        if address.postal:
            gd = pgeocode.GeoDistance("ca")
            distance = gd.query_postal_code(origin, address.postal)
        elif address.longitude:
            nm = pgeocode.Nominatim("ca")
            query = nm.query_postal_code(origin)
            longitude, latitude = query.longitude, query.latitude
            clinicCoordinates = [address.longitude, address.latitude]
            distance = pgeocode.haversine_distance([[longitude, latitude]], [[clinicCoordinates]])
        else:
            distance = 15

        try:
            if isnan(distance):
                distance = 15
        except TypeError:
            distance = 15


        # Magic equation to modify score change based on # of vaccines left
        try:
            score_supply = -(10*log((1/64)*appointment.amount - 2))
            if (score_supply > 0) or isnan(score_supply):
                raise ValueError
        except ValueError:
            score_supply = 0


        if appointment.dates:
            currentDate = datetime.datetime.now()
            nextAppointmentDate = appointment.dates[0]
            deltaDays = (nextAppointmentDate - currentDate).days
            dateScore = deltaDays*2
        else:
            dateScore = 50


        # Now we'll use some more magic equations to calculate score...
        score = (1/100*(distance**3)) + score_supply + dateScore

        appointments_scored.append((appointment, score))

    if appointments_scored:
        appointments_sorted = sorted(appointments_scored, key=lambda x: x[1])
        return appointments_sorted


client = VFClient()
slash = SlashCommand(client, sync_commands=True)

options = []
options.append(create_option(name="postal", description="THE FIRST 3 LETTERS of your postal code.",
                             option_type=3, required=True))

dose_choices = [create_choice(name="1", value=1), create_choice(name="2", value=2), create_choice(name="3", value=3)]
options.append(create_option(name="dose", description="Dose # you are looking for", option_type=4, required=True,
                             choices=dose_choices))

vaccine_choices = [create_choice(name="Pfizer", value="Pfizer"), create_choice(name="Moderna", value="Moderna")]
options.append(create_option(name="vaccine", description="OPTIONAL: The vaccine type to filter by - will return results"
                             " ONLY if they have this type", option_type=3, choices=vaccine_choices, required=False))

async def find_appointments(postal: str, dose: int, vaccine=None):
    APIS = [VaccineOntarioAPI(), VaxFinderAPI()]
    appointments = APIS[0].get_appointments_from_postal(postal, dose=dose, vaccine=vaccine)
    if not appointments:
        appointments = APIS[1].get_appointments_from_postal(postal, dose=dose, vaccine=vaccine)
    return [appointment[0] for appointment in get_appointment_scores(postal, appointments)]


@slash.slash(name="find", description="Find the closest available vaccine appointment, with the fewest requirements",
            options=options)
async def find(ctx, postal: str, dose: int, vaccine=None):
    if not (0 < len(postal) < 4):
        await ctx.send("❗ <@%d>, please only enter the *first 3 digits* of your postal code!" % ctx.author.id,
                       delete_after=8.0)
        return
    await ctx.defer(hidden=True)

    client.useCounter += 1

    try:
        best_appointment = (await find_appointments(postal, dose, vaccine))[0]
        await asyncio.sleep(3) # Ensures that we wait >3 seconds before sending, as to not cause issues with ctx.defer
        await ctx.send("**<@%d>, DMing the best appointment!**" % ctx.author.id, hidden=True)
        try:
            await ctx.author.send("**<@%d>, Here is the closest and most accessible appointment found**:" % ctx.author.id,
                              embed=best_appointment.format_to_embed())
        except discord.errors.Forbidden:
            await ctx.send("<@%d>, you've disabled DMs from server members, so no appointments can be sent. "
                       "Please enable this to use the bot." % ctx.author.id, hidden=True)

    except IndexError:
        await ctx.send("**Sorry <@%d> - no appointments were found near your postal code (%s)!**" %
                       (ctx.author.id, postal), hidden=True)
        return

@slash.slash(name="findall", description="Find all vaccine appointments nearby and send via DM", options=options)
async def findall(ctx, postal:str, dose: int, vaccine=None):
    if not (len(postal) == 3):
        await ctx.send("❗ <@%d>, please enter the *first 3 digits* of your postal code!" % ctx.author.id,
                    hidden=True)
        return
    await ctx.defer(hidden=True)

    client.useCounter += 1

    appointments_accessible = (await find_appointments(postal, dose, vaccine))[:10]

    if not appointments_accessible:
        await ctx.send("**Sorry <@%d> - no appointments were found near your postal code (%s)!**" %
                       (ctx.author.id, postal), delete_after=8.0, hidden=True)
        return

    await ctx.send("<@%d>, sending you available appointments via direct message!" % ctx.author.id, hidden=True)
    user = ctx.author
    try:
        await user.send("\U0001F537 Here's everything I've found for **%s**:" % postal)
        for appointment in appointments_accessible:
            await user.send(embed=appointment.format_to_embed())
    except discord.errors.Forbidden:
        await ctx.send("<@%d>, you've disabled DMs from server members, so no appointments can be sent. "
                 "Please enable this to use the bot." % ctx.author.id, hidden=True)

@client.event
async def on_slash_command_error(ctx, e):
    await ctx.send("‼ <@%d> **An error occured while trying to process your request. " 
             "Please try again. If this continues, please ping or message the developer and share the text below:**"
             % ctx.author.id, embed=discord.Embed(title="Error Details", description="```%s```" % repr(e)), hidden=True)

client.logUses.start()
client.run(keyring.get_password("VaxFinderDiscord", "BotToken"))
