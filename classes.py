import threading
from enum import Enum
from pydantic import BaseModel
import time

class SensorExchange:
    def __init__(self):
        self._temperature_value = 0
        self._temperature_status = SensorStatus.FAULTY
        self._temperature_timestamp = time.time()
        self._temperature_lock = threading.Lock()

    def update_temperature(self, new_temperature, status):
        with self._temperature_lock:
            self._temperature_value = new_temperature
            self._temperature_status = status
            if status == SensorStatus.WORKING:
                self._temperature_timestamp = time.time()

    def get_temperature(self):
        with self._temperature_lock:
            return self._temperature_value, self._temperature_status, self._temperature_timestamp

class SensorStatus(str, Enum):
    WORKING = "working"
    FAULTY = "faulty"

class SensorData(BaseModel):
    temperature: float
    status: SensorStatus
    timestamp: float

class InverterData(BaseModel):
    rpm: float
    max_torque: float
