from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import threading
import RPi.GPIO as GPIO
import Adafruit_DHT

app = FastAPI()

class SensorData(BaseModel):
    temperature: float
    humidity: float

@app.get("/api/sensors", response_model=SensorData)
async def get_sensors():
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)
    return {"temperature": temperature, "humidity": humidity}

@app.post("/api/relay/control")
async def control_relay(state: str):
    threading.Thread(target=control_relay_thread, args=(state,)).start()
    return {"status": f"Relay turned {state}"}

def init_relay():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)

def control_relay_thread(state):
    GPIO.output(18, GPIO.HIGH if state == "on" else GPIO.LOW)

async def poll_sensors():
    while True:
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, 4)
        print(f"Temperature: {temperature}°C, Humidity: {humidity}%")
        await asyncio.sleep(5)

def main():
    init_relay()
    asyncio.create_task(poll_sensors())
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())

if __name__ == "__main__":
    main()