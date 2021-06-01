from dataclasses import dataclass
from typing import List
from discord import Embed
import datetime

from finderbot import tools

@dataclass
class Requirement:
    name: str
    description: str

@dataclass
class Region:
    line1: str = ""
    line2: str = ""
    city: str = ""
    province: str = ""
    postal: str = ""

@dataclass
class Location:
    name: str
    address: Region
    phone: str = ""
    url: str = ""


class VaxAppointment():

    def __init__(self, location: Location, requirements: List[Requirement], vaccine: int, amount: int,
                 dates: List[datetime.datetime]):
        self.location = location
        self.requirements = requirements
        self.vaccine = vaccine
        self.amount = amount
        self.dates = dates
        self.vaccinecodes = {1: "Unknown", 3: "Pfizer", 4: "Moderna", 5: "AstraZeneca"}

    def __eq__(self, other):
        if not isinstance(other, VaxAppointment):
            raise ValueError("Can't compare non-VaxAppointment classes")

        return self.__dict__ == other.__dict__


    def format_to_embed(self):
        color = tools.get_color_from_name(self.location.name)
        if color:
            embed_color = int(color, 16)
        else:
            embed_color = 0
        embed = Embed(title=self.location.name, color=embed_color)
        embed.description = "**Vaccine**\U0001F489: %s\n" % self.vaccinecodes[self.vaccine]
        embed.description += "**Reported vaccines available (may not be accurate):** %d\n" % (self.amount)
        if self.requirements:
            embed.description += "**You may need to be:\n**"
            requirements = ["    -%s\n" % requirement.description for requirement in self.requirements]
            for requirement in requirements:
                embed.description += requirement
            embed.description += '\n'

        embed.description += "**Address**:\n"
        address = self.location.address
        if address.line1:
            embed.description += address.line1 + "\n"
        if address.line2:
            embed.description += address.line2 + "\n"
        if address.city:
            embed.description += address.city + "\n"
        if address.province:
            embed.description += address.province + "\n"
        if address.postal:
            embed.description += address.postal + "\n\n"

        embed.description += "Dates available: %s\n\n" % "; ".join([date.strftime("%Y-%m-%d") for date in self.dates])

        if self.location.phone:
            embed.description += "**Call**: %s\n" % self.location.phone
        if self.location.url:
            embed.description += "**Booking URL**: %s" % self.location.url

        img = tools.get_logo_from_name(self.location.name)
        if img:
            embed.set_thumbnail(url=img)


        embed.set_footer(text="This information is gathered both automatically and via volunteers and is not "
                                "guaranteed to be accurate. Please verify yourself via the provided booking options to "
                                "ensure these appointments are available to you and requirements are accurate.")


        return embed

