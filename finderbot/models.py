from dataclasses import dataclass
from typing import List
from discord import Embed

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

    def __init__(self, location: Location, requirements: List[Requirement], vaccine: int, amount: int):
        self.location = location
        self.requirements = requirements
        self.vaccine = vaccine
        self.amount = amount
        self.vaccinecodes = {1: "Pfizer", 2: "Moderna"}

    def format_to_embed(self):
        embed = Embed(title=self.location.name)
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

        if self.location.phone:
            embed.description += "**Call**: %s\n" % self.location.phone
        if self.location.url:
            embed.description += "**Booking URL**: %s" % self.location.url

        return embed

