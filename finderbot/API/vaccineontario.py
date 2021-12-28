from finderbot.models import *
from finderbot.API.api import FinderAPI

from google.cloud import firestore
from google.oauth2 import service_account
import keyring
import pgeocode
import os
import time
import json

vaccineTypes = ["Pfizer", "Moderna", "J&J"]

class VaccineOntarioAPI(FinderAPI):
    def __init__(self, ratelimit=10):
        super().__init__(ratelimit)
        credentials = service_account.Credentials.from_service_account_file(keyring.get_password("VaxFinderDiscord", "VOKeyfile"))
        self._database = firestore.Client(credentials=credentials)

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

        clinics_slot_ref = self._database.collection(u"clinic").where("slots_left", "!=", {})
        clinics_slot = [clinic.to_dict() for clinic in clinics_slot_ref.stream()]

        clinics_walkin_ref = self._database.collection(u"clinic").where("walkin_times", "!=", [])
        clinics_walkin = [clinic.to_dict() for clinic in clinics_walkin_ref.stream()]


        clinics = clinics_slot
        for clinic in clinics_walkin:
            if clinic not in clinics_slot:
                clinics.append(clinic)

        with open("cache/VO-%d" % time.time(), "w") as f:
            json.dump(clinics, f, default=str)
        return clinics


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
            clinicAddress = clinic["address"].split(", ")
            address.line1 = clinicAddress[0]
            address.city = clinicAddress[1]
            postal = " ".join(clinicAddress[-1].split(" ")[1:])
            if postal:
                address.postal = postal
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
                    dates.append(datetime.datetime.strptime(date, "%Y-%m-%d"))
                    amount_left += clinic["slots_left"][date]
            except KeyError:
                pass

            walkin_dates = {}
            try:
                for walkin_date in clinic["walkin_times"].keys():
                    formattedDate = datetime.datetime.strptime(walkin_date, "%Y-%m-%d")
                    walkin_dates[formattedDate] = clinic["walkin_times"][walkin_date]
            except (KeyError, AttributeError):
                pass

            if not walkin_dates:
                walkin_dates = None

            appointment = VaxAppointment(location, requirements, vaccines, amount_left, sorted(dates), [dose], walkin_dates)
            locatedAppointments.append(appointment)

        return locatedAppointments

