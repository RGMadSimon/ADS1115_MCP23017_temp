from fastapi import FastAPI
from pydantic import BaseModel
from ADS1115_SMBUS2_lib import*
from MCP23017_SMBUS2_lib import*
from classes import*
import asyncio
import threading
import uvicorn
from enum import Enum

app = FastAPI()
sens_exchange = SensorExchange()

@app.post("/api/motor/control")
async def control_motor(motor_data: InverterData):
    print('RPM ' + str(motor_data.rpm))
    return {"RPM": f" {motor_data.rpm}", "maxtorque": f" {motor_data.max_torque}"}

@app.get("/")
async def root():
    return {"message": "Temperature at /api/sensors"}

@app.get("/api/sensors", response_model=SensorData)
async def get_sensors():
    temperature, status, timestamp = sens_exchange.get_temperature()
    #status = SensorStatus.WORKING
    return {"temperature": temperature, "status": status, "timestamp": timestamp}

@app.post("/api/relay/control")
async def control_relay(state: bool):
    threading.Thread(target=relay_set_state, args=(state,)).start()
    return {"status": f"Relay turned {state}"}

def I2C_thread(exchange):
    # Create SMBUS bus object
    i2c_bus = SMBus(1)
    conn_to_adc = ADS1115_SMBUS2_conn(i2c_bus)
    # Set channel, Voltage input range, samples/second
    conn_to_adc.set_config_register(adcMuxSelectAN0, adcPlusMinus4Volts, adcDataRate16sps)
    #initialize analog read for storing in case of error
    analog_input_0 = 0
    # Sensor polling
    while(True):
        try:
            # Write config register
            conn_to_adc.write_conf()
            # Make sure ADS1115 received correct config (read it)
            if not conn_to_adc.double_check_config():
                continue
            # wait (polling read cycle) for conversion to be ready
            conn_to_adc.wait_conversion_ready()
            # Read a byte from the specified register
            analog_input_0 = conn_to_adc.read_conversion_result()
            exchange.update_temperature(analog_input_0, SensorStatus.FAULTY if conn_to_adc.I2C_alarm else SensorStatus.WORKING)
            #print("   AN0: " + str(exchange.get_temperature()))
        except Exception as e:
            exchange.update_temperature(analog_input_0, SensorStatus.FAULTY)
            print(f"Error: {e}")

def I2C_thread2(exchange):
    # Create SMBUS bus object
    i2c_bus = SMBus(1)
    # Create I2C GPIO object
    i2c_gpio = MCP23017_SMBUS2_conn(i2c_bus)
    # I2C main loop
    while True:
        # Write config register (IOCON)
        if not i2c_gpio.write_conf():
            continue
        # Write i/o direction register
        if not i2c_gpio.write_io_direction(0x00):
            continue
        while(True):
            if not i2c_gpio.write_gpio(0xff):
                break
            time.sleep(0.5)
            if not i2c_gpio.write_gpio(0x00):
                break
            time.sleep(0.5)

def relay_set_state(cmd):
    if cmd:
        print('relay on')
    else:
        print('relay off')
    #print('relay state: ' + cmd)

def main():
    i2c_thread = threading.Thread(target=I2C_thread2, kwargs={"exchange": sens_exchange})
    i2c_thread.start()

    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())

if __name__ == '__main__':
    main()
