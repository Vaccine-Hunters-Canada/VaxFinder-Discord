import json

with open("finderbot/resources/logos.json", "r") as f:
    logo_data = f.read()
logos = json.loads(logo_data)

with open("finderbot/resources/colors.json", "r") as f:
    color_data = f.read()
colors = json.loads(color_data)

def get_logo_from_name(name: str):
    '''
    Finds the logo associated with a certain location name.
    :param name: The full name of a location.
    :return: A link to the logo, if found; otherwise, None
    '''
    for logo in logos.keys():
        if logo in name.lower():
            return logos[logo]

def get_color_from_name(name: str):
    '''
        Finds the color associated with a certain location name.
        :param name: The full name of a location.
        :return: A hex color (string)
    '''
    for color in colors.keys():
        if color in name.lower():
            return colors[color]