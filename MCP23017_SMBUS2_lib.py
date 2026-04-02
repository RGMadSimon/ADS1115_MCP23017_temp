from smbus2 import SMBus
from MCP23017 import*
import time

class MCP23017_SMBUS2_conn():
    def __init__(self, bus):
        self.mcp23017_device_addr = 0x20
        # Initialize I2C bus
        self.bus = bus
        # Define config (IOCON) register content
        self.iocon = MCP23017_SMBUS2_conn.compose_iocon_register(bank=0, sequential_op=1)
        # Store desired GPIO direction and output value
        self.gpio_dir = 0xff
        self.gpio_out = 0
        # Define timeout variable
        self.timeout = 0.2
        # Alarms / diagnostic
        self.I2C_alarm = False
        self.last_error = None

    # Write IOCON (config) register
    def write_conf(self):
        write_ok = self.write_and_check(MCP23017_IOCON_ADDR, self.iocon)
        return write_ok

    # Write I/O direction register
    def write_io_direction(self, direction_byte):
        self.gpio_dir = direction_byte
        write_ok = self.write_and_check(MCP23017_IODIRA_ADDR, self.gpio_dir)
        return write_ok
    
    # Write GPIO
    def write_gpio(self, gpio_out_byte):
        self.gpio_out = gpio_out_byte
        write_ok = self.write_and_check(MCP23017_GPIOA_ADDR, self.gpio_out)
        return write_ok

    # Read GPIO
    def read_gpio(self):
        return self.read_and_check(MCP23017_GPIOA_ADDR)
    
    # general "write-and-check register" function
    def write_and_check(self, reg_address, to_write):
        time_started = time.time()
        try:
            while time.time() - time_started < self.timeout:
                try:
                    self.bus.write_byte_data(self.mcp23017_device_addr, reg_address, to_write)
                    to_check = self.bus.read_byte_data(self.mcp23017_device_addr, reg_address)
                except Exception as e:
                    continue
                if to_check == to_write:
                    self.I2C_alarm = False
                    return True
            raise RuntimeError("I2C - MCP23017 - register write failed")
        except Exception as e:
            return self.report_bug_and_close(e)
        #print('I2C timeout')
        #self.I2C_alarm = True
        #return False
    
    # general "read and check for timeouts" function
    def read_and_check(self, reg_address):
        time_started = time.time()
        while time.time() - time_started < self.timeout:
            try:
                data_read = self.bus.read_byte_data(self.mcp23017_device_addr, reg_address)
            except Exception as e:
                continue
            self.I2C_alarm = False
            return True, data_read
        print('I2C timeout (MCP23017)')
        self.I2C_alarm = True
        return False, 0x00

    # Compose config register (IOCON) content
    def compose_iocon_register(bank = 0, sequential_op = 1):
        return (bank << 7) | (sequential_op << 5)

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