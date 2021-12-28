import json
from finderbot.models import VaxAppointment

with open("finderbot/resources/logos.json", "r") as f:
    logo_data = f.read()
logos = json.loads(logo_data)

with open("finderbot/resources/colors.json", "r") as f:
    color_data = f.read()
colors = json.loads(color_data)

def get_logo_from_appointment(appointment: VaxAppointment):
    '''
    Finds the logo associated with a certain location name.
    :param name: The full name of a location.
    :return: A link to the logo, if found; otherwise, None
    '''
    if appointment.location.url == "https://covid19.ontariohealth.ca/":
        return "https://cdn.discordapp.com/attachments/756982558025056289/925248696919150662/4c39d441f2ff5aec306d9ce7494f2da4.png"

    if appointment.location.url.startswith("https://york.verto"):
        return "https://cdn.discordapp.com/attachments/756982558025056289/925513598825017394/YR_logo_og.png"

    name = appointment.location.name
    for logo in logos.keys():
        if logo in name.lower():
            return logos[logo]

def get_color_from_appointment(appointment: VaxAppointment):
    '''
        Finds the color associated with a certain location name.
        :param name: The full name of a location.
        :return: A hex color (string)
    '''
    if appointment.location.url == "https://covid19.ontariohealth.ca/":
        return "000000"

    if appointment.location.url.startswith("https://york.verto"):
        return "004fa6"

    name = appointment.location.name
    for color in colors.keys():
        if color in name.lower():
            return colors[color]