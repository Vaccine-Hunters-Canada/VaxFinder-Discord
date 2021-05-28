import requests
import json
from finderbot.models import *

def get_appointments_from_postal(postal: str, dose=1):
    '''
    Finds appointments, using the VaxFinder API, near a postal code.
    :param postal: The first 3 letters of a postal code as a string.
    :return: A list of VaxAppointments, or None if none are found
    '''
    r = requests.get("https://vax-availability-api.azurewebsites.net/api/v1/vaccine-locations"
                        "?postal_code=%s&include_empty=false" % postal)
    appointments = json.loads(r.text)
    vaxappointments = []
    for appointment in appointments:
        address = Region()
        addressdata = appointment["address"]
        if addressdata["line1"]:
            address.line1 = addressdata["line1"]
        if addressdata["line2"]:
            address.line2 = addressdata["line2"]
        if addressdata["city"]:
            address.city = addressdata["city"]
        if addressdata["province"]:
            address.province = addressdata["province"]
        if addressdata["postcode"]:
            address.postal = addressdata["postcode"]

        loc = Location(appointment["name"], address)
        if appointment["phone"]:
            loc.phone = appointment["phone"]
        if appointment["url"]:
            loc.url = appointment["url"]

        for availability in appointment["vaccineAvailabilities"]:
            if availability["tags"]:
                print(availability["tags"])
                tags = availability["tags"].split(',')
                if "dose2" in tags:
                    if dose == 1:
                        continue
                else:
                    if dose == 2:
                        continue
            else:
                if dose == 2:
                    continue
            requirements = []
            reqdata = availability["requirements"]
            for requirement in reqdata:
                requirements.append(Requirement(requirement["name"], requirement["description"]))

            vaccine = availability["vaccine"]
            amount = availability["numberTotal"]
            vaxappointments.append(VaxAppointment(loc, requirements, vaccine, amount))

    return vaxappointments if vaxappointments else None