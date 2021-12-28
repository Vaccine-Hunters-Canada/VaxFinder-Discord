from dataclasses import dataclass
from typing import List, Optional, Dict
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
    longitude: float = 0.0
    latitude: float = 0.0

@dataclass
class Location:
    name: str
    address: Region
    phone: str = ""
    url: str = ""


class VaxAppointment():

    def __init__(self, location: Location, requirements: List[Requirement], vaccines: List[str], amount: int,
                 dates: List[datetime.datetime], doses=[1], walkinDates: Optional[Dict[datetime.datetime, str]]=None):
        self.location = location
        self.requirements = requirements
        self.vaccines = vaccines
        self.amount = amount
        self.dates = dates
        self.walkinDates = walkinDates
        self.doses = doses
        #self.vaccinecodes = {1: "Unknown", 3: "Pfizer", 4: "Moderna", 5: "AstraZeneca"}

    def __eq__(self, other):
        if not isinstance(other, VaxAppointment):
            raise ValueError("Can't compare non-VaxAppointment classes")

        return self.__dict__ == other.__dict__


    def format_to_embed(self):
        color = tools.get_color_from_appointment(self)
        if color:
            embed_color = int(color, 16)
        else:
            embed_color = int("ffffff", 16)
        embed = Embed(title=self.location.name, color=embed_color)
        embed.description = "**Vaccines**\U0001F489: %s\n" % ",".join(self.vaccines)
        embed.description += "**Reported vaccines available (may not be accurate):** %d\n" % (self.amount)
        embed.description += "**Dose #s available:** %s\n" % ", ".join([str(dosenum) for dosenum in self.doses])
        if self.requirements:
            embed.description += "**Eligibility Requirements:\n**"
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

        if self.walkinDates:
            embed.description += "*This location allows walk-ins*\n"

        if self.dates:
            embed.description += "Dates available: %s\n\n" % "; ".join([date.strftime("%Y-%m-%d") for date in self.dates])
        if self.walkinDates:
            embed.description += "Times available for walk-ins: \n%s\n\n" % " \n".join(
                ["%s: *%s*" % (date.strftime("%Y-%m-%d"), self.walkinDates[date]) for date in self.walkinDates.keys()])

        if self.location.phone:
            embed.description += "**Call**: %s\n" % self.location.phone
        if self.location.url:
            embed.description += "**Booking URL**: %s" % self.location.url

        img = tools.get_logo_from_appointment(self)
        if img:
            embed.set_thumbnail(url=img)

        footer = "This information is gathered both automatically and via volunteers and is not " \
                 "guaranteed to be accurate. Please verify yourself via the provided booking options to " \
                 "ensure these appointments are available to you and requirements are correct."
        if self.location.address.province.lower() == "ontario":
            footer += "\nBe sure to check out the provincial booking site as well: https://vaccine.covaxonbooking.ca/"
        elif self.location.address.province.lower() == "alberta":
            footer += "\nBe sure to check out the provincial booking site: " \
                      "https://www.albertahealthservices.ca/topics/page17295.aspx."
        embed.set_footer(text=footer)


        return embed

