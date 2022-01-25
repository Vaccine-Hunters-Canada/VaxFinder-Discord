import requests
import json

from finderbot.models import *
from finderbot.API.api import FinderAPI


vaccines = ["Pfizer", "Moderna", "AstraZeneca"]


class VaxFinderAPI(FinderAPI):
    def __init__(self, ratelimit=10):
        super().__init__(ratelimit)

    def _appointments_from_postal(self, postal: str, dose=1, vaccine=None):
        '''
        Finds appointments, using the VaxFinder API, near a postal code.
        :param postal: The first 3 letters of a postal code as a string.
        :return: A list of VaxAppointments, or None if none are found
        '''
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        r = requests.get("https://vax-availability-api.azurewebsites.net/api/v1/vaccine-locations"
                            "?postal_code=%s&include_empty=false&min_date=%s" % (postal, today))
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
                doses = [1]
                vaccineType = ["Unknown"]
                if availability["tags"]:
                    tags = availability["tags"].split(',')
                    if "2nd Dose" in tags:
                        doses.append(2)
                    if "3rd Dose" in tags:
                        doses.append(3)

                    for vax in vaccines:
                        if vax in tags:
                            vaccineType = [vax]

                    if dose not in doses:
                        continue
                    if vaccine:
                        if vaccineType != [vaccine]:
                            continue

                requirements = []
                reqdata = availability["requirements"]
                for requirement in reqdata:
                    requirements.append(Requirement(requirement["name"], requirement["description"]))

                amount = availability["numberTotal"]
                date = datetime.datetime.strptime(availability["date"].split("T")[0], "%Y-%m-%d")

                # Check if this same appointment exists with another date - if so, just add the date to that
                seen = False
                for idx, appointment in enumerate(vaxappointments):
                    if (appointment.requirements == requirements) and (appointment.location == loc):
                        nappointment = appointment
                        nappointment.dates.append(date)
                        vaxappointments[idx] = nappointment
                        vaxappointments[idx].amount += amount
                        seen = True

                if not seen:
                    vaxappointments.append(VaxAppointment(loc, requirements, vaccineType, amount, [date], doses))

        return vaxappointments if vaxappointments else None