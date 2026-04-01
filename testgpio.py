
from gpiozero import LED
from gpiozero.pins.lgpio import LGPIOFactory

factory = LGPIOFactory()
gpio8 = LED(17, pin_factory=factory)
