from smbus2 import SMBus
from ADS1115 import*
import time

class ADS1115_SMBUS2_conn():
    def __init__(self, bus):
        self.ads1115_addr = 0x49
        self.chan = 0
        # Initialize I2C bus
        self.bus = bus
        # Define config register content
        self.conf = 0
        # Define timeout variable
        self.time_last_config_set = 0
        self.conversion_timeout = 0.5
        self.i2c_timeout = 0.5
        # Alarms / diagnostic
        self.I2C_alarm = False
        self.last_error = None
        # Store last conversion
        self.last_read = 0
        self.last_read_timestamp = 0

    def set_config_register(self, mux_select, prog_gain, data_rate):
        config_register = (0x1 << 15) | (mux_select << 12) | (prog_gain << 9) | (adcSingleShotConversion << 8) | (data_rate << 5) | (adcComparatorOff)
        self.conf = config_register
    
    def get_reading(self):
        return self.last_read, self.I2C_alarm, self.last_read_timestamp

    # Write config register
    def write_conf(self):
        if self.bus is None:
            return False
        f_send = flip_msb_lsb(self.conf)
        try:
            self.bus.write_word_data(self.ads1115_addr, config_register_address, f_send)
            self.time_last_config_set = time.time()
            self.I2C_alarm = False
            return True
        except Exception as e:
            return self.report_bug_and_close(e)

    def double_check_config(self):
        if self.bus is None:
            return False
        try:
            data_read = self.bus.read_word_data(self.ads1115_addr, config_register_address)
            f_read = flip_msb_lsb(data_read) | 0x8000  # force OS bit high (it will be zero because conversion not done)
            self.I2C_alarm = not (f_read == self.conf)
            return f_read == self.conf
        except Exception as e:
            return self.report_bug_and_close(e)

    def wait_conversion_ready(self):
        if self.bus is None:
            return False
        try:
            while time.time() - self.time_last_config_set < self.conversion_timeout:
                try:
                    data_read = self.bus.read_word_data(self.ads1115_addr, config_register_address)
                except Exception as e:
                    return self.report_bug_and_close(e)
                f_read = flip_msb_lsb(data_read)
                os_bit = (f_read & 0x8000) >> 15
                if os_bit:
                    self.I2C_alarm = False
                    return True
            raise RuntimeError("I2C - ADS1115 - conversion time out")
        except Exception as e:
            return self.report_bug_and_close(e)

    def read_conversion_result(self):
        if self.bus is None:
            return False
        try:
            data_read = self.bus.read_word_data(self.ads1115_addr, conversion_register_address)
            f_read = flip_msb_lsb(data_read) / 32768
            self.last_read = f_read * 4.096
            self.last_read_timestamp = time.time()
            self.I2C_alarm = False
            return self.last_read
        except Exception as e:
            return self.report_bug_and_close(e)

    def report_bug_and_close(self, e):
        # Report I2C fault of this sensor
        self.I2C_alarm = True
        # Print if not repetitive
        if e.args != self.last_error:
            print(f"Error: {e}")
        self.last_error = e.args
        if self.bus is not None:
            if hasattr(self.bus, 'fileno'):  # Check if the bus has a fileno() method
                self.bus.close()
                self.bus = None
        return False

def main():
    while(True):

        conn_to_adc = ADS1115_SMBUS2_conn()
        conn_to_adc.set_config_register(adcMuxSelectAN0, adcPlusMinus4Volts, adcDataRate16sps)

        try:
            # Write config register
            conn_to_adc.write_conf()

            # Make sure ADS1115 received correct config
            if not conn_to_adc.double_check_config():
                continue

            # wait for conversion to be ready
            conn_to_adc.wait_conversion_ready()

            # Read a byte from the specified register
            analog_input_0 = conn_to_adc.read_conversion_result()
            print("   AN0: " + str(analog_input_0))

        except Exception as e:
            print(f"Error: {e}")



if __name__ == "__main__":
    main()