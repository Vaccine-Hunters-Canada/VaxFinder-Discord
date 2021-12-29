from finderbot.models import *
from finderbot.API.api import FinderAPI

import requests
import pgeocode
import os
import time
import datetime
import json

vaccineTypes = ["Pfizer", "Moderna", "J&J"]

class VaccineOntarioAPI(FinderAPI):
    def __init__(self, ratelimit=10):
        super().__init__(ratelimit)

    def _get_VO_clinics(self) -> list:
        try:
            os.mkdir("cache")
        except FileExistsError:
            pass

        cacheFile = None
        for fname in os.listdir("cache"):
            if fname.startswith("VO-"):
                cacheFile = fname

        if cacheFile:
            creationTime = int(cacheFile.split("VO-")[1])
            if time.time() - creationTime > 600:
                os.remove("cache/%s" % cacheFile)
            else:
                with open("cache/%s" % cacheFile, "r") as f:
                    return json.load(f)

        data = requests.get("https://firebasestorage.googleapis.com/v0/b/vaxhunterstoronto.appspot.com/o/clinics.json?alt=media").text
        clinics = json.loads(data)["clinics"]
        open_clinics = []
        for clinic in clinics:
            try:
                if clinic["slots_left"] != {}:
                    open_clinics.append(clinic)
                    continue
            except KeyError:
                pass
            try:
                if (clinic["walkin_times"] != []) and (clinic["walkin_times"] != {}):
                    open_clinics.append(clinic)
            except KeyError:
                pass


        with open("cache/VO-%d" % time.time(), "w") as f:
            json.dump(open_clinics, f, default=str)
        return open_clinics


    def _appointments_from_postal(self, postal: str, dose=1):
        gd = pgeocode.Nominatim("ca")
        postalData = gd.query_postal_code(postal)
        longitude, latitude = postalData.longitude, postalData.latitude
        distance = 12

        clinics = self._get_VO_clinics()
        nearbyClinics = []

        for clinic in clinics:
            try:
                clinic_coordinates = (clinic["location"]["lng"], clinic["location"]["lat"])
            except KeyError:
                clinic_coordinates = (0,0)

            if pgeocode.haversine_distance([(longitude, latitude)], [clinic_coordinates]) < distance:
                nearbyClinics.append(clinic)
            elif (postal in clinic["address"]):
                nearbyClinics.append(clinic)

        locatedAppointments = []
        for clinic in nearbyClinics:
            try:
                if dose != clinic["dose_number"]:
                    continue
            except KeyError:
                continue

            address = Region()
            address.province = "Ontario"
            clinicAddress = [address.lstrip() for address in clinic["address"].split(",")] # some addresses are seperated by commas, and not commas followed by a space -_-
            try:
                address.line1 = clinicAddress[0]
                address.city = clinicAddress[1]
                postalCode = None

                if (len(clinicAddress[-1]) == 7) or (len(clinicAddress[-1]) == 6):
                    if clinicAddress[-1] != "Ontario":
                        postalCode = clinicAddress[-1]
                elif len(clinicAddress[-1]) > 7: # province was thrown in
                     postalCode = " ".join(clinicAddress[-1].split(" ")[-2:])
                else: #it might just not be there
                    pass

                if postalCode:
                    address.postal = postalCode

            except IndexError:
                address.line1 = "Unknown"

            try:
                address.longitude = clinic["location"]["lng"]
                address.latitude = clinic["latitude"]["lat"]
            except KeyError:
                pass

            location = Location(clinic["name"], address)
            location.url = clinic["registration_link"]

            vaccines = []
            for vaccine in vaccineTypes:
                if vaccine in clinic["vaccineType"]:
                    vaccines.append(vaccine)

            requirements = []
            try:
                for requirement in clinic["eligibility"].split("; "):
                    requirements.append(Requirement(requirement, requirement))
            except AttributeError:
                pass

            dates = []
            amount_left = 1
            try:
                for date in clinic["slots_left"].keys():
                    formattedDate = datetime.datetime.strptime(date, "%Y-%m-%d")
                    if (formattedDate - datetime.datetime.now()).days >= -1:
                        dates.append(formattedDate)
                    amount_left += clinic["slots_left"][date]
            except KeyError:
                pass

            walkin_dates = {}
            try:
                for walkin_date in clinic["walkin_times"].keys():
                    formattedDate = datetime.datetime.strptime(walkin_date, "%Y-%m-%d")
                    if (formattedDate - datetime.datetime.now()).days >= -1:
                        walkin_dates[formattedDate] = clinic["walkin_times"][walkin_date]
            except (KeyError, AttributeError):
                pass

            if not walkin_dates:
                walkin_dates = None

            appointment = VaxAppointment(location, requirements, vaccines, amount_left, sorted(dates), [dose], walkin_dates)
            locatedAppointments.append(appointment)

        return locatedAppointments

