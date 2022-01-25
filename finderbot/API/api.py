from finderbot.models import *
import time
from typing import Optional, List

class FinderAPI():
    def __init__(self, ratelimit=10):
        self.ratelimit = ratelimit
        self._executionCounter = 0
        self._startTime = time.time()

    def _appointments_from_postal(self, postal: str, dose=1, vaccine=None):
        raise NotImplementedError

    def get_appointments_from_postal(self, postal: str, dose=1, vaccine=None) -> Optional[List[VaxAppointment]]:
        if (time.time() - self._startTime) >= 1:
            self._startTime = time.time()
            self._executionCounter = 0
        else:
            self._executionCounter += 1

        if self._executionCounter == self.ratelimit:
            time.sleep(1)

        return self._appointments_from_postal(postal, dose, vaccine)